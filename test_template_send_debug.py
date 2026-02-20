#!/usr/bin/env python3
"""Debug template send storage issue"""
import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:10000"

def test_template_send():
    """Test template send with full logging"""
    
    print("\n" + "="*60)
    print("TESTING TEMPLATE SEND WITH SUPABASE STORAGE")
    print("="*60)
    
    # First, let's get a list of templates to use
    print("\n1. FETCHING AVAILABLE TEMPLATES...")
    try:
        response = requests.get(f"{API_BASE}/templates/status", timeout=5)
        print(f"   Response Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total Templates: {data.get('total', 0)}")
            print(f"   Approved: {data.get('approved_count', 0)}")
            print(f"   Pending: {data.get('pending_count', 0)}")
            print(f"   Rejected: {data.get('rejected_count', 0)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Now test sending a template
    print("\n2. SENDING TEMPLATE MESSAGE...")
    
    test_payload = {
        "phone": "919876543210",  # Test phone number
        "template_id": "hello_world",  # Common template name
        "variables": {}
    }
    
    print(f"   Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE}/template/send",
            json=test_payload,
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body:")
        
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2))
            
            if response.status_code == 200:
                print("\n   ✓ Template sent successfully")
                print(f"   Message ID: {response_data.get('message_id')}")
                print(f"   Stored in Supabase: {response_data.get('stored_in_supabase')}")
            else:
                print(f"\n   ✗ Error: {response_data.get('error')}")
        except:
            print(f"   {response.text}")
    
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # Check if it was stored
    print("\n3. CHECKING RECENT MESSAGES (SUPABASE)...")
    
    try:
        response = requests.get(
            f"{API_BASE}/recent-messages?phone=919876543210&limit=5",
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get('messages', [])
            print(f"   Total Messages Found: {len(messages)}")
            
            if messages:
                print("\n   Recent messages:")
                for i, msg in enumerate(messages[:3], 1):
                    print(f"   {i}. {msg.get('message', '')[:80]}")
                    print(f"      - Direction: {msg.get('direction')}")
                    print(f"      - Status: {msg.get('status')}")
                    print(f"      - Sent by: {msg.get('sender_name')}")
                    print(f"      - Created: {msg.get('created_at')}")
            else:
                print("   ✗ NO MESSAGES FOUND FOR THIS PHONE NUMBER")
                print("\n   Checking ALL messages to see if any were stored...")
                
                response = requests.get(
                    f"{API_BASE}/recent-messages?limit=10",
                    timeout=10
                )
                data = response.json()
                all_messages = data.get('messages', [])
                print(f"   Total messages in database: {len(all_messages)}")
                
                if all_messages:
                    print("\n   Latest 3 messages in database:")
                    for i, msg in enumerate(all_messages[:3], 1):
                        print(f"   {i}. Phone: {msg.get('phone')}")
                        print(f"      Message: {msg.get('message', '')[:80]}")
                        print(f"      Direction: {msg.get('direction')}")
        else:
            print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_template_send()
