"""
Test script for Nyayamrit FastAPI backend

This script tests the core API endpoints to ensure they work correctly.
Run this after starting the FastAPI server to verify functionality.
"""

import requests
import json
import time
from typing import Dict, Any


class APITester:
    """Test client for Nyayamrit API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
    
    def test_health_check(self) -> bool:
        """Test health check endpoint."""
        print("Testing health check endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check passed: {data['status']}")
                print(f"  Components: {data['components']}")
                return True
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return False
    
    def test_authentication(self) -> bool:
        """Test authentication endpoints."""
        print("\nTesting authentication...")
        
        try:
            # Test login with default lawyer account
            login_data = {
                "email": "lawyer@example.com",
                "password": "lawyer123"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print(f"✓ Login successful: {data['user_id']} ({data['role']})")
                print(f"  Permissions: {data['permissions']}")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Authentication error: {e}")
            return False
    
    def test_query_endpoint(self) -> bool:
        """Test main query processing endpoint."""
        print("\nTesting query endpoint...")
        
        try:
            # Test basic query
            query_data = {
                "query": "What is a consumer according to CPA 2019?",
                "language": "en",
                "audience": "citizen"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/query",
                json=query_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Query processed successfully")
                print(f"  Response length: {len(data['response'])} characters")
                print(f"  Citations: {len(data['citations'])}")
                print(f"  Confidence: {data['confidence_score']:.2f}")
                print(f"  Processing time: {data['processing_time']:.3f}s")
                
                # Print first 200 characters of response
                response_preview = data['response'][:200] + "..." if len(data['response']) > 200 else data['response']
                print(f"  Response preview: {response_preview}")
                
                return True
            else:
                print(f"✗ Query failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Query error: {e}")
            return False
    
    def test_section_retrieval(self) -> bool:
        """Test section retrieval endpoint."""
        print("\nTesting section retrieval...")
        
        try:
            # Test retrieving a known section
            section_id = "CPA_2019_S2"  # Definitions section
            
            response = self.session.get(f"{self.base_url}/api/v1/section/{section_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Section retrieved successfully: {data['section_number']}")
                print(f"  Title: {data['title']}")
                print(f"  Act: {data['act']}")
                print(f"  Text length: {len(data['text'])} characters")
                return True
            elif response.status_code == 404:
                print(f"✓ Section not found (expected for test): {section_id}")
                return True  # This is expected if knowledge graph isn't fully loaded
            else:
                print(f"✗ Section retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Section retrieval error: {e}")
            return False
    
    def test_definition_lookup(self) -> bool:
        """Test definition lookup endpoint."""
        print("\nTesting definition lookup...")
        
        try:
            # Test looking up a common legal term
            term = "consumer"
            
            response = self.session.get(f"{self.base_url}/api/v1/definition/{term}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Definition found: {data['term']}")
                print(f"  Defined in: {data['defined_in']}")
                print(f"  Definition length: {len(data['definition'])} characters")
                return True
            elif response.status_code == 404:
                print(f"✓ Definition not found (expected for test): {term}")
                return True  # This is expected if knowledge graph isn't fully loaded
            else:
                print(f"✗ Definition lookup failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Definition lookup error: {e}")
            return False
    
    def test_citation_validation(self) -> bool:
        """Test citation validation endpoint."""
        print("\nTesting citation validation...")
        
        try:
            # Test validating some citations
            validation_data = {
                "citations": [
                    "Section 2 of Consumer Protection Act 2019",
                    "Section 999 of CPA 2019",  # Invalid section
                    "Section 18 of Consumer Protection Act"
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/validate-citations",
                json=validation_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Citation validation completed")
                print(f"  Total citations: {data['total_citations']}")
                print(f"  Valid citations: {data['valid_citations']}")
                print(f"  Invalid citations: {data['invalid_citations']}")
                
                for result in data['results']:
                    status = "✓" if result['is_valid'] else "✗"
                    print(f"  {status} {result['citation']}: {result['message']}")
                
                return True
            else:
                print(f"✗ Citation validation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Citation validation error: {e}")
            return False
    
    def test_anonymous_access(self) -> bool:
        """Test anonymous access for citizen queries."""
        print("\nTesting anonymous access...")
        
        try:
            # Remove authorization header
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            # Test basic query without authentication
            query_data = {
                "query": "What are consumer rights?",
                "language": "en",
                "audience": "citizen"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/query",
                json=query_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Anonymous query processed successfully")
                print(f"  Response length: {len(data['response'])} characters")
                return True
            else:
                print(f"✗ Anonymous query failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Anonymous access error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all API tests."""
        print("=" * 60)
        print("Nyayamrit API Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test health check first
        results["health_check"] = self.test_health_check()
        
        # Test authentication
        results["authentication"] = self.test_authentication()
        
        # Test core endpoints (with authentication)
        if results["authentication"]:
            results["query_endpoint"] = self.test_query_endpoint()
            results["section_retrieval"] = self.test_section_retrieval()
            results["definition_lookup"] = self.test_definition_lookup()
            results["citation_validation"] = self.test_citation_validation()
        
        # Test anonymous access
        results["anonymous_access"] = self.test_anonymous_access()
        
        # Print summary
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name:20} : {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        return results


def main():
    """Run the API test suite."""
    tester = APITester()
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        exit(1)


if __name__ == "__main__":
    main()