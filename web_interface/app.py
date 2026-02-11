"""
Nyayamrit FastAPI Backend - Main API Gateway

This module implements the main FastAPI application with core endpoints for the
Nyayamrit GraphRAG-based judicial assistant system.

Core endpoints:
- /api/v1/query: Main query processing endpoint
- /api/v1/section/{section_id}: Direct section retrieval
- /api/v1/definition/{term}: Definition lookup
- /api/v1/validate-citations: Bulk citation validation

Features:
- Authentication and authorization framework
- Integration with GraphRAG reasoning engine
- Multilingual support via translation layer
- Comprehensive error handling and logging
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

# Import Nyayamrit components
from query_engine.graphrag_engine import GraphRAGEngine, GraphRAGResponse
from llm_integration.llm_manager import LLMManager, FallbackStrategy
from llm_integration.providers import OpenAIProvider, LLMProviderType
from llm_integration.confidence_scorer import ConfidenceScorer
from llm_integration.validation import ResponseValidator
from llm_integration.prompt_templates import CitationConstraints, CitationFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Global components (initialized in lifespan)
graphrag_engine: Optional[GraphRAGEngine] = None
llm_manager: Optional[LLMManager] = None
confidence_scorer: Optional[ConfidenceScorer] = None
response_validator: Optional[ResponseValidator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting Nyayamrit API server...")
    
    global graphrag_engine, llm_manager, confidence_scorer, response_validator
    
    try:
        # Initialize GraphRAG engine
        graphrag_engine = GraphRAGEngine(
            knowledge_graph_path="knowledge_graph",
            max_context_length=8000
        )
        logger.info("GraphRAG engine initialized")
        
        # Initialize LLM manager with fallback strategy
        llm_manager = LLMManager(fallback_strategy=FallbackStrategy.SEQUENTIAL)
        
        # Add OpenAI provider if API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            openai_provider = OpenAIProvider(
                api_key=openai_api_key,
                model="gpt-4",
                max_tokens=2000,
                temperature=0.1
            )
            llm_manager.add_provider(
                name="openai_gpt4",
                provider=openai_provider,
                priority=10,
                max_requests_per_minute=60,
                cost_per_token=0.00003  # Approximate cost
            )
            logger.info("OpenAI GPT-4 provider added")
        else:
            logger.warning("OPENAI_API_KEY not found - LLM functionality will be limited")
        
        # Initialize confidence scorer
        confidence_scorer = ConfidenceScorer()
        logger.info("Confidence scorer initialized")
        
        # Initialize response validator
        response_validator = ResponseValidator(
            knowledge_graph_path="knowledge_graph"
        )
        logger.info("Response validator initialized")
        
        # Validate knowledge graph
        validation_results = graphrag_engine.validate_knowledge_graph()
        if not validation_results['is_valid']:
            logger.error(f"Knowledge graph validation failed: {validation_results['errors']}")
        else:
            logger.info(f"Knowledge graph validated successfully: {validation_results['stats']}")
        
        logger.info("Nyayamrit API server startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nyayamrit API server...")


# Create FastAPI application
app = FastAPI(
    title="Nyayamrit API",
    description="GraphRAG-based Judicial Assistant for Indian Legal System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)


# Pydantic models for API requests and responses
class QueryRequest(BaseModel):
    """Request model for query processing."""
    query: str = Field(..., min_length=1, max_length=1000, description="User's natural language query")
    language: str = Field(default="en", description="Query language code (en, hi, ta, etc.)")
    audience: str = Field(default="citizen", description="Target audience: citizen, lawyer, or judge")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation context")
    
    @validator('audience')
    def validate_audience(cls, v):
        if v not in ['citizen', 'lawyer', 'judge']:
            raise ValueError('audience must be one of: citizen, lawyer, judge')
        return v
    
    @validator('language')
    def validate_language(cls, v):
        # Supported languages (initially English only, expand for multilingual support)
        supported_langs = ['en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'or', 'as']
        if v not in supported_langs:
            raise ValueError(f'language must be one of: {", ".join(supported_langs)}')
        return v


class Citation(BaseModel):
    """Citation information for legal provisions."""
    section_id: str = Field(..., description="Unique section identifier")
    section_number: str = Field(..., description="Human-readable section number")
    title: str = Field(..., description="Section title")
    act: str = Field(..., description="Act name")
    url: Optional[str] = Field(default=None, description="URL to full text")


class QueryResponse(BaseModel):
    """Response model for query processing."""
    response: str = Field(..., description="Generated response text")
    citations: List[Citation] = Field(default=[], description="List of legal citations")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Response confidence score")
    requires_review: bool = Field(..., description="Whether response requires human review")
    translated: bool = Field(default=False, description="Whether response was translated")
    original_language: str = Field(default="en", description="Original query language")
    processing_time: float = Field(..., description="Processing time in seconds")
    reasoning_explanation: Optional[str] = Field(default=None, description="Explanation of reasoning process")


class Section(BaseModel):
    """Section information model."""
    section_id: str
    section_number: str
    title: str
    text: str
    act: str
    chapter: Optional[str] = None
    page_number: Optional[int] = None
    effective_date: Optional[str] = None  # Changed from datetime to string


class Definition(BaseModel):
    """Definition information model."""
    term: str
    definition: str
    defined_in: str
    section_reference: str
    act: str


class ValidationResult(BaseModel):
    """Citation validation result."""
    citation: str
    is_valid: bool
    section_found: bool
    message: str
    suggested_correction: Optional[str] = None


class BulkValidationRequest(BaseModel):
    """Request for bulk citation validation."""
    citations: List[str] = Field(..., min_items=1, max_items=100, description="List of citations to validate")


class BulkValidationResponse(BaseModel):
    """Response for bulk citation validation."""
    results: List[ValidationResult]
    total_citations: int
    valid_citations: int
    invalid_citations: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    components: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None


# Import authentication components
from web_interface.auth import (
    User, UserLogin, UserCreate, TokenResponse, 
    auth_manager, Permission, UserRole
)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """
    Get current user from authentication token.
    
    Validates JWT tokens and returns user information.
    Allows anonymous access for basic citizen queries.
    """
    if not credentials:
        # Allow anonymous access for citizen queries
        return auth_manager.create_anonymous_user()
    
    # Validate JWT token
    token = credentials.credentials
    user = auth_manager.verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def check_permission(required_permission: Permission):
    """Dependency to check if user has required permission."""
    async def permission_checker(user: User = Depends(get_current_user)):
        if user and user.has_permission(required_permission):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{required_permission.value}' required"
        )
    return permission_checker


# Middleware for request logging and performance monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and measure response time."""
    start_time = time.time()
    
    # Generate request ID
    request_id = f"req_{int(time.time() * 1000)}"
    
    # Log request
    logger.info(f"[{request_id}] {request.method} {request.url.path} - Start")
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(f"[{request_id}] {request.method} {request.url.path} - "
                   f"Status: {response.status_code}, Time: {process_time:.3f}s")
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] {request.method} {request.url.path} - "
                    f"Error: {str(e)}, Time: {process_time:.3f}s")
        raise


# Authentication endpoints

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register_user(user_data: UserCreate) -> TokenResponse:
    """
    Register a new user account.
    
    Creates a new user with the specified role and returns an access token.
    Note: In production, user registration would require additional verification.
    """
    try:
        # Create user
        user = auth_manager.create_user(user_data)
        
        # Generate access token
        access_token = auth_manager.create_access_token(user)
        
        logger.info(f"New user registered: {user.user_id} ({user.role.value})")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_manager.config.access_token_expire_minutes * 60,
            user_id=user.user_id,
            role=user.role.value,
            permissions=[perm.value for perm in user.permissions]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin) -> TokenResponse:
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns a JWT access token for API access.
    """
    try:
        # Authenticate user
        user = auth_manager.authenticate_user(login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate access token
        access_token = auth_manager.create_access_token(user)
        
        logger.info(f"User logged in: {user.user_id} ({user.role.value})")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_manager.config.access_token_expire_minutes * 60,
            user_id=user.user_id,
            role=user.role.value,
            permissions=[perm.value for perm in user.permissions]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@app.post("/api/v1/auth/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: User = Depends(get_current_user)
):
    """
    Logout user and revoke access token.
    
    Revokes the current access token to prevent further use.
    """
    if credentials:
        token = credentials.credentials
        auth_manager.revoke_token(token)
        logger.info(f"User logged out: {user.user_id}")
    
    return {"message": "Successfully logged out"}


@app.get("/api/v1/auth/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    Returns information about the currently authenticated user.
    """
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role.value,
        "permissions": [perm.value for perm in user.permissions],
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Nyayamrit API",
        "description": "GraphRAG-based Judicial Assistant for Indian Legal System",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    components = {}
    
    # Check GraphRAG engine
    if graphrag_engine:
        try:
            stats = graphrag_engine.get_performance_stats()
            components["graphrag_engine"] = "healthy"
        except Exception as e:
            components["graphrag_engine"] = f"unhealthy: {str(e)}"
    else:
        components["graphrag_engine"] = "not_initialized"
    
    # Check LLM manager
    if llm_manager:
        try:
            provider_health = llm_manager.health_check_all_providers()
            healthy_providers = sum(1 for status in provider_health.values() if status)
            components["llm_manager"] = f"healthy ({healthy_providers} providers)"
        except Exception as e:
            components["llm_manager"] = f"unhealthy: {str(e)}"
    else:
        components["llm_manager"] = "not_initialized"
    
    # Overall status
    overall_status = "healthy" if all("healthy" in status for status in components.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version="1.0.0",
        components=components
    )


@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    user: User = Depends(get_current_user)
) -> QueryResponse:
    """
    Main query processing endpoint.
    
    Processes natural language queries through the complete GraphRAG pipeline:
    1. Parse query intent and extract entities
    2. Traverse knowledge graph to retrieve relevant provisions
    3. Build structured context for LLM
    4. Generate response using LLM with citation constraints
    5. Validate response against knowledge graph
    6. Calculate confidence score
    7. Return formatted response with citations
    """
    start_time = time.time()
    
    try:
        # Validate components are initialized
        if not graphrag_engine or not llm_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service components not initialized"
            )
        
        # Process query through GraphRAG engine
        logger.info(f"Processing query for user {user.user_id}: {request.query[:100]}...")
        
        graphrag_response = graphrag_engine.process_query(
            query=request.query,
            language=request.language,
            audience=request.audience
        )
        
        # Generate LLM response if context is available
        if graphrag_response.llm_context.primary_provisions:
            try:
                # Determine query complexity for provider selection
                complexity = graphrag_response.get_complexity_level()
                
                # Generate response using LLM manager
                llm_response = llm_manager.generate_response(
                    query=request.query,
                    context=graphrag_response.llm_context,
                    audience=request.audience,
                    intent_type=graphrag_response.query_intent.intent_type
                )
                
                response_text = llm_response.content
                
                # Validate response against knowledge graph
                if response_validator:
                    from llm_integration.prompt_templates import CitationConstraints, CitationFormat
                    citation_constraints = CitationConstraints(
                        format_type=CitationFormat.STANDARD,
                        require_all_claims=True,
                        max_unsupported_claims=0
                    )
                    
                    validation_result = response_validator.validate_response(
                        response=response_text,
                        context=graphrag_response.llm_context,
                        graph_context=graphrag_response.graph_context,
                        citation_constraints=citation_constraints,
                        query_intent=graphrag_response.query_intent,
                        audience=request.audience
                    )
                    
                    if not validation_result.is_valid:
                        logger.warning(f"Response validation failed: {validation_result.issues}")
                        # Use corrected response if available
                        if validation_result.corrected_response:
                            response_text = validation_result.corrected_response
                
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                # Fallback to graph-only response
                response_text = _generate_fallback_response(graphrag_response)
        else:
            # No relevant provisions found
            response_text = "I couldn't find specific information about your query in the Consumer Protection Act 2019. Please try rephrasing your question or ask about consumer rights, definitions, or specific sections."
        
        # Calculate confidence score
        if confidence_scorer:
            confidence_score_result = confidence_scorer.score_response(
                query_intent=graphrag_response.query_intent,
                graph_context=graphrag_response.graph_context,
                llm_context=graphrag_response.llm_context,
                llm_response=response_text,
                audience=request.audience
            )
            confidence_score = confidence_score_result.overall_score
        else:
            confidence_score = graphrag_response.get_confidence_score()
        
        # Build citations
        citations = _build_citations(graphrag_response.graph_context)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Generate reasoning explanation for transparency
        reasoning_explanation = None
        if request.audience in ['lawyer', 'judge']:
            reasoning_explanation = graphrag_engine.explain_reasoning(graphrag_response)
        
        return QueryResponse(
            response=response_text,
            citations=citations,
            confidence_score=confidence_score,
            requires_review=confidence_score < 0.8,
            translated=request.language != "en",
            original_language=request.language,
            processing_time=processing_time,
            reasoning_explanation=reasoning_explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@app.get("/api/v1/section/{section_id}", response_model=Section)
async def get_section(
    section_id: str,
    user: User = Depends(get_current_user)
) -> Section:
    """
    Direct section retrieval by section ID.
    
    Args:
        section_id: Unique section identifier (e.g., "CPA2019_2")
        
    Returns:
        Section information with full text and metadata
    """
    try:
        if not graphrag_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GraphRAG engine not initialized"
            )
        
        # Search for section in knowledge graph
        sections = graphrag_engine.graph_traversal.sections
        section_data = None
        
        for section in sections:
            if section.get('section_id') == section_id:
                section_data = section
                break
        
        if not section_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section '{section_id}' not found"
            )
        
        # Convert effective_date to string if it's a datetime object
        effective_date = section_data.get('effective_date')
        if effective_date and hasattr(effective_date, 'isoformat'):
            effective_date = effective_date.isoformat()
        elif effective_date and not isinstance(effective_date, str):
            effective_date = str(effective_date)
        
        return Section(
            section_id=section_data['section_id'],
            section_number=section_data['section_number'],
            title=section_data.get('title', ''),
            text=section_data['text'],
            act=section_data['act'],
            chapter=section_data.get('chapter'),
            page_number=section_data.get('page_number'),
            effective_date=effective_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Section retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Section retrieval failed: {str(e)}"
        )


@app.get("/api/v1/definition/{term}", response_model=Definition)
async def get_definition(
    term: str,
    user: User = Depends(get_current_user)
) -> Definition:
    """
    Definition lookup by legal term.
    
    Args:
        term: Legal term to define (e.g., "consumer", "unfair trade practice")
        
    Returns:
        Definition information with source section reference
    """
    try:
        if not graphrag_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GraphRAG engine not initialized"
            )
        
        # Search for definition in knowledge graph
        definitions = graphrag_engine.graph_traversal.definitions
        definition_data = None
        
        # Search by exact term match or partial match
        term_lower = term.lower()
        for definition in definitions:
            if definition.get('term', '').lower() == term_lower:
                definition_data = definition
                break
        
        # If no exact match, try partial match
        if not definition_data:
            for definition in definitions:
                if term_lower in definition.get('term', '').lower():
                    definition_data = definition
                    break
        
        if not definition_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Definition for '{term}' not found"
            )
        
        return Definition(
            term=definition_data['term'],
            definition=definition_data['definition'],
            defined_in=definition_data['defined_in'],
            section_reference=definition_data.get('clause_reference', definition_data['defined_in']),
            act=definition_data.get('act', 'Consumer Protection Act, 2019')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Definition lookup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Definition lookup failed: {str(e)}"
        )


@app.post("/api/v1/validate-citations", response_model=BulkValidationResponse)
async def validate_citations(
    request: BulkValidationRequest,
    user: User = Depends(check_permission(Permission.CITATION_VALIDATION))
) -> BulkValidationResponse:
    """
    Bulk citation validation for lawyers.
    
    Validates a list of legal citations against the knowledge graph
    to ensure they exist and are correctly formatted.
    
    Args:
        request: List of citations to validate
        
    Returns:
        Validation results for each citation
    """
    try:
        if not graphrag_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GraphRAG engine not initialized"
            )
        
        results = []
        valid_count = 0
        
        for citation in request.citations:
            validation_result = _validate_single_citation(citation)
            results.append(validation_result)
            
            if validation_result.is_valid:
                valid_count += 1
        
        return BulkValidationResponse(
            results=results,
            total_citations=len(request.citations),
            valid_citations=valid_count,
            invalid_citations=len(request.citations) - valid_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Citation validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation validation failed: {str(e)}"
        )


# Helper methods

def _generate_fallback_response(graphrag_response: GraphRAGResponse) -> str:
    """Generate fallback response when LLM is unavailable."""
    if graphrag_response.graph_context.nodes:
        # Return first relevant provision
        node = graphrag_response.graph_context.nodes[0]
        node_text = ""
        if hasattr(node, 'content'):
            node_text = node.content.get('text', 'No text available')
        elif hasattr(node, 'get'):
            node_text = node.get('text', 'No text available')
        else:
            node_text = str(node)
        
        return f"Based on the Consumer Protection Act 2019:\n\n{node_text}\n\n[This is a direct excerpt from the legal text. For detailed explanation, please try again later.]"
    else:
        return "I couldn't find specific information about your query in the Consumer Protection Act 2019. Please try rephrasing your question."


def _build_citations(graph_context) -> List[Citation]:
    """Build citation list from graph context."""
    citations = []
    
    for node in graph_context.nodes:
        node_data = {}
        if hasattr(node, 'content'):
            node_data = node.content
        elif hasattr(node, 'get'):
            node_data = node
        else:
            continue
            
        section_id = node_data.get('section_id')
        if section_id:
            citation = Citation(
                section_id=section_id,
                section_number=node_data.get('section_number', ''),
                title=node_data.get('title', ''),
                act=node_data.get('act', 'Consumer Protection Act, 2019'),
                url=None  # Could add URL to full text in future
            )
            citations.append(citation)
    
    return citations


def _validate_single_citation(citation: str) -> ValidationResult:
    """Validate a single citation against the knowledge graph."""
    import re
    
    # Extract section number from citation
    section_patterns = [
        r'[Ss]ection\s+(\d+(?:\.\d+)*)',
        r'[Ss]\.\s*(\d+(?:\.\d+)*)',
        r'[Ss]ec\.\s*(\d+(?:\.\d+)*)'
    ]
    
    section_number = None
    for pattern in section_patterns:
        match = re.search(pattern, citation)
        if match:
            section_number = match.group(1)
            break
    
    if not section_number:
        return ValidationResult(
            citation=citation,
            is_valid=False,
            section_found=False,
            message="Could not extract section number from citation",
            suggested_correction=None
        )
    
    # Check if section exists in knowledge graph
    if graphrag_engine:
        sections = graphrag_engine.graph_traversal.sections
        for section in sections:
            if section.get('section_number') == section_number:
                return ValidationResult(
                    citation=citation,
                    is_valid=True,
                    section_found=True,
                    message="Citation is valid",
                    suggested_correction=None
                )
    
    return ValidationResult(
        citation=citation,
        is_valid=False,
        section_found=False,
        message=f"Section {section_number} not found in Consumer Protection Act 2019",
        suggested_correction=None
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "detail": str(exc.detail),
            "timestamp": datetime.now().isoformat(),
            "request_id": request.headers.get("X-Request-ID")
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error response."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "request_id": request.headers.get("X-Request-ID")
        }
    )


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )