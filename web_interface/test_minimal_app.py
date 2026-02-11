"""
Minimal FastAPI test to verify basic functionality
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Nyayamrit API Test", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/")
async def root():
    return {"message": "Nyayamrit API is running"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", message="API is working")

@app.get("/test-imports")
async def test_imports():
    """Test if all required modules can be imported"""
    try:
        # Test basic imports
        import fastapi
        import uvicorn
        from jose import jwt
        import bcrypt
        
        # Test GraphRAG imports
        from query_engine.graphrag_engine import GraphRAGEngine
        from llm_integration.llm_manager import LLMManager
        
        return {
            "status": "success",
            "message": "All imports successful",
            "modules": {
                "fastapi": str(fastapi.__version__),
                "uvicorn": "available",
                "jose": "available", 
                "bcrypt": "available",
                "graphrag_engine": "available",
                "llm_manager": "available"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Import failed: {str(e)}",
            "error_type": type(e).__name__
        }

if __name__ == "__main__":
    import uvicorn
    print("Starting minimal FastAPI test server...")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")