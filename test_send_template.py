"""
Test Send Template Endpoint
Tests the /send-template API endpoint for Agent Dashboard
"""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:10000"

def test_send_template():
    """Test sending a WhatsApp template message"""
    
    print("\n" + "="*60)
    print("Testing /send-template Endpoint")
    print("="*60)
    
    # Test 1: Send basic template (greeting)
    print("\n[TEST 1] Send greeting template without variables")
    template_payload = {
        "phone": "919876543210",  # Replace with test phone
        "template_id": "greeting",
        "variables": {}
    }
    
    try:
        response = requests.post(
            f"{API_URL}/send-template",
            json=template_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Template sent successfully!")
            data = response.json()
            print(f"  - Message ID: {data.get('message_id')}")
            print(f"  - Template: {data.get('template_id')}")
            print(f"  - Sent At: {data.get('sent_at')}")
        else:
            print(f"✗ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Send template with variables
    print("\n[TEST 2] Send template with variable substitution")
    template_with_vars = {
        "phone": "919876543210",  # Replace with test phone
        "template_id": "order_confirmation",
        "variables": {
            "order_id": "ORD-2026-001",
            "customer_name": "John Doe"
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/send-template",
            json=template_with_vars,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Template with variables sent successfully!")
            data = response.json()
            print(f"  - Message ID: {data.get('message_id')}")
            print(f"  - Variables: {data.get('variables_used')}")
        else:
            print(f"✗ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Check response headers
    print("\n[TEST 3] Verify response headers")
    try:
        response = requests.post(
            f"{API_URL}/send-template",
            json=template_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        headers = response.headers
        print("Response Headers:")
        important_headers = [
            "X-API-Version",
            "X-API-Name",
            "Cache-Control",
            "X-Content-Type-Options",
            "X-Frame-Options"
        ]
        
        for header in important_headers:
            if header in headers:
                print(f"  ✓ {header}: {headers.get(header)}")
            else:
                print(f"  ✗ {header}: NOT FOUND")
                
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: Get Swagger documentation
    print("\n[TEST 4] Download Swagger specification")
    try:
        response = requests.get(f"{API_URL}/swagger.json", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            paths = data.get("paths", {})
            
            if "/send-template" in paths:
                print("✓ /send-template endpoint found in Swagger spec!")
                endpoint_spec = paths.get("/send-template", {})
                print(f"  - Methods: {list(endpoint_spec.keys())}")
                
                post_spec = endpoint_spec.get("post", {})
                print(f"  - Description: {post_spec.get('description', 'N/A')}")
            else:
                print("✗ /send-template not in Swagger spec")
                print(f"Available endpoints: {list(paths.keys())[:5]}...")
        else:
            print(f"✗ Failed to get Swagger spec: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_send_template()
