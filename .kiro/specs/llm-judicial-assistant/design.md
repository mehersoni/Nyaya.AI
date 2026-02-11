# Design Document
## Nyayamrit: GraphRAG-Based Judicial Assistant System

### 1. Overview

Nyayamrit is a GraphRAG-based judicial assistant that combines deterministic knowledge graph reasoning with Large Language Model capabilities to provide accurate, citation-grounded legal information. The system architecture prioritizes hallucination mitigation through graph-constrained retrieval and maintains strict separation between authoritative legal text and AI-generated explanations.

**Core Architecture Principles:**
- **Graph-First Retrieval**: All queries traverse the knowledge graph before LLM processing
- **Citation Preservation**: Every response includes traceable citations to source legal provisions
- **Confidence Scoring**: All outputs include confidence metrics based on knowledge graph coverage
- **Human-in-the-Loop**: Low-confidence responses flagged for expert review
- **Modular Design**: Clear separation between ingestion, reasoning, LLM, and presentation layers

## High-Level Architecture

The bird's eye view of your entire system.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ PDF Documents  │  │ User Queries   │  │ Bhashini API   │         │
│  │ (CPA 2019)     │  │ (NL/Regional)  │  │ (Translation)  │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE GRAPH LAYER                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Legal Ontology (Neo4j / JSON)                               │   │
│  │  • Sections, Clauses, Definitions, Rights                    │   │
│  │  • Contains, References, Defines edges                       │   │
│  │  • Amendment tracking with temporal versioning               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GRAPHRAG REASONING ENGINE                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Query Parser │→ │ Graph        │→ │ Context      │               │
│  │ (Intent)     │  │ Traversal    │  │ Builder      │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Confidence   │  │ Citation     │  │ Validation   │               │
│  │ Scorer       │  │ Extractor    │  │ Layer        │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LLM LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  LLM Provider (OpenAI GPT-4 / Anthropic Claude)              │   │
│  │  • Prompt Engineering with retrieved context                 │   │
│  │  • Response generation with citation constraints             │   │
│  │  • Multi-provider fallback support                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Web UI       │  │ REST API     │  │ Mobile UI    │               │
│  │ (React)      │  │ (FastAPI)    │  │ (Future)     │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Translation  │  │ Citation     │  │ Feedback     │               │
│  │ (Bhashini)   │  │ Formatter    │  │ Collection   │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MONITORING & GOVERNANCE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Audit Logs   │  │ Performance  │  │ Quality      │               │
│  │              │  │ Metrics      │  │ Assurance    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

## Major Components

Defined roles for the frontend, backend, and AI services.

### Frontend Components
- **Web UI (React)**: User interface for citizens, lawyers, and judges
- **REST API Client**: Communication with backend services
- **Translation Interface**: Integration with Bhashini API for multilingual support
- **Citation Formatter**: Display legal citations in proper format

### Backend Components
- **FastAPI Server**: Main API gateway and request routing
- **GraphRAG Reasoning Engine**: Core logic for graph traversal and LLM integration
- **Knowledge Graph Layer**: Legal data storage and retrieval (Neo4j/JSON)
- **Authentication & Authorization**: Role-based access control

### AI Services
- **LLM Provider**: OpenAI GPT-4 / Anthropic Claude for response generation
- **Bhashini API**: Government translation service for Indian languages
- **Query Parser**: Natural language intent extraction
- **Confidence Scorer**: Response quality assessment

## System & User Flows

A clear map of how data moves from input to output.

### Query Processing Flow

```
User Query (Hindi)
    ↓
[Translation Layer]
    ↓ (English query)
[Query Parser]
    ↓ (QueryIntent)
[Graph Traversal]
    ↓ (GraphContext with legal provisions)
[Context Builder]
    ↓ (LLMContext with formatted text)
[LLM Provider]
    ↓ (LLM Response with citations)
[Response Validator]
    ↓ (Validated response)
[Confidence Scorer]
    ↓ (Response + confidence score)
[Translation Layer]
    ↓ (Hindi response)
[Response Formatter]
    ↓
Display: Hindi explanation + English legal text + Citations
```

### Knowledge Graph Ingestion Flow

```
PDF Document (CPA 2019)
    ↓
[PDF Parser] → Extract text with page numbers
    ↓
[Section Extractor] → Identify sections and chapters
    ↓
[Clause Parser] → Extract numbered clauses
    ↓
[Definition Extractor] → Extract legal definitions
    ↓
[Reference Detector] → Identify cross-references
    ↓
[Graph Builder] → Create nodes and edges
    ↓
[Schema Validator] → Validate against JSON Schema
    ↓
[Integrity Checker] → Verify referential integrity
    ↓
[Knowledge Graph] → Store in Neo4j/JSON
    ↓
[Index Builder] → Create search indexes
```

## AWS Integration

How you strategically leverage AWS services.

### Core AWS Services
- **Amazon EKS**: Kubernetes cluster for container orchestration
- **Amazon RDS**: PostgreSQL for user data and audit logs
- **Amazon ElastiCache**: Redis for caching frequently accessed data
- **Amazon S3**: Storage for PDF documents and static assets
- **AWS Lambda**: Serverless functions for background processing
- **Amazon CloudFront**: CDN for global content delivery

### Security & Compliance
- **AWS IAM**: Identity and access management
- **AWS KMS**: Key management for encryption
- **AWS CloudTrail**: Audit logging for compliance
- **AWS WAF**: Web application firewall protection
- **AWS Certificate Manager**: SSL/TLS certificate management

### Monitoring & Operations
- **Amazon CloudWatch**: Metrics, logs, and alerting
- **AWS X-Ray**: Distributed tracing for performance monitoring
- **AWS Config**: Configuration compliance monitoring
- **Amazon SNS**: Notification service for alerts

## Technical Logic

Proof that you've thought through how the pieces connect.

### 3. Component Design

#### 3.1 Knowledge Graph Layer

**Purpose**: Store and manage structured legal data with strict schema validation and referential integrity.

**Technology Stack**:
- **Phase 1**: JSON files with JSON Schema validation (existing system)
- **Phase 2+**: Neo4j graph database for complex queries and scalability

**Node Types**:
```python
# Sections
{
  "section_id": "CPA2019_2",
  "act": "Consumer Protection Act, 2019",
  "section_number": "2",
  "title": "Definitions",
  "text": "In this Act, unless the context otherwise requires,—",
  "chapter": "I",
  "source_pdf": "consumer_protection_act_2019.pdf",
  "page_number": 5,
  "effective_date": "2019-08-09",
  "amendment_history": []
}

# Clauses
{
  "clause_id": "CPA2019_2_1",
  "parent_section": "CPA2019_2",
  "label": "(1)",
  "text": "\"advertisement\" means any audio or visual publicity...",
  "clause_type": "definition"
}

# Definitions
{
  "definition_id": "CPA2019_DEF_consumer",
  "term": "consumer",
  "definition": "any person who—(i) buys any goods for a consideration...",
  "defined_in": "CPA2019_2",
  "clause_reference": "CPA2019_2_7"
}

# Rights (extracted from text)
{
  "right_id": "CPA2019_RIGHT_001",
  "description": "Right to be protected against marketing of goods and services which are hazardous to life and property",
  "granted_by": "CPA2019_2_9",
  "beneficiary": "consumer",
  "right_type": "consumer_right"
}
```

**Edge Types**:
```python
# Contains (hierarchical structure)
{
  "parent": "CPA2019_CHAPTER_I",
  "child": "CPA2019_2",
  "relation": "contains"
}

# References (cross-references)
{
  "from": "CPA2019_10",
  "to": "CPA2019_2",
  "reference_type": "cross_reference",
  "context": "as defined in section 2"
}

# Defines (definition relationships)
{
  "source": "CPA2019_2",
  "target": "CPA2019_DEF_consumer",
  "relation": "defines"
}

# Amends (amendment tracking - Phase 2)
{
  "amending_act": "CPA_AMENDMENT_2021",
  "target_section": "CPA2019_2",
  "amendment_type": "modification",
  "effective_date": "2021-07-23"
}
```

**Schema Validation**:
- All nodes and edges validated against JSON Schema Draft 07
- `additionalProperties: false` for strict validation
- Referential integrity checks before commit
- Automated validation in CI/CD pipeline

#### 3.2 GraphRAG Reasoning Engine

**Purpose**: Perform graph-constrained retrieval and reasoning to ground LLM responses in knowledge graph facts.

**Components**:

##### 3.2.1 Query Parser
```python
class QueryParser:
    """Parse natural language queries to extract intent and entities."""
    
    def parse_query(self, query: str, language: str = "en") -> QueryIntent:
        """
        Extract legal intent from user query.
        
        Returns:
            QueryIntent with:
            - intent_type: "definition_lookup", "section_retrieval", 
                          "rights_query", "scenario_analysis"
            - entities: List of legal terms, section numbers
            - temporal_context: Date for temporal queries
            - confidence: Confidence score for intent classification
        """
        pass
```

##### 3.2.2 Graph Traversal Engine
```python
class GraphTraversal:
    """Traverse knowledge graph to retrieve relevant legal provisions."""
    
    def retrieve_context(self, intent: QueryIntent) -> GraphContext:
        """
        Traverse graph based on query intent.
        
        Strategies:
        - Direct lookup: Section/clause by ID
        - Keyword search: Full-text search on legal text
        - Relationship traversal: Follow edges (contains, references, defines)
        - Multi-hop reasoning: Combine multiple provisions
        
        Returns:
            GraphContext with:
            - nodes: List of relevant legal provisions
            - edges: Relationships between provisions
            - citations: Formatted citations for each node
            - confidence: Coverage score based on graph completeness
        """
        pass
    
    def traverse_relationships(self, start_node: str, 
                              relation_types: List[str],
                              max_depth: int = 3) -> List[Node]:
        """Multi-hop graph traversal for complex queries."""
        pass
```

##### 3.2.3 Context Builder
```python
class ContextBuilder:
    """Build structured context for LLM from graph data."""
    
    def build_context(self, graph_context: GraphContext) -> LLMContext:
        """
        Format graph data for LLM consumption.
        
        Structure:
        1. Primary provisions (directly relevant)
        2. Related provisions (cross-references)
        3. Definitions (for legal terms)
        4. Hierarchical context (parent sections/chapters)
        
        Returns:
            LLMContext with:
            - formatted_text: Structured text for LLM prompt
            - citations: Citation map for response validation
            - metadata: Source tracking for audit
        """
        pass
```

##### 3.2.4 Confidence Scorer
```python
class ConfidenceScorer:
    """Assign confidence scores to responses based on graph coverage."""
    
    def score_response(self, query: QueryIntent, 
                      graph_context: GraphContext,
                      llm_response: str) -> ConfidenceScore:
        """
        Calculate confidence based on:
        - Graph coverage: % of query entities found in graph
        - Citation density: Number of citations in response
        - Reasoning chain length: Multi-hop reasoning complexity
        - LLM uncertainty: Model confidence scores
        
        Returns:
            ConfidenceScore with:
            - overall_score: 0.0 to 1.0
            - coverage_score: Graph coverage metric
            - citation_score: Citation quality metric
            - requires_review: Boolean flag for human review
        """
        pass
```

##### 3.2.5 Validation Layer
```python
class ResponseValidator:
    """Validate LLM responses against knowledge graph."""
    
    def validate_response(self, llm_response: str, 
                         graph_context: GraphContext) -> ValidationResult:
        """
        Validate that all legal claims in response are grounded in graph.
        
        Checks:
        - All citations exist in knowledge graph
        - No unsupported legal claims
        - Correct citation format
        - No contradictions with graph data
        
        Returns:
            ValidationResult with:
            - is_valid: Boolean
            - errors: List of validation errors
            - warnings: List of potential issues
            - corrected_response: Auto-corrected version if possible
        """
        pass
```

#### 3.3 LLM Integration Layer

**Purpose**: Interface with LLM providers using graph-constrained prompts to generate explanations.

**Design Principles**:
- **Prompt Engineering**: Structured prompts with retrieved context
- **Citation Constraints**: Explicit instructions to cite sources
- **Multi-Provider Support**: Abstraction layer for different LLM APIs
- **Fallback Strategy**: Graceful degradation if primary LLM unavailable

**LLM Provider Interface**:
```python
class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    def generate_response(self, prompt: str, 
                         context: LLMContext,
                         constraints: Dict) -> LLMResponse:
        """Generate response with graph-constrained prompt."""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 implementation."""
    
    def generate_response(self, prompt: str, 
                         context: LLMContext,
                         constraints: Dict) -> LLMResponse:
        """
        Use GPT-4 with structured prompt:
        
        System: You are Nyayamrit, a legal assistant. You MUST cite 
                all legal claims using [Citation: Section X] format.
                Only use information from the provided context.
        
        Context: {formatted legal provisions from graph}
        
        User Query: {user question}
        
        Instructions:
        - Provide clear explanation in simple language
        - Include exact legal text in quotes
        - Cite every legal claim with [Citation: ...]
        - If information not in context, say "Information not available"
        """
        pass
```

**Prompt Template**:
```python
SYSTEM_PROMPT = """
You are Nyayamrit, an AI legal assistant for Indian law. Your role is to provide 
accurate legal information grounded in authoritative sources.

CRITICAL RULES:
1. ONLY use information from the provided legal context
2. CITE every legal claim using [Citation: Section X, Clause Y]
3. If information is not in context, respond: "Information not available in current knowledge base"
4. Distinguish between legal text (in quotes) and your explanation
5. Use simple, accessible language for citizen queries
6. Include disclaimers that this is information, not legal advice

RESPONSE FORMAT:
- Brief answer to the question
- Relevant legal text (quoted)
- Simple explanation
- Citations for all claims
- Disclaimer
"""

USER_PROMPT_TEMPLATE = """
LEGAL CONTEXT:
{graph_context}

USER QUERY:
{user_question}

AUDIENCE:
{audience_type}  # citizen, lawyer, or judge

Please provide a response following the rules above.
"""
```

#### 3.4 Multilingual Translation Layer

**Purpose**: Integrate with Bhashini API for multilingual support across 10+ Indian languages.

**Translation Workflow**:
```
User Query (Hindi) → Bhashini Translate → English Query
                                              ↓
                                    GraphRAG Processing
                                              ↓
                                    English Response
                                              ↓
                                    Bhashini Translate → Hindi Response
                                              ↓
                                    Display: Hindi explanation + English legal text
```

**Bhashini Integration**:
```python
class BhashiniTranslator:
    """Interface with Bhashini API for translation."""
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.supported_languages = [
            "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or", "as"
        ]
    
    def translate_query(self, text: str, 
                       source_lang: str, 
                       target_lang: str = "en") -> TranslationResult:
        """
        Translate user query to English for processing.
        
        Returns:
            TranslationResult with:
            - translated_text: English translation
            - confidence: Translation confidence score
            - detected_language: Auto-detected source language
            - legal_terms: Identified legal terms (preserved)
        """
        pass
    
    def translate_response(self, text: str, 
                          target_lang: str,
                          legal_glossary: Dict) -> TranslationResult:
        """
        Translate response back to user's language.
        
        Special handling:
        - Preserve legal terminology using glossary
        - Keep citations in English
        - Maintain formatting and structure
        """
        pass
    
    def handle_translation_error(self, error: Exception) -> str:
        """Fallback to English-only mode if translation fails."""
        return "Translation service unavailable. Displaying in English."
```

**Legal Glossary Management**:
```python
class LegalGlossary:
    """Maintain legal term translations across languages."""
    
    def __init__(self):
        self.glossary = {
            "consumer": {
                "hi": "उपभोक्ता",
                "ta": "நுகர்வோர்",
                # ... other languages
            },
            "unfair trade practice": {
                "hi": "अनुचित व्यापार प्रथा",
                # ... other languages
            }
        }
    
    def get_translation(self, term: str, target_lang: str) -> str:
        """Get legal term translation from glossary."""
        pass
    
    def add_term(self, term: str, translations: Dict[str, str]):
        """Add new legal term to glossary (human-validated)."""
        pass
```

#### 3.5 Web Interface Layer

**Purpose**: Provide user-friendly interfaces for citizens, lawyers, and judges.

**Technology Stack**:
- **Frontend**: React with TypeScript
- **Backend API**: FastAPI (Python)
- **State Management**: Redux
- **UI Components**: Material-UI or Chakra UI
- **Accessibility**: WCAG 2.1 Level AA compliance

**User Interface Components**:

##### 3.5.1 Citizen Interface
```typescript
interface CitizenChatInterface {
  // Chat-based interface with conversational flow
  components: {
    ChatWindow: React.FC;           // Main chat interface
    QueryInput: React.FC;           // Text input with language selector
    ResponseDisplay: React.FC;      // Formatted response with citations
    ExampleQuestions: React.FC;     // Suggested queries
    LanguageSelector: React.FC;     // 10+ Indian languages
    DisclaimerBanner: React.FC;     // Legal disclaimer
  };
  
  features: {
    conversationHistory: boolean;   // Maintain context
    citationHighlighting: boolean;  // Clickable citations
    feedbackButtons: boolean;       // Thumbs up/down
    shareResponse: boolean;         // Share via link
  };
}
```

##### 3.5.2 Lawyer Interface
```typescript
interface LawyerResearchInterface {
  components: {
    AdvancedSearch: React.FC;       // Boolean queries, filters
    CitationViewer: React.FC;       // Detailed provision view
    CrossReferencePanel: React.FC;  // Related provisions
    ExportTools: React.FC;          // Citation export formats
    AnnotationEditor: React.FC;     // Private notes
    ResearchHistory: React.FC;      // Query history
  };
  
  features: {
    bulkCitationValidation: boolean;
    apiAccess: boolean;             // REST API for integrations
    amendmentTracking: boolean;     // Temporal queries
    citationExport: string[];       // ["Bluebook", "Indian Citation Manual"]
  };
}
```

##### 3.5.3 Judge Interface (Phase 4)
```typescript
interface JudgeAnalysisInterface {
  components: {
    CaseAnalyzer: React.FC;         // Case law analysis
    PrecedentSearch: React.FC;      // Similar case finder
    StatutoryLinkage: React.FC;     // Link cases to statutes
    BiasDetector: React.FC;         // Bias flagging
    AuditLog: React.FC;             // Interaction history
  };
  
  features: {
    secureAccess: boolean;          // MFA, role-based access
    precedentAnalysis: boolean;     // ML-powered insights
    patternRecognition: boolean;    // Case outcome patterns
    auditTrail: boolean;            // Comprehensive logging
  };
  
  security: {
    authentication: "MFA";
    authorization: "RBAC";
    auditLogging: "comprehensive";
  };
}
```

**API Design**:
```python
# FastAPI Backend
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI(title="Nyayamrit API")

class QueryRequest(BaseModel):
    query: str
    language: str = "en"
    audience: str = "citizen"  # citizen, lawyer, judge
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    citations: List[Citation]
    confidence_score: float
    requires_review: bool
    translated: bool
    original_language: str

@app.post("/api/v1/query")
async def process_query(request: QueryRequest, 
                       user: User = Depends(get_current_user)) -> QueryResponse:
    """
    Main query endpoint.
    
    Flow:
    1. Translate query if non-English
    2. Parse intent and extract entities
    3. Traverse knowledge graph
    4. Build context for LLM
    5. Generate response with LLM
    6. Validate response against graph
    7. Calculate confidence score
    8. Translate response if needed
    9. Return formatted response
    """
    pass

@app.get("/api/v1/section/{section_id}")
async def get_section(section_id: str) -> Section:
    """Direct section retrieval by ID."""
    pass

@app.get("/api/v1/definition/{term}")
async def get_definition(term: str) -> Definition:
    """Definition lookup by legal term."""
    pass

@app.post("/api/v1/validate-citations")
async def validate_citations(citations: List[str]) -> ValidationResult:
    """Bulk citation validation for lawyers."""
    pass
```

#### 3.6 Monitoring and Governance Layer

**Purpose**: Ensure system quality, performance, and ethical compliance through continuous monitoring.

**Components**:

##### 3.6.1 Audit Logging
```python
class AuditLogger:
    """Comprehensive audit logging for governance."""
    
    def log_query(self, user_id: str, query: str, 
                 response: str, confidence: float,
                 audience: str, timestamp: datetime):
        """Log all user interactions."""
        pass
    
    def log_judge_interaction(self, judge_id: str, 
                             case_id: str, query: str,
                             response: str, timestamp: datetime):
        """Special logging for judge features with enhanced security."""
        pass
    
    def log_validation_failure(self, query: str, response: str,
                              validation_errors: List[str]):
        """Log responses that failed validation."""
        pass
```

##### 3.6.2 Performance Monitoring
```python
class PerformanceMonitor:
    """Track system performance metrics."""
    
    metrics = {
        "query_latency": Histogram,          # Response time distribution
        "graph_traversal_time": Histogram,   # Graph query performance
        "llm_latency": Histogram,            # LLM API response time
        "translation_latency": Histogram,    # Bhashini API latency
        "confidence_scores": Histogram,      # Distribution of confidence
        "validation_failures": Counter,      # Failed validations
        "concurrent_users": Gauge,           # Active users
        "cache_hit_rate": Gauge,            # Cache effectiveness
    }
    
    def track_query_performance(self, query_id: str, 
                               stages: Dict[str, float]):
        """Track performance across query processing stages."""
        pass
```

##### 3.6.3 Quality Assurance
```python
class QualityAssurance:
    """Continuous quality monitoring and improvement."""
    
    def analyze_user_feedback(self, feedback: List[Feedback]) -> QAReport:
        """Analyze thumbs up/down and detailed feedback."""
        pass
    
    def identify_knowledge_gaps(self, failed_queries: List[Query]) -> List[Gap]:
        """Identify areas where knowledge graph is incomplete."""
        pass
    
    def flag_for_expert_review(self, low_confidence_responses: List[Response]):
        """Queue responses for legal expert validation."""
        pass
    
    def generate_qa_report(self, period: str) -> QAReport:
        """
        Generate quality assurance report:
        - Citation accuracy rate
        - User satisfaction scores
        - Knowledge graph coverage
        - Validation failure rate
        - Expert review outcomes
        """
        pass
```

### 4. Data Flow

#### 4.1 Query Processing Flow

```
User Query (Hindi)
    ↓
[Translation Layer]
    ↓ (English query)
[Query Parser]
    ↓ (QueryIntent)
[Graph Traversal]
    ↓ (GraphContext with legal provisions)
[Context Builder]
    ↓ (LLMContext with formatted text)
[LLM Provider]
    ↓ (LLM Response with citations)
[Response Validator]
    ↓ (Validated response)
[Confidence Scorer]
    ↓ (Response + confidence score)
[Translation Layer]
    ↓ (Hindi response)
[Response Formatter]
    ↓
Display: Hindi explanation + English legal text + Citations
```

#### 4.2 Knowledge Graph Ingestion Flow

```
PDF Document (CPA 2019)
    ↓
[PDF Parser] → Extract text with page numbers
    ↓
[Section Extractor] → Identify sections and chapters
    ↓
[Clause Parser] → Extract numbered clauses
    ↓
[Definition Extractor] → Extract legal definitions
    ↓
[Reference Detector] → Identify cross-references
    ↓
[Graph Builder] → Create nodes and edges
    ↓
[Schema Validator] → Validate against JSON Schema
    ↓
[Integrity Checker] → Verify referential integrity
    ↓
[Knowledge Graph] → Store in Neo4j/JSON
    ↓
[Index Builder] → Create search indexes
```

### 5. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


#### Property 1: Legal Text Preservation (Round-Trip)
*For any* legal text ingested into the knowledge graph, retrieving it by its identifier should return the exact same text without modification, interpretation, or paraphrasing.

**Validates: Requirements 1.3**

#### Property 2: Ingestion Completeness
*For any* legal document with known structure (sections, clauses, definitions, cross-references), ingesting it should extract and represent all entities as graph nodes and edges with complete structural preservation.

**Validates: Requirements 1.1, 1.2, 7.1**

#### Property 3: Deterministic Identifier Assignment (Idempotence)
*For any* legal entity, ingesting it multiple times should produce the same unique identifier each time.

**Validates: Requirements 1.4**

#### Property 4: Schema Validation Correctness
*For any* knowledge graph data, validation should pass if and only if the data conforms to the JSON schema and maintains referential integrity.

**Validates: Requirements 1.5**

#### Property 5: Graph-First Retrieval Ordering
*For any* user query, the system should retrieve relevant legal provisions from the knowledge graph before invoking the LLM for response generation.

**Validates: Requirements 2.1**

#### Property 6: Citation Grounding
*For any* LLM-generated response containing legal claims, all claims should have corresponding citations that exist in the knowledge graph.

**Validates: Requirements 2.2**

#### Property 7: No Hallucination on Missing Data
*For any* query about information not present in the knowledge graph, the response should explicitly state "information not available" and contain no fabricated legal claims.

**Validates: Requirements 2.3**

#### Property 8: Visual Distinction Between Legal Text and Explanation
*For any* response, the rendered output should have distinct formatting for retrieved legal text versus LLM-generated explanations.

**Validates: Requirements 2.5, 3.4**

#### Property 9: Confidence Score Assignment
*For any* response, the system should assign a confidence score between 0.0 and 1.0 based on knowledge graph coverage, and responses with confidence below 0.8 should be flagged for human review.

**Validates: Requirements 2.6, 2.7, 11.2**

#### Property 10: Intent Extraction Completeness
*For any* natural language query, the system should extract at least one intent classification (definition_lookup, section_retrieval, rights_query, or scenario_analysis).

**Validates: Requirements 3.1**

#### Property 11: Domain-Specific Retrieval
*For any* query about consumer rights, all retrieved provisions should be from CPA 2019 and semantically related to consumer rights.

**Validates: Requirements 3.2**

#### Property 12: Conversation Context Preservation
*For any* follow-up question within a session, the system should have access to context from all previous questions in that session.

**Validates: Requirements 3.5**

#### Property 13: Translation Round-Trip Workflow
*For any* query in a supported regional language, the system should translate it to English for processing, generate a response, translate the explanation back to the user's language, and display both the translated explanation and original English legal text.

**Validates: Requirements 4.3, 4.4, 4.6**

#### Property 14: Legal Glossary Preservation
*For any* legal term in the glossary, translation should use the glossary term rather than generic translation.

**Validates: Requirements 4.5**

#### Property 15: Clickable Citation Links
*For any* response containing citations, all citations should be rendered as clickable links to the corresponding legal provisions.

**Validates: Requirements 5.2**

#### Property 16: Exact Citation Retrieval
*For any* valid section number, clause reference, or legal term, the system should retrieve the exact corresponding legal provision from the knowledge graph.

**Validates: Requirements 6.1**

#### Property 17: Boolean Query Correctness
*For any* Boolean query (AND, OR, NOT), the results should satisfy the Boolean logic constraints.

**Validates: Requirements 6.2**

#### Property 18: Cross-Reference Display
*For any* section with cross-references in the knowledge graph, displaying that section should include all cross-references and related provisions.

**Validates: Requirements 6.3**

#### Property 19: Case Law Linkage
*For any* case law that references a statutory provision, there should be a corresponding edge in the knowledge graph linking the case to the statute.

**Validates: Requirements 7.2**

#### Property 20: Multi-Provision Retrieval
*For any* query requiring multiple legal provisions, the system should identify and retrieve all relevant sections via graph path traversal.

**Validates: Requirements 8.2**

#### Property 21: Conflict Detection
*For any* pair of legal provisions that contradict each other, the system should flag the conflict in the response.

**Validates: Requirements 8.3**

#### Property 22: Reasoning Explanation with Citations
*For any* response involving multi-step reasoning, the explanation should include step-by-step citations showing the reasoning chain.

**Validates: Requirements 8.5**

#### Property 23: PII Storage with Consent
*For any* stored data containing personally identifiable information, there should be a corresponding consent record.

**Validates: Requirements 10.2**

#### Property 24: Validation Before Display
*For any* LLM response, validation against the knowledge graph should occur before the response is displayed to the user.

**Validates: Requirements 11.1**

#### Property 25: Performance Thresholds
*For any* simple query (single section lookup), response time should be less than 3 seconds, and for any complex query (multi-step reasoning), response time should be less than 10 seconds.

**Validates: Requirements 12.1, 12.2**

#### Property 26: Bias Flagging
*For any* legal precedent with detected bias indicators (gender, caste, religion), the system should flag it for judicial awareness.

**Validates: Requirements 13.2**

#### Property 27: No Case Outcome Predictions
*For any* response, it should not contain predictions about case outcomes or judicial decisions.

**Validates: Requirements 13.3**

#### Property 28: Disclaimer Presence
*For any* response, a disclaimer about AI limitations and the non-binding nature of the information should be present.

**Validates: Requirements 13.4**

### 6. Error Handling

#### 6.1 Knowledge Graph Errors
- **Missing Entity**: Return "Information not available" with suggestion to check official sources
- **Broken Reference**: Log error, attempt to resolve via alternative graph paths
- **Schema Validation Failure**: Reject ingestion, log detailed error, alert administrators

#### 6.2 LLM Errors
- **API Timeout**: Retry with exponential backoff, fallback to secondary provider
- **Rate Limit**: Queue request, inform user of delay
- **Invalid Response**: Reject response, log for analysis, return error message to user
- **Hallucination Detected**: Block response, flag for human review, log incident

#### 6.3 Translation Errors
- **Bhashini API Unavailable**: Fallback to English-only mode, inform user
- **Translation Confidence Low**: Display warning, show original English text
- **Unsupported Language**: Inform user, suggest supported languages

#### 6.4 Performance Errors
- **Query Timeout**: Return partial results with explanation
- **High Load**: Implement rate limiting, queue requests
- **Cache Miss**: Fetch from knowledge graph, update cache

### 7. Testing Strategy

#### 7.1 Unit Testing
- Test each component independently (query parser, graph traversal, LLM interface)
- Mock external dependencies (LLM API, Bhashini API)
- Test edge cases (empty queries, malformed input, missing data)
- Test error handling paths

#### 7.2 Property-Based Testing
- Implement all 28 correctness properties as property-based tests
- Use Hypothesis (Python) for property test generation
- Run minimum 100 iterations per property test
- Tag each test with feature name and property number
- Example:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: llm-judicial-assistant, Property 1: Legal Text Preservation
@given(st.text(min_size=10, max_size=1000))
def test_legal_text_preservation(legal_text):
    """For any legal text, ingestion then retrieval should return exact same text."""
    # Ingest text into knowledge graph
    entity_id = ingest_legal_text(legal_text)
    
    # Retrieve text by ID
    retrieved_text = retrieve_legal_text(entity_id)
    
    # Assert exact match
    assert retrieved_text == legal_text
```

#### 7.3 Integration Testing
- Test full query processing pipeline end-to-end
- Test knowledge graph ingestion pipeline
- Test multilingual workflow with Bhashini integration
- Test authentication and authorization flows

#### 7.4 Performance Testing
- Load testing with 1000+ concurrent users
- Latency testing for simple and complex queries
- Cache effectiveness testing
- Database query optimization testing

#### 7.5 Security Testing
- Penetration testing for web interface
- Authentication and authorization testing
- Data encryption verification
- Audit log integrity testing

#### 7.6 User Acceptance Testing
- Citizen interface testing with non-legal users (n=100)
- Lawyer interface testing with legal professionals (n=50)
- Judge interface testing with judicial officers (n=20, Phase 4)
- Multilingual testing with native speakers (n=10 per language)

#### 7.7 Bias and Ethics Testing
- Bias audit of case law data (Phase 4)
- Fairness metrics evaluation
- Transparency and explainability testing
- Human oversight validation

### 8. Deployment Architecture

#### 8.1 Development Environment
- Local development with Docker Compose
- JSON-based knowledge graph for rapid iteration
- Mock LLM and translation services for testing
- Hot reload for frontend and backend

#### 8.2 Staging Environment
- Kubernetes cluster on cloud infrastructure
- Neo4j graph database
- Real LLM and Bhashini API integration
- Subset of production data for testing

#### 8.3 Production Environment
- Multi-region Kubernetes deployment for high availability
- Neo4j cluster with read replicas
- Redis cache for frequently accessed data
- CDN for static assets
- Load balancer with auto-scaling
- Monitoring and alerting (Prometheus, Grafana)
- Centralized logging (ELK stack)

**Infrastructure Diagram**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (HTTPS)                    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Web Server  │    │  Web Server  │    │  Web Server  │
│  (React)     │    │  (React)     │    │  (React)     │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                    │
└─────────────────────────────────────────────────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  GraphRAG    │    │  LLM Service │    │  Translation │
│  Engine      │    │  (OpenAI)    │    │  (Bhashini)  │
└──────────────┘    └──────────────┘    └──────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              Neo4j Graph Database (Cluster)                 │
│              • Primary (Read/Write)                         │
│              • Replicas (Read-Only)                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Cache Layer                        │
└─────────────────────────────────────────────────────────────┘
```

### 9. Security Architecture

#### 9.1 Authentication and Authorization
- **Citizens**: Anonymous access or optional registration
- **Lawyers**: Email/password with MFA, OAuth2 integration
- **Judges**: Mandatory MFA, government ID verification, role-based access control

#### 9.2 Data Protection
- TLS 1.3 for all data in transit
- Encryption at rest for sensitive data
- PII anonymization for analytics
- Regular security audits and penetration testing

#### 9.3 Audit and Compliance
- Comprehensive audit logs for all user interactions
- Tamper-proof logging for judge features
- GDPR/DPDP Act compliance for data handling
- Regular compliance reviews

### 10. Scalability Considerations

#### 10.1 Horizontal Scaling
- Stateless API servers for easy scaling
- Load balancing across multiple instances
- Auto-scaling based on CPU/memory/request rate

#### 10.2 Database Scaling
- Neo4j clustering with read replicas
- Sharding by Act/legal domain (future)
- Query optimization and indexing

#### 10.3 Caching Strategy
- Redis for frequently accessed provisions
- CDN for static assets
- LLM response caching for common queries
- Cache invalidation on knowledge graph updates

#### 10.4 Performance Optimization
- Lazy loading for large legal documents
- Pagination for search results
- Asynchronous processing for non-critical tasks
- Connection pooling for database access

### 11. Monitoring and Observability

#### 11.1 Metrics
- Query latency (p50, p95, p99)
- Error rates by component
- LLM API usage and costs
- Translation API usage
- Cache hit rates
- Concurrent users
- Knowledge graph query performance

#### 11.2 Logging
- Structured logging (JSON format)
- Centralized log aggregation (ELK stack)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs for request tracing

#### 11.3 Alerting
- High error rates
- Performance degradation
- External API failures
- Security incidents
- Low confidence response spikes

#### 11.4 Dashboards
- Real-time system health dashboard
- User analytics dashboard
- Quality assurance dashboard
- Cost monitoring dashboard

### 12. Technology Stack Summary

**Backend**:
- Python 3.9+ (FastAPI, Pydantic, Hypothesis)
- Neo4j (graph database)
- Redis (caching)
- PostgreSQL (user data, audit logs)

**Frontend**:
- React with TypeScript
- Redux (state management)
- Material-UI or Chakra UI (components)
- Axios (API client)

**Infrastructure**:
- Docker and Kubernetes
- Nginx (load balancer)
- Prometheus and Grafana (monitoring)
- ELK stack (logging)

**External Services**:
- OpenAI GPT-4 or Anthropic Claude (LLM)
- Bhashini API (translation)
- Government cloud infrastructure (preferred)

**Development Tools**:
- Git (version control)
- GitHub Actions (CI/CD)
- pytest (testing)
- mypy (type checking)
- black (code formatting)
- ESLint and Prettier (frontend linting)

### 13. Future Enhancements

#### 13.1 Phase 5: Advanced Features
- Voice interface with speech-to-text
- Legal document analysis and summarization
- Automated legal research report generation
- Integration with e-courts system

#### 13.2 Phase 6: Expansion
- State-level Acts and regulations
- International law and comparative analysis
- Legal education modules
- Blockchain-based audit trails

#### 13.3 Technical Improvements
- Local LLM deployment for cost reduction
- Advanced caching strategies
- Real-time knowledge graph updates
- Federated learning for privacy-preserving ML

---

## Conclusion

Nyayamrit's design prioritizes accuracy, transparency, and ethical AI use through GraphRAG architecture, comprehensive validation, and human oversight. The phased approach ensures incremental validation and continuous improvement, while the modular design allows for future enhancements and scalability. By grounding all LLM outputs in a deterministic knowledge graph and maintaining clear separation between authoritative legal text and AI-generated explanations, Nyayamrit aims to provide reliable, accessible legal information to citizens, lawyers, and judges across India.


---

## Appendix A: Critical Design Refinements

### A.1 Authority Boundary Signaling (Epistemic Scope)

**Purpose**: Explicitly model the scope and limitations of each response to prevent over-reliance and make limitations machine-visible.

**Scope Metadata Model**:
```python
class ScopeMetadata(BaseModel):
    """Epistemic scope metadata for every response."""
    
    jurisdiction: str              # "India (Central)" or "India (State: Maharashtra)"
    legal_domain: str              # "Consumer Protection Act, 2019"
    temporal_validity: date        # "As of 2024-01-15"
    coverage_completeness: float   # 0.0 to 1.0 (e.g., 0.92 = 92% of Act ingested)
    exclusions: List[str]          # ["State-level rules", "Case law", "Subordinate legislation"]
    last_updated: datetime         # When knowledge graph was last updated
    amendment_status: str          # "Current" or "Pending amendments not yet ingested"
```

**Response Format with Scope**:
```python
class NyayamritResponse(BaseModel):
    response_text: str
    citations: List[Citation]
    confidence_score: float
    scope_metadata: ScopeMetadata
    disclaimers: List[str]
    requires_review: bool
```

**UI Display**:
- Scope metadata displayed in collapsible panel
- Visual indicators for coverage completeness (progress bar)
- Warnings for low coverage or pending amendments
- Automatic alerts when temporal validity is outdated

**Benefits**:
- Prevents citizen over-reliance on incomplete information
- Makes limitations machine-visible for automated checks
- Supports UI warnings automatically based on metadata
- Enables temporal queries with explicit validity dates

### A.2 Amendment Ingestion Governance (Temporal Correctness)

**Purpose**: Define authoritative sources, update pipeline, and governance for maintaining temporal correctness.

**Authoritative Source Hierarchy**:
```python
class AuthoritativeSource(Enum):
    GAZETTE_OF_INDIA = 1        # Highest authority
    INDIA_CODE = 2              # Official government portal
    MINISTRY_NOTIFICATIONS = 3  # Ministry-specific updates
    OFFICIAL_GAZETTES = 4       # State gazettes for state laws
```

**Amendment Ingestion Pipeline**:
```
Gazette of India Publication
    ↓
[Automated Monitoring] → Alert on new amendment
    ↓
[Human Review Gate] → Legal expert validates amendment
    ↓ (Approved)
[Ingestion Pipeline] → Extract amendment details
    ↓
[Graph Update] → Create amendment nodes and edges
    ↓
[Validation] → Verify referential integrity
    ↓
[Temporal Versioning] → Update effective dates
    ↓
[Deployment] → Update production knowledge graph
    ↓
[Notification] → Alert users of updated provisions
```

**Update Latency SLA**:
- **Critical amendments** (affecting fundamental rights): 3-5 business days
- **Standard amendments**: 7-14 business days
- **Minor corrections**: 14-30 business days

**Human-in-the-Loop Update Gate**:
```python
class AmendmentReview:
    """Human review process for amendments."""
    
    def review_amendment(self, amendment: Amendment) -> ReviewDecision:
        """
        Legal expert reviews amendment before ingestion.
        
        Checks:
        - Authenticity of source
        - Correct interpretation of amendment text
        - Impact on existing provisions
        - Cross-references and dependencies
        
        Returns:
            ReviewDecision: APPROVE, REJECT, or REQUEST_CLARIFICATION
        """
        pass
```

**Rollback Semantics**:
```python
class VersionControl:
    """Version control for knowledge graph updates."""
    
    def create_snapshot(self, version_id: str, metadata: Dict):
        """Create snapshot before amendment ingestion."""
        pass
    
    def rollback_to_version(self, version_id: str):
        """Rollback to previous version if issues detected."""
        pass
    
    def compare_versions(self, v1: str, v2: str) -> VersionDiff:
        """Compare two versions to identify changes."""
        pass
```

**Temporal Correctness Guarantees**:
- All provisions tagged with `effective_date` and `superseded_date`
- Temporal queries return provisions valid as of specified date
- Amendment history preserved for audit and analysis
- Automatic flagging of provisions with pending amendments

### A.3 Conflict Semantics Formalization

**Purpose**: Define precise conflict types and response behavior for handling contradictions in legal provisions.

**Conflict Types**:
```python
class ConflictType(Enum):
    EXPLICIT_TEXTUAL_CONTRADICTION = "explicit_contradiction"
    # Two provisions directly contradict each other
    # Example: Section A says "X is allowed", Section B says "X is prohibited"
    
    TEMPORAL_OVERRIDE = "temporal_override"
    # Later amendment supersedes earlier provision
    # Example: 2021 amendment modifies 2019 provision
    
    JURISDICTIONAL_DIVERGENCE = "jurisdictional_divergence"
    # Central law vs. State law conflict
    # Example: Central Act allows X, State Act prohibits X
    
    INTERPRETIVE_DIVERGENCE = "interpretive_divergence"
    # Case law interprets statute differently than plain text
    # Example: Supreme Court narrows scope of statutory provision
    
    HIERARCHICAL_CONFLICT = "hierarchical_conflict"
    # Constitutional provision vs. statutory provision
    # Example: Act conflicts with Fundamental Right

class LegalConflict(BaseModel):
    conflict_id: str
    conflict_type: ConflictType
    provisions: List[str]          # IDs of conflicting provisions
    description: str               # Human-readable explanation
    resolution_principle: str      # "Later in time", "Higher authority", etc.
    detected_date: datetime
    requires_expert_review: bool
```

**Conflict Detection Algorithm**:
```python
class ConflictDetector:
    """Detect conflicts between legal provisions."""
    
    def detect_explicit_contradiction(self, p1: Provision, p2: Provision) -> Optional[LegalConflict]:
        """
        Detect textual contradictions using semantic analysis.
        
        Method:
        - Extract legal predicates (allows, prohibits, requires)
        - Compare predicates for same subject matter
        - Flag if predicates are contradictory
        """
        pass
    
    def detect_temporal_override(self, provisions: List[Provision]) -> List[LegalConflict]:
        """
        Detect amendments that override earlier provisions.
        
        Method:
        - Check amendment_history for each provision
        - Identify superseded provisions
        - Create temporal_override conflicts
        """
        pass
    
    def detect_hierarchical_conflict(self, p1: Provision, p2: Provision) -> Optional[LegalConflict]:
        """
        Detect conflicts between different levels of law.
        
        Hierarchy (highest to lowest):
        1. Constitution
        2. Central Acts
        3. State Acts
        4. Rules and Regulations
        """
        pass
```

**Response Behavior for Conflicts**:
```python
class ConflictResponseStrategy:
    """Define how system responds to detected conflicts."""
    
    def handle_conflict(self, conflict: LegalConflict) -> ConflictResponse:
        """
        System behavior when conflict detected:
        
        1. FLAG, NOT RESOLVE
           - System does not choose which provision applies
           - Presents both provisions to user
           - Explains nature of conflict
        
        2. PROVIDE CONTEXT
           - Cite dates and effective periods
           - Explain hierarchical relationship
           - Reference resolution principles (if known)
        
        3. RECOMMEND EXPERT CONSULTATION
           - For complex conflicts, recommend legal advice
           - Provide contact information for legal aid
        
        Returns:
            ConflictResponse with:
            - conflict_explanation: Human-readable description
            - all_provisions: All conflicting provisions
            - resolution_guidance: General principles (not binding advice)
            - expert_consultation_recommended: Boolean
        """
        pass
```

**Example Conflict Response**:
```
⚠️ POTENTIAL CONFLICT DETECTED

Conflict Type: Temporal Override
Provisions:
- Section 2(7) of CPA 2019 (Original, effective 2019-08-09)
- Section 2(7) of CPA 2019 (Amended, effective 2021-07-23)

Explanation:
The definition of "consumer" was amended in 2021. The current definition 
(as of 2024-01-15) is the amended version. The original definition is 
superseded but preserved for historical reference.

Resolution Principle:
Later amendment supersedes earlier provision (lex posterior derogat legi priori).

Current Applicable Provision:
[Display amended Section 2(7)]

Historical Provision (Superseded):
[Display original Section 2(7)]

⚠️ This is informational only. For legal advice, consult a qualified lawyer.
```

### A.4 Confidence Score Calibration

**Purpose**: Define empirical calibration process and threshold justification for confidence scores.

**Confidence Score Components**:
```python
class ConfidenceComponents(BaseModel):
    """Detailed breakdown of confidence score calculation."""
    
    graph_coverage: float          # 0.0-1.0: % of query entities found in graph
    citation_density: float        # 0.0-1.0: Citations per claim ratio
    reasoning_chain_length: float  # 0.0-1.0: Inverse of chain length (shorter = higher confidence)
    llm_uncertainty: float         # 0.0-1.0: LLM model confidence
    temporal_validity: float       # 0.0-1.0: How current is the data
    
    def calculate_overall(self) -> float:
        """
        Weighted average of components:
        - graph_coverage: 40%
        - citation_density: 30%
        - reasoning_chain_length: 15%
        - llm_uncertainty: 10%
        - temporal_validity: 5%
        """
        return (
            0.40 * self.graph_coverage +
            0.30 * self.citation_density +
            0.15 * self.reasoning_chain_length +
            0.10 * self.llm_uncertainty +
            0.05 * self.temporal_validity
        )
```

**Empirical Calibration Process**:
```python
class ConfidenceCalibration:
    """Calibrate confidence scores against human expert judgments."""
    
    def calibrate_thresholds(self, gold_set: List[QueryResponsePair]) -> CalibrationResult:
        """
        Calibration process:
        
        1. Create gold standard dataset
           - 500+ queries with expert-validated responses
           - Diverse query types (simple, complex, ambiguous)
           - Expert ratings: CORRECT, PARTIALLY_CORRECT, INCORRECT
        
        2. Calculate confidence scores for all gold set responses
        
        3. Analyze correlation between confidence and correctness
           - Plot confidence vs. accuracy
           - Identify optimal thresholds
        
        4. Set thresholds based on desired precision/recall
           - High confidence (>0.9): 95%+ accuracy
           - Medium confidence (0.7-0.9): 85%+ accuracy
           - Low confidence (<0.7): <85% accuracy, requires review
        
        5. Validate on held-out test set
        
        Returns:
            CalibrationResult with:
            - optimal_thresholds: Dict[str, float]
            - accuracy_by_threshold: Dict[float, float]
            - calibration_curve: List[Tuple[float, float]]
        """
        pass
```

**Threshold Justification**:
```python
CONFIDENCE_THRESHOLDS = {
    "high": 0.9,        # 95%+ accuracy, auto-display without review
    "medium": 0.8,      # 90%+ accuracy, display with caution notice
    "low": 0.7,         # 85%+ accuracy, flag for expert review
    "very_low": 0.5,    # <85% accuracy, block display, require review
}

THRESHOLD_JUSTIFICATION = {
    0.9: "Empirically validated to achieve 95%+ accuracy on gold standard dataset",
    0.8: "Achieves 90%+ accuracy, suitable for citizen queries with caution notice",
    0.7: "Achieves 85%+ accuracy, requires expert review before display",
    0.5: "Below acceptable accuracy threshold, must be reviewed and corrected",
}
```

**Continuous Calibration**:
```python
class ContinuousCalibration:
    """Ongoing calibration based on user feedback and expert review."""
    
    def update_calibration(self, feedback: List[UserFeedback]):
        """
        Continuously update calibration based on:
        - User feedback (thumbs up/down)
        - Expert review outcomes
        - Detected errors and corrections
        
        Process:
        - Monthly recalibration using new feedback data
        - Adjust component weights if needed
        - Update thresholds if accuracy drifts
        """
        pass
    
    def generate_calibration_report(self, period: str) -> CalibrationReport:
        """
        Generate report on confidence score performance:
        - Accuracy by confidence bucket
        - False positive/negative rates
        - Calibration curve
        - Recommendations for threshold adjustments
        """
        pass
```

**UI Display of Confidence**:
```
High Confidence (0.9-1.0):
✅ High confidence response
   Based on complete knowledge graph coverage

Medium Confidence (0.8-0.9):
⚠️ Medium confidence response
   Some information may be incomplete. Verify with official sources.

Low Confidence (0.7-0.8):
⚠️ Low confidence response
   Limited knowledge graph coverage. This response has been flagged for expert review.
   Please consult official sources or legal counsel.

Very Low (<0.7):
❌ Response blocked
   Insufficient information to provide reliable answer.
   Please consult official legal sources or a qualified lawyer.
```