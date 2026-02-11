"""
Demo: LLM Integration with GraphRAG Engine

This demo shows how the new LLM integration layer works with the existing
GraphRAG engine to provide complete legal assistance with proper citations.
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

from query_engine.graphrag_engine import GraphRAGEngine
from llm_integration.llm_manager import LLMManager, FallbackStrategy
from llm_integration.prompt_templates import CitationFormat
from llm_integration.validation import ResponseValidator, CitationConstraints


class MockLLMProvider:
    """Mock LLM provider for demonstration without API keys"""
    
    def __init__(self, name: str):
        self.name = name
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def generate_response(self, prompt, context, constraints):
        """Generate a mock response with proper citations"""
        self.request_count += 1
        
        # Extract available citations from context
        citations = list(context.citations.keys())
        
        # Generate response based on query content
        if "consumer" in prompt.lower():
            response_content = f"""Based on the Consumer Protection Act, 2019, a consumer is defined as any person who buys goods for consideration or uses goods with the approval of the buyer.

According to the legal definition: "consumer means any person who buys any goods for a consideration which has been paid or promised..." [{citations[0] if citations else 'Citation-1'}]

This definition establishes that consumers include:
1. Direct purchasers of goods
2. Users of goods with buyer's approval
3. Those under deferred payment systems

However, it excludes persons who obtain goods for resale or commercial purposes [{citations[0] if citations else 'Citation-1'}].

**Your Rights as a Consumer:**
As a consumer under this Act, you are entitled to protection against hazardous goods and services, and you have the right to seek redressal for any deficiency in goods or services.

**Disclaimer:** This information is provided for educational purposes only and does not constitute legal advice. For legal advice specific to your situation, please consult a qualified lawyer."""
        
        elif "section" in prompt.lower():
            response_content = f"""Here is the relevant section from the Consumer Protection Act, 2019:

**Section 2: Definitions** [{citations[0] if citations else 'Citation-1'}]

"In this Act, unless the context otherwise requires,—"

This section contains the fundamental definitions that establish the scope and application of the Consumer Protection Act. It defines key terms including 'consumer', 'trader', 'manufacturer', and other essential concepts.

The definitions in this section are crucial for understanding your rights and the Act's applicability to various situations.

**Disclaimer:** This information is provided for educational purposes only and does not constitute legal advice."""
        
        else:
            response_content = f"""Based on the available information in the Consumer Protection Act, 2019:

{context.formatted_text[:300]}...

For more specific information about your situation, please refer to the relevant sections of the Act or consult with a qualified legal professional.

**Disclaimer:** This information is provided for educational purposes only and does not constitute legal advice."""
        
        # Mock response object
        class MockResponse:
            def __init__(self, content, provider):
                self.content = content
                self.provider = provider
                self.model = "mock-model"
                self.usage = {"prompt_tokens": 150, "completion_tokens": 200, "total_tokens": 350}
                self.response_time = 1.5
                self.finish_reason = "stop"
            
            def get_cost_estimate(self):
                return 0.001  # Mock cost
        
        return MockResponse(response_content, self.name)
    
    def is_available(self):
        return True
    
    def get_stats(self):
        return {
            'provider': self.name,
            'model': 'mock-model',
            'request_count': self.request_count,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost
        }


def main():
    """Demonstrate LLM integration with GraphRAG"""
    
    print("🏛️  Nyayamrit: LLM Integration Demo")
    print("=" * 50)
    
    try:
        # Initialize GraphRAG engine
        print("📚 Initializing GraphRAG engine...")
        graphrag_engine = GraphRAGEngine("knowledge_graph")
        
        # Validate knowledge graph
        kg_validation = graphrag_engine.validate_knowledge_graph()
        print(f"Knowledge graph loaded: {kg_validation['is_valid']}")
        print(f"Sections: {kg_validation['stats'].get('sections', 0)}")
        print(f"Definitions: {kg_validation['stats'].get('definitions', 0)}")
        
        # Initialize LLM manager with mock provider
        print("\n🤖 Setting up LLM integration...")
        llm_manager = LLMManager(FallbackStrategy.SEQUENTIAL)
        
        # Add mock provider (in real usage, this would be OpenAI/Anthropic)
        mock_provider = MockLLMProvider("mock-gpt4")
        llm_manager.add_provider("mock", mock_provider, priority=1)
        
        # Initialize validator
        validator = ResponseValidator()
        
        print("✅ LLM integration ready!")
        
        # Demo queries
        demo_queries = [
            {
                "query": "What is a consumer under the Consumer Protection Act?",
                "audience": "citizen",
                "description": "Definition lookup for citizen"
            },
            {
                "query": "Show me Section 2 of CPA 2019",
                "audience": "lawyer", 
                "description": "Section retrieval for lawyer"
            },
            {
                "query": "What are my rights if I bought defective goods?",
                "audience": "citizen",
                "description": "Rights query scenario"
            }
        ]
        
        print("\n" + "=" * 50)
        print("🔍 Processing Demo Queries")
        print("=" * 50)
        
        for i, demo in enumerate(demo_queries, 1):
            print(f"\n📋 Query {i}: {demo['description']}")
            print(f"Question: \"{demo['query']}\"")
            print(f"Audience: {demo['audience']}")
            print("-" * 40)
            
            # Step 1: Process with GraphRAG
            print("🔄 Step 1: GraphRAG processing...")
            graphrag_response = graphrag_engine.process_query(
                query=demo["query"],
                audience=demo["audience"]
            )
            
            print(f"  Intent: {graphrag_response.query_intent.intent_type.value}")
            print(f"  Confidence: {graphrag_response.get_confidence_score():.2f}")
            print(f"  Nodes retrieved: {len(graphrag_response.graph_context.nodes)}")
            print(f"  Citations available: {graphrag_response.llm_context.get_citation_count()}")
            
            # Step 2: Generate LLM response
            print("🤖 Step 2: LLM response generation...")
            llm_response = llm_manager.generate_response(
                query=demo["query"],
                context=graphrag_response.llm_context,
                audience=demo["audience"],
                intent_type=graphrag_response.query_intent.intent_type,
                citation_format=CitationFormat.STANDARD
            )
            
            print(f"  Provider: {llm_response.provider}")
            print(f"  Response time: {llm_response.response_time:.2f}s")
            print(f"  Tokens: {llm_response.usage['total_tokens']}")
            
            # Step 3: Validate response
            print("✅ Step 3: Response validation...")
            citation_constraints = CitationConstraints(
                format_type=CitationFormat.STANDARD,
                require_all_claims=True,
                allow_inference=False
            )
            
            validation_result = validator.validate_response(
                response=llm_response.content,
                context=graphrag_response.llm_context,
                graph_context=graphrag_response.graph_context,
                citation_constraints=citation_constraints
            )
            
            print(f"  Valid: {'✅' if validation_result.is_valid else '❌'}")
            print(f"  Confidence: {validation_result.confidence_score:.2f}")
            print(f"  Citations found: {validation_result.citation_count}")
            print(f"  Issues: {len(validation_result.issues)}")
            
            # Show validation issues if any
            if validation_result.issues:
                print("  Validation issues:")
                for issue in validation_result.issues[:2]:  # Show first 2
                    print(f"    - {issue.severity.value}: {issue.message}")
            
            # Show response preview
            print("\n📄 Response Preview:")
            response_lines = llm_response.content.split('\n')
            for line in response_lines[:8]:  # Show first 8 lines
                if line.strip():
                    print(f"  {line}")
            if len(response_lines) > 8:
                print("  ...")
            
            print()
        
        # Show final statistics
        print("=" * 50)
        print("📊 Final Statistics")
        print("=" * 50)
        
        # GraphRAG stats
        graphrag_stats = graphrag_engine.get_performance_stats()
        print(f"GraphRAG queries processed: {graphrag_stats['total_queries']}")
        print(f"Average processing time: {graphrag_stats['average_processing_time']:.2f}s")
        
        # LLM stats
        llm_stats = llm_manager.get_provider_stats()
        print(f"LLM requests: {llm_stats['manager_stats']['total_requests']}")
        print(f"Success rate: {llm_stats['manager_stats']['success_rate']:.1%}")
        print(f"Total estimated cost: ${llm_stats['manager_stats']['total_cost']:.4f}")
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 Next Steps:")
        print("1. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables")
        print("2. Install: pip install openai anthropic")
        print("3. Replace MockLLMProvider with real providers")
        print("4. Integrate with web interface for complete system")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()