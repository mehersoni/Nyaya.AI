"""
Demo script for Nyayamrit GraphRAG Reasoning Engine

This script demonstrates the capabilities of the GraphRAG engine
with various types of legal queries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_engine import GraphRAGEngine


def demo_query(engine, query, audience="citizen"):
    """Demo a single query with detailed output"""
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"AUDIENCE: {audience.upper()}")
    print(f"{'='*60}")
    
    response = engine.process_query(query, audience=audience)
    
    # Show query analysis
    print(f"\n📊 QUERY ANALYSIS:")
    print(f"   Intent Type: {response.query_intent.intent_type.value}")
    print(f"   Confidence: {response.query_intent.confidence:.2f}")
    print(f"   Legal Terms: {', '.join(response.query_intent.legal_terms) if response.query_intent.legal_terms else 'None'}")
    print(f"   Section Numbers: {', '.join(response.query_intent.section_numbers) if response.query_intent.section_numbers else 'None'}")
    
    # Show retrieval results
    print(f"\n🔍 KNOWLEDGE GRAPH RETRIEVAL:")
    print(f"   Nodes Retrieved: {len(response.graph_context.nodes)}")
    print(f"   Citations Generated: {response.llm_context.get_citation_count()}")
    print(f"   Final Confidence: {response.get_confidence_score():.2f}")
    print(f"   Processing Time: {response.processing_metadata['processing_time']:.3f}s")
    
    # Show formatted context (truncated for demo)
    print(f"\n📄 FORMATTED CONTEXT:")
    context_preview = response.llm_context.formatted_text
    if len(context_preview) > 800:
        context_preview = context_preview[:800] + "\n\n[... truncated for demo ...]"
    print(context_preview)
    
    # Show reasoning explanation
    print(f"\n🧠 REASONING EXPLANATION:")
    explanation = engine.explain_reasoning(response)
    print(explanation)
    
    return response


def main():
    """Run the GraphRAG demo"""
    print("🏛️  NYAYAMRIT GRAPHRAG REASONING ENGINE DEMO")
    print("=" * 60)
    
    # Initialize engine
    print("Initializing GraphRAG Engine...")
    engine = GraphRAGEngine()
    
    # Validate knowledge graph
    validation = engine.validate_knowledge_graph()
    print(f"✓ Knowledge Graph Loaded:")
    print(f"  - {validation['stats']['sections']} Sections")
    print(f"  - {validation['stats']['definitions']} Definitions") 
    print(f"  - {validation['stats']['rights']} Rights")
    print(f"  - {validation['stats']['clauses']} Clauses")
    
    # Demo queries for different intent types
    demo_queries = [
        ("What does 'consumer' mean in legal terms?", "citizen"),
        ("Show me Section 18 of Consumer Protection Act", "lawyer"),
        ("What compensation can I claim for defective products?", "citizen"),
        ("How to file a consumer complaint?", "citizen"),
        ("Define unfair trade practice", "lawyer")
    ]
    
    print(f"\n🚀 RUNNING DEMO QUERIES...")
    
    for i, (query, audience) in enumerate(demo_queries, 1):
        print(f"\n\n{'#'*10} DEMO {i}/{len(demo_queries)} {'#'*10}")
        demo_query(engine, query, audience)
        
        if i < len(demo_queries):
            input("\nPress Enter to continue to next demo...")
    
    # Show performance summary
    print(f"\n\n{'='*60}")
    print("📈 PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    
    stats = engine.get_performance_stats()
    print(f"Total Queries Processed: {stats['total_queries']}")
    print(f"Average Processing Time: {stats['average_processing_time']:.3f}s")
    print(f"Total Processing Time: {stats['total_processing_time']:.3f}s")
    
    # Show similar query suggestions
    print(f"\n💡 SIMILAR QUERY SUGGESTIONS:")
    suggestions = engine.get_similar_queries("What are consumer rights?")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    print(f"\n✅ Demo completed successfully!")
    print(f"The GraphRAG engine is ready for integration with LLM providers.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()