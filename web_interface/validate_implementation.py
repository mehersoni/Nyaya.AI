#!/usr/bin/env python3
"""
Implementation Validation Script for Task 7.1

This script validates that all the required endpoints from task 7.1 are implemented
and working correctly according to the requirements.

Task 7.1 Requirements:
- Implement main API gateway with /api/v1/query endpoint
- Add section retrieval, definition lookup, citation validation endpoints  
- Include authentication and authorization framework
- Requirements: 5.1, 6.1, 10.4
"""

import requests
import json
import sys
from typing import Dict, List, Any


class ImplementationValidator:
    """Validates the FastAPI implementation against task requirements."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.validation_results = []
    
    def validate_requirement(self, requirement: str, test_func, description: str) -> bool:
        """Validate a specific requirement."""
        print(f"\n🔍 Validating: {description}")
        try:
            result = test_func()
            if result:
                print(f"✅ PASS: {requirement}")
                self.validation_results.append((requirement, True, description))
                return True
            else:
                print(f"❌ FAIL: {requirement}")
                self.validation_results.append((requirement, False, description))
                return False
        except Exception as e:
            print(f"❌ ERROR: {requirement} - {str(e)}")
            self.validation_results.append((requirement, False, f"{description} - Error: {str(e)}"))
            return False
    
    def test_main_api_gateway(self) -> bool:
        """Test main API gateway with /api/v1/query endpoint."""
        response = self.session.post(f"{self.base_url}/api/v1/query", json={
            "query": "What is a consumer?",
            "language": "en", 
            "audience": "citizen"
        })
        
        if response.status_code != 200:
            return False
            
        data = response.json()
        required_fields = ['response', 'citations', 'confidence_score', 'requires_review', 'processing_time']
        
        return all(field in data for field in required_fields)
    
    def test_section_retrieval(self) -> bool:
        """Test section retrieval endpoint."""
        response = self.session.get(f"{self.base_url}/api/v1/section/CPA_2019_S2")
        
        if response.status_code != 200:
            return False
            
        data = response.json()
        required_fields = ['section_id', 'section_number', 'title', 'text', 'act']
        
        return all(field in data for field in required_fields)
    
    def test_definition_lookup(self) -> bool:
        """Test definition lookup endpoint."""
        response = self.session.get(f"{self.base_url}/api/v1/definition/consumer")
        
        if response.status_code != 200:
            return False
            
        data = response.json()
        required_fields = ['term', 'definition', 'defined_in', 'section_reference', 'act']
        
        return all(field in data for field in required_fields)
    
    def test_citation_validation(self) -> bool:
        """Test citation validation endpoint."""
        # First authenticate to get required permissions
        login_response = self.session.post(f"{self.base_url}/api/v1/auth/login", json={
            "email": "lawyer@example.com",
            "password": "lawyer123"
        })
        
        if login_response.status_code != 200:
            return False
            
        token = login_response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/validate-citations", 
            json={"citations": ["Section 2 of Consumer Protection Act 2019"]},
            headers=headers
        )
        
        if response.status_code != 200:
            return False
            
        data = response.json()
        required_fields = ['results', 'total_citations', 'valid_citations', 'invalid_citations']
        
        return all(field in data for field in required_fields)
    
    def test_authentication_framework(self) -> bool:
        """Test authentication and authorization framework."""
        # Test login endpoint
        login_response = self.session.post(f"{self.base_url}/api/v1/auth/login", json={
            "email": "lawyer@example.com",
            "password": "lawyer123"
        })
        
        if login_response.status_code != 200:
            return False
            
        login_data = login_response.json()
        required_fields = ['access_token', 'token_type', 'user_id', 'role', 'permissions']
        
        if not all(field in login_data for field in required_fields):
            return False
        
        # Test protected endpoint with token
        token = login_data['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        protected_response = self.session.post(
            f"{self.base_url}/api/v1/validate-citations",
            json={"citations": ["Section 2"]},
            headers=headers
        )
        
        return protected_response.status_code == 200
    
    def test_role_based_access(self) -> bool:
        """Test role-based access control."""
        # Login as citizen (should have limited permissions)
        citizen_response = self.session.post(f"{self.base_url}/api/v1/auth/login", json={
            "email": "citizen@example.com",
            "password": "citizen123"
        })
        
        if citizen_response.status_code != 200:
            return False
            
        citizen_data = citizen_response.json()
        
        # Check that citizen has appropriate permissions
        citizen_permissions = citizen_data.get('permissions', [])
        expected_citizen_permissions = ['query']
        
        return all(perm in citizen_permissions for perm in expected_citizen_permissions)
    
    def test_anonymous_access(self) -> bool:
        """Test anonymous access for citizen queries."""
        # Remove any authorization headers
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        response = self.session.post(f"{self.base_url}/api/v1/query", json={
            "query": "What are consumer rights?",
            "language": "en",
            "audience": "citizen"
        })
        
        return response.status_code == 200
    
    def test_api_documentation(self) -> bool:
        """Test API documentation endpoints."""
        docs_response = self.session.get(f"{self.base_url}/docs")
        redoc_response = self.session.get(f"{self.base_url}/redoc")
        
        return docs_response.status_code == 200 and redoc_response.status_code == 200
    
    def test_health_monitoring(self) -> bool:
        """Test health check endpoint."""
        response = self.session.get(f"{self.base_url}/health")
        
        if response.status_code != 200:
            return False
            
        data = response.json()
        required_fields = ['status', 'timestamp', 'version', 'components']
        
        return all(field in data for field in required_fields)
    
    def test_error_handling(self) -> bool:
        """Test proper error handling."""
        # Test 404 for non-existent section
        response = self.session.get(f"{self.base_url}/api/v1/section/NONEXISTENT")
        if response.status_code != 404:
            return False
        
        # Test 404 for non-existent definition
        response = self.session.get(f"{self.base_url}/api/v1/definition/nonexistent")
        if response.status_code != 404:
            return False
        
        # Test validation error for invalid query
        response = self.session.post(f"{self.base_url}/api/v1/query", json={
            "query": "",  # Empty query should fail validation
            "language": "invalid",  # Invalid language
            "audience": "invalid"   # Invalid audience
        })
        
        return response.status_code == 422  # Validation error
    
    def run_validation(self) -> bool:
        """Run complete validation suite."""
        print("=" * 80)
        print("🚀 FastAPI Backend Implementation Validation")
        print("   Task 7.1: Create FastAPI backend with core endpoints")
        print("=" * 80)
        
        validations = [
            ("REQ-7.1.1", self.test_main_api_gateway, "Main API gateway with /api/v1/query endpoint"),
            ("REQ-7.1.2", self.test_section_retrieval, "Section retrieval endpoint"),
            ("REQ-7.1.3", self.test_definition_lookup, "Definition lookup endpoint"),
            ("REQ-7.1.4", self.test_citation_validation, "Citation validation endpoint"),
            ("REQ-7.1.5", self.test_authentication_framework, "Authentication and authorization framework"),
            ("REQ-5.1.1", self.test_role_based_access, "Role-based access control (Req 5.1)"),
            ("REQ-6.1.1", self.test_anonymous_access, "Anonymous access for citizens (Req 6.1)"),
            ("REQ-10.4.1", self.test_api_documentation, "API documentation (Req 10.4)"),
            ("REQ-HEALTH", self.test_health_monitoring, "Health monitoring endpoint"),
            ("REQ-ERROR", self.test_error_handling, "Proper error handling")
        ]
        
        passed = 0
        total = len(validations)
        
        for req_id, test_func, description in validations:
            if self.validate_requirement(req_id, test_func, description):
                passed += 1
        
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        
        for req_id, result, description in self.validation_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{req_id:12} {status:8} {description}")
        
        print(f"\n🎯 Overall Result: {passed}/{total} validations passed")
        
        if passed == total:
            print("🎉 SUCCESS: All requirements validated successfully!")
            print("   Task 7.1 implementation is complete and working correctly.")
            return True
        else:
            print("⚠️  PARTIAL: Some validations failed.")
            print("   Please review the failed requirements above.")
            return False


def main():
    """Main validation entry point."""
    validator = ImplementationValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to FastAPI server at http://127.0.0.1:8000")
        print("   Please ensure the server is running with: python web_interface/app.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()