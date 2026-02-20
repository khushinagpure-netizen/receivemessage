#!/usr/bin/env python
"""
Comprehensive API Test Suite
Tests all endpoints to verify they're working
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE = "http://localhost:10000"

# Test phone numbers
TEST_PHONE_1 = "7974734809"  # Will be auto-formatted to 917974734809
TEST_PHONE_2 = "919876543210"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def print_test(name: str, passed: bool, response: Dict[str, Any] = None):
    """Print test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"\n{name}")
    print(f"Status: {status}")
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")

def test_api(name: str, method: str, endpoint: str, data: Dict[str, Any] = None) -> tuple[bool, Dict[str, Any]]:
    """Test an API endpoint"""
    try:
        url = f"{API_BASE}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return False, {}
        
        result = response.json() if response.text else {}
        passed = response.status_code in [200, 201]
        
        print_test(name, passed, result)
        return passed, result
    
    except Exception as e:
        print_test(name, False, {"error": str(e)})
        return False, {}

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("COMPREHENSIVE API TEST SUITE")
    print("="*60 + Colors.END)
    
    results = {}
    
    # ========== HEALTH CHECK ==========
    print(f"\n{Colors.BLUE}[HEALTH CHECK]{Colors.END}")
    results["health"] = test_api(
        "1. API Health Status",
        "GET",
        "/status"
    )
    
    # ========== SEND MESSAGE ENDPOINTS ==========
    print(f"\n{Colors.BLUE}[SEND MESSAGE]{Colors.END}")
    
    results["send_text"] = test_api(
        "2. Send Text Message",
        "POST",
        "/send-message",
        {
            "phone": TEST_PHONE_1,
            "message": "🧪 Test message from API test suite"
        }
    )
    
    results["send_media"] = test_api(
        "3. Send Media (Image)",
        "POST",
        "/send-media",
        {
            "phone": TEST_PHONE_1,
            "media_url": "https://picsum.photos/400/300",
            "media_type": "image",
            "caption": "Test image from API suite"
        }
    )
    
    results["send_template"] = test_api(
        "4. Send Template Message",
        "POST",
        "/send-template",
        {
            "phone": TEST_PHONE_1,
            "template_id": "greetings",
            "variables": {"name": "TestUser"}
        }
    )
    
    # ========== RECEIVE MESSAGE ==========
    print(f"\n{Colors.BLUE}[RECEIVE MESSAGE]{Colors.END}")
    
    results["receive_simple"] = test_api(
        "5. Simulate Receive Message & AI Reply",
        "POST",
        "/receive-simple",
        {
            "phone": TEST_PHONE_1,
            "message_text": "What are your business hours?",
            "name": "Test Customer"
        }
    )
    
    # ========== LEAD MANAGEMENT ==========
    print(f"\n{Colors.BLUE}[LEAD MANAGEMENT]{Colors.END}")
    
    results["create_lead"] = test_api(
        "6. Create Lead",
        "POST",
        "/leads/create",
        {
            "phone": TEST_PHONE_2,
            "name": "Test Lead"
        }
    )
    
    results["list_leads"] = test_api(
        "7. List All Leads",
        "GET",
        "/leads"
    )
    
    results["lead_status"] = test_api(
        "8. Update Lead Status",
        "POST",
        "/leads/status",
        {
            "phone": TEST_PHONE_1,
            "status": "contacted"
        }
    )
    
    # ========== CONVERSATION ENDPOINTS ==========
    print(f"\n{Colors.BLUE}[CONVERSATIONS]{Colors.END}")
    
    results["get_conversation"] = test_api(
        "9. Get Conversation History",
        "GET",
        f"/get-conversation?phone=91{TEST_PHONE_1}"
    )
    
    results["recent_messages"] = test_api(
        "10. Get Recent Messages",
        "GET",
        f"/recent-messages?phone=91{TEST_PHONE_1}"
    )
    
    results["received_messages"] = test_api(
        "11. Get Received Messages",
        "GET",
        "/received-messages"
    )
    
    # ========== ANALYTICS & SENTIMENT ==========
    print(f"\n{Colors.BLUE}[ANALYTICS & SENTIMENT]{Colors.END}")
    
    results["analytics"] = test_api(
        "12. Get Analytics",
        "GET",
        f"/analytics?phone=91{TEST_PHONE_1}"
    )
    
    results["sentiment"] = test_api(
        "13. Get Sentiment Analysis",
        "GET",
        f"/sentiment?phone=91{TEST_PHONE_1}"
    )
    
    # ========== TEMPLATE MANAGEMENT ==========
    print(f"\n{Colors.BLUE}[TEMPLATE MANAGEMENT]{Colors.END}")
    
    results["create_template"] = test_api(
        "14. Create Message Template",
        "POST",
        "/create-template",
        {
            "template_name": f"test_template_{int(time.time())}",
            "category": "MARKETING",
            "body": "Hello {{1}}, this is a test template!"
        }
    )
    
    results["list_templates"] = test_api(
        "15. List Templates",
        "GET",
        "/templates"
    )
    
    # ========== MESSAGE STATUS ==========
    print(f"\n{Colors.BLUE}[MESSAGE STATUS]{Colors.END}")
    
    results["message_status"] = test_api(
        "16. Update Message Status",
        "POST",
        "/message-status",
        {
            "message_id": "test_msg_id",
            "status": "delivered",
            "error_code": None,
            "error_message": None
        }
    )
    
    # ========== SUMMARY ==========
    print(f"\n{Colors.BLUE}{'='*60}")
    print("TEST SUMMARY")
    print("="*60 + Colors.END)
    
    passed = sum(1 for v in results.values() if v[0])
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {Colors.GREEN}{passed}{Colors.END}")
    print(f"Failed: {Colors.RED}{total - passed}{Colors.END}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print(f"\n{Colors.BLUE}Test Details:{Colors.END}")
    for name, (passed, _) in results.items():
        status = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
        print(f"  {status} {name}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ ALL TESTS PASSED!{Colors.END}")
    else:
        print(f"\n{Colors.RED}✗ Some tests failed. Check errors above.{Colors.END}")
    
    print(f"\n{Colors.BLUE}Next Steps:{Colors.END}")
    print(f"1. Check Supabase Dashboard to verify data is being stored")
    print(f"2. Go to: https://supabase.com/dashboard > Your Project > Table Editor")
    print(f"3. Look for newly created records in: messages, conversations, leads")
    print(f"4. Test real-time by subscribing in your frontend")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.END}")
