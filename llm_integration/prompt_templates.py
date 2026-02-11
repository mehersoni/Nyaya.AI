"""
Prompt Template Management

This module provides structured prompt templates with citation constraints
for different query types and audiences.

Key components:
- PromptTemplateManager: Manages prompt templates for different scenarios
- CitationConstraints: Defines citation formatting rules
- Template builders for different audiences and query types
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from query_engine.query_parser import IntentType
from query_engine.context_builder import LLMContext


class CitationFormat(Enum):
    """Supported citation formats"""
    STANDARD = "standard"  # [Citation: Section X]
    DETAILED = "detailed"  # [Citation: Section X, Clause Y of Act Name]
    BLUEBOOK = "bluebook"  # Bluebook legal citation format
    INDIAN = "indian"      # Indian Citation Manual format


@dataclass
class CitationConstraints:
    """Citation formatting and validation constraints"""
    format_type: CitationFormat
    require_all_claims: bool = True  # Require citation for every legal claim
    allow_inference: bool = False    # Allow reasonable legal inferences
    max_unsupported_claims: int = 0  # Maximum unsupported claims allowed
    
    def get_format_instructions(self) -> str:
        """Get formatting instructions for the citation format."""
        if self.format_type == CitationFormat.STANDARD:
            return "Use format: [Citation: Section X] or [Citation: Definition of Term]"
        elif self.format_type == CitationFormat.DETAILED:
            return "Use format: [Citation: Section X, Clause Y of Consumer Protection Act, 2019]"
        elif self.format_type == CitationFormat.BLUEBOOK:
            return "Use Bluebook citation format: Consumer Protection Act § X (India 2019)"
        elif self.format_type == CitationFormat.INDIAN:
            return "Use Indian Citation Manual format: Section X, Consumer Protection Act, 2019"
        else:
            return "Use standard citation format"


class PromptTemplateManager:
    """Manages prompt templates for different scenarios and audiences."""
    
    def __init__(self):
        """Initialize the prompt template manager."""
        self._init_base_templates()
        self._init_audience_templates()
        self._init_intent_templates()
    
    def _init_base_templates(self):
        """Initialize base system prompt templates."""
        self.base_system_prompt = """You are Nyayamrit, an AI legal assistant for Indian law. Your role is to provide accurate legal information grounded in authoritative sources.

CRITICAL RULES:
1. ONLY use information from the provided legal context
2. CITE every legal claim using the specified citation format
3. If information is not in context, respond: "Information not available in current knowledge base"
4. Distinguish between legal text (in quotes) and your explanation
5. Include disclaimers that this is information, not legal advice
6. Never make predictions about case outcomes or judicial decisions

RESPONSE STRUCTURE:
1. Direct answer to the question
2. Relevant legal provisions (quoted with citations)
3. Clear explanation in appropriate language
4. Disclaimer about non-binding nature

Remember: You provide information only, not legal advice or binding determinations."""
    
    def _init_audience_templates(self):
        """Initialize audience-specific prompt modifications."""
        self.audience_templates = {
            "citizen": {
                "language_instruction": "Use simple, accessible language that non-lawyers can understand. Avoid legal jargon and explain technical terms.",
                "structure_instruction": "Provide practical guidance and explain what the law means for everyday situations.",
                "disclaimer": "This information is for educational purposes only. For legal advice specific to your situation, consult a qualified lawyer."
            },
            "lawyer": {
                "language_instruction": "Use precise legal terminology and include technical details. Provide comprehensive analysis.",
                "structure_instruction": "Include cross-references, related provisions, and analytical context for legal research.",
                "disclaimer": "This information is for research purposes. Verify all citations and consult primary sources for legal practice."
            },
            "judge": {
                "language_instruction": "Use formal legal language appropriate for judicial consideration. Include analytical framework.",
                "structure_instruction": "Provide comprehensive legal analysis with precedent context and interpretive guidance.",
                "disclaimer": "This analysis is assistive only. Judicial discretion and independent legal analysis remain paramount."
            }
        }
    
    def _init_intent_templates(self):
        """Initialize intent-specific prompt modifications."""
        self.intent_templates = {
            IntentType.DEFINITION_LOOKUP: {
                "focus": "Provide clear, authoritative definitions with legal context and practical implications.",
                "structure": "1. Definition (quoted from law), 2. Explanation in simple terms, 3. Examples if helpful"
            },
            IntentType.SECTION_RETRIEVAL: {
                "focus": "Present the complete section text with proper context and cross-references.",
                "structure": "1. Full section text (quoted), 2. Context within the Act, 3. Related provisions"
            },
            IntentType.RIGHTS_QUERY: {
                "focus": "Explain consumer rights clearly with enforcement mechanisms and practical guidance.",
                "structure": "1. Specific rights applicable, 2. How to exercise these rights, 3. Remedies available"
            },
            IntentType.SCENARIO_ANALYSIS: {
                "focus": "Analyze the legal scenario step-by-step with applicable provisions and potential outcomes.",
                "structure": "1. Legal analysis of situation, 2. Applicable laws and rights, 3. Recommended actions"
            }
        }
    
    def build_system_prompt(self, audience: str, intent_type: IntentType,
                           citation_constraints: CitationConstraints,
                           additional_constraints: Optional[Dict[str, Any]] = None) -> str:
        """
        Build a complete system prompt for the given parameters.
        
        Args:
            audience: Target audience (citizen, lawyer, judge)
            intent_type: Type of query intent
            citation_constraints: Citation formatting requirements
            additional_constraints: Additional constraints or instructions
            
        Returns:
            Complete system prompt string
        """
        prompt_parts = [self.base_system_prompt]
        
        # Add audience-specific instructions
        if audience in self.audience_templates:
            audience_template = self.audience_templates[audience]
            prompt_parts.append(f"\nAUDIENCE: {audience.upper()}")
            prompt_parts.append(f"Language: {audience_template['language_instruction']}")
            prompt_parts.append(f"Structure: {audience_template['structure_instruction']}")
        
        # Add intent-specific instructions
        if intent_type in self.intent_templates:
            intent_template = self.intent_templates[intent_type]
            prompt_parts.append(f"\nQUERY TYPE: {intent_type.value.upper()}")
            prompt_parts.append(f"Focus: {intent_template['focus']}")
            prompt_parts.append(f"Response Structure: {intent_template['structure']}")
        
        # Add citation constraints
        prompt_parts.append(f"\nCITATION FORMAT:")
        prompt_parts.append(citation_constraints.get_format_instructions())
        
        if citation_constraints.require_all_claims:
            prompt_parts.append("REQUIREMENT: Every legal claim must have a supporting citation.")
        
        if not citation_constraints.allow_inference:
            prompt_parts.append("RESTRICTION: Do not make inferences beyond what is explicitly stated in the context.")
        
        # Add additional constraints
        if additional_constraints:
            prompt_parts.append("\nADDITIONAL CONSTRAINTS:")
            for key, value in additional_constraints.items():
                prompt_parts.append(f"{key}: {value}")
        
        # Add final disclaimer
        if audience in self.audience_templates:
            disclaimer = self.audience_templates[audience]['disclaimer']
            prompt_parts.append(f"\nDISCLAIMER: {disclaimer}")
        
        return "\n".join(prompt_parts)
    
    def build_user_prompt(self, query: str, context: LLMContext,
                         intent_type: IntentType, audience: str) -> str:
        """
        Build the user prompt with context and query.
        
        Args:
            query: User's original query
            context: Structured context from knowledge graph
            intent_type: Type of query intent
            audience: Target audience
            
        Returns:
            Complete user prompt string
        """
        prompt_parts = []
        
        # Add legal context
        prompt_parts.append("LEGAL CONTEXT:")
        prompt_parts.append(context.formatted_text)
        
        # Add available citations
        if context.citations:
            prompt_parts.append("\nAVAILABLE CITATIONS:")
            for key, citation in context.citations.items():
                prompt_parts.append(f"{key}: {citation}")
        
        # Add context metadata for transparency
        prompt_parts.append(f"\nCONTEXT METADATA:")
        prompt_parts.append(f"- Primary Provisions: {len(context.primary_provisions)}")
        prompt_parts.append(f"- Related Provisions: {len(context.related_provisions)}")
        prompt_parts.append(f"- Definitions: {len(context.definitions)}")
        prompt_parts.append(f"- Total Citations: {context.get_citation_count()}")
        
        # Add query-specific instructions
        if intent_type == IntentType.DEFINITION_LOOKUP:
            prompt_parts.append("\nINSTRUCTIONS: Focus on providing clear definitions with legal authority.")
        elif intent_type == IntentType.SECTION_RETRIEVAL:
            prompt_parts.append("\nINSTRUCTIONS: Present the complete section with proper context.")
        elif intent_type == IntentType.RIGHTS_QUERY:
            prompt_parts.append("\nINSTRUCTIONS: Explain rights clearly with practical guidance.")
        elif intent_type == IntentType.SCENARIO_ANALYSIS:
            prompt_parts.append("\nINSTRUCTIONS: Analyze the scenario step-by-step with applicable law.")
        
        # Add the user query
        prompt_parts.append(f"\nUSER QUERY:")
        prompt_parts.append(query)
        
        # Add final instruction
        prompt_parts.append("\nPlease provide a response following all the rules and constraints above.")
        
        return "\n".join(prompt_parts)
    
    def get_fallback_prompt(self, query: str, error_message: str) -> str:
        """
        Generate a fallback prompt when knowledge graph lookup fails.
        
        Args:
            query: Original user query
            error_message: Error that occurred during processing
            
        Returns:
            Fallback prompt explaining the limitation
        """
        return f"""I apologize, but I encountered an issue processing your query: "{query}"

Error: {error_message}

As Nyayamrit, I can only provide information that is available in my knowledge base of Indian legal statutes. Currently, I have access to the Consumer Protection Act, 2019.

If your query relates to:
- Consumer rights and protections
- Definitions of consumer-related terms
- Complaint procedures under CPA 2019
- Unfair trade practices

Please try rephrasing your question, and I'll do my best to help with the available information.

For legal matters outside my current knowledge base, I recommend:
1. Consulting the official Government of India legal databases
2. Speaking with a qualified lawyer
3. Contacting relevant consumer protection authorities

Disclaimer: This is an AI assistant providing information only, not legal advice."""
    
    def validate_response_format(self, response: str, 
                                citation_constraints: CitationConstraints) -> Dict[str, Any]:
        """
        Validate that the response follows the required format and citation constraints.
        
        Args:
            response: Generated response to validate
            citation_constraints: Citation requirements to check against
            
        Returns:
            Validation result with errors and warnings
        """
        import re
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'citation_count': 0,
            'unsupported_claims': []
        }
        
        # Count citations in response
        citation_patterns = [
            r'\[Citation: [^\]]+\]',  # Standard format
            r'\[Ref: [^\]]+\]',       # Alternative format
        ]
        
        total_citations = 0
        for pattern in citation_patterns:
            citations = re.findall(pattern, response)
            total_citations += len(citations)
        
        validation_result['citation_count'] = total_citations
        
        # Check for legal claims without citations
        legal_claim_patterns = [
            r'\b(?:section|clause|act|law|provision|statute)\s+\d+\b',
            r'\b(?:according to|under|pursuant to|as per)\b',
            r'\b(?:the law states|legally|statutorily)\b'
        ]
        
        potential_claims = 0
        for pattern in legal_claim_patterns:
            claims = re.findall(pattern, response, re.IGNORECASE)
            potential_claims += len(claims)
        
        # Validate citation requirements
        if citation_constraints.require_all_claims and total_citations == 0 and potential_claims > 0:
            validation_result['errors'].append("Legal claims found but no citations provided")
            validation_result['is_valid'] = False
        
        # Check for disclaimer
        disclaimer_patterns = [
            r'\bdisclaimer\b',
            r'\bnot legal advice\b',
            r'\binformation only\b',
            r'\bconsult.*lawyer\b'
        ]
        
        has_disclaimer = any(re.search(pattern, response, re.IGNORECASE) 
                           for pattern in disclaimer_patterns)
        
        if not has_disclaimer:
            validation_result['warnings'].append("Response should include appropriate disclaimer")
        
        # Check for "information not available" when appropriate
        if "information not available" in response.lower():
            validation_result['warnings'].append("Response indicates information not available - verify this is appropriate")
        
        return validation_result
    
    def get_template_for_error(self, error_type: str, audience: str = "citizen") -> str:
        """
        Get appropriate error response template.
        
        Args:
            error_type: Type of error (timeout, rate_limit, api_error, etc.)
            audience: Target audience for the error message
            
        Returns:
            Error response template
        """
        error_templates = {
            "timeout": "I apologize, but I'm experiencing a delay in processing your request. Please try again in a moment.",
            "rate_limit": "I'm currently experiencing high demand. Please wait a moment and try your question again.",
            "api_error": "I'm experiencing technical difficulties. Please try again later or contact support if the issue persists.",
            "validation_error": "I encountered an issue validating the legal information. For accuracy, please consult official legal sources.",
            "unknown": "I encountered an unexpected issue processing your request. Please try rephrasing your question or contact support."
        }
        
        base_message = error_templates.get(error_type, error_templates["unknown"])
        
        if audience == "citizen":
            disclaimer = "For immediate legal assistance, please contact a lawyer or relevant authorities."
        elif audience == "lawyer":
            disclaimer = "Please verify information through primary legal sources."
        else:
            disclaimer = "Please consult authoritative legal databases for critical information."
        
        return f"{base_message}\n\n{disclaimer}"