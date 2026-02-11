#!/usr/bin/env python3
"""
Nyayamrit Deployment Demo Server

This script creates a comprehensive demonstration deployment of the Nyayamrit
GraphRAG-based Judicial Assistant system for presentations and showcases.

Features:
- Interactive API demonstration
- System status dashboard
- Live query examples
- Performance metrics
- Knowledge graph statistics
"""

import os
import sys
import time
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from web_interface.app import app as nyayamrit_app
from query_engine.graphrag_engine import GraphRAGEngine
from llm_integration.llm_manager import LLMManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create demo app
demo_app = FastAPI(
    title="Nyayamrit Deployment Demo",
    description="Interactive demonstration of the Nyayamrit GraphRAG-based Judicial Assistant",
    version="1.0.0"
)

# Add CORS middleware
demo_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the main Nyayamrit API
demo_app.mount("/api", nyayamrit_app)

# Templates for HTML pages
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Global variables for demo
demo_stats = {
    "start_time": datetime.now(),
    "total_queries": 0,
    "successful_queries": 0,
    "average_response_time": 0.0,
    "knowledge_graph_stats": {},
    "recent_queries": []
}


@demo_app.get("/", response_class=HTMLResponse)
async def deployment_dashboard(request: Request):
    """Main deployment dashboard for presentations."""
    
    # Get system statistics
    try:
        # Initialize GraphRAG engine for stats with correct path
        kg_path = Path(__file__).parent.parent / "knowledge_graph"
        graphrag_engine = GraphRAGEngine(
            knowledge_graph_path=str(kg_path),
            max_context_length=8000
        )
        
        kg_stats = graphrag_engine.get_performance_stats()
        validation_results = graphrag_engine.validate_knowledge_graph()
        
        demo_stats["knowledge_graph_stats"] = {
            **kg_stats["knowledge_graph_stats"],
            "validation": validation_results
        }
        
    except Exception as e:
        logger.error(f"Failed to get GraphRAG stats: {e}")
        demo_stats["knowledge_graph_stats"] = {"error": str(e)}
    
    # Calculate uptime
    uptime = datetime.now() - demo_stats["start_time"]
    uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
    
    context = {
        "request": request,
        "title": "Nyayamrit Deployment Demo",
        "system_name": "Nyayamrit: GraphRAG-Based Judicial Assistant",
        "uptime": uptime_str,
        "stats": demo_stats,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "api_base_url": "/api"
    }
    
    return templates.TemplateResponse("deployment_dashboard.html", context)


@demo_app.get("/demo/live")
async def live_demo_page(request: Request):
    """Interactive live demo page."""
    
    context = {
        "request": request,
        "title": "Live Demo - Nyayamrit",
        "api_base_url": "/api"
    }
    
    return templates.TemplateResponse("live_demo.html", context)


@demo_app.get("/demo/stats")
async def get_demo_stats():
    """Get current demo statistics."""
    
    # Update knowledge graph stats
    try:
        kg_path = Path(__file__).parent.parent / "knowledge_graph"
        graphrag_engine = GraphRAGEngine(
            knowledge_graph_path=str(kg_path),
            max_context_length=8000
        )
        
        kg_stats = graphrag_engine.get_performance_stats()
        demo_stats["knowledge_graph_stats"] = kg_stats["knowledge_graph_stats"]
        
    except Exception as e:
        logger.error(f"Failed to update stats: {e}")
    
    # Calculate uptime
    uptime = datetime.now() - demo_stats["start_time"]
    
    return {
        "uptime_seconds": uptime.total_seconds(),
        "uptime_formatted": f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m",
        "total_queries": demo_stats["total_queries"],
        "successful_queries": demo_stats["successful_queries"],
        "success_rate": demo_stats["successful_queries"] / max(1, demo_stats["total_queries"]),
        "average_response_time": demo_stats["average_response_time"],
        "knowledge_graph_stats": demo_stats["knowledge_graph_stats"],
        "recent_queries": demo_stats["recent_queries"][-10:],  # Last 10 queries
        "timestamp": datetime.now().isoformat()
    }


@demo_app.post("/demo/query")
async def demo_query(request: Request):
    """Process a demo query and update statistics."""
    
    start_time = time.time()
    
    try:
        # Get request data
        data = await request.json()
        query = data.get("query", "")
        audience = data.get("audience", "citizen")
        
        # Forward to main API
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    "http://127.0.0.1:8000/api/v1/query",
                    json={
                        "query": query,
                        "language": "en",
                        "audience": audience
                    }
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                else:
                    response_data = {"error": f"API returned {response.status_code}", "detail": response.text}
                    
            except Exception as e:
                response_data = {"error": "API connection failed", "detail": str(e)}
                response = type('MockResponse', (), {'status_code': 500})()
            
        # Update statistics
        processing_time = time.time() - start_time
        demo_stats["total_queries"] += 1
        
        if response.status_code == 200:
            demo_stats["successful_queries"] += 1
        
        # Update average response time
        if demo_stats["total_queries"] == 1:
            demo_stats["average_response_time"] = processing_time
        else:
            demo_stats["average_response_time"] = (
                demo_stats["average_response_time"] * (demo_stats["total_queries"] - 1) + processing_time
            ) / demo_stats["total_queries"]
        
        # Add to recent queries
        demo_stats["recent_queries"].append({
            "query": query[:100] + "..." if len(query) > 100 else query,
            "audience": audience,
            "timestamp": datetime.now().isoformat(),
            "response_time": processing_time,
            "success": response.status_code == 200,
            "confidence": response_data.get("confidence_score", 0) if response.status_code == 200 else 0
        })
        
        # Keep only last 50 queries
        if len(demo_stats["recent_queries"]) > 50:
            demo_stats["recent_queries"] = demo_stats["recent_queries"][-50:]
        
        return response_data
        
    except Exception as e:
        logger.error(f"Demo query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@demo_app.get("/demo/examples")
async def get_demo_examples():
    """Get example queries for different audiences."""
    
    examples = {
        "citizen": [
            "What is a consumer according to CPA 2019?",
            "What are my rights as a consumer?",
            "How can I file a complaint against unfair trade practices?",
            "What compensation can I claim for defective products?",
            "Where can I seek redressal for consumer disputes?"
        ],
        "lawyer": [
            "Show me Section 2 of Consumer Protection Act 2019",
            "What does Section 18 say about consumer rights?",
            "Find all sections related to unfair trade practices",
            "What are the penalties under Section 21?",
            "Explain the complaint procedure under CPA 2019"
        ],
        "judge": [
            "Analyze the relationship between Sections 2 and 18",
            "What are the key provisions for consumer protection?",
            "Compare complaint procedures across different sections",
            "Identify all rights granted to consumers under the Act",
            "What are the enforcement mechanisms in CPA 2019?"
        ]
    }
    
    return examples


@demo_app.get("/demo/health")
async def demo_health_check():
    """Comprehensive health check for demo."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "demo_stats": demo_stats
    }
    
    # Check main API health
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get("http://127.0.0.1:8000/health")
                if response.status_code == 200:
                    health_status["components"]["main_api"] = "healthy"
                    health_status["api_health"] = response.json()
                else:
                    health_status["components"]["main_api"] = "unhealthy"
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["components"]["main_api"] = f"connection_error: {str(e)}"
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["main_api"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check knowledge graph
    try:
        kg_path = Path(__file__).parent.parent / "knowledge_graph"
        graphrag_engine = GraphRAGEngine(
            knowledge_graph_path=str(kg_path),
            max_context_length=8000
        )
        validation_results = graphrag_engine.validate_knowledge_graph()
        
        if validation_results["is_valid"]:
            health_status["components"]["knowledge_graph"] = "healthy"
        else:
            health_status["components"]["knowledge_graph"] = "warnings"
            health_status["status"] = "degraded"
            
        health_status["knowledge_graph_validation"] = validation_results
        
    except Exception as e:
        health_status["components"]["knowledge_graph"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status


def create_demo_templates():
    """Create HTML templates for the demo."""
    
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Main dashboard template
    dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800">{{ system_name }}</h1>
                    <p class="text-gray-600 mt-2">GraphRAG-based Legal Assistant for Indian Consumer Protection Law</p>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-500">System Uptime</div>
                    <div class="text-2xl font-bold text-green-600">{{ uptime }}</div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <a href="/demo/live" class="bg-blue-500 hover:bg-blue-600 text-white p-6 rounded-lg shadow-lg transition-colors">
                <i class="fas fa-play-circle text-3xl mb-3"></i>
                <h3 class="text-xl font-semibold">Live Demo</h3>
                <p class="text-blue-100">Try the interactive query interface</p>
            </a>
            
            <a href="/api/docs" class="bg-green-500 hover:bg-green-600 text-white p-6 rounded-lg shadow-lg transition-colors">
                <i class="fas fa-book text-3xl mb-3"></i>
                <h3 class="text-xl font-semibold">API Documentation</h3>
                <p class="text-green-100">Explore the REST API endpoints</p>
            </a>
            
            <a href="/demo/health" class="bg-purple-500 hover:bg-purple-600 text-white p-6 rounded-lg shadow-lg transition-colors">
                <i class="fas fa-heartbeat text-3xl mb-3"></i>
                <h3 class="text-xl font-semibold">System Health</h3>
                <p class="text-purple-100">Check system status and metrics</p>
            </a>
        </div>

        <!-- Statistics Dashboard -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <i class="fas fa-search text-blue-500 text-2xl mr-3"></i>
                    <div>
                        <div class="text-2xl font-bold">{{ stats.total_queries }}</div>
                        <div class="text-gray-600">Total Queries</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <i class="fas fa-check-circle text-green-500 text-2xl mr-3"></i>
                    <div>
                        <div class="text-2xl font-bold">{{ stats.successful_queries }}</div>
                        <div class="text-gray-600">Successful Queries</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <i class="fas fa-clock text-yellow-500 text-2xl mr-3"></i>
                    <div>
                        <div class="text-2xl font-bold">{{ "%.3f"|format(stats.average_response_time) }}s</div>
                        <div class="text-gray-600">Avg Response Time</div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white p-6 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <i class="fas fa-database text-indigo-500 text-2xl mr-3"></i>
                    <div>
                        <div class="text-2xl font-bold">{{ stats.knowledge_graph_stats.get('sections_loaded', 0) }}</div>
                        <div class="text-gray-600">Legal Sections</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Knowledge Graph Statistics -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold mb-4">Knowledge Graph Statistics</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="text-center">
                    <div class="text-3xl font-bold text-blue-600">{{ stats.knowledge_graph_stats.get('sections_loaded', 0) }}</div>
                    <div class="text-gray-600">Sections</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-green-600">{{ stats.knowledge_graph_stats.get('definitions_loaded', 0) }}</div>
                    <div class="text-gray-600">Definitions</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-purple-600">{{ stats.knowledge_graph_stats.get('rights_loaded', 0) }}</div>
                    <div class="text-gray-600">Rights</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold text-red-600">{{ stats.knowledge_graph_stats.get('clauses_loaded', 0) }}</div>
                    <div class="text-gray-600">Clauses</div>
                </div>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">Recent Query Activity</h2>
            <div id="recent-queries" class="space-y-3">
                {% for query in stats.recent_queries[-5:] %}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div class="flex-1">
                        <div class="font-medium">{{ query.query }}</div>
                        <div class="text-sm text-gray-600">{{ query.audience }} • {{ query.timestamp }}</div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="text-sm">{{ "%.3f"|format(query.response_time) }}s</span>
                        {% if query.success %}
                        <i class="fas fa-check-circle text-green-500"></i>
                        {% else %}
                        <i class="fas fa-times-circle text-red-500"></i>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center mt-8 text-gray-600">
            <p>Nyayamrit Deployment Demo • Last Updated: {{ current_time }}</p>
        </div>
    </div>

    <script>
        // Auto-refresh stats every 30 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/demo/stats');
                const stats = await response.json();
                
                // Update counters
                document.querySelector('[data-stat="total_queries"]').textContent = stats.total_queries;
                document.querySelector('[data-stat="successful_queries"]').textContent = stats.successful_queries;
                document.querySelector('[data-stat="average_response_time"]').textContent = stats.average_response_time.toFixed(3) + 's';
                
                // Update recent queries
                const recentQueriesDiv = document.getElementById('recent-queries');
                recentQueriesDiv.innerHTML = stats.recent_queries.slice(-5).map(query => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                        <div class="flex-1">
                            <div class="font-medium">${query.query}</div>
                            <div class="text-sm text-gray-600">${query.audience} • ${query.timestamp}</div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="text-sm">${query.response_time.toFixed(3)}s</span>
                            ${query.success ? 
                                '<i class="fas fa-check-circle text-green-500"></i>' : 
                                '<i class="fas fa-times-circle text-red-500"></i>'
                            }
                        </div>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Failed to update stats:', error);
            }
        }, 30000);
    </script>
</body>
</html>
    '''
    
    # Live demo template
    live_demo_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8" x-data="demoApp()">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800">Nyayamrit Live Demo</h1>
                    <p class="text-gray-600 mt-2">Interactive GraphRAG-based Legal Assistant</p>
                </div>
                <a href="/" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                    <i class="fas fa-arrow-left mr-2"></i>Back to Dashboard
                </a>
            </div>
        </div>

        <!-- Audience Selection -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Select Your Role</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button @click="setAudience('citizen')" 
                        :class="audience === 'citizen' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'"
                        class="p-4 rounded-lg transition-colors">
                    <i class="fas fa-user text-2xl mb-2"></i>
                    <div class="font-semibold">Citizen</div>
                    <div class="text-sm">Simple explanations of rights</div>
                </button>
                
                <button @click="setAudience('lawyer')" 
                        :class="audience === 'lawyer' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'"
                        class="p-4 rounded-lg transition-colors">
                    <i class="fas fa-balance-scale text-2xl mb-2"></i>
                    <div class="font-semibold">Lawyer</div>
                    <div class="text-sm">Detailed legal analysis</div>
                </button>
                
                <button @click="setAudience('judge')" 
                        :class="audience === 'judge' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'"
                        class="p-4 rounded-lg transition-colors">
                    <i class="fas fa-gavel text-2xl mb-2"></i>
                    <div class="font-semibold">Judge</div>
                    <div class="text-sm">Comprehensive legal reasoning</div>
                </button>
            </div>
        </div>

        <!-- Example Questions -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Example Questions</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <template x-for="example in examples[audience]" :key="example">
                    <button @click="query = example" 
                            class="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors">
                        <i class="fas fa-question-circle text-blue-500 mr-2"></i>
                        <span x-text="example"></span>
                    </button>
                </template>
            </div>
        </div>

        <!-- Query Interface -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Ask Your Question</h2>
            <div class="flex space-x-4">
                <input type="text" 
                       x-model="query" 
                       @keyup.enter="submitQuery()"
                       placeholder="Enter your legal question..."
                       class="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                <button @click="submitQuery()" 
                        :disabled="loading || !query.trim()"
                        class="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg transition-colors">
                    <i class="fas fa-paper-plane mr-2"></i>
                    <span x-text="loading ? 'Processing...' : 'Ask'"></span>
                </button>
            </div>
        </div>

        <!-- Response Display -->
        <div x-show="response" class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Response</h2>
            
            <!-- Response Content -->
            <div class="prose max-w-none mb-4">
                <div x-html="response?.response || ''"></div>
            </div>
            
            <!-- Citations -->
            <div x-show="response?.citations?.length > 0" class="mb-4">
                <h3 class="font-semibold mb-2">Legal Citations:</h3>
                <div class="space-y-2">
                    <template x-for="citation in response?.citations || []" :key="citation.section_id">
                        <div class="bg-blue-50 p-3 rounded border-l-4 border-blue-500">
                            <div class="font-medium" x-text="citation.title"></div>
                            <div class="text-sm text-gray-600" x-text="`${citation.act} - Section ${citation.section_number}`"></div>
                        </div>
                    </template>
                </div>
            </div>
            
            <!-- Metadata -->
            <div class="flex items-center justify-between text-sm text-gray-600 border-t pt-4">
                <div class="flex items-center space-x-4">
                    <span>Confidence: <span class="font-medium" x-text="((response?.confidence_score || 0) * 100).toFixed(1) + '%'"></span></span>
                    <span>Processing Time: <span class="font-medium" x-text="(response?.processing_time || 0).toFixed(3) + 's'"></span></span>
                </div>
                <div x-show="response?.requires_review" class="text-yellow-600">
                    <i class="fas fa-exclamation-triangle mr-1"></i>
                    Requires Expert Review
                </div>
            </div>
        </div>

        <!-- Error Display -->
        <div x-show="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div class="flex items-center">
                <i class="fas fa-exclamation-circle text-red-500 mr-2"></i>
                <span class="text-red-700" x-text="error"></span>
            </div>
        </div>
    </div>

    <script>
        function demoApp() {
            return {
                audience: 'citizen',
                query: '',
                response: null,
                error: null,
                loading: false,
                examples: {
                    citizen: [
                        "What is a consumer according to CPA 2019?",
                        "What are my rights as a consumer?",
                        "How can I file a complaint against unfair trade practices?",
                        "What compensation can I claim for defective products?",
                        "Where can I seek redressal for consumer disputes?"
                    ],
                    lawyer: [
                        "Show me Section 2 of Consumer Protection Act 2019",
                        "What does Section 18 say about consumer rights?",
                        "Find all sections related to unfair trade practices",
                        "What are the penalties under Section 21?",
                        "Explain the complaint procedure under CPA 2019"
                    ],
                    judge: [
                        "Analyze the relationship between Sections 2 and 18",
                        "What are the key provisions for consumer protection?",
                        "Compare complaint procedures across different sections",
                        "Identify all rights granted to consumers under the Act",
                        "What are the enforcement mechanisms in CPA 2019?"
                    ]
                },
                
                setAudience(newAudience) {
                    this.audience = newAudience;
                    this.response = null;
                    this.error = null;
                },
                
                async submitQuery() {
                    if (!this.query.trim()) return;
                    
                    this.loading = true;
                    this.error = null;
                    this.response = null;
                    
                    try {
                        const response = await fetch('/demo/query', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                query: this.query,
                                audience: this.audience
                            })
                        });
                        
                        if (response.ok) {
                            this.response = await response.json();
                        } else {
                            const errorData = await response.json();
                            this.error = errorData.detail || 'Query failed';
                        }
                    } catch (error) {
                        this.error = 'Network error: ' + error.message;
                    } finally {
                        this.loading = false;
                    }
                }
            }
        }
    </script>
</body>
</html>
    '''
    
    # Write templates
    with open(templates_dir / "deployment_dashboard.html", "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    
    with open(templates_dir / "live_demo.html", "w", encoding="utf-8") as f:
        f.write(live_demo_html)
    
    logger.info("Demo templates created successfully")


def main():
    """Start the deployment demo server."""
    
    # Create templates
    create_demo_templates()
    
    # Environment configuration
    host = os.getenv("DEMO_HOST", "127.0.0.1")
    port = int(os.getenv("DEMO_PORT", "8080"))
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Nyayamrit Deployment Demo")
    logger.info("=" * 60)
    logger.info(f"Demo Dashboard: http://{host}:{port}")
    logger.info(f"Live Demo: http://{host}:{port}/demo/live")
    logger.info(f"API Docs: http://{host}:{port}/api/docs")
    logger.info(f"Health Check: http://{host}:{port}/demo/health")
    logger.info("=" * 60)
    
    try:
        uvicorn.run(
            demo_app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Demo server shutdown requested by user")
    except Exception as e:
        logger.error(f"Demo server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()