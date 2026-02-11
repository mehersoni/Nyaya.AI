#!/usr/bin/env python3
"""
Simple Nyayamrit Demo Server

A simplified deployment demo that works reliably for presentations.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    # If python-dotenv is not installed, manually load the .env file
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create demo app
app = FastAPI(
    title="Nyayamrit Demo",
    description="Simple demonstration of Nyayamrit GraphRAG system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo statistics with detailed tracking
demo_stats = {
    "start_time": datetime.now(),
    "total_queries": 0,
    "successful_queries": 0,
    "failed_queries": 0,
    "knowledge_graph_loaded": False,
    "query_history": [],
    "average_response_time": 0.0,
    "gemini_enabled": False
}

@app.get("/", response_class=HTMLResponse)
async def demo_dashboard():
    """Simple demo dashboard."""
    
    # Try to get knowledge graph stats
    try:
        from query_engine.graphrag_engine import GraphRAGEngine
        kg_path = Path(__file__).parent.parent / "knowledge_graph"
        engine = GraphRAGEngine(knowledge_graph_path=str(kg_path))
        stats = engine.get_performance_stats()
        kg_stats = stats.get("knowledge_graph_stats", {})
        demo_stats["knowledge_graph_loaded"] = True
    except Exception as e:
        logger.error(f"Failed to load knowledge graph: {e}")
        kg_stats = {"error": str(e)}
        demo_stats["knowledge_graph_loaded"] = False
    
    uptime = datetime.now() - demo_stats["start_time"]
    uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Nyayamrit Demo Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h1 class="text-4xl font-bold text-blue-600 mb-2">
                <i class="fas fa-balance-scale mr-3"></i>Nyayamrit
            </h1>
            <p class="text-xl text-gray-600">GraphRAG-based Judicial Assistant for Indian Legal System</p>
            <p class="text-gray-500 mt-2">Consumer Protection Act 2019 • System Uptime: {uptime_str}</p>
        </div>

        <!-- System Status -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <i class="fas fa-server text-green-500 text-3xl mr-4"></i>
                    <div>
                        <div class="text-2xl font-bold text-green-600">Online</div>
                        <div class="text-gray-600">System Status</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <i class="fas fa-database text-blue-500 text-3xl mr-4"></i>
                    <div>
                        <div class="text-2xl font-bold text-blue-600">{kg_stats.get('sections_loaded', 'N/A')}</div>
                        <div class="text-gray-600">Legal Sections</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <i class="fas fa-search text-purple-500 text-3xl mr-4"></i>
                    <div>
                        <div class="text-2xl font-bold text-purple-600">{demo_stats['total_queries']}</div>
                        <div class="text-gray-600">Total Queries</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Query Statistics -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-4 rounded-lg shadow">
                <div class="text-center">
                    <div class="text-2xl font-bold text-green-600">{demo_stats['successful_queries']}</div>
                    <div class="text-gray-600">Successful</div>
                </div>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <div class="text-center">
                    <div class="text-2xl font-bold text-red-600">{demo_stats['failed_queries']}</div>
                    <div class="text-gray-600">Failed</div>
                </div>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <div class="text-center">
                    <div class="text-2xl font-bold text-blue-600">{demo_stats['average_response_time']:.2f}s</div>
                    <div class="text-gray-600">Avg Response</div>
                </div>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
                <div class="text-center">
                    <div class="text-2xl font-bold {'text-green-600' if demo_stats['gemini_enabled'] else 'text-gray-400'}">{('✓' if demo_stats['gemini_enabled'] else '✗')}</div>
                    <div class="text-gray-600">Gemini API</div>
                </div>
            </div>
        </div>

        <!-- Knowledge Graph Stats -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold mb-4">Knowledge Graph Statistics</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="text-center">
                    <div class="text-3xl font-bold text-blue-600">{kg_stats.get('sections_loaded', 0)}</div>
                    <div class="text-gray-600">Sections</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-green-600">{kg_stats.get('definitions_loaded', 0)}</div>
                    <div class="text-gray-600">Definitions</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-purple-600">{kg_stats.get('rights_loaded', 0)}</div>
                    <div class="text-gray-600">Rights</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-red-600">{kg_stats.get('clauses_loaded', 0)}</div>
                    <div class="text-gray-600">Clauses</div>
                </div>
            </div>
        </div>

        <!-- Demo Interface -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold mb-4">Interactive Demo</h2>
            
            <!-- Query Interface -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Ask a Legal Question:</label>
                <div class="flex space-x-4">
                    <input type="text" id="queryInput" 
                           placeholder="e.g., What is a consumer according to CPA 2019?"
                           class="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <button onclick="submitQuery()" 
                            class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors">
                        <i class="fas fa-paper-plane mr-2"></i>Ask
                    </button>
                </div>
            </div>

            <!-- Example Questions -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Example Questions:</label>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <button onclick="setQuery('What is a consumer according to CPA 2019?')" 
                            class="text-left p-2 bg-gray-50 hover:bg-gray-100 rounded transition-colors">
                        What is a consumer according to CPA 2019?
                    </button>
                    <button onclick="setQuery('What are consumer rights under the Act?')" 
                            class="text-left p-2 bg-gray-50 hover:bg-gray-100 rounded transition-colors">
                        What are consumer rights under the Act?
                    </button>
                    <button onclick="setQuery('How to file a consumer complaint?')" 
                            class="text-left p-2 bg-gray-50 hover:bg-gray-100 rounded transition-colors">
                        How to file a consumer complaint?
                    </button>
                    <button onclick="setQuery('What is unfair trade practice?')" 
                            class="text-left p-2 bg-gray-50 hover:bg-gray-100 rounded transition-colors">
                        What is unfair trade practice?
                    </button>
                </div>
            </div>

            <!-- Response Area -->
            <div id="responseArea" class="hidden">
                <label class="block text-sm font-medium text-gray-700 mb-2">Response:</label>
                <div id="responseContent" class="p-4 bg-gray-50 rounded-lg border"></div>
                <div id="responseMetadata" class="mt-2 text-sm text-gray-600"></div>
            </div>

            <!-- Loading Indicator -->
            <div id="loadingIndicator" class="hidden text-center py-4">
                <i class="fas fa-spinner fa-spin text-2xl text-blue-500"></i>
                <p class="text-gray-600 mt-2">Processing your query...</p>
            </div>
        </div>

        <!-- API Access -->
        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">API Access</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <a href="/docs" target="_blank" 
                   class="flex items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">
                    <i class="fas fa-book text-blue-500 text-2xl mr-4"></i>
                    <div>
                        <div class="font-semibold">API Documentation</div>
                        <div class="text-sm text-gray-600">Interactive Swagger UI</div>
                    </div>
                </a>
                <a href="/health" target="_blank" 
                   class="flex items-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
                    <i class="fas fa-heartbeat text-green-500 text-2xl mr-4"></i>
                    <div>
                        <div class="font-semibold">Health Check</div>
                        <div class="text-sm text-gray-600">System status monitoring</div>
                    </div>
                </a>
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center mt-8 text-gray-500">
            <p>Nyayamrit GraphRAG-based Judicial Assistant • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <script>
        function setQuery(query) {{
            document.getElementById('queryInput').value = query;
        }}

        async function submitQuery() {{
            const query = document.getElementById('queryInput').value.trim();
            if (!query) return;

            const loadingIndicator = document.getElementById('loadingIndicator');
            const responseArea = document.getElementById('responseArea');
            
            // Show loading
            loadingIndicator.classList.remove('hidden');
            responseArea.classList.add('hidden');

            try {{
                const response = await fetch('/query', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ query: query, audience: 'citizen' }})
                }});

                const data = await response.json();
                
                // Hide loading
                loadingIndicator.classList.add('hidden');
                
                if (response.ok) {{
                    // Show response
                    let responseHtml = '<div class="prose max-w-none">' + 
                        (data.response || 'No response generated') + 
                        '</div>';
                    
                    // Add Gemini enhancement indicator
                    if (data.gemini_enhanced) {{
                        responseHtml += '<div class="mt-2 p-2 bg-blue-50 rounded text-sm text-blue-700">' +
                            '<i class="fas fa-robot mr-1"></i>Enhanced with Gemini AI' +
                            '</div>';
                    }}
                    
                    document.getElementById('responseContent').innerHTML = responseHtml;
                    
                    let metadata = `Processing time: ${{(data.processing_time || 0).toFixed(3)}}s`;
                    if (data.confidence_score !== undefined) {{
                        metadata += ` • Confidence: ${{(data.confidence_score * 100).toFixed(1)}}%`;
                    }}
                    if (data.citations && data.citations.length > 0) {{
                        metadata += ` • Citations: ${{data.citations.length}}`;
                    }}
                    if (data.query_id) {{
                        metadata += ` • Query #${{data.query_id}}`;
                    }}
                    
                    document.getElementById('responseMetadata').textContent = metadata;
                    responseArea.classList.remove('hidden');
                }} else {{
                    document.getElementById('responseContent').innerHTML = 
                        '<div class="text-red-600">Error: ' + (data.detail || 'Query failed') + '</div>';
                    document.getElementById('responseMetadata').textContent = '';
                    responseArea.classList.remove('hidden');
                }}
            }} catch (error) {{
                loadingIndicator.classList.add('hidden');
                document.getElementById('responseContent').innerHTML = 
                    '<div class="text-red-600">Network error: ' + error.message + '</div>';
                document.getElementById('responseMetadata').textContent = '';
                responseArea.classList.remove('hidden');
            }}
        }}

        // Allow Enter key to submit
        document.getElementById('queryInput').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                submitQuery();
            }}
        }});
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html)


@app.post("/query")
async def process_query(request: Request):
    """Process a demo query with enhanced tracking and Gemini API integration."""
    
    try:
        data = await request.json()
        query = data.get("query", "")
        audience = data.get("audience", "citizen")
        
        demo_stats["total_queries"] += 1
        query_start_time = time.time()
        
        # Try to process with GraphRAG engine first
        try:
            from query_engine.graphrag_engine import GraphRAGEngine
            kg_path = Path(__file__).parent.parent / "knowledge_graph"
            engine = GraphRAGEngine(knowledge_graph_path=str(kg_path))
            
            response = engine.process_query(query=query, audience=audience)
            processing_time = time.time() - query_start_time
            
            # Try to enhance response with Gemini API if available
            enhanced_response = None
            gemini_used = False
            
            try:
                enhanced_response = await _enhance_with_gemini(query, response, audience)
                if enhanced_response:
                    gemini_used = True
                    demo_stats["gemini_enabled"] = True
            except Exception as e:
                logger.warning(f"Gemini enhancement failed: {e}")
                demo_stats["gemini_enabled"] = False
            
            # Generate response based on graph context
            if response.graph_context.nodes:
                # Check if this is a rights query that needs comprehensive response
                if response.query_intent.intent_type.value == "rights_query":
                    response_text = _build_comprehensive_rights_response(response, query, enhanced_response, gemini_used)
                elif response.query_intent.intent_type.value == "scenario_analysis":
                    response_text = _build_comprehensive_scenario_response(response, query, enhanced_response, gemini_used)
                else:
                    # Use first relevant node for other query types
                    node = response.graph_context.nodes[0]
                    response_text = _build_single_node_response(node, enhanced_response, gemini_used)
                
                citations = []
                for node in response.graph_context.nodes[:5]:  # Max 5 citations for comprehensive responses
                    citation = _extract_citation_from_node(node)
                    if citation:
                        citations.append(citation)
                
                # Update statistics
                demo_stats["successful_queries"] += 1
                _update_response_time_stats(processing_time)
                
                # Add to query history
                _add_to_query_history(query, audience, processing_time, True, gemini_used)
                
                return {
                    "response": response_text,
                    "citations": citations,
                    "confidence_score": response.get_confidence_score(),
                    "processing_time": processing_time,
                    "requires_review": response.requires_human_review(),
                    "gemini_enhanced": gemini_used,
                    "query_id": len(demo_stats["query_history"])
                }
            else:
                # No relevant nodes found
                demo_stats["failed_queries"] += 1
                _update_response_time_stats(processing_time)
                _add_to_query_history(query, audience, processing_time, False, False)
                
                return {
                    "response": "I couldn't find specific information about your query in the Consumer Protection Act 2019. Please try rephrasing your question or ask about consumer rights, definitions, or specific sections.",
                    "citations": [],
                    "confidence_score": 0.5,
                    "processing_time": processing_time,
                    "requires_review": True,
                    "gemini_enhanced": False,
                    "query_id": len(demo_stats["query_history"])
                }
                
        except Exception as e:
            logger.error(f"GraphRAG processing failed: {e}")
            processing_time = time.time() - query_start_time
            demo_stats["failed_queries"] += 1
            _update_response_time_stats(processing_time)
            _add_to_query_history(query, audience, processing_time, False, False)
            
            return {
                "response": f"System is currently processing your query. The GraphRAG engine is initializing. Please try again in a moment.\\n\\nQuery: {query}\\n\\nNote: This is a demonstration system based on the Consumer Protection Act 2019.",
                "citations": [],
                "confidence_score": 0.3,
                "processing_time": processing_time,
                "requires_review": True,
                "gemini_enhanced": False,
                "query_id": len(demo_stats["query_history"])
            }
            
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        demo_stats["failed_queries"] += 1
        raise HTTPException(status_code=500, detail=str(e))


async def _enhance_with_gemini(query: str, response, audience: str) -> Optional[str]:
    """Enhance response using Gemini API with improved integration."""
    
    # Check if Gemini API key is available
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        return None
    
    try:
        # Import enhanced Gemini provider
        sys.path.append(str(Path(__file__).parent.parent))
        from llm_integration.providers import GeminiProvider
        
        # Create enhanced Gemini provider with correct model
        gemini = GeminiProvider(api_key=gemini_api_key, model="gemini-1.5-flash")
        
        if not gemini.is_available():
            return None
        
        # Use the enhanced LLM context from GraphRAG response
        llm_context = response.llm_context
        
        # Build enhanced constraints with intent information
        constraints = {
            'audience': audience,
            'citation_format': 'standard',
            'intent_type': response.query_intent.intent_type.value,
            'max_length': 2000
        }
        
        # Generate enhanced response with intent-specific optimization
        gemini_response = gemini.generate_response(
            prompt=query,
            context=llm_context,
            constraints=constraints
        )
        
        return gemini_response.content
        
    except Exception as e:
        logger.warning(f"Gemini enhancement failed: {e}")
        return None


def _build_comprehensive_rights_response(response, query: str, enhanced_response: str, gemini_used: bool) -> str:
    """Build comprehensive response for rights queries with all six fundamental rights."""
    
    # If we have enhanced Gemini response, use it
    if enhanced_response and gemini_used:
        return enhanced_response
    
    # Use the enhanced context from GraphRAG response if available
    if hasattr(response, 'llm_context') and response.llm_context.formatted_text:
        context_text = response.llm_context.formatted_text
        
        # Check if comprehensive rights are already in context
        if "Fundamental Consumer Rights (Section 2(9)" in context_text:
            return context_text + """

**HOW TO EXERCISE YOUR RIGHTS:**

1. **Document Everything**: Keep receipts, warranties, and correspondence
2. **Contact the Business First**: Try to resolve issues directly
3. **File a Complaint**: Use the District Consumer Commission if needed
4. **Know Your Timeframes**: Generally 2 years from the date of issue
5. **Seek Legal Help**: Consult a lawyer for complex cases

**ENFORCEMENT MECHANISMS:**
- District Consumer Commission (up to ₹1 crore)
- State Consumer Commission (₹1 crore to ₹10 crore)  
- National Consumer Commission (above ₹10 crore)
- Central Consumer Protection Authority (for violations)

**Source:** Consumer Protection Act, 2019"""
    
    # Fallback: Build comprehensive rights response manually
    response_parts = []
    response_parts.append("**YOUR FUNDAMENTAL CONSUMER RIGHTS**")
    response_parts.append("As a consumer under the Consumer Protection Act, 2019, you have the following rights:\n")
    
    # Six fundamental consumer rights
    fundamental_rights = [
        {
            "title": "1. Right to Safety",
            "description": "Protection against goods and services which are hazardous to life and property"
        },
        {
            "title": "2. Right to be Informed", 
            "description": "Right to be informed about the quality, quantity, potency, purity, standard and price of goods or services"
        },
        {
            "title": "3. Right to Choose",
            "description": "Right to be assured of access to a variety of goods and services at competitive prices"
        },
        {
            "title": "4. Right to be Heard",
            "description": "Right to be heard and to be assured that consumer interests will receive due consideration"
        },
        {
            "title": "5. Right to Seek Redressal",
            "description": "Right to seek redressal against unfair trade practices or restrictive trade practices or unscrupulous exploitation of consumers"
        },
        {
            "title": "6. Right to Consumer Education",
            "description": "Right to consumer education and to be informed about consumer rights and remedies"
        }
    ]
    
    for right in fundamental_rights:
        response_parts.append(f"**{right['title']}**: {right['description']}")
    
    response_parts.append("\n**LEGAL FOUNDATION:** Section 2(9) of the Consumer Protection Act, 2019")
    
    response_parts.append("""
**HOW TO EXERCISE YOUR RIGHTS:**

1. **Document Everything**: Keep receipts, warranties, and correspondence
2. **Contact the Business First**: Try to resolve issues directly
3. **File a Complaint**: Use the District Consumer Commission if needed
4. **Know Your Timeframes**: Generally 2 years from the date of issue
5. **Seek Legal Help**: Consult a lawyer for complex cases

**ENFORCEMENT MECHANISMS:**
- District Consumer Commission (up to ₹1 crore)
- State Consumer Commission (₹1 crore to ₹10 crore)  
- National Consumer Commission (above ₹10 crore)
- Central Consumer Protection Authority (for violations)

**Source:** Consumer Protection Act, 2019""")
    
    return "\n".join(response_parts)


def _build_comprehensive_scenario_response(response, query: str, enhanced_response: str, gemini_used: bool) -> str:
    """Build comprehensive response for scenario analysis queries with enhanced features."""
    
    # If we have enhanced Gemini response, use it
    if enhanced_response and gemini_used:
        return enhanced_response
    
    query_lower = query.lower()
    
    # Use the enhanced context from GraphRAG response
    if hasattr(response, 'llm_context') and response.llm_context.formatted_text:
        # Extract the enhanced context that includes comprehensive rights coverage
        context_text = response.llm_context.formatted_text
        
        # Add procedural guidance for scenario analysis
        if any(term in query_lower for term in ['defective', 'faulty', 'damaged', 'defect']):
            procedural_guidance = """

**PROCEDURAL CHECKLIST FOR DEFECTIVE GOODS:**

1. **Document the Issue**: Take photos, keep receipts, and record details of the defect
2. **Contact the Seller**: Try to resolve the issue directly with the seller first
3. **File a Complaint**: You may file a complaint before the District Consumer Commission within 2 years
4. **Required Documents**: Attach invoice, proof of defect, and any correspondence with seller
5. **Available Remedies**: Seek refund/replacement/compensation as appropriate
6. **Time Limits**: File within 2 years of discovering the defect
7. **Jurisdiction**: File with the District Commission where you reside or where the cause of action arose

**ENFORCEMENT**: The Consumer Commission has the power to order refund, replacement, or compensation."""
            
            return context_text + procedural_guidance
        
        elif any(term in query_lower for term in ['false', 'misleading', 'advertisement']):
            procedural_guidance = """

**PROCEDURAL CHECKLIST FOR FALSE ADVERTISEMENTS:**

1. **Document the Advertisement**: Save screenshots, copies, or recordings of the misleading ad
2. **Report to CCPA**: The Central Consumer Protection Authority can take action against false ads
3. **File Consumer Complaint**: You may file a complaint before the District Consumer Commission within 2 years
4. **Required Documents**: Attach proof of the advertisement and any evidence of misleading claims
5. **Available Remedies**: Seek compensation for any loss suffered due to the false advertisement
6. **Penalties**: Violators can face penalties up to ₹10 lakh (₹50 lakh for repeat violations)
7. **Enforcement**: CCPA can investigate and take suo motu action against false advertisements

**ENFORCEMENT**: Both consumer commissions and CCPA have jurisdiction over false advertisement cases."""
            
            return context_text + procedural_guidance
        
        else:
            # Generic procedural guidance
            procedural_guidance = """

**GENERAL PROCEDURAL GUIDANCE:**

1. **Identify Your Rights**: Review the consumer rights that apply to your situation
2. **Document Everything**: Keep all receipts, correspondence, and evidence
3. **Try Direct Resolution**: Contact the seller/service provider first
4. **File Complaint if Needed**: You may file a complaint before the District Consumer Commission within 2 years
5. **Required Documents**: Attach all relevant proof and documentation
6. **Available Remedies**: Seek appropriate relief based on your specific situation
7. **Time Limits**: Generally 2 years from the date of cause of action

**ENFORCEMENT**: Consumer Commissions have the power to provide effective relief to consumers."""
            
            return context_text + procedural_guidance
    
    # Fallback to original logic if enhanced context not available
    if any(term in query_lower for term in ['false', 'misleading', 'advertisement', 'advertise']):
        return _build_false_ad_response(response.graph_context.nodes)
    elif any(term in query_lower for term in ['defective', 'faulty', 'damaged', 'defect']):
        return _build_defective_goods_response(response.graph_context.nodes)
    else:
        return _build_generic_comprehensive_response(response.graph_context.nodes)


def _build_false_ad_response(nodes) -> str:
    """Build comprehensive response for false advertisement scenarios."""
    
    response_parts = []
    response_parts.append("**False/Misleading Advertisement - Your Legal Options**\n")
    
    # Find and add definition
    for node in nodes:
        if node.node_type == 'definition' and 'misleading advertisement' in node.content.get('term', '').lower():
            definition = node.content.get('definition', '')
            response_parts.append(f"**What constitutes misleading advertisement:**")
            response_parts.append(f"{definition}\n")
            break
    
    # Find and add CCPA powers (Section 18)
    for node in nodes:
        if node.node_type == 'section' and node.content.get('section_number') == '18':
            response_parts.append("**Central Consumer Protection Authority (CCPA) Role:**")
            response_parts.append("The CCPA has the power to investigate false advertisements and take action against violators.\n")
            break
    
    # Find and add penalties (Section 21)
    for node in nodes:
        if node.node_type == 'section' and node.content.get('section_number') == '21':
            response_parts.append("**Penalties for False Advertisements:**")
            response_parts.append("- Manufacturers/endorsers: Up to ₹10 lakh penalty (₹50 lakh for repeat violations)")
            response_parts.append("- Publishers: Up to ₹10 lakh penalty")
            response_parts.append("- Endorsers can be banned from endorsements for 1-3 years\n")
            break
    
    # Find and add complaint filing process (Section 35)
    for node in nodes:
        if node.node_type == 'section' and node.content.get('section_number') == '35':
            response_parts.append("**How to File a Complaint:**")
            response_parts.append("You can file a complaint with the District Consumer Commission regarding false advertisements.")
            response_parts.append("Complaints can be filed electronically as well.\n")
            break
    
    response_parts.append("**Next Steps:**")
    response_parts.append("1. Document the false advertisement (screenshots, copies)")
    response_parts.append("2. File a complaint with the District Consumer Commission")
    response_parts.append("3. The CCPA can also take suo motu action against false advertisements")
    
    response_parts.append("\n**Source:** Consumer Protection Act, 2019")
    
    return "\n".join(response_parts)


def _build_defective_goods_response(nodes) -> str:
    """Build comprehensive response for defective goods scenarios."""
    
    response_parts = []
    response_parts.append("**Defective Goods - Your Consumer Rights**\n")
    
    # Find and add definition of defect
    for node in nodes:
        if node.node_type == 'definition' and 'defect' in node.content.get('term', '').lower():
            definition = node.content.get('definition', '')
            response_parts.append(f"**What constitutes a defect:**")
            response_parts.append(f"{definition}\n")
            break
    
    # Add complaint filing process
    response_parts.append("**How to File a Complaint (Section 35):**")
    response_parts.append("You can file a complaint with the District Consumer Commission if you purchased defective goods.")
    response_parts.append("Complaints can be filed electronically.\n")
    
    # Add available remedies
    response_parts.append("**Available Remedies (Section 39):**")
    response_parts.append("- Removal of defects from the goods")
    response_parts.append("- Replacement of defective goods")
    response_parts.append("- Return of the price paid")
    response_parts.append("- Payment of compensation for loss or injury\n")
    
    response_parts.append("**Next Steps:**")
    response_parts.append("1. Keep all purchase receipts and documentation")
    response_parts.append("2. Try to resolve with the seller first")
    response_parts.append("3. File a complaint with District Consumer Commission if needed")
    
    response_parts.append("\n**Source:** Consumer Protection Act, 2019")
    
    return "\n".join(response_parts)


def _build_generic_comprehensive_response(nodes) -> str:
    """Build generic comprehensive response from multiple nodes."""
    
    response_parts = []
    response_parts.append("**Legal Information - Consumer Protection Act 2019**\n")
    
    # Add definitions first
    definitions = [node for node in nodes if node.node_type == 'definition']
    if definitions:
        response_parts.append("**Relevant Definitions:**")
        for node in definitions[:2]:  # Max 2 definitions
            term = node.content.get('term', '')
            definition = node.content.get('definition', '')
            response_parts.append(f"- **{term.title()}:** {definition}")
        response_parts.append("")
    
    # Add sections
    sections = [node for node in nodes if node.node_type == 'section']
    if sections:
        response_parts.append("**Relevant Legal Provisions:**")
        for node in sections[:3]:  # Max 3 sections
            section_num = node.content.get('section_number', '')
            text = node.content.get('text', '')[:200]
            response_parts.append(f"- **Section {section_num}:** {text}...")
        response_parts.append("")
    
    response_parts.append("**Source:** Consumer Protection Act, 2019")
    response_parts.append("For complete legal text and context, please refer to the full Act.")
    
    return "\n".join(response_parts)


def _build_single_node_response(node, enhanced_response: str, gemini_used: bool) -> str:
    """Build response from a single node with enhanced formatting."""
    
    # If we have enhanced Gemini response, use it
    if enhanced_response and gemini_used:
        return enhanced_response
    
    # Extract node information with proper field mapping
    if hasattr(node, 'content'):
        node_text = node.content.get('text', '')
        node_title = node.content.get('title', 'Legal Provision')
        section_id = node.content.get('section_id', '')
        term = node.content.get('term', '')
        definition = node.content.get('definition', '')
        description = node.content.get('description', '')
    else:
        # Fallback for other node types
        node_text = str(node)[:200]
        node_title = 'Legal Provision'
        section_id = ''
        term = ''
        definition = ''
        description = ''
    
    if node.node_type == 'definition':
        response_text = f"""**Definition: {term.title()}**

{definition}

**Legal Foundation:** This definition is provided in Section 2 of the Consumer Protection Act, 2019.

**Practical Application:** Understanding this definition is crucial for determining your rights and remedies under the Act.

**Source:** Consumer Protection Act, 2019"""
        
    elif node.node_type == 'right':
        response_text = f"""**Consumer Right: {description or node_title}**

{node_text or description}

**Legal Foundation:** This right is granted under the Consumer Protection Act, 2019.

**Enforcement:** You can enforce this right by filing a complaint with the appropriate Consumer Commission.

**Source:** Consumer Protection Act, 2019"""
        
    elif node_text:
        response_text = f"""**{node_title}**

{node_text}

**Legal Foundation:** Section {section_id.replace('CPA_2019_S', '') if section_id else 'N/A'} of the Consumer Protection Act, 2019.

**Practical Guidance:** This provision establishes important rights and procedures for consumers.

**Source:** Consumer Protection Act, 2019"""
        
    else:
        response_text = f"""**{node_title}**

I found a relevant provision but the detailed text is not available in the current knowledge base. Please try a more specific query or refer to the complete Consumer Protection Act 2019 for detailed information.

**Recommendation:** Try asking about specific consumer rights, definitions, or complaint procedures.

**Source:** Consumer Protection Act, 2019"""
    
    return response_text


def _extract_citation_from_node(node) -> Optional[Dict]:
    """Extract citation information from a node."""
    
    if hasattr(node, 'content'):
        section_id = node.content.get('section_id', '')
        section_num = node.content.get('section_number', '')
        title = node.content.get('title', '')
        term = node.content.get('term', '')
    else:
        return None
    
    if section_id:
        return {
            "section_id": section_id,
            "section_number": section_num or section_id.replace('CPA_2019_S', ''),
            "title": title,
            "act": "Consumer Protection Act, 2019"
        }
    elif term:
        return {
            "section_id": f"DEF_{term}",
            "section_number": "2",
            "title": f"Definition of '{term}'",
            "act": "Consumer Protection Act, 2019"
        }
    
    return None


def _update_response_time_stats(processing_time: float):
    """Update average response time statistics."""
    if demo_stats["average_response_time"] == 0:
        demo_stats["average_response_time"] = processing_time
    else:
        # Exponential moving average
        demo_stats["average_response_time"] = (
            0.8 * demo_stats["average_response_time"] + 0.2 * processing_time
        )


def _add_to_query_history(query: str, audience: str, processing_time: float, 
                         success: bool, gemini_used: bool):
    """Add query to history for tracking."""
    
    # Keep only last 50 queries to prevent memory issues
    if len(demo_stats["query_history"]) >= 50:
        demo_stats["query_history"].pop(0)
    
    demo_stats["query_history"].append({
        "timestamp": datetime.now().isoformat(),
        "query": query[:100] + "..." if len(query) > 100 else query,  # Truncate long queries
        "audience": audience,
        "processing_time": processing_time,
        "success": success,
        "gemini_used": gemini_used
    })


@app.get("/health")
async def health_check():
    """Health check endpoint with enhanced statistics."""
    
    try:
        from query_engine.graphrag_engine import GraphRAGEngine
        kg_path = Path(__file__).parent.parent / "knowledge_graph"
        engine = GraphRAGEngine(knowledge_graph_path=str(kg_path))
        validation = engine.validate_knowledge_graph()
        
        # Calculate success rate
        success_rate = 0.0
        if demo_stats["total_queries"] > 0:
            success_rate = demo_stats["successful_queries"] / demo_stats["total_queries"]
        
        return {
            "status": "healthy" if validation["is_valid"] else "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - demo_stats["start_time"]),
            "query_statistics": {
                "total_queries": demo_stats["total_queries"],
                "successful_queries": demo_stats["successful_queries"],
                "failed_queries": demo_stats["failed_queries"],
                "success_rate": round(success_rate * 100, 1),
                "average_response_time": round(demo_stats["average_response_time"], 3),
                "gemini_enabled": demo_stats["gemini_enabled"]
            },
            "knowledge_graph": validation,
            "components": {
                "graphrag_engine": "healthy" if validation["is_valid"] else "warnings",
                "knowledge_graph": "loaded" if demo_stats["knowledge_graph_loaded"] else "error",
                "gemini_api": "enabled" if demo_stats["gemini_enabled"] else "disabled"
            },
            "recent_queries": demo_stats["query_history"][-5:] if demo_stats["query_history"] else []
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - demo_stats["start_time"]),
            "query_statistics": {
                "total_queries": demo_stats["total_queries"],
                "successful_queries": demo_stats["successful_queries"],
                "failed_queries": demo_stats["failed_queries"],
                "success_rate": 0.0,
                "average_response_time": demo_stats["average_response_time"],
                "gemini_enabled": demo_stats["gemini_enabled"]
            },
            "error": str(e),
            "components": {
                "graphrag_engine": f"error: {str(e)}",
                "knowledge_graph": "error",
                "gemini_api": "unknown"
            },
            "recent_queries": []
        }


@app.get("/docs")
async def api_docs():
    """Redirect to API documentation."""
    return HTMLResponse("""
    <html>
    <head><title>API Documentation</title></head>
    <body>
        <h1>Nyayamrit API Documentation</h1>
        <p>This is a simplified demo. For full API documentation, please refer to the main API server.</p>
        <h2>Available Endpoints:</h2>
        <ul>
            <li><strong>GET /</strong> - Demo dashboard</li>
            <li><strong>POST /query</strong> - Process legal queries</li>
            <li><strong>GET /health</strong> - System health check</li>
            <li><strong>GET /query-history</strong> - View recent query history</li>
        </ul>
        <h2>Query Example:</h2>
        <pre>
POST /query
{
    "query": "What is a consumer according to CPA 2019?",
    "audience": "citizen"
}
        </pre>
    </body>
    </html>
    """)


@app.get("/query-history")
async def get_query_history():
    """Get recent query history for monitoring."""
    return {
        "total_queries": demo_stats["total_queries"],
        "successful_queries": demo_stats["successful_queries"],
        "failed_queries": demo_stats["failed_queries"],
        "success_rate": round(demo_stats["successful_queries"] / max(1, demo_stats["total_queries"]) * 100, 1),
        "average_response_time": round(demo_stats["average_response_time"], 3),
        "gemini_enabled": demo_stats["gemini_enabled"],
        "query_history": demo_stats["query_history"],
        "timestamp": datetime.now().isoformat()
    }


def main():
    """Start the simple demo server."""
    
    host = "127.0.0.1"
    port = 8080
    
    print("=" * 60)
    print("🚀 Nyayamrit Simple Demo Server")
    print("=" * 60)
    print(f"Demo URL: http://{host}:{port}")
    print(f"Health Check: http://{host}:{port}/health")
    print("=" * 60)
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\\nDemo server stopped by user")
    except Exception as e:
        print(f"Demo server failed: {e}")


if __name__ == "__main__":
    main()