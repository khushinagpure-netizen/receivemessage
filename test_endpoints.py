#!/usr/bin/env python3
"""
Test Admin/Agent Endpoint After Database Setup
"""

import requests
import json

def test_endpoints():
    """Test the admin/agent endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Admin/Agent Endpoints")
    print("=" * 40)
    
    # Test admin list
    try:
        response = requests.get(f"{base_url}/admin/list", timeout=10)
        print(f"GET /admin/list: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success: {data.get('count', 0)} admins found")
        else:
            print(f"  ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test agent list
    try:
        response = requests.get(f"{base_url}/agent/list", timeout=10)
        print(f"GET /agent/list: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Success: {data.get('count', 0)} agents found")
        else:
            print(f"  ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test admin creation
    try:
        test_admin = {
            "email": "test@katyayani.com",
            "name": "Test Admin",
            "password": "test123",
            "role": "admin"
        }
        response = requests.post(
            f"{base_url}/admin/create", 
            json=test_admin, 
            timeout=10
        )
        print(f"POST /admin/create: Status {response.status_code}")
        if response.status_code == 201:
            print("  ✅ Admin creation working!")
        else:
            print(f"  ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test agent creation
    try:
        test_agent = {
            "email": "agent@katyayani.com",
            "name": "Test Agent",
            "password": "test123",
            "role": "agent"
        }
        response = requests.post(
            f"{base_url}/agent/create",
            json=test_agent,
            timeout=10
        )
        print(f"POST /agent/create: Status {response.status_code}")
        if response.status_code == 201:
            print("  ✅ Agent creation working!")
        else:
            print(f"  ❌ Failed: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\n🎯 RESULT:")
    print("If you see ✅ statuses above, your database fix worked!")
    print("If you see ❌ errors, run the SQL script again in Supabase")

if __name__ == "__main__":
    test_endpoints()