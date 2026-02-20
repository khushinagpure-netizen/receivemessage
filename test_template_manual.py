"""
Quick test script for manual template creation
Run this to test if the API is working correctly
"""
import requests
import json

BASE_URL = "http://localhost:10000"

def test_manual_template():
    """Test manual template creation"""
    print("=" * 60)
    print("Testing MANUAL Template Creation")
    print("=" * 60)
    
    payload = {
        "name": "test_manual_order",
        "creation_mode": "manual",
        "content": "Hello! Your order has been confirmed. Thank you for shopping with us!",
        "category": "UTILITY",
        "title": "Order Confirmation Test"
    }
    
    print("\n Sending request:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/template/create",
            json=payload,
            timeout=30
        )
        
        print(f"\n Response Status: {response.status_code}")
        print("\n Response Body:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
            
            if response.status_code == 201:
                print("\n SUCCESS! Manual template created")
                print(f"   - Template Name: {response_json.get('template_name')}")
                print(f"   - Creation Mode: {response_json.get('creation_mode')}")
                print(f"   - Template ID: {response_json.get('template_id')}")
            elif response.status_code == 422:
                print("\n VALIDATION ERROR (422)")
                print("   The request body failed validation.")
                if 'detail' in response_json:
                    print(f"   Details: {json.dumps(response_json['detail'], indent=2)}")
            elif response.status_code == 409:
                print("\n  CONFLICT (409) - Template already exists")
                print("   Try a different name or delete the existing template")
            else:
                print(f"\n ERROR: {response.status_code}")
        except:
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("\n CONNECTION ERROR")
        print("   Server is not running on http://localhost:10000")
        print("   Start the server with: python main.py")
    except Exception as e:
        print(f"\n ERROR: {e}")


def test_ai_template():
    """Test AI template creation"""
    print("\n" + "=" * 60)
    print("Testing AI Template Creation")
    print("=" * 60)
    
    payload = {
        "name": "test_ai_welcome",
        "creation_mode": "ai",
        "prompt": "Create a friendly welcome message for new customers",
        "category": "MARKETING",
        "title": "AI Welcome Test"
    }
    
    print("\n Sending request:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{BASE_URL}/template/create",
            json=payload,
            timeout=30
        )
        
        print(f"\n Response Status: {response.status_code}")
        print("\n Response Body:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
            
            if response.status_code == 201:
                print("\n SUCCESS! AI template created")
                print(f"   - Template Name: {response_json.get('template_name')}")
                print(f"   - Creation Mode: {response_json.get('creation_mode')}")
                print(f"   - Generated Content: {response_json.get('template_content')[:100]}...")
            elif response.status_code == 422:
                print("\n VALIDATION ERROR (422)")
                if 'detail' in response_json:
                    print(f"   Details: {json.dumps(response_json['detail'], indent=2)}")
            else:
                print(f"\n❌ ERROR: {response.status_code}")
        except:
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR - Server not running")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


def test_template_status():
    """Test template status endpoint"""
    print("\n" + "=" * 60)
    print("Testing Template Status Endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/templates/status", timeout=10)
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Template Statistics:")
            print(f"   Total Templates: {data.get('total_templates')}")
            print(f"   Approved: {data.get('approved')}")
            print(f"   Pending: {data.get('pending')}")
            print(f"   Rejected: {data.get('rejected')}")
            print(f"\n   Status Breakdown: {json.dumps(data.get('status_breakdown'), indent=2)}")
            print(f"   Category Breakdown: {json.dumps(data.get('category_breakdown'), indent=2)}")
        else:
            print(response.json())
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    print("\n🚀 WhatsApp Template API Test Suite")
    print("Make sure your API server is running on http://localhost:10000\n")
    
    # Test manual template
    test_manual_template()
    
    # Test AI template
    test_ai_template()
    
    # Test status endpoint
    test_template_status()
    
    print("\n" + "=" * 60)
    print("✅ Test Suite Complete")
    print("=" * 60)
