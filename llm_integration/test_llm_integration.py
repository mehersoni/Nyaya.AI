"""
Test Suite for LLM Integration Layer

This module provides comprehensive tests for the LLM integration layer,
including provider functionality, prompt templates, validation, and
multi-provider fallback strategies.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

from .providers import LLMProvider, OpenAIProvider, LLMResponse, LLMError
from .prompt_templates import PromptTemplateManager, CitationConstraints, CitationFormat
from .llm_manager import LLMManager, FallbackStrategy
from .validation import ResponseValidator, ValidationSeverity
from query_engine.context_builder import LLMContext
from query_engine.query_parser import IntentType
from query_engine.graph_traversal import GraphContext, GraphNode


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self, name: str, should_fail: bool = False, response_time: float = 1.0):
        super().__init__("mock_key", "mock_model")
        self.name = name
        self.should_fail = should_fail
        self.response_time = response_time
        self.call_count = 0
    
    def generate_response(self, prompt: str, context: LLMContext, 
                         constraints: Dict[str, Any]) -> LLMResponse:
        self.call_count += 1
        
        if self.should_fail:
            raise LLMError(f"Mock failure from {self.name}", self.name, "mock_error")
        
        # Simulate processing time
        time.sleep(self.response_time)
        
        # Generate mock response based on context
        mock_content = f"""Based on the Consumer Protection Act, 2019, I can provide the following information:

The relevant legal provision states: "Consumer means any person who buys any goods for a consideration..." [Citation: Citation-1]

This definition establishes the scope of consumer protection under the Act. A consumer is entitled to various rights including the right to be protected against hazardous goods and services.

Disclaimer: This information is provided for educational purposes only and does not constitute legal advice."""
        
        return LLMResponse(
            content=mock_content,
            provider=self.name,
            model="mock_model",
            usage={"prompt_tokens": 100, "completion_tokens": 150, "total_tokens": 250},
            response_time=self.response_time,
            finish_reason="stop"
        )
    
    def is_available(self) -> bool:
        return not self.should_fail


def create_mock_context() -> LLMContext:
    """Create mock LLM context for testing"""
    return LLMContext(
        formatted_text="""=== PRIMARY LEGAL PROVISIONS ===
**Section 2: Definitions** [Citation-1]

In this Act, unless the context otherwise requires,—
(7) "consumer" means any person who—
(i) buys any goods for a consideration which has been paid or promised or partly paid and partly promised, or under any system of deferred payment and includes any user of such goods other than the person who buys such goods for consideration paid or promised or partly paid and partly promised, or under any system of deferred payment, when such use is made with the approval of such person, but does not include a person who obtains such goods for resale or for any commercial purpose;

=== LEGAL DEFINITIONS ===
**CONSUMER**: Any person who buys goods for consideration or uses goods with approval of buyer, excluding those who obtain goods for resale or commercial purpose [Citation-1]""",
        citations={"Citation-1": "Section 2(7), Consumer Protection Act, 2019"},
        metadata={"confidence": 0.9, "audience": "citizen"},
        primary_provisions=["Section 2"],
        related_provisions=[],
        definitions=["consumer"],
        hierarchical_context=["Chapter I - Preliminary"]
    )


def create_mock_graph_context() -> GraphContext:
    """Create mock graph context for testing"""
    section_node = GraphNode(
        node_id="CPA2019_2",
        node_type="section",
        content={
            "section_number": "2",
            "title": "Definitions",
            "text": "In this Act, unless the context otherwise requires,—",
            "act": "Consumer Protection Act, 2019"
        }
    )
    
    return GraphContext(
        nodes=[section_node],
        edges=[],
        citations=["Section 2, Consumer Protection Act, 2019"],
        confidence=0.9,
        traversal_path=["CPA2019_2"]
    )


class TestPromptTemplateManager:
    """Test prompt template management"""
    
    def test_system_prompt_generation(self):
        """Test system prompt generation for different audiences"""
        manager = PromptTemplateManager()
        constraints = CitationConstraints(CitationFormat.STANDARD)
        
        # Test citizen prompt
        citizen_prompt = manager.build_system_prompt(
            audience="citizen",
            intent_type=IntentType.DEFINITION_LOOKUP,
            citation_constraints=constraints
        )
        
        assert "simple, accessible language" in citizen_prompt
        assert "AUDIENCE: CITIZEN" in citizen_prompt
        assert "DEFINITION_LOOKUP" in citizen_prompt
        
        # Test lawyer prompt
        lawyer_prompt = manager.build_system_prompt(
            audience="lawyer",
            intent_type=IntentType.SECTION_RETRIEVAL,
            citation_constraints=constraints
        )
        
        assert "precise legal terminology" in lawyer_prompt
        assert "AUDIENCE: LAWYER" in lawyer_prompt
    
    def test_user_prompt_generation(self):
        """Test user prompt generation with context"""
        manager = PromptTemplateManager()
        context = create_mock_context()
        
        user_prompt = manager.build_user_prompt(
            query="What is a consumer?",
            context=context,
            intent_type=IntentType.DEFINITION_LOOKUP,
            audience="citizen"
        )
        
        assert "LEGAL CONTEXT:" in user_prompt
        assert "AVAILABLE CITATIONS:" in user_prompt
        assert "What is a consumer?" in user_prompt
        assert "Citation-1" in user_prompt
    
    def test_citation_format_instructions(self):
        """Test different citation format instructions"""
        manager = PromptTemplateManager()
        
        # Standard format
        standard_constraints = CitationConstraints(CitationFormat.STANDARD)
        standard_prompt = manager.build_system_prompt(
            audience="citizen",
            intent_type=IntentType.DEFINITION_LOOKUP,
            citation_constraints=standard_constraints
        )
        assert "[Citation: Section X]" in standard_prompt
        
        # Detailed format
        detailed_constraints = CitationConstraints(CitationFormat.DETAILED)
        detailed_prompt = manager.build_system_prompt(
            audience="lawyer",
            intent_type=IntentType.SECTION_RETRIEVAL,
            citation_constraints=detailed_constraints
        )
        assert "Consumer Protection Act, 2019" in detailed_prompt


class TestLLMManager:
    """Test LLM manager functionality"""
    
    def test_provider_management(self):
        """Test adding and removing providers"""
        manager = LLMManager()
        
        # Add providers
        provider1 = MockLLMProvider("provider1")
        provider2 = MockLLMProvider("provider2")
        
        manager.add_provider("provider1", provider1, priority=2)
        manager.add_provider("provider2", provider2, priority=1)
        
        assert len(manager.providers) == 2
        assert manager.providers["provider1"].priority == 2
        
        # Remove provider
        manager.remove_provider("provider1")
        assert len(manager.providers) == 1
        assert "provider1" not in manager.providers
    
    def test_fallback_strategy(self):
        """Test multi-provider fallback"""
        manager = LLMManager(FallbackStrategy.SEQUENTIAL)
        
        # Add providers with different priorities
        failing_provider = MockLLMProvider("failing", should_fail=True)
        working_provider = MockLLMProvider("working", should_fail=False)
        
        manager.add_provider("failing", failing_provider, priority=2)  # Higher priority
        manager.add_provider("working", working_provider, priority=1)
        
        context = create_mock_context()
        
        # Should fallback to working provider
        response = manager.generate_response(
            query="What is a consumer?",
            context=context,
            audience="citizen"
        )
        
        assert response.provider == "working"
        assert failing_provider.call_count == 1  # Should have tried failing provider first
        assert working_provider.call_count == 1  # Should have fallen back to working provider
    
    def test_provider_health_checks(self):
        """Test provider health checking"""
        manager = LLMManager()
        
        healthy_provider = MockLLMProvider("healthy", should_fail=False)
        unhealthy_provider = MockLLMProvider("unhealthy", should_fail=True)
        
        manager.add_provider("healthy", healthy_provider)
        manager.add_provider("unhealthy", unhealthy_provider)
        
        # Perform health checks
        results = manager.health_check_all_providers()
        
        assert results["healthy"] == True
        assert results["unhealthy"] == False
    
    def test_cost_estimation(self):
        """Test cost estimation functionality"""
        manager = LLMManager()
        
        provider = MockLLMProvider("test")
        manager.add_provider("test", provider, cost_per_token=0.00002)
        
        context = create_mock_context()
        estimated_cost = manager.estimate_cost(
            query="What is a consumer?",
            context=context,
            provider_name="test"
        )
        
        assert estimated_cost > 0
        assert isinstance(estimated_cost, float)


class TestResponseValidator:
    """Test response validation functionality"""
    
    def test_citation_validation(self):
        """Test citation validation"""
        validator = ResponseValidator()
        context = create_mock_context()
        graph_context = create_mock_graph_context()
        constraints = CitationConstraints(CitationFormat.STANDARD)
        
        # Valid response with proper citations
        valid_response = """A consumer is defined as any person who buys goods for consideration [Citation: Citation-1].
        
        This definition is found in Section 2 of the Consumer Protection Act, 2019.
        
        Disclaimer: This information is for educational purposes only."""
        
        result = validator.validate_response(
            response=valid_response,
            context=context,
            graph_context=graph_context,
            citation_constraints=constraints
        )
        
        assert result.is_valid
        assert result.citation_count > 0
        assert not result.has_errors()
    
    def test_invalid_citation_detection(self):
        """Test detection of invalid citations"""
        validator = ResponseValidator()
        context = create_mock_context()
        graph_context = create_mock_graph_context()
        constraints = CitationConstraints(CitationFormat.STANDARD)
        
        # Response with invalid citation
        invalid_response = """A consumer is defined as any person who buys goods [Citation: Invalid-Citation].
        
        This is not properly cited."""
        
        result = validator.validate_response(
            response=invalid_response,
            context=context,
            graph_context=graph_context,
            citation_constraints=constraints
        )
        
        assert not result.is_valid
        assert result.has_errors()
        
        # Check for invalid citation error
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        assert any("invalid_citation" in error.issue_type for error in errors)
    
    def test_prohibited_language_detection(self):
        """Test detection of prohibited predictive language"""
        validator = ResponseValidator()
        context = create_mock_context()
        graph_context = create_mock_graph_context()
        constraints = CitationConstraints(CitationFormat.STANDARD)
        
        # Response with prohibited language
        prohibited_response = """I predict that the court will rule in favor of the consumer.
        
        The judge will likely find that this is a valid case."""
        
        result = validator.validate_response(
            response=prohibited_response,
            context=context,
            graph_context=graph_context,
            citation_constraints=constraints
        )
        
        assert not result.is_valid
        assert result.has_errors()
        
        # Check for predictive language error
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        assert any("predictive_language" in error.issue_type for error in errors)
    
    def test_disclaimer_validation(self):
        """Test disclaimer requirement validation"""
        validator = ResponseValidator()
        context = create_mock_context()
        graph_context = create_mock_graph_context()
        constraints = CitationConstraints(CitationFormat.STANDARD)
        
        # Response without disclaimer
        no_disclaimer_response = """A consumer is defined as any person who buys goods [Citation: Citation-1]."""
        
        result = validator.validate_response(
            response=no_disclaimer_response,
            context=context,
            graph_context=graph_context,
            citation_constraints=constraints
        )
        
        # Should have warning about missing disclaimer
        warnings = result.get_issues_by_severity(ValidationSeverity.WARNING)
        assert any("missing_disclaimer" in warning.issue_type for warning in warnings)


class TestIntegration:
    """Integration tests for complete LLM workflow"""
    
    def test_complete_workflow(self):
        """Test complete workflow from query to validated response"""
        # Setup
        manager = LLMManager()
        provider = MockLLMProvider("test_provider")
        manager.add_provider("test", provider)
        
        context = create_mock_context()
        
        # Generate response
        response = manager.generate_response(
            query="What is a consumer under CPA 2019?",
            context=context,
            audience="citizen",
            intent_type=IntentType.DEFINITION_LOOKUP
        )
        
        # Validate response
        validator = ResponseValidator()
        graph_context = create_mock_graph_context()
        constraints = CitationConstraints(CitationFormat.STANDARD)
        
        validation_result = validator.validate_response(
            response=response.content,
            context=context,
            graph_context=graph_context,
            citation_constraints=constraints
        )
        
        # Assertions
        assert response.provider == "test_provider"
        assert response.content is not None
        assert len(response.content) > 0
        assert validation_result.citation_count > 0
        assert "consumer" in response.content.lower()
        assert "disclaimer" in response.content.lower()
    
    def test_error_handling_workflow(self):
        """Test error handling in complete workflow"""
        manager = LLMManager()
        
        # Add only failing providers
        failing_provider1 = MockLLMProvider("fail1", should_fail=True)
        failing_provider2 = MockLLMProvider("fail2", should_fail=True)
        
        manager.add_provider("fail1", failing_provider1, priority=2)
        manager.add_provider("fail2", failing_provider2, priority=1)
        
        context = create_mock_context()
        
        # Should raise LLMError when all providers fail
        with pytest.raises(LLMError):
            manager.generate_response(
                query="What is a consumer?",
                context=context,
                audience="citizen"
            )
        
        # Verify both providers were attempted
        assert failing_provider1.call_count == 1
        assert failing_provider2.call_count == 1


def test_openai_provider_initialization():
    """Test OpenAI provider initialization (if available)"""
    try:
        # This will only work if OpenAI library is installed and API key is provided
        provider = OpenAIProvider(api_key="test_key")
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.1
    except ImportError:
        # Skip test if OpenAI library not available
        pytest.skip("OpenAI library not available")


if __name__ == "__main__":
    # Run basic tests
    print("Running LLM Integration Tests...")
    
    # Test prompt template manager
    print("✓ Testing prompt template manager...")
    test_manager = TestPromptTemplateManager()
    test_manager.test_system_prompt_generation()
    test_manager.test_user_prompt_generation()
    
    # Test LLM manager
    print("✓ Testing LLM manager...")
    test_llm_manager = TestLLMManager()
    test_llm_manager.test_provider_management()
    test_llm_manager.test_fallback_strategy()
    
    # Test validator
    print("✓ Testing response validator...")
    test_validator = TestResponseValidator()
    test_validator.test_citation_validation()
    test_validator.test_invalid_citation_detection()
    
    # Test integration
    print("✓ Testing complete integration...")
    test_integration = TestIntegration()
    test_integration.test_complete_workflow()
    
    print("All tests passed! ✓")