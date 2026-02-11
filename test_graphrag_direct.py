#!/usr/bin/env python3
"""
Test GraphRAG engine directly to see the raw context being generated
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_engine.graphrag_engine import GraphRAGEngine

def test_graphrag_direct():
    """Test GraphRAG engine directly"""
    
    # Initialize the GraphRAG engine
    engine = GraphRAGEngine()
    
    # Test query
    test_query = "I bought defective goods"
    
    print(f"Testing GraphRAG engine with: '{test_query}'")
    print("=" * 60)
    
    # Process the query
    response = engine.process_query(test_query, audience="citizen")
    
    # Print detailed analysis
    print("QUERY INTENT:")
    print(f"- Type: {response.query_intent.intent_type.value}")
    print(f"- Confidence: {response.query_intent.confidence:.2f}")
    print(f"- Legal Terms: {response.query_intent.legal_terms}")
    print(f"- Section Numbers: {response.query_intent.section_numbers}")
    print()
    
    print("GRAPH CONTEXT:")
    print(f"- Nodes Retrieved: {len(response.graph_context.nodes)}")
    print(f"- Traversal Path: {response.graph_context.traversal_path}")
    print()
    
    print("RETRIEVED NODES:")
    for i, node in enumerate(response.graph_context.nodes, 1):
        print(f"{i}. {node.get_citation()}")
        print(f"   Type: {node.node_type}")
        if node.node_type == 'section':
            section_num = node.content.get('section_number', 'Unknown')
            text = node.get_text()
            print(f"   Section {section_num}: {text[:200]}...")
        elif node.node_type == 'definition':
            term = node.content.get('term', 'Unknown')
            definition = node.content.get('definition', '')
            print(f"   Definition of '{term}': {definition}")
        elif node.node_type == 'right':
            description = node.content.get('description', '')
            print(f"   Right: {description[:200]}...")
        print()
    
    print("LLM CONTEXT:")
    print(f"- Formatted Text Length: {len(response.llm_context.formatted_text)}")
    print(f"- Primary Provisions: {len(response.llm_context.primary_provisions)}")
    print(f"- Related Provisions: {len(response.llm_context.related_provisions)}")
    print(f"- Definitions: {len(response.llm_context.definitions)}")
    print()
    
    print("FORMATTED CONTEXT FOR LLM:")
    print("-" * 40)
    print(response.llm_context.formatted_text[:1000])
    if len(response.llm_context.formatted_text) > 1000:
        print("... (truncated)")
    print()
    
    print("PROCESSING METADATA:")
    for key, value in response.processing_metadata.items():
        print(f"- {key}: {value}")

if __name__ == "__main__":
    test_graphrag_direct()