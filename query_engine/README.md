# Nyayamrit GraphRAG Reasoning Engine

This directory contains the implementation of the GraphRAG (Graph-based Retrieval-Augmented Generation) reasoning engine for the Nyayamrit judicial assistant system.

## Overview

The GraphRAG engine combines deterministic knowledge graph reasoning with structured context building to provide accurate, citation-grounded legal information. It implements a three-stage pipeline:

1. **Query Parsing**: Extract legal intent from natural language queries
2. **Graph Traversal**: Navigate knowledge graph to find relevant provisions  
3. **Context Building**: Format retrieved data for LLM consumption

## Architecture

```
User Query → QueryParser → GraphTraversal → ContextBuilder → LLM Context
```

### Components

#### 1. QueryParser (`query_parser.py`)
- Extracts intent from natural language queries
- Supports 4 intent types: definition_lookup, section_retrieval, rights_query, scenario_analysis
- Identifies legal terms, section numbers, and entities
- Provides confidence scoring for intent classification

#### 2. GraphTraversal (`graph_traversal.py`)
- Navigates the legal knowledge graph to find relevant provisions
- Supports multiple traversal strategies:
  - Direct lookup by section/clause ID
  - Keyword search across legal text
  - Relationship traversal (contains, references, defines)
  - Multi-hop reasoning for complex queries
- Returns structured GraphContext with nodes, edges, and citations

#### 3. ContextBuilder (`context_builder.py`)
- Formats graph data into structured context for LLM consumption
- Organizes content into sections:
  - Primary provisions (directly relevant)
  - Legal definitions
  - Consumer rights
  - Related provisions
  - Hierarchical context
- Supports audience-specific formatting (citizen, lawyer, judge)
- Manages context length limits and citation generation

#### 4. GraphRAGEngine (`graphrag_engine.py`)
- Main orchestration engine that coordinates all components
- Provides end-to-end query processing
- Includes performance monitoring and error handling
- Supports reasoning explanation and query suggestions

## Knowledge Graph Structure

The engine works with JSON-based knowledge graph data:

### Node Types
- **Sections**: Legal sections with full text and metadata
- **Clauses**: Numbered clauses within sections
- **Definitions**: Legal term definitions
- **Rights**: Consumer rights extracted from legal text

### Edge Types
- **Contains**: Hierarchical relationships (chapter → section → clause)
- **References**: Cross-references between sections
- **Defines**: Definition relationships (section → term)

## Usage

### Basic Usage

```python
from query_engine import GraphRAGEngine

# Initialize engine
engine = GraphRAGEngine()

# Process a query
response = engine.process_query("What are my consumer rights?", audience="citizen")

# Access results
print(f"Intent: {response.query_intent.intent_type}")
print(f"Confidence: {response.get_confidence_score()}")
print(f"Context: {response.llm_context.formatted_text}")
print(f"Citations: {response.llm_context.citations}")
```

### Advanced Usage

```python
# Validate knowledge graph
validation = engine.validate_knowledge_graph()
print(f"Valid: {validation['is_valid']}")

# Get performance stats
stats = engine.get_performance_stats()
print(f"Avg processing time: {stats['average_processing_time']}")

# Explain reasoning
explanation = engine.explain_reasoning(response)
print(explanation)

# Get similar queries
suggestions = engine.get_similar_queries("consumer rights")
```

## Query Types Supported

### 1. Definition Lookup
- **Example**: "What does 'consumer' mean?"
- **Intent**: definition_lookup
- **Returns**: Legal definitions with source citations

### 2. Section Retrieval
- **Example**: "Show me Section 18"
- **Intent**: section_retrieval  
- **Returns**: Full section text with related clauses

### 3. Rights Query
- **Example**: "What are my consumer rights?"
- **Intent**: rights_query
- **Returns**: Relevant consumer rights with enforcement mechanisms

### 4. Scenario Analysis
- **Example**: "I bought a defective product, what can I do?"
- **Intent**: scenario_analysis
- **Returns**: Relevant provisions, rights, and procedural information

## Audience-Specific Formatting

The engine formats responses for different audiences:

### Citizen
- Simplified language and headers
- Plain-language explanations
- Focus on practical rights and remedies

### Lawyer
- Technical legal language
- Comprehensive citation summaries
- Cross-reference information

### Judge
- Judicial context and analysis
- Precedent-related information
- Legal reasoning frameworks

## Performance Characteristics

- **Query Processing**: < 100ms for simple queries, < 500ms for complex
- **Knowledge Graph**: Supports 100+ sections, 50+ definitions, 35+ rights
- **Context Length**: Configurable, default 8000 characters
- **Confidence Scoring**: 0.0-1.0 scale with human review threshold at 0.8

## Testing

Run the test suite:

```bash
# Basic functionality test
python query_engine/test_graphrag.py

# Comprehensive integration tests
python test_graphrag_integration.py

# Interactive demo
python demo_graphrag.py
```

## Configuration

The engine can be configured during initialization:

```python
engine = GraphRAGEngine(
    knowledge_graph_path="path/to/knowledge_graph",
    max_context_length=8000
)
```

## Error Handling

The engine includes comprehensive error handling:
- Invalid queries return low-confidence responses
- Missing knowledge graph data is handled gracefully
- Processing errors are logged and returned in response metadata

## Integration Points

The GraphRAG engine is designed to integrate with:
- **LLM Providers**: Formatted context ready for GPT-4, Claude, etc.
- **Translation Services**: Bhashini API for multilingual support
- **Web Interfaces**: REST API endpoints for citizen/lawyer/judge UIs
- **Monitoring Systems**: Performance metrics and audit logging

## Future Enhancements

Planned improvements include:
- Neo4j graph database support for better scalability
- Machine learning-based intent classification
- Temporal query support for amendment tracking
- Advanced reasoning with legal precedents
- Bias detection and mitigation

## Dependencies

- Python 3.9+
- Standard library only (json, re, pathlib, dataclasses, enum, typing)
- No external dependencies for core functionality

## License

Part of the Nyayamrit judicial assistant system.