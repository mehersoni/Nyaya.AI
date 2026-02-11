"""
Simple test script to verify GraphRAG engine functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_engine.graphrag_engine import GraphRAGEngine


def test_basic_functionality():
    """Test basic GraphRAG engine functionality"""
    print("Initializing GraphRAG Engine...")
    
    try:
        engine = GraphRAGEngine()
        print("✓ Engine initialized successfully")
        
        # Validate knowledge graph
        print("\nValidating knowledge graph...")
        validation = engine.validate_knowledge_graph()
        print(f"✓ Knowledge graph valid: {validation['is_valid']}")
        print(f"  - Sections: {validation['stats'].get('sections', 0)}")
        print(f"  - Definitions: {validation['stats'].get('definitions', 0)}")
        print(f"  - Rights: {validation['stats'].get('rights', 0)}")
        
        if validation['warnings']:
            print("  Warnings:")
            for warning in validation['warnings'][:3]:
                print(f"    - {warning}")
        
        # Test different query types
        test_queries = [
            ("What is a consumer?", "definition_lookup"),
            ("Show me section 2", "section_retrieval"),
            ("What are my consumer rights?", "rights_query"),
            ("I bought a defective product", "scenario_analysis")
        ]
        
        print("\nTesting query processing...")
        for query, expected_intent in test_queries:
            print(f"\nQuery: '{query}'")
            response = engine.process_query(query)
            
            print(f"  Intent: {response.query_intent.intent_type.value}")
            print(f"  Confidence: {response.query_intent.confidence:.2f}")
            print(f"  Nodes found: {len(response.graph_context.nodes)}")
            print(f"  Context length: {response.llm_context.get_total_length()}")
            print(f"  Citations: {response.llm_context.get_citation_count()}")
            
            if response.llm_context.formatted_text:
                preview = response.llm_context.formatted_text[:200] + "..."
                print(f"  Context preview: {preview}")
        
        # Performance stats
        print(f"\nPerformance Stats:")
        stats = engine.get_performance_stats()
        print(f"  Total queries: {stats['total_queries']}")
        print(f"  Avg processing time: {stats['average_processing_time']:.3f}s")
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_basic_functionality()