#!/usr/bin/env python
"""
Complete API Testing and Setup Script
Tests all endpoints and provides detailed diagnostics
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE = "http://localhost:10000"
TEST_PHONE = "917974734809"
TEST_PHONE_ALT = "919876543210"

class APITester:
    def __init__(self, base_url=API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def test_endpoint(self, method: str, endpoint: str, payload=None, params=None) -> Dict[str, Any]:
        """Test an API endpoint"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method == "POST":
                response = self.session.post(url, json=payload, timeout=10)
            else:
                response = self.session.request(method, url, json=payload, timeout=10)
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status": response.status_code,
                "success": response.status_code in [200, 201],
                "response": response.json() if response.text else None,
                "error": None
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "status": 0,
                "success": False,
                "response": None,
                "error": str(e)
            }
            self.results.append(result)
            return result
    
    def print_result(self, result: Dict[str, Any]):
        """Pretty print a test result"""
        status_icon = "✓" if result["success"] else "✗"
        print(f"\n{status_icon} {result['method']} {result['endpoint']}")
        print(f"  Status: {result['status']}")
        if result['error']:
            print(f"  Error: {result['error']}")
        if result['response']:
            print(f"  Response: {json.dumps(result['response'], indent=2)[:200]}...")

def main():
    print("\n" + "="*60)
    print("Multi-Channel Communication API - Complete Test Suite")
    print("="*60)
    
    tester = APITester()
    
    # Test 1: Health Check
    print("\n[TEST 1] Health Check")
    result = tester.test_endpoint("GET", "/")
    tester.print_result(result)
    
    if not result["success"]:
        print("\n✗ Server is not running. Start with: python main.py")
        return
    
    # Test 2: Status
    print("\n[TEST 2] API Status")
    result = tester.test_endpoint("GET", "/status")
    tester.print_result(result)
    
    # Test 3: Receive Message (No WhatsApp API needed)
    print("\n[TEST 3] Receive Message - Inbound")
    payload = {
        "phone": TEST_PHONE,
        "message_text": "Hello! This is a test message from the test suite",
        "name": "Test User"
    }
    result = tester.test_endpoint("POST", "/receive-simple", payload)
    tester.print_result(result)
    
    # Wait a moment for database writes
    time.sleep(1)
    
    # Test 4: Get Conversation
    print("\n[TEST 4] Get Conversation History")
    result = tester.test_endpoint("GET", "/get-conversation", params={"phone": TEST_PHONE})
    tester.print_result(result)
    
    # Test 5: Analytics - All
    print("\n[TEST 5] Get Analytics - All Phones")
    result = tester.test_endpoint("GET", "/analytics")
    tester.print_result(result)
    
    # Test 6: Analytics - Specific Phone
    print("\n[TEST 6] Get Analytics - Specific Phone")
    result = tester.test_endpoint("GET", "/analytics", params={"phone": TEST_PHONE})
    tester.print_result(result)
    
    # Test 7: Recent Messages
    print("\n[TEST 7] Get Recent Messages")
    result = tester.test_endpoint("GET", "/recent-messages")
    tester.print_result(result)
    
    # Test 8: Leads List
    print("\n[TEST 8] Get Leads")
    result = tester.test_endpoint("GET", "/leads")
    tester.print_result(result)
    
    # Test 9: Another receive message to test multiple messages
    print("\n[TEST 9] Receive Another Message")
    payload = {
        "phone": TEST_PHONE,
        "message_text": "Second test message",
        "name": "Test User"
    }
    result = tester.test_endpoint("POST", "/receive-simple", payload)
    tester.print_result(result)
    
    time.sleep(1)
    
    # Test 10: Analytics after multiple messages
    print("\n[TEST 10] Get Analytics After Multiple Messages")
    result = tester.test_endpoint("GET", "/analytics", params={"phone": TEST_PHONE})
    tester.print_result(result)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = len(tester.results)
    passed = sum(1 for r in tester.results if r["success"])
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\n" + "="*60)
    print("SETUP INSTRUCTIONS")
    print("="*60)
    
    print("""
1. **Supabase Setup:**
   - Go to your Supabase dashboard: https://app.supabase.com
   - Open SQL Editor and run: SUPABASE_COMPLETE_SETUP.sql
   - This creates all required tables and views

2. **Environment Variables (.env):**
   - ACCESS_TOKEN: Your WhatsApp Business API token
   - PHONE_NUMBER_ID: Your WhatsApp Phone Number ID
   - SUPABASE_URL: Your Supabase project URL
   - SUPABASE_ANON_KEY: Your Supabase anon key
   - GEMINI_API_KEY: Your Google Gemini API key

3. **Start the Server:**
   python main.py
   
   The server will start on http://localhost:10000

4. **Interactive Documentation:**
   - Swagger UI: http://localhost:10000/docs
   - ReDoc: http://localhost:10000/redoc

5. **Test Endpoints:**
   - Use the test suite above
   - Or use the interactive documentation
   - Or use curl/Postman
    """)

if __name__ == "__main__":
    main()
