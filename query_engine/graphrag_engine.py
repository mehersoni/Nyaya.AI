"""
GraphRAG Reasoning Engine

This module provides the main GraphRAG engine that coordinates query parsing,
graph traversal, and context building for the Nyayamrit judicial assistant.

The engine integrates:
- QueryParser: Extract intent from natural language queries
- GraphTraversal: Navigate knowledge graph to find relevant provisions
- ContextBuilder: Format retrieved data for LLM consumption
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from query_engine.query_parser import QueryParser, QueryIntent
from query_engine.graph_traversal import GraphTraversal, GraphContext
from query_engine.context_builder import ContextBuilder, LLMContext


@dataclass
class GraphRAGResponse:
    """Complete response from GraphRAG engine"""
    query_intent: QueryIntent
    graph_context: GraphContext
    llm_context: LLMContext
    processing_metadata: Dict[str, Any]
    
    def get_confidence_score(self) -> float:
        """Get overall confidence score for the response"""
        return self.llm_context.metadata.get('confidence', 0.0)
    
    def requires_human_review(self) -> bool:
        """Check if response requires human expert review"""
        return self.get_confidence_score() < 0.8
    
    def get_complexity_level(self) -> str:
        """Get query complexity level"""
        return self.processing_metadata.get('complexity', 'unknown')


class GraphRAGEngine:
    """Main GraphRAG reasoning engine that coordinates all components."""
    
    def __init__(self, knowledge_graph_path: str = "knowledge_graph", 
                 max_context_length: int = 8000):
        """
        Initialize the GraphRAG engine.
        
        Args:
            knowledge_graph_path: Path to knowledge graph data
            max_context_length: Maximum context length for LLM
        """
        self.query_parser = QueryParser()
        self.graph_traversal = GraphTraversal(knowledge_graph_path)
        self.context_builder = ContextBuilder(max_context_length)
        
        # Performance tracking
        self.query_count = 0
        self.total_processing_time = 0.0
    
    def process_query(self, query: str, language: str = "en", 
                     audience: str = "citizen") -> GraphRAGResponse:
        """
        Process a natural language query through the complete GraphRAG pipeline.
        
        Args:
            query: User's natural language query
            language: Query language (default: "en")
            audience: Target audience ("citizen", "lawyer", "judge")
            
        Returns:
            GraphRAGResponse with complete processing results
        """
        import time
        start_time = time.time()
        
        try:
            # Step 1: Parse query intent
            query_intent = self.query_parser.parse_query(query, language)
            
            # Step 2: Traverse knowledge graph
            graph_context = self.graph_traversal.retrieve_context(query_intent)
            
            # Step 3: Build LLM context
            llm_context = self.context_builder.build_context(graph_context, query_intent)
            
            # Step 4: Format for specific audience
            llm_context = self.context_builder.format_for_audience(llm_context, audience)
            
            # Calculate processing metadata
            processing_time = time.time() - start_time
            complexity = self.query_parser.get_query_complexity(query_intent)
            
            processing_metadata = {
                'processing_time': processing_time,
                'complexity': complexity,
                'language': language,
                'audience': audience,
                'nodes_retrieved': len(graph_context.nodes),
                'edges_traversed': len(graph_context.edges),
                'context_length': llm_context.get_total_length(),
                'citation_count': llm_context.get_citation_count()
            }
            
            # Update performance tracking
            self.query_count += 1
            self.total_processing_time += processing_time
            
            return GraphRAGResponse(
                query_intent=query_intent,
                graph_context=graph_context,
                llm_context=llm_context,
                processing_metadata=processing_metadata
            )
            
        except Exception as e:
            # Return error response
            error_metadata = {
                'error': str(e),
                'processing_time': time.time() - start_time,
                'complexity': 'error',
                'language': language,
                'audience': audience
            }
            
            # Create minimal error context
            error_context = LLMContext(
                formatted_text=f"Error processing query: {str(e)}",
                citations={},
                metadata={'error': True, 'confidence': 0.0},
                primary_provisions=[],
                related_provisions=[],
                definitions=[],
                hierarchical_context=[]
            )
            
            # Create minimal error intent
            from query_engine.query_parser import IntentType
            error_intent = QueryIntent(
                intent_type=IntentType.SCENARIO_ANALYSIS,
                entities=[],
                section_numbers=[],
                legal_terms=[],
                confidence=0.0,
                original_query=query
            )
            
            # Create minimal error graph context
            error_graph_context = GraphContext(
                nodes=[],
                edges=[],
                citations=[],
                confidence=0.0,
                traversal_path=[]
            )
            
            return GraphRAGResponse(
                query_intent=error_intent,
                graph_context=error_graph_context,
                llm_context=error_context,
                processing_metadata=error_metadata
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the engine."""
        avg_processing_time = (self.total_processing_time / self.query_count 
                              if self.query_count > 0 else 0.0)
        
        return {
            'total_queries': self.query_count,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': avg_processing_time,
            'knowledge_graph_stats': {
                'sections_loaded': len(self.graph_traversal.sections),
                'definitions_loaded': len(self.graph_traversal.definitions),
                'rights_loaded': len(self.graph_traversal.rights),
                'clauses_loaded': len(self.graph_traversal.clauses)
            }
        }
    
    def validate_knowledge_graph(self) -> Dict[str, Any]:
        """Validate the loaded knowledge graph for completeness."""
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'stats': {}
        }
        
        try:
            # Check if basic data is loaded
            if not self.graph_traversal.sections:
                validation_results['errors'].append("No sections loaded")
                validation_results['is_valid'] = False
            
            if not self.graph_traversal.definitions:
                validation_results['warnings'].append("No definitions loaded")
            
            if not self.graph_traversal.rights:
                validation_results['warnings'].append("No rights loaded")
            
            # Check for orphaned references
            section_ids = {s['section_id'] for s in self.graph_traversal.sections}
            
            # Check references in edges
            for edge in self.graph_traversal.references_edges:
                if edge['from'] not in section_ids:
                    validation_results['warnings'].append(
                        f"Reference from unknown section: {edge['from']}"
                    )
                if edge['to'] not in section_ids:
                    validation_results['warnings'].append(
                        f"Reference to unknown section: {edge['to']}"
                    )
            
            # Collect stats
            validation_results['stats'] = {
                'sections': len(self.graph_traversal.sections),
                'clauses': len(self.graph_traversal.clauses),
                'definitions': len(self.graph_traversal.definitions),
                'rights': len(self.graph_traversal.rights),
                'contains_edges': len(self.graph_traversal.contains_edges),
                'reference_edges': len(self.graph_traversal.references_edges),
                'defines_edges': len(self.graph_traversal.defines_edges)
            }
            
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {str(e)}")
            validation_results['is_valid'] = False
        
        return validation_results
    
    def explain_reasoning(self, response: GraphRAGResponse) -> str:
        """
        Generate explanation of the reasoning process for transparency.
        
        Args:
            response: GraphRAG response to explain
            
        Returns:
            Human-readable explanation of the reasoning process
        """
        explanation_parts = []
        
        # Query analysis
        intent = response.query_intent
        explanation_parts.append(f"**Query Analysis:**")
        explanation_parts.append(f"- Intent Type: {intent.intent_type.value}")
        explanation_parts.append(f"- Confidence: {intent.confidence:.2f}")
        explanation_parts.append(f"- Legal Terms Found: {', '.join(intent.legal_terms) if intent.legal_terms else 'None'}")
        explanation_parts.append(f"- Section Numbers: {', '.join(intent.section_numbers) if intent.section_numbers else 'None'}")
        
        # Graph traversal
        graph_ctx = response.graph_context
        explanation_parts.append(f"\n**Knowledge Graph Traversal:**")
        explanation_parts.append(f"- Nodes Retrieved: {len(graph_ctx.nodes)}")
        explanation_parts.append(f"- Relationships Found: {len(graph_ctx.edges)}")
        explanation_parts.append(f"- Traversal Path: {' → '.join(graph_ctx.traversal_path[:5])}")
        if len(graph_ctx.traversal_path) > 5:
            explanation_parts.append("  (truncated)")
        
        # Context building
        llm_ctx = response.llm_context
        explanation_parts.append(f"\n**Context Construction:**")
        explanation_parts.append(f"- Primary Provisions: {len(llm_ctx.primary_provisions)}")
        explanation_parts.append(f"- Related Provisions: {len(llm_ctx.related_provisions)}")
        explanation_parts.append(f"- Definitions Included: {len(llm_ctx.definitions)}")
        explanation_parts.append(f"- Citations Generated: {llm_ctx.get_citation_count()}")
        explanation_parts.append(f"- Context Length: {llm_ctx.get_total_length()} characters")
        
        # Overall assessment
        explanation_parts.append(f"\n**Overall Assessment:**")
        explanation_parts.append(f"- Final Confidence: {response.get_confidence_score():.2f}")
        explanation_parts.append(f"- Complexity Level: {response.get_complexity_level()}")
        explanation_parts.append(f"- Requires Review: {'Yes' if response.requires_human_review() else 'No'}")
        
        return "\n".join(explanation_parts)
    
    def get_similar_queries(self, query: str, limit: int = 5) -> List[str]:
        """
        Get suggestions for similar queries based on the current query.
        
        Args:
            query: Current query
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested similar queries
        """
        # Parse current query to understand intent
        intent = self.query_parser.parse_query(query)
        
        suggestions = []
        
        if intent.intent_type.value == "definition_lookup":
            suggestions.extend([
                "What does 'unfair trade practice' mean?",
                "Define consumer rights under CPA 2019",
                "What is the meaning of 'defective goods'?",
                "Explain the term 'misleading advertisement'"
            ])
        elif intent.intent_type.value == "section_retrieval":
            suggestions.extend([
                "Show me Section 2 of Consumer Protection Act",
                "What does Section 18 say about consumer rights?",
                "Find Section 35 about filing complaints",
                "Get Section 21 about penalties"
            ])
        elif intent.intent_type.value == "rights_query":
            suggestions.extend([
                "What are my rights as a consumer?",
                "How can I file a complaint against unfair practices?",
                "What compensation can I claim for defective products?",
                "Where can I seek redressal for consumer disputes?"
            ])
        elif intent.intent_type.value == "scenario_analysis":
            suggestions.extend([
                "I bought a defective product, what can I do?",
                "The seller is refusing to refund, what are my options?",
                "I saw a misleading advertisement, how to complain?",
                "The service provider is charging extra, is this legal?"
            ])
        
        # Add some general suggestions
        suggestions.extend([
            "What is Consumer Protection Act 2019?",
            "How to file a consumer complaint?",
            "What are the different consumer commissions?"
        ])
        
        # Remove duplicates and limit
        unique_suggestions = list(set(suggestions))
        return unique_suggestions[:limit]