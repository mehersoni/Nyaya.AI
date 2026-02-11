#!/usr/bin/env python3
"""
Test the complaint filing procedural query
"""

import requests
import json

def test_complaint_filing_query():
    """Test how to file a consumer complaint query"""
    
    url = "http://localhost:8080/query"
    
    test_query = "How to file a consumer complaint?"
    
    payload = {
        "query": test_query,
        "language": "en",
        "audience": "citizen"
    }
    
    print(f"Testing query: '{test_query}'")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✓ Server responded successfully")
            print(f"Response length: {len(result.get('response', ''))} characters")
            print()
            
            # Print the response
            print("Response:")
            print("-" * 40)
            print(result.get('response', 'No response'))
            print()
            
            # Check citations
            citations = result.get('citations', [])
            print(f"Citations ({len(citations)}):")
            for i, citation in enumerate(citations, 1):
                if isinstance(citation, dict):
                    section_num = citation.get('section_number', 'Unknown')
                    act = citation.get('act', 'Unknown Act')
                    title = citation.get('title', '')
                    print(f"{i}. Section {section_num}, {act}")
                    if title:
                        print(f"   Title: {title}")
                else:
                    print(f"{i}. {citation}")
            print()
            
            # Analyze content according to your criteria
            response_text = result.get('response', '').lower()
            citation_sections = []
            
            for citation in citations:
                if isinstance(citation, dict):
                    section_num = citation.get('section_number', '')
                    citation_sections.append(section_num)
            
            print("ANALYSIS ACCORDING TO YOUR CRITERIA:")
            print()
            
            # Check for Section 35 (essential)
            has_section_35 = '35' in citation_sections or 'section 35' in response_text
            print(f"✅ Section 35 (filing of complaints): {'✔️ Correctly included' if has_section_35 else '❌ Missing - CRITICAL'}")
            
            # Check for Section 39 (contextually valid)
            has_section_39 = '39' in citation_sections or 'section 39' in response_text
            print(f"✅ Section 39 (District Commission powers): {'✔️ Acceptable and helpful' if has_section_39 else '⚠️ Missing context'}")
            
            # Check for Section 2 (optional but noisy)
            has_section_2 = '2' in citation_sections or 'section 2' in response_text
            print(f"⚠️ Section 2 (definitions): {'⚠️ Included (slightly noisy but not wrong)' if has_section_2 else '✔️ Not included (cleaner)'}")
            
            print()
            print("PROCEDURAL CONTENT CHECK:")
            
            # Check for procedural guidance
            has_who_can_file = any(term in response_text for term in ['who can file', 'consumer', 'association', 'complainant'])
            has_where_to_file = any(term in response_text for term in ['district commission', 'where to file', 'jurisdiction'])
            has_how_to_file = any(term in response_text for term in ['how to file', 'electronically', 'complaint'])
            
            print(f"- Who can file: {'✔️' if has_who_can_file else '❌'}")
            print(f"- Where to file: {'✔️' if has_where_to_file else '❌'}")
            print(f"- How to file: {'✔️' if has_how_to_file else '❌'}")
            
            print()
            print("OVERALL ASSESSMENT:")
            
            # Essential criteria
            essential_met = has_section_35
            helpful_context = has_section_39
            not_too_noisy = True  # Section 2 is acceptable even if slightly noisy
            
            if essential_met and helpful_context:
                print("🎯 EXCELLENT: Query properly answered with correct legal provisions")
                print("   - Core provision (Section 35) included ✔️")
                print("   - Helpful context (Section 39) included ✔️")
                if has_section_2:
                    print("   - Definitions included (slightly noisy but legally correct) ⚠️")
                return True
            elif essential_met:
                print("✅ GOOD: Core provision included, could use more context")
                return True
            else:
                print("❌ POOR: Missing essential Section 35")
                return False
                
        else:
            print(f"❌ Server error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to demo server")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_complaint_filing_query()