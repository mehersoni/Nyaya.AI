"""
LLM Integration Layer for Nyayamrit

This module provides the LLM integration layer that interfaces with various
LLM providers using graph-constrained prompts to generate explanations.

Key components:
- LLMProvider: Abstract interface for LLM providers
- OpenAIProvider: OpenAI GPT-4 implementation
- PromptTemplates: Structured prompt templates with citation constraints
- LLMManager: Multi-provider fallback strategy
"""

from .providers import LLMProvider, OpenAIProvider, AnthropicProvider
from .prompt_templates import PromptTemplateManager, CitationConstraints
from .llm_manager import LLMManager, LLMResponse, LLMError
from .validation import ResponseValidator, ValidationResult

__all__ = [
    'LLMProvider',
    'OpenAIProvider', 
    'AnthropicProvider',
    'PromptTemplateManager',
    'CitationConstraints',
    'LLMManager',
    'LLMResponse',
    'LLMError',
    'ResponseValidator',
    'ValidationResult'
]