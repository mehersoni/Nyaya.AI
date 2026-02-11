"""
Basic test for LLM integration without external dependencies
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

try:
    # Test imports
    from llm_integration.providers import LLMProvider, LLMResponse, LLMError
    from llm_integration.prompt_templates import PromptTemplateManager, CitationConstraints, CitationFormat
    from llm_integration.llm_manager import LLMManager, FallbackStrategy
    from llm_integration.validation import ResponseValidator, ValidationResult
    
    print("✅ All imports successful")
    
    # Test basic functionality
    print("\n🧪 Testing basic functionality...")
    
    # Test prompt template manager
    prompt_manager = PromptTemplateManager()
    constraints = CitationConstraints(CitationFormat.STANDARD)
    
    from query_engine.query_parser import IntentType
    
    system_prompt = prompt_manager.build_system_prompt(
        audience="citizen",
        intent_type=IntentType.DEFINITION_LOOKUP,
        citation_constraints=constraints
    )
    
    assert "AUDIENCE: CITIZEN" in system_prompt
    assert "DEFINITION_LOOKUP" in system_prompt
    print("✅ Prompt template manager working")
    
    # Test LLM manager
    llm_manager = LLMManager(FallbackStrategy.SEQUENTIAL)
    assert llm_manager.fallback_strategy == FallbackStrategy.SEQUENTIAL
    print("✅ LLM manager initialization working")
    
    # Test response validator
    validator = ResponseValidator()
    assert validator is not None
    print("✅ Response validator initialization working")
    
    # Test citation constraints
    constraints = CitationConstraints(
        format_type=CitationFormat.STANDARD,
        require_all_claims=True,
        allow_inference=False
    )
    
    format_instructions = constraints.get_format_instructions()
    assert "Citation: Section X" in format_instructions
    print("✅ Citation constraints working")
    
    print("\n🎉 All basic tests passed!")
    print("\nLLM Integration Layer is ready for use!")
    print("\nTo use with actual LLM providers:")
    print("1. Set environment variables: OPENAI_API_KEY or ANTHROPIC_API_KEY")
    print("2. Install provider libraries: pip install openai anthropic")
    print("3. Run: python llm_integration/example_usage.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)