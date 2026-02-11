#!/usr/bin/env python3
"""
Test all scenario types to ensure the fix doesn't break other functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_engine.graphrag_engine import GraphRAGEngine

def test_all_scenarios():
    """Test different types of queries to ensure all work correctly"""
    
    engine = GraphRAGEngine()
    
    test_cases = [
        {
            "query": "I bought defective goods",
            "expected_type": "scenario_analysis",
            "expected_sections": ["35", "39"],
            "expected_definitions": ["defect"]
        },
        {
            "query": "What does consumer mean?",
            "expected_type": "definition_lookup", 
            "expected_definitions": ["consumer"]
        },
        {
            "query": "Show me Section 35",
            "expected_type": "section_retrieval",
            "expected_sections": ["35"]
        },
        {
            "query": "What are my consumer rights?",
            "expected_type": "rights_query",
            "expected_rights": True
        },
        {
            "query": "The seller is overcharging me",
            "expected_type": "scenario_analysis",
            "expected_sections": ["35", "39"]
        }
    ]
    
    print("Testing All Scenario Types")
    print("=" * 50)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        print(f"\n{i}. Testing: '{query}'")
        
        response = engine.process_query(query)
        
        # Check intent type
        actual_intent = response.query_intent.intent_type.value
        expected_intent = test_case["expected_type"]
        
        intent_correct = actual_intent == expected_intent
        print(f"   Intent: {actual_intent} {'✅' if intent_correct else '❌'}")
        
        if not intent_correct:
            all_passed = False
        
        # Check sections
        if "expected_sections" in test_case:
            section_numbers = []
            for node in response.graph_context.nodes:
                if node.node_type == 'section':
                    section_numbers.append(node.content.get('section_number'))
            
            expected_sections = test_case["expected_sections"]
            sections_found = any(sec in section_numbers for sec in expected_sections)
            print(f"   Sections: {section_numbers} {'✅' if sections_found else '❌'}")
            
            if not sections_found:
                all_passed = False
        
        # Check definitions
        if "expected_definitions" in test_case:
            definitions = []
            for node in response.graph_context.nodes:
                if node.node_type == 'definition':
                    definitions.append(node.content.get('term'))
            
            expected_definitions = test_case["expected_definitions"]
            definitions_found = any(def_term in definitions for def_term in expected_definitions)
            print(f"   Definitions: {definitions} {'✅' if definitions_found else '❌'}")
            
            if not definitions_found:
                all_passed = False
        
        # Check rights
        if "expected_rights" in test_case:
            rights_count = sum(1 for node in response.graph_context.nodes if node.node_type == 'right')
            rights_found = rights_count > 0
            print(f"   Rights: {rights_count} found {'✅' if rights_found else '❌'}")
            
            if not rights_found:
                all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - All scenario types working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Check individual results above")
    
    return all_passed

if __name__ == "__main__":
    test_all_scenarios()