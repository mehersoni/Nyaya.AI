"""
Integration test for GraphRAG Reasoning Engine

This test verifies that all components of the GraphRAG engine work together correctly:
- Query parsing extracts correct intent
- Graph traversal finds relevant provisions
- Context builder formats data properly
- End-to-end processing works for different query types
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_engine import GraphRAGEngine, IntentType


def test_definition_lookup():
    """Test definition lookup functionality"""
    print("Testing definition lookup...")
    
    engine = GraphRAGEngine()
    
    # Test consumer definition
    response = engine.process_query("What does consumer mean?")
    
    assert response.query_intent.intent_type == IntentType.DEFINITION_LOOKUP
    assert response.query_intent.confidence > 0.2
    assert len(response.graph_context.nodes) > 0
    assert 'consumer' in response.llm_context.formatted_text.lower()
    assert response.llm_context.get_citation_count() > 0
    
    print("✓ Definition lookup test passed")


def test_section_retrieval():
    """Test section retrieval functionality"""
    print("Testing section retrieval...")
    
    engine = GraphRAGEngine()
    
    # Test section 2 retrieval
    response = engine.process_query("Show me section 2 of CPA")
    
    assert response.query_intent.intent_type == IntentType.SECTION_RETRIEVAL
    assert '2' in response.query_intent.section_numbers
    assert len(response.graph_context.nodes) > 0
    assert 'section 2' in response.llm_context.formatted_text.lower()
    
    print("✓ Section retrieval test passed")


def test_rights_query():
    """Test consumer rights query functionality"""
    print("Testing rights query...")
    
    engine = GraphRAGEngine()
    
    # Test consumer rights query
    response = engine.process_query("What are my rights as a consumer?")
    
    assert response.query_intent.intent_type == IntentType.RIGHTS_QUERY
    assert len(response.graph_context.nodes) > 0
    assert 'right' in response.llm_context.formatted_text.lower()
    
    print("✓ Rights query test passed")


def test_scenario_analysis():
    """Test scenario analysis functionality"""
    print("Testing scenario analysis...")
    
    engine = GraphRAGEngine()
    
    # Test defective product scenario
    response = engine.process_query("I bought a defective product, what can I do?")
    
    assert response.query_intent.intent_type == IntentType.SCENARIO_ANALYSIS
    assert len(response.graph_context.nodes) > 0
    assert response.llm_context.get_citation_count() > 0
    
    print("✓ Scenario analysis test passed")


def test_audience_formatting():
    """Test audience-specific formatting"""
    print("Testing audience formatting...")
    
    engine = GraphRAGEngine()
    
    # Test same query for different audiences
    query = "What are consumer rights?"
    
    citizen_response = engine.process_query(query, audience="citizen")
    lawyer_response = engine.process_query(query, audience="lawyer")
    
    # Citizen response should have simplified headers
    assert "YOUR RIGHTS" in citizen_response.llm_context.formatted_text
    
    # Lawyer response should have citation summary
    assert "CITATION SUMMARY" in lawyer_response.llm_context.formatted_text
    
    print("✓ Audience formatting test passed")


def test_confidence_scoring():
    """Test confidence scoring mechanism"""
    print("Testing confidence scoring...")
    
    engine = GraphRAGEngine()
    
    # Clear query should have higher confidence
    clear_response = engine.process_query("What is a consumer?")
    
    # Vague query should have lower confidence
    vague_response = engine.process_query("Tell me about stuff")
    
    assert clear_response.get_confidence_score() > vague_response.get_confidence_score()
    
    print("✓ Confidence scoring test passed")


def test_performance():
    """Test performance characteristics"""
    print("Testing performance...")
    
    engine = GraphRAGEngine()
    
    # Process multiple queries
    queries = [
        "What is unfair trade practice?",
        "Show me section 18",
        "What are my consumer rights?",
        "I have a complaint about misleading advertisement"
    ]
    
    for query in queries:
        response = engine.process_query(query)
        processing_time = response.processing_metadata['processing_time']
        
        # Should process within reasonable time (< 1 second)
        assert processing_time < 1.0, f"Query took too long: {processing_time}s"
    
    stats = engine.get_performance_stats()
    assert stats['total_queries'] == len(queries)
    assert stats['average_processing_time'] < 1.0
    
    print("✓ Performance test passed")


def test_error_handling():
    """Test error handling for edge cases"""
    print("Testing error handling...")
    
    engine = GraphRAGEngine()
    
    # Empty query
    response = engine.process_query("")
    # Empty queries should still work but with low confidence
    assert response.llm_context.get_total_length() > 0
    
    # Very long query
    long_query = "What is " + "consumer " * 100 + "rights?"
    response = engine.process_query(long_query)
    assert response.llm_context.get_total_length() > 0
    
    # Nonsensical query
    response = engine.process_query("xyz abc def random words")
    assert response.llm_context.get_total_length() > 0
    
    print("✓ Error handling test passed")


def run_all_tests():
    """Run all integration tests"""
    print("Running GraphRAG Integration Tests...")
    print("=" * 50)
    
    try:
        test_definition_lookup()
        test_section_retrieval()
        test_rights_query()
        test_scenario_analysis()
        test_audience_formatting()
        test_confidence_scoring()
        test_performance()
        test_error_handling()
        
        print("=" * 50)
        print("✓ All integration tests passed successfully!")
        
        # Print summary stats
        engine = GraphRAGEngine()
        validation = engine.validate_knowledge_graph()
        
        print(f"\nKnowledge Graph Summary:")
        print(f"  - Sections: {validation['stats'].get('sections', 0)}")
        print(f"  - Definitions: {validation['stats'].get('definitions', 0)}")
        print(f"  - Rights: {validation['stats'].get('rights', 0)}")
        print(f"  - Clauses: {validation['stats'].get('clauses', 0)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)