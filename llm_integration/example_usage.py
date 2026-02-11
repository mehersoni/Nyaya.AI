"""
Example Usage of LLM Integration Layer

This script demonstrates how to use the LLM integration layer with the
GraphRAG engine to generate legal responses with proper citation constraints
and multi-provider fallback.
"""

import os
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import LLM integration components
from llm_integration import (
    LLMManager, OpenAIProvider, AnthropicProvider,
    PromptTemplateManager, CitationConstraints, CitationFormat,
    ResponseValidator, FallbackStrategy
)

# Import query engine components
from query_engine.graphrag_engine import GraphRAGEngine
from query_engine.query_parser import IntentType


class NyayamritLLMService:
    """
    Complete LLM service for Nyayamrit that integrates GraphRAG with LLM providers.
    
    This service coordinates:
    - Knowledge graph retrieval via GraphRAG
    - LLM response generation with multiple providers
    - Response validation and citation checking
    - Audience-specific formatting
    """
    
    def __init__(self, knowledge_graph_path: str = "knowledge_graph"):
        """
        Initialize the Nyayamrit LLM service.
        
        Args:
            knowledge_graph_path: Path to knowledge graph data
        """
        # Initialize GraphRAG engine
        self.graphrag_engine = GraphRAGEngine(knowledge_graph_path)
        
        # Initialize LLM manager with fallback strategy
        self.llm_manager = LLMManager(FallbackStrategy.PERFORMANCE_OPTIMIZED)
        
        # Initialize response validator
        self.validator = ResponseValidator()
        
        # Setup providers
        self._setup_providers()
        
        logger.info("Nyayamrit LLM service initialized")
    
    def _setup_providers(self):
        """Setup LLM providers with API keys from environment variables."""
        
        # Setup OpenAI provider if API key available
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                openai_provider = OpenAIProvider(
                    api_key=openai_key,
                    model="gpt-4",
                    temperature=0.1,
                    max_tokens=2000
                )
                
                self.llm_manager.add_provider(
                    name="openai_gpt4",
                    provider=openai_provider,
                    priority=2,  # High priority for GPT-4
                    max_requests_per_minute=50,
                    cost_per_token=0.00003  # Approximate GPT-4 cost
                )
                
                logger.info("Added OpenAI GPT-4 provider")
                
            except Exception as e:
                logger.warning(f"Failed to setup OpenAI provider: {e}")
        
        # Setup Anthropic provider if API key available
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            try:
                anthropic_provider = AnthropicProvider(
                    api_key=anthropic_key,
                    model="claude-3-sonnet-20240229",
                    temperature=0.1,
                    max_tokens=2000
                )
                
                self.llm_manager.add_provider(
                    name="anthropic_claude",
                    provider=anthropic_provider,
                    priority=1,  # Lower priority as fallback
                    max_requests_per_minute=40,
                    cost_per_token=0.000015  # Approximate Claude cost
                )
                
                logger.info("Added Anthropic Claude provider")
                
            except Exception as e:
                logger.warning(f"Failed to setup Anthropic provider: {e}")
        
        # Check if any providers were added
        if not self.llm_manager.providers:
            logger.warning("No LLM providers configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables.")
    
    def process_legal_query(self, query: str, audience: str = "citizen",
                           language: str = "en", citation_format: str = "standard") -> dict:
        """
        Process a legal query end-to-end with GraphRAG and LLM integration.
        
        Args:
            query: User's legal query
            audience: Target audience (citizen, lawyer, judge)
            language: Query language (currently only 'en' supported)
            citation_format: Citation format (standard, detailed, bluebook, indian)
            
        Returns:
            Dictionary with response, validation results, and metadata
        """
        try:
            logger.info(f"Processing query: '{query}' for audience: {audience}")
            
            # Step 1: Process query through GraphRAG engine
            graphrag_response = self.graphrag_engine.process_query(
                query=query,
                language=language,
                audience=audience
            )
            
            logger.info(f"GraphRAG processing complete. Confidence: {graphrag_response.get_confidence_score():.2f}")
            
            # Step 2: Generate LLM response if providers available
            if not self.llm_manager.providers:
                return self._create_fallback_response(query, graphrag_response)
            
            # Map citation format
            format_mapping = {
                "standard": CitationFormat.STANDARD,
                "detailed": CitationFormat.DETAILED,
                "bluebook": CitationFormat.BLUEBOOK,
                "indian": CitationFormat.INDIAN
            }
            citation_fmt = format_mapping.get(citation_format, CitationFormat.STANDARD)
            
            # Generate response with LLM
            llm_response = self.llm_manager.generate_response(
                query=query,
                context=graphrag_response.llm_context,
                audience=audience,
                intent_type=graphrag_response.query_intent.intent_type,
                citation_format=citation_fmt
            )
            
            logger.info(f"LLM response generated by {llm_response.provider} in {llm_response.response_time:.2f}s")
            
            # Step 3: Validate response
            citation_constraints = CitationConstraints(
                format_type=citation_fmt,
                require_all_claims=True,
                allow_inference=False
            )
            
            validation_result = self.validator.validate_response(
                response=llm_response.content,
                context=graphrag_response.llm_context,
                graph_context=graphrag_response.graph_context,
                citation_constraints=citation_constraints
            )
            
            logger.info(f"Response validation complete. Valid: {validation_result.is_valid}, "
                       f"Confidence: {validation_result.confidence_score:.2f}")
            
            # Step 4: Compile final response
            return {
                "success": True,
                "response": llm_response.content,
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "confidence_score": validation_result.confidence_score,
                    "citation_count": validation_result.citation_count,
                    "issues": [
                        {
                            "severity": issue.severity.value,
                            "type": issue.issue_type,
                            "message": issue.message
                        }
                        for issue in validation_result.issues
                    ]
                },
                "metadata": {
                    "query_intent": graphrag_response.query_intent.intent_type.value,
                    "graphrag_confidence": graphrag_response.get_confidence_score(),
                    "llm_provider": llm_response.provider,
                    "processing_time": graphrag_response.processing_metadata["processing_time"] + llm_response.response_time,
                    "token_usage": llm_response.usage,
                    "estimated_cost": llm_response.get_cost_estimate(),
                    "audience": audience,
                    "citation_format": citation_format
                },
                "reasoning_explanation": self.graphrag_engine.explain_reasoning(graphrag_response)
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": self._get_error_response(query, str(e), audience)
            }
    
    def _create_fallback_response(self, query: str, graphrag_response) -> dict:
        """Create fallback response when no LLM providers are available."""
        
        # Use GraphRAG context to create a basic response
        context = graphrag_response.llm_context
        
        fallback_content = f"""Based on the Consumer Protection Act, 2019, here is the relevant information:

{context.formatted_text}

Available Citations:
{chr(10).join(f"- {key}: {citation}" for key, citation in context.citations.items())}

Disclaimer: This is a basic information retrieval. For comprehensive legal analysis, please ensure LLM providers are configured or consult a qualified lawyer."""
        
        return {
            "success": True,
            "response": fallback_content,
            "validation": {
                "is_valid": True,
                "confidence_score": graphrag_response.get_confidence_score(),
                "citation_count": len(context.citations),
                "issues": []
            },
            "metadata": {
                "query_intent": graphrag_response.query_intent.intent_type.value,
                "graphrag_confidence": graphrag_response.get_confidence_score(),
                "llm_provider": "fallback",
                "processing_time": graphrag_response.processing_metadata["processing_time"],
                "mode": "fallback_no_llm"
            },
            "reasoning_explanation": self.graphrag_engine.explain_reasoning(graphrag_response)
        }
    
    def _get_error_response(self, query: str, error: str, audience: str) -> str:
        """Generate error response for failed queries."""
        
        prompt_manager = PromptTemplateManager()
        return prompt_manager.get_template_for_error("unknown", audience)
    
    def get_service_stats(self) -> dict:
        """Get comprehensive service statistics."""
        
        graphrag_stats = self.graphrag_engine.get_performance_stats()
        llm_stats = self.llm_manager.get_provider_stats()
        
        return {
            "graphrag_engine": graphrag_stats,
            "llm_providers": llm_stats,
            "service_health": {
                "graphrag_loaded": len(graphrag_stats["knowledge_graph_stats"]["sections_loaded"]) > 0,
                "llm_providers_available": len([p for p in llm_stats["providers"].values() if p["enabled"]]) > 0
            }
        }
    
    def validate_knowledge_graph(self) -> dict:
        """Validate the knowledge graph completeness."""
        return self.graphrag_engine.validate_knowledge_graph()


def main():
    """Example usage of the Nyayamrit LLM service."""
    
    print("🏛️  Nyayamrit LLM Integration Example")
    print("=" * 50)
    
    # Initialize service
    print("Initializing Nyayamrit LLM service...")
    service = NyayamritLLMService()
    
    # Check service health
    stats = service.get_service_stats()
    print(f"GraphRAG loaded: {stats['service_health']['graphrag_loaded']}")
    print(f"LLM providers available: {stats['service_health']['llm_providers_available']}")
    
    # Validate knowledge graph
    kg_validation = service.validate_knowledge_graph()
    print(f"Knowledge graph valid: {kg_validation['is_valid']}")
    if kg_validation['warnings']:
        print(f"Warnings: {len(kg_validation['warnings'])}")
    
    print("\n" + "=" * 50)
    
    # Example queries for different audiences
    example_queries = [
        {
            "query": "What is a consumer under the Consumer Protection Act?",
            "audience": "citizen",
            "description": "Citizen asking for definition"
        },
        {
            "query": "Show me Section 2 of CPA 2019",
            "audience": "lawyer",
            "description": "Lawyer requesting specific section"
        },
        {
            "query": "What are my rights if I bought a defective product?",
            "audience": "citizen",
            "description": "Citizen asking about rights"
        },
        {
            "query": "I received misleading advertisement, what can I do?",
            "audience": "citizen",
            "description": "Citizen scenario analysis"
        }
    ]
    
    # Process example queries
    for i, example in enumerate(example_queries, 1):
        print(f"\n📋 Example {i}: {example['description']}")
        print(f"Query: \"{example['query']}\"")
        print(f"Audience: {example['audience']}")
        print("-" * 30)
        
        # Process query
        result = service.process_legal_query(
            query=example["query"],
            audience=example["audience"],
            citation_format="standard"
        )
        
        if result["success"]:
            print("✅ Response generated successfully")
            print(f"Validation: {'✅ Valid' if result['validation']['is_valid'] else '❌ Invalid'}")
            print(f"Confidence: {result['validation']['confidence_score']:.2f}")
            print(f"Citations: {result['validation']['citation_count']}")
            
            if result["metadata"].get("llm_provider"):
                print(f"Provider: {result['metadata']['llm_provider']}")
                print(f"Processing time: {result['metadata']['processing_time']:.2f}s")
            
            # Show first 200 characters of response
            response_preview = result["response"][:200] + "..." if len(result["response"]) > 200 else result["response"]
            print(f"\nResponse preview:\n{response_preview}")
            
            # Show validation issues if any
            if result["validation"]["issues"]:
                print(f"\nValidation issues ({len(result['validation']['issues'])}):")
                for issue in result["validation"]["issues"][:3]:  # Show first 3
                    print(f"  - {issue['severity']}: {issue['message']}")
        
        else:
            print("❌ Query processing failed")
            print(f"Error: {result['error']}")
        
        print()
    
    # Show final statistics
    print("=" * 50)
    print("📊 Final Service Statistics")
    final_stats = service.get_service_stats()
    
    print(f"Total GraphRAG queries: {final_stats['graphrag_engine']['total_queries']}")
    print(f"Average processing time: {final_stats['graphrag_engine']['average_processing_time']:.2f}s")
    
    if final_stats['llm_providers']['providers']:
        print(f"LLM requests: {final_stats['llm_providers']['manager_stats']['total_requests']}")
        print(f"Success rate: {final_stats['llm_providers']['manager_stats']['success_rate']:.2%}")
        print(f"Total cost: ${final_stats['llm_providers']['manager_stats']['total_cost']:.4f}")


if __name__ == "__main__":
    main()