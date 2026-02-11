"""
LLM Provider Implementations

This module implements the abstract LLMProvider interface and concrete
implementations for different LLM services (OpenAI, Anthropic, Gemini).

The providers handle:
- API communication with LLM services
- Request/response formatting
- Error handling and retries
- Rate limiting and cost tracking
- Enhanced formatting for legal responses
- Intent-specific response optimization
"""

import json
import time
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

# Optional imports for LLM providers
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from query_engine.context_builder import LLMContext


logger = logging.getLogger(__name__)


class LLMProviderType(Enum):
    """Supported LLM provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


@dataclass
class LLMResponse:
    """Response from LLM provider"""
    content: str
    provider: str
    model: str
    usage: Dict[str, Any]
    response_time: float
    confidence: Optional[float] = None
    finish_reason: Optional[str] = None
    
    def get_token_count(self) -> int:
        """Get total token count from usage"""
        return self.usage.get('total_tokens', 0)
    
    def get_cost_estimate(self) -> float:
        """Get estimated cost in USD"""
        # Basic cost estimation - should be updated with current pricing
        if self.provider == "openai":
            if "gpt-4" in self.model:
                input_tokens = self.usage.get('prompt_tokens', 0)
                output_tokens = self.usage.get('completion_tokens', 0)
                # GPT-4 pricing (approximate)
                return (input_tokens * 0.00003) + (output_tokens * 0.00006)
        elif self.provider == "gemini":
            # Gemini Pro pricing (approximate)
            input_tokens = self.usage.get('prompt_tokens', 0)
            output_tokens = self.usage.get('completion_tokens', 0)
            return (input_tokens * 0.000125) + (output_tokens * 0.000375)
        return 0.0


class LLMError(Exception):
    """Base exception for LLM provider errors"""
    
    def __init__(self, message: str, provider: str, error_type: str = "unknown"):
        super().__init__(message)
        self.provider = provider
        self.error_type = error_type


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Initialize LLM provider.
        
        Args:
            api_key: API key for the provider
            model: Model name to use
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
    
    @abstractmethod
    def generate_response(self, prompt: str, context: LLMContext,
                         constraints: Dict[str, Any]) -> LLMResponse:
        """
        Generate response with graph-constrained prompt.
        
        Args:
            prompt: User prompt/query
            context: Structured context from knowledge graph
            constraints: Citation and formatting constraints
            
        Returns:
            LLMResponse with generated content and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this provider."""
        return {
            'provider': self.__class__.__name__,
            'model': self.model,
            'request_count': self.request_count,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'avg_tokens_per_request': self.total_tokens / max(1, self.request_count)
        }


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4)
            **kwargs: Additional OpenAI configuration
        """
        super().__init__(api_key, model, **kwargs)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=api_key)
        
        # Configuration
        self.temperature = kwargs.get('temperature', 0.1)  # Low temperature for legal accuracy
        self.max_tokens = kwargs.get('max_tokens', 2000)
        self.timeout = kwargs.get('timeout', 30)
        
        logger.info(f"Initialized OpenAI provider with model: {model}")
    
    def generate_response(self, prompt: str, context: LLMContext,
                         constraints: Dict[str, Any]) -> LLMResponse:
        """
        Generate response using OpenAI GPT-4.
        
        Args:
            prompt: User prompt/query
            context: Structured context from knowledge graph
            constraints: Citation and formatting constraints
            
        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.time()
        
        try:
            # Build system message with constraints
            system_message = self._build_system_message(constraints)
            
            # Build user message with context
            user_message = self._build_user_message(prompt, context, constraints)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            # Extract response data
            content = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            response_time = time.time() - start_time
            
            # Update statistics
            self.request_count += 1
            self.total_tokens += usage['total_tokens']
            
            # Create response object
            llm_response = LLMResponse(
                content=content,
                provider="openai",
                model=self.model,
                usage=usage,
                response_time=response_time,
                finish_reason=response.choices[0].finish_reason
            )
            
            # Update cost tracking
            self.total_cost += llm_response.get_cost_estimate()
            
            logger.info(f"OpenAI response generated in {response_time:.2f}s, "
                       f"tokens: {usage['total_tokens']}")
            
            return llm_response
            
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMError(f"Rate limit exceeded: {e}", "openai", "rate_limit")
        
        except openai.APITimeoutError as e:
            logger.error(f"OpenAI API timeout: {e}")
            raise LLMError(f"API timeout: {e}", "openai", "timeout")
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"API error: {e}", "openai", "api_error")
        
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider: {e}")
            raise LLMError(f"Unexpected error: {e}", "openai", "unknown")
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available and configured."""
        if not OPENAI_AVAILABLE:
            return False
        
        if not self.api_key:
            return False
        
        try:
            # Test API connection with a minimal request
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI provider not available: {e}")
            return False
    
    def _build_system_message(self, constraints: Dict[str, Any]) -> str:
        """Build system message with citation constraints."""
        
        audience = constraints.get('audience', 'citizen')
        citation_format = constraints.get('citation_format', 'standard')
        query_intent = constraints.get('intent_type', 'general')
        
        # Enhanced system message with intent-specific instructions
        system_message = f"""You are Nyayamrit, an AI legal assistant for Indian law. Your role is to provide accurate legal information grounded in authoritative sources.

CRITICAL RULES:
1. ONLY use information from the provided legal context
2. CITE every legal claim using [Citation: Section X] format
3. If information is not in context, respond: "Information not available in current knowledge base"
4. Distinguish between legal text (in quotes) and your explanation
5. Use language appropriate for {audience} audience
6. Include disclaimers that this is information, not legal advice
7. DEDUPLICATE citations - avoid repeating the same section number

INTENT-SPECIFIC FORMATTING:

{self._get_intent_specific_instructions(query_intent, audience)}

RESPONSE STRUCTURE:
- Brief, direct answer to the question
- Relevant legal text (quoted with citations)
- Clear explanation in simple language
- Practical guidance where appropriate
- All citations must reference provided context
- End with appropriate disclaimer

AUDIENCE: {audience.upper()}
- If citizen: Use simple, accessible language with step-by-step guidance
- If lawyer: Include technical details and cross-references  
- If judge: Add legal analysis and precedent context

CITATION FORMAT: {citation_format}
- Standard: [Citation: Section X]
- Detailed: [Citation: Section X, Clause Y of Act Name]
- Bluebook: Follow Bluebook citation format

CITATION DEDUPLICATION: Always remove duplicate section references in your citation list.

Remember: You are providing information only, not legal advice or binding determinations."""
        
        return system_message
    
    def _get_intent_specific_instructions(self, intent_type: str, audience: str) -> str:
        """Get intent-specific formatting instructions."""
        
        if intent_type == "rights_query":
            return """
RIGHTS QUERY FORMATTING:
- Start with "As a consumer under the Consumer Protection Act, 2019, you have the following rights:"
- List all six fundamental consumer rights explicitly:
  1. Right to safety (protection against hazardous goods)
  2. Right to be informed (complete product information)
  3. Right to choose (access to variety of goods at competitive prices)
  4. Right to be heard (representation in consumer forums)
  5. Right to seek redressal (compensation for defective goods/services)
  6. Right to consumer education (awareness of rights and remedies)
- Anchor all rights to Section 2(9) of the Consumer Protection Act, 2019
- Include enforcement mechanisms and complaint procedures
- Provide practical guidance on exercising these rights"""
        
        elif intent_type == "scenario_analysis":
            return """
SCENARIO ANALYSIS FORMATTING:
- Provide a clear procedural checklist
- Include specific steps: "You may file a complaint before the District Commission within 2 years"
- List required documents: "attach invoice, proof of defect"
- Specify available remedies: "seek refund/replacement/compensation"
- Include time limits and jurisdictional requirements
- Focus on practical actionable steps rather than abstract legal principles
- Do NOT evaluate definition accuracy - focus on procedural guidance"""
        
        elif intent_type == "definition_lookup":
            return """
DEFINITION FORMATTING:
- Provide the exact legal definition in quotes
- Include the defining section reference
- Explain the definition in simple terms
- Give practical examples where helpful
- Ensure definition accuracy is paramount"""
        
        elif intent_type == "section_retrieval":
            return """
SECTION RETRIEVAL FORMATTING:
- Quote the complete section text
- Provide clear explanation of what the section means
- Include related provisions if relevant
- Explain practical implications"""
        
        return ""
    
    def _build_user_message(self, prompt: str, context: LLMContext, 
                           constraints: Dict[str, Any]) -> str:
        """Build user message with context and query."""
        
        # Enhanced context formatting with deduplication
        formatted_citations = self._format_citations_deduplicated(context.citations)
        
        user_message = f"""LEGAL CONTEXT:
{context.formatted_text}

AVAILABLE CITATIONS (DEDUPLICATED):
{formatted_citations}

USER QUERY:
{prompt}

QUERY INTENT: {constraints.get('intent_type', 'general')}

Please provide a response following the rules above. Ensure all legal claims are supported by citations from the provided context. Remember to deduplicate any repeated section references in your response."""
        
        return user_message
    
    def _format_citations_deduplicated(self, citations: Dict[str, str]) -> str:
        """Format available citations with deduplication."""
        if not citations:
            return "No citations available"
        
        # Deduplicate citations by section number
        seen_sections = set()
        deduplicated_citations = {}
        
        for key, citation in citations.items():
            # Extract section number for deduplication
            section_match = re.search(r'Section (\d+)', citation)
            if section_match:
                section_num = section_match.group(1)
                if section_num not in seen_sections:
                    seen_sections.add(section_num)
                    deduplicated_citations[key] = citation
            else:
                # Keep non-section citations as-is
                deduplicated_citations[key] = citation
        
        formatted = []
        for key, citation in deduplicated_citations.items():
            formatted.append(f"{key}: {citation}")
        
        return "\n".join(formatted)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-3-sonnet)
            **kwargs: Additional Anthropic configuration
        """
        super().__init__(api_key, model, **kwargs)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Configuration
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 2000)
        self.timeout = kwargs.get('timeout', 30)
        
        logger.info(f"Initialized Anthropic provider with model: {model}")
    
    def generate_response(self, prompt: str, context: LLMContext,
                         constraints: Dict[str, Any]) -> LLMResponse:
        """
        Generate response using Anthropic Claude.
        
        Args:
            prompt: User prompt/query
            context: Structured context from knowledge graph
            constraints: Citation and formatting constraints
            
        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.time()
        
        try:
            # Build system message
            system_message = self._build_system_message(constraints)
            
            # Build user message
            user_message = self._build_user_message(prompt, context, constraints)
            
            # Make API call
            response = self.client.messages.create(
                model=self.model,
                system=system_message,
                messages=[{"role": "user", "content": user_message}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract response data
            content = response.content[0].text
            usage = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            response_time = time.time() - start_time
            
            # Update statistics
            self.request_count += 1
            self.total_tokens += usage['total_tokens']
            
            # Create response object
            llm_response = LLMResponse(
                content=content,
                provider="anthropic",
                model=self.model,
                usage=usage,
                response_time=response_time,
                finish_reason=response.stop_reason
            )
            
            logger.info(f"Anthropic response generated in {response_time:.2f}s, "
                       f"tokens: {usage['total_tokens']}")
            
            return llm_response
            
        except anthropic.RateLimitError as e:
            logger.error(f"Anthropic rate limit exceeded: {e}")
            raise LLMError(f"Rate limit exceeded: {e}", "anthropic", "rate_limit")
        
        except anthropic.APITimeoutError as e:
            logger.error(f"Anthropic API timeout: {e}")
            raise LLMError(f"API timeout: {e}", "anthropic", "timeout")
        
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMError(f"API error: {e}", "anthropic", "api_error")
        
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic provider: {e}")
            raise LLMError(f"Unexpected error: {e}", "anthropic", "unknown")
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available and configured."""
        if not ANTHROPIC_AVAILABLE:
            return False
        
        if not self.api_key:
            return False
        
        try:
            # Test API connection
            # Note: Anthropic doesn't have a simple test endpoint like OpenAI
            # We'll just check if the client can be created
            return True
        except Exception as e:
            logger.warning(f"Anthropic provider not available: {e}")
            return False
    
    def _build_system_message(self, constraints: Dict[str, Any]) -> str:
        """Build system message with citation constraints."""
        # Use same system message as OpenAI for consistency
        return OpenAIProvider._build_system_message(self, constraints)
    
    def _build_user_message(self, prompt: str, context: LLMContext, 
                           constraints: Dict[str, Any]) -> str:
        """Build user message with context and query."""
        # Use same user message format as OpenAI for consistency
        return OpenAIProvider._build_user_message(self, prompt, context, constraints)


class LocalLLMProvider(LLMProvider):
    """Local LLM implementation (placeholder for future local models)."""
    
    def __init__(self, model_path: str, **kwargs):
        """
        Initialize local LLM provider.
        
        Args:
            model_path: Path to local model
            **kwargs: Additional configuration
        """
        super().__init__("", model_path, **kwargs)
        self.model_path = model_path
        
        logger.info(f"Initialized local LLM provider with model: {model_path}")
    
    def generate_response(self, prompt: str, context: LLMContext,
                         constraints: Dict[str, Any]) -> LLMResponse:
        """
        Generate response using local LLM.
        
        Note: This is a placeholder implementation.
        """
        # Placeholder implementation
        raise NotImplementedError("Local LLM provider not yet implemented")
    
    def is_available(self) -> bool:
        """Check if local LLM is available."""
        # Placeholder - would check if model file exists and is loadable
        return False


class GeminiProvider(LLMProvider):
    """Google Gemini implementation."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", **kwargs):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            model: Model name (default: gemini-1.5-flash)
            **kwargs: Additional Gemini configuration
        """
        super().__init__(api_key, model, **kwargs)
        
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI library not installed. Run: pip install google-generativeai")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
        
        # Configuration
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_output_tokens', 2000)
        self.timeout = kwargs.get('timeout', 30)
        
        # Generation config
        self.generation_config = genai.types.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            candidate_count=1
        )
        
        logger.info(f"Initialized Gemini provider with model: {model}")
    
    def generate_response(self, prompt: str, context: LLMContext,
                         constraints: Dict[str, Any]) -> LLMResponse:
        """
        Generate response using Google Gemini.
        
        Args:
            prompt: User prompt/query
            context: Structured context from knowledge graph
            constraints: Citation and formatting constraints
            
        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.time()
        
        try:
            # Build system message and user message
            system_message = self._build_system_message(constraints)
            user_message = self._build_user_message(prompt, context, constraints)
            
            # Combine system and user messages for Gemini
            full_prompt = f"{system_message}\n\n{user_message}"
            
            # Make API call
            response = self.client.generate_content(
                full_prompt,
                generation_config=self.generation_config
            )
            
            # Extract response data
            content = response.text
            
            # Gemini doesn't provide detailed token usage in the same way
            # We'll estimate based on content length
            estimated_input_tokens = len(full_prompt.split()) * 1.3
            estimated_output_tokens = len(content.split()) * 1.3
            
            usage = {
                'prompt_tokens': int(estimated_input_tokens),
                'completion_tokens': int(estimated_output_tokens),
                'total_tokens': int(estimated_input_tokens + estimated_output_tokens)
            }
            
            response_time = time.time() - start_time
            
            # Update statistics
            self.request_count += 1
            self.total_tokens += usage['total_tokens']
            
            # Create response object
            llm_response = LLMResponse(
                content=content,
                provider="gemini",
                model=self.model,
                usage=usage,
                response_time=response_time,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else None
            )
            
            # Update cost tracking
            self.total_cost += llm_response.get_cost_estimate()
            
            logger.info(f"Gemini response generated in {response_time:.2f}s, "
                       f"estimated tokens: {usage['total_tokens']}")
            
            return llm_response
            
        except Exception as e:
            # Handle various Gemini API errors
            error_msg = str(e).lower()
            
            if "quota" in error_msg or "rate" in error_msg:
                logger.error(f"Gemini rate limit exceeded: {e}")
                raise LLMError(f"Rate limit exceeded: {e}", "gemini", "rate_limit")
            elif "timeout" in error_msg:
                logger.error(f"Gemini API timeout: {e}")
                raise LLMError(f"API timeout: {e}", "gemini", "timeout")
            elif "api" in error_msg or "key" in error_msg:
                logger.error(f"Gemini API error: {e}")
                raise LLMError(f"API error: {e}", "gemini", "api_error")
            else:
                logger.error(f"Unexpected error in Gemini provider: {e}")
                raise LLMError(f"Unexpected error: {e}", "gemini", "unknown")
    
    def is_available(self) -> bool:
        """Check if Gemini provider is available and configured."""
        if not GEMINI_AVAILABLE:
            return False
        
        if not self.api_key:
            return False
        
        try:
            # Test API connection with a simple request
            test_response = self.client.generate_content("Hello")
            return bool(test_response.text)
        except Exception as e:
            logger.warning(f"Gemini provider not available: {e}")
            return False
    
    def _build_system_message(self, constraints: Dict[str, Any]) -> str:
        """Build system message with citation constraints."""
        # Use same system message as OpenAI for consistency
        return OpenAIProvider._build_system_message(self, constraints)
    
    def _build_user_message(self, prompt: str, context: LLMContext, 
                           constraints: Dict[str, Any]) -> str:
        """Build user message with context and query."""
        # Use same user message format as OpenAI for consistency
        return OpenAIProvider._build_user_message(self, prompt, context, constraints)