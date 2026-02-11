"""
Unit Tests for Confidence Scoring System

Tests the ConfidenceScorer class and its components to ensure accurate
confidence score calculation based on graph coverage, citation density,
and reasoning chain metrics.
"""

import pytest
from unittest.mock import Mock, MagicMock

from llm_integration.confidence_scorer import (
    ConfidenceScorer, ConfidenceLevel, ConfidenceComponents, ConfidenceScore
)
from query_engine.context_builder import LLMContext
from query_engine.graph_traversal import GraphContext, GraphNode
from query_engine.query_parser import QueryIntent, IntentType


class TestConfidenceScorer:
    """Test cases for ConfidenceScorer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ConfidenceScorer()
        
        # Create mock query intent
        self.mock_intent = Mock(spec=QueryIntent)
        self.mock_intent.intent_type = IntentType.SCENARIO_ANALYSIS
        self.mock_intent.legal_terms = ["consumer", "unfair trade practice"]
        self.mock_intent.section_numbers = ["2", "10"]
        self.mock_intent.confidence = 0.8
        
        # Create mock graph context
        self.mock_graph_context = Mock(spec=GraphContext)
        self.mock_graph_context.confidence = 0.9
        
        # Create mock nodes
        section_node = Mock(spec=GraphNode)
        section_node.node_type = 'section'
        section_node.content = {'section_number': '2', 'act': 'Consumer Protection Act, 2019'}
        section_node.get_text.return_value = "This section defines consumer rights and unfair trade practices."
        
        definition_node = Mock(spec=GraphNode)
        definition_node.node_type = 'definition'
        definition_node.content = {'term': 'consumer', 'definition': 'A person who buys goods or services'}
        definition_node.get_text.return_value = "A person who buys goods or services"
        
        self.mock_graph_context.nodes = [section_node, definition_node]
        
        # Create mock LLM context
        self.mock_llm_context = Mock(spec=LLMContext)
        self.mock_llm_context.formatted_text = "Legal context about consumer protection"
        self.mock_llm_context.citations = {"Citation-1": "Section 2, Consumer Protection Act, 2019"}
        
        # Sample responses for testing
        self.high_quality_response = """
        Based on Section 2 of the Consumer Protection Act, 2019, a consumer has the right to be protected against unfair trade practices [Citation: Section 2, CPA 2019]. 
        
        Unfair trade practices include misleading advertisements and defective products. According to the Act, consumers can file complaints with consumer forums [Citation: Section 10, CPA 2019].
        
        This information is provided for educational purposes only and does not constitute legal advice.
        """
        
        self.low_quality_response = """
        Consumers have rights. The law protects them.
        """
        
        self.no_citation_response = """
        Section 2 states that consumers have rights to protection. The Consumer Protection Act provides various remedies for unfair trade practices.
        """
    
    def test_score_response_high_quality(self):
        """Test confidence scoring for high-quality response."""
        score = self.scorer.score_response(
            self.mock_intent,
            self.mock_graph_context,
            self.mock_llm_context,
            self.high_quality_response,
            audience="citizen"
        )
        
        assert isinstance(score, ConfidenceScore)
        assert score.overall_score >= 0.7  # Should be reasonably high
        assert score.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH, ConfidenceLevel.MEDIUM]
        assert len(score.metadata) > 0
        assert score.metadata['audience'] == 'citizen'
        assert score.metadata['citation_count'] >= 2
    
    def test_score_response_low_quality(self):
        """Test confidence scoring for low-quality response."""
        score = self.scorer.score_response(
            self.mock_intent,
            self.mock_graph_context,
            self.mock_llm_context,
            self.low_quality_response,
            audience="citizen"
        )
        
        assert score.overall_score < 0.7  # Should be low
        assert score.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW, ConfidenceLevel.MEDIUM]
        assert score.requires_human_review is True
        assert len(score.review_reasons) > 0
    
    def test_score_response_no_citations(self):
        """Test confidence scoring for response without citations."""
        score = self.scorer.score_response(
            self.mock_intent,
            self.mock_graph_context,
            self.mock_llm_context,
            self.no_citation_response,
            audience="lawyer"
        )
        
        # Should have low citation density score
        assert score.components.citation_density < 0.5
        assert score.requires_human_review is True
        assert any("citation" in reason.lower() for reason in score.review_reasons)
    
    def test_audience_specific_scoring(self):
        """Test that scoring varies appropriately by audience."""
        # Test citizen scoring
        citizen_score = self.scorer.score_response(
            self.mock_intent,
            self.mock_graph_context,
            self.mock_llm_context,
            self.high_quality_response,
            audience="citizen"
        )
        
        # Test lawyer scoring
        lawyer_score = self.scorer.score_response(
            self.mock_intent,
            self.mock_graph_context,
            self.mock_llm_context,
            self.high_quality_response,
            audience="lawyer"
        )
        
        # Test judge scoring
        judge_score = self.scorer.score_response(
            self.mock_intent,
            self.mock_graph_context,
            self.mock_llm_context,
            self.high_quality_response,
            audience="judge"
        )
        
        # Judge should have stricter requirements
        assert judge_score.requires_human_review or judge_score.overall_score >= 0.9
        
        # Verify different weights are applied
        assert citizen_score.metadata['weights_used'] != lawyer_score.metadata['weights_used']
        assert lawyer_score.metadata['weights_used'] != judge_score.metadata['weights_used']
    
    def test_graph_coverage_calculation(self):
        """Test graph coverage score calculation."""
        # Test with good coverage
        components = self.scorer._calculate_confidence_components(
            self.mock_intent,
            self.mock_graph_context,
            self.mock_llm_context,
            self.high_quality_response,
            "citizen"
        )
        
        assert 0.0 <= components.graph_coverage <= 1.0
        assert components.graph_coverage > 0.5  # Should have decent coverage
        
        # Test with no graph nodes
        empty_graph_context = Mock(spec=GraphContext)
        empty_graph_context.nodes = []
        empty_graph_context.confidence = 0.0
        
        empty_components = self.scorer._calculate_confidence_components(
            self.mock_intent,
            empty_graph_context,
            self.mock_llm_context,
            self.high_quality_response,
            "citizen"
        )
        
        assert empty_components.graph_coverage == 0.0
    
    def test_citation_density_calculation(self):
        """Test citation density score calculation."""
        # Test response with good citation density
        citation_score = self.scorer._calculate_citation_density(
            self.high_quality_response, "citizen"
        )
        assert 0.0 <= citation_score <= 1.0
        assert citation_score > 0.5  # Should be decent
        
        # Test response with no citations
        no_citation_score = self.scorer._calculate_citation_density(
            self.no_citation_response, "lawyer"
        )
        assert no_citation_score < 0.5  # Should be low
        
        # Test response with no legal claims
        simple_response = "Hello, how can I help you today?"
        simple_score = self.scorer._calculate_citation_density(simple_response, "citizen")
        assert simple_score == 1.0  # No claims, no citations needed
    
    def test_reasoning_chain_calculation(self):
        """Test reasoning chain score calculation."""
        # Test complex reasoning response
        complex_response = """
        According to Section 2, consumers have rights. Therefore, when unfair trade practices occur,
        consumers can seek remedies. However, they must first file a complaint. As a result,
        the process involves multiple steps.
        """
        
        reasoning_score = self.scorer._calculate_reasoning_chain_score(
            self.mock_intent,
            self.mock_graph_context,
            complex_response
        )
        
        assert 0.0 <= reasoning_score <= 1.0
        assert reasoning_score > 0.7  # Should be high for complex reasoning
        
        # Test simple response
        simple_reasoning_score = self.scorer._calculate_reasoning_chain_score(
            self.mock_intent,
            self.mock_graph_context,
            "Consumers have rights."
        )
        
        assert simple_reasoning_score < reasoning_score
    
    def test_response_quality_calculation(self):
        """Test response quality score calculation."""
        # Test well-structured response
        quality_score = self.scorer._calculate_response_quality(
            self.high_quality_response, "citizen"
        )
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.6
        
        # Test very short response
        short_quality_score = self.scorer._calculate_response_quality(
            "Yes.", "citizen"
        )
        assert short_quality_score < quality_score
        
        # Test very long response
        long_response = "This is a very long response. " * 200
        long_quality_score = self.scorer._calculate_response_quality(
            long_response, "citizen"
        )
        assert long_quality_score < quality_score
    
    def test_human_review_thresholds(self):
        """Test human review threshold logic."""
        # Test with score below 0.8 threshold
        low_score_components = ConfidenceComponents(
            graph_coverage=0.3,
            citation_density=0.2,
            reasoning_chain_score=0.4,
            response_quality=0.5,
            temporal_validity=1.0,
            audience_appropriateness=0.8
        )
        
        requires_review, reasons = self.scorer._requires_human_review(
            0.6, low_score_components, "citizen", self.mock_intent
        )
        
        assert requires_review is True
        assert len(reasons) > 0
        assert any("0.8" in reason for reason in reasons)
        
        # Test judge audience with medium confidence
        judge_requires_review, judge_reasons = self.scorer._requires_human_review(
            0.85, low_score_components, "judge", self.mock_intent
        )
        
        assert judge_requires_review is True
        assert any("judge" in reason.lower() for reason in judge_reasons)
    
    def test_confidence_level_determination(self):
        """Test confidence level determination from scores."""
        assert self.scorer._determine_confidence_level(0.95) == ConfidenceLevel.VERY_HIGH
        assert self.scorer._determine_confidence_level(0.85) == ConfidenceLevel.HIGH
        assert self.scorer._determine_confidence_level(0.75) == ConfidenceLevel.MEDIUM
        assert self.scorer._determine_confidence_level(0.65) == ConfidenceLevel.LOW
        assert self.scorer._determine_confidence_level(0.45) == ConfidenceLevel.VERY_LOW
    
    def test_citation_counting(self):
        """Test citation counting functionality."""
        response_with_citations = """
        This is based on Section 2 [Citation: Section 2, CPA 2019] and also 
        references Section 10 [Citation: Section 10, CPA 2019]. Additionally,
        see (Section 15 of CPA 2019) for more details.
        """
        
        citation_count = self.scorer._count_citations(response_with_citations)
        assert citation_count >= 3  # Should find all citation formats
        
        # Test response without citations
        no_citation_count = self.scorer._count_citations("This has no citations.")
        assert no_citation_count == 0
    
    def test_legal_claims_counting(self):
        """Test legal claims counting functionality."""
        response_with_claims = """
        Section 2 states that consumers have rights. The Consumer Protection Act requires
        businesses to provide fair services. Consumers are entitled to seek remedies
        according to the law.
        """
        
        claims_count = self.scorer._count_legal_claims(response_with_claims)
        assert claims_count >= 3  # Should find multiple legal claims
        
        # Test response without legal claims
        no_claims_count = self.scorer._count_legal_claims("Hello, how are you?")
        assert no_claims_count == 0
    
    def test_threshold_updates(self):
        """Test threshold update functionality."""
        original_threshold = self.scorer.confidence_thresholds[ConfidenceLevel.HIGH]
        
        new_thresholds = {ConfidenceLevel.HIGH: 0.75}
        self.scorer.update_thresholds(new_thresholds)
        
        assert self.scorer.confidence_thresholds[ConfidenceLevel.HIGH] == 0.75
        assert self.scorer.confidence_thresholds[ConfidenceLevel.HIGH] != original_threshold
        
        # Test invalid threshold
        invalid_thresholds = {ConfidenceLevel.HIGH: 1.5}  # Invalid value
        self.scorer.update_thresholds(invalid_thresholds)
        
        # Should not update with invalid value
        assert self.scorer.confidence_thresholds[ConfidenceLevel.HIGH] == 0.75
    
    def test_calibration_stats(self):
        """Test calibration statistics retrieval."""
        stats = self.scorer.get_calibration_stats()
        
        assert 'thresholds' in stats
        assert 'audience_weights' in stats
        assert 'citation_requirements' in stats
        
        assert len(stats['thresholds']) == 5  # All confidence levels
        assert 'citizen' in stats['audience_weights']
        assert 'lawyer' in stats['audience_weights']
        assert 'judge' in stats['audience_weights']
    
    def test_confidence_score_display_messages(self):
        """Test confidence score display messages."""
        very_high_score = ConfidenceScore(
            overall_score=0.95,
            confidence_level=ConfidenceLevel.VERY_HIGH,
            components=Mock(),
            requires_human_review=False,
            review_reasons=[],
            metadata={}
        )
        
        message = very_high_score.get_display_message()
        assert "high confidence" in message.lower()
        assert len(message) > 10  # Should be descriptive
        
        very_low_score = ConfidenceScore(
            overall_score=0.3,
            confidence_level=ConfidenceLevel.VERY_LOW,
            components=Mock(),
            requires_human_review=True,
            review_reasons=["Low score"],
            metadata={}
        )
        
        low_message = very_low_score.get_display_message()
        assert "limited confidence" in low_message.lower()
        assert very_low_score.should_block_display() is True
    
    def test_weighted_average_calculation(self):
        """Test weighted average calculation in ConfidenceComponents."""
        components = ConfidenceComponents(
            graph_coverage=0.8,
            citation_density=0.9,
            reasoning_chain_score=0.7,
            response_quality=0.6,
            temporal_validity=1.0,
            audience_appropriateness=0.8
        )
        
        weights = {
            'graph_coverage': 0.3,
            'citation_density': 0.3,
            'reasoning_chain': 0.2,
            'response_quality': 0.2
        }
        
        weighted_avg = components.get_weighted_average(weights)
        assert 0.0 <= weighted_avg <= 1.0
        
        # Test with empty weights
        empty_avg = components.get_weighted_average({})
        assert empty_avg == 0.0


if __name__ == "__main__":
    pytest.main([__file__])