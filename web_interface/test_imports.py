"""
Test script to verify all imports work correctly
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_basic_imports():
    """Test basic FastAPI and auth imports"""
    print("Testing basic imports...")
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
        
        import uvicorn
        print("✓ Uvicorn imported successfully")
        
        from jose import jwt
        print("✓ JWT (jose) imported successfully")
        
        import bcrypt
        print("✓ bcrypt imported successfully")
        
        from pydantic import BaseModel
        print("✓ Pydantic imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Basic import failed: {e}")
        return False

def test_auth_module():
    """Test auth module imports"""
    print("\nTesting auth module...")
    try:
        from web_interface.auth import (
            User, UserLogin, UserCreate, TokenResponse, 
            auth_manager, Permission, UserRole
        )
        print("✓ Auth module imported successfully")
        
        # Test creating a user
        user = auth_manager.create_anonymous_user()
        print(f"✓ Anonymous user created: {user.user_id}")
        
        return True
    except Exception as e:
        print(f"✗ Auth module import failed: {e}")
        return False

def test_graphrag_imports():
    """Test GraphRAG engine imports"""
    print("\nTesting GraphRAG imports...")
    try:
        from query_engine.graphrag_engine import GraphRAGEngine
        print("✓ GraphRAG engine imported successfully")
        
        from query_engine.query_parser import QueryParser
        print("✓ Query parser imported successfully")
        
        from query_engine.graph_traversal import GraphTraversal
        print("✓ Graph traversal imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ GraphRAG import failed: {e}")
        return False

def test_llm_imports():
    """Test LLM integration imports"""
    print("\nTesting LLM imports...")
    try:
        from llm_integration.llm_manager import LLMManager
        print("✓ LLM manager imported successfully")
        
        from llm_integration.providers import LLMProvider
        print("✓ LLM providers imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ LLM import failed: {e}")
        return False

def test_fastapi_app_creation():
    """Test creating FastAPI app"""
    print("\nTesting FastAPI app creation...")
    try:
        from fastapi import FastAPI, HTTPException, Depends
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(title="Test App")
        print("✓ FastAPI app created successfully")
        
        # Test adding middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
        print("✓ CORS middleware added successfully")
        
        return True
    except Exception as e:
        print(f"✗ FastAPI app creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Nyayamrit FastAPI Import Test Suite")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_auth_module,
        test_graphrag_imports,
        test_llm_imports,
        test_fastapi_app_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "PASS" if result else "FAIL"
        print(f"{test.__name__:25} : {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All import tests passed! Ready to run FastAPI server.")
    else:
        print("⚠️  Some imports failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)