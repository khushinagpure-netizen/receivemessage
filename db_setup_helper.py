#!/usr/bin/env python3
"""
Database Setup Helper Script
This script helps verify and set up your Supabase database tables
"""

import requests
import os
from typing import Dict, List
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in Supabase"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Supabase not configured")
            return False
        
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Test table by trying to read from it
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?limit=1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            print(f"⚠️  Error checking {table_name}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking {table_name}: {e}")
        return False

def verify_database_setup() -> Dict[str, bool]:
    """Verify all required tables exist"""
    required_tables = [
        "admins",
        "agents", 
        "leads",
        "conversations",
        "messages",
        "message_templates",
        "api_logs",
        "lead_tags",
        "automation_rules",
        "broadcast_campaigns"
    ]
    
    print("🔍 Checking database tables...")
    print("=" * 50)
    
    results = {}
    for table in required_tables:
        exists = check_table_exists(table)
        status = "✅" if exists else "❌"
        print(f"{status} {table}")
        results[table] = exists
    
    print("=" * 50)
    
    existing_count = sum(results.values())
    total_count = len(results)
    
    print(f"📊 Results: {existing_count}/{total_count} tables exist")
    
    if existing_count == total_count:
        print("🎉 SUCCESS: All required tables are set up!")
        return results
    else:
        missing = [table for table, exists in results.items() if not exists]
        print(f"❌ MISSING TABLES: {', '.join(missing)}")
        print("\n📝 ACTION REQUIRED:")
        print("1. Open your Supabase Dashboard")
        print("2. Go to SQL Editor")
        print("3. Copy and paste the entire supabase_setup.sql file")
        print("4. Click 'RUN' to execute")
        print("5. Run this script again to verify")
        
        return results

def test_admin_creation():
    """Test admin creation after tables are set up"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Supabase not configured")
            return False
        
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Test admin creation
        test_admin = {
            "email": f"test_{os.urandom(4).hex()}@example.com",
            "name": "Test Admin",
            "password_hash": "test_hash",
            "role": "admin",
            "status": "active"
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/admins",
            headers=headers,
            json=test_admin,
            timeout=10
        )
        
        if response.status_code == 201:
            admin_data = response.json()[0]
            print(f"✅ Admin creation test successful! ID: {admin_data['id']}")
            
            # Clean up test admin
            admin_id = admin_data['id']
            delete_response = requests.delete(
                f"{SUPABASE_URL}/rest/v1/admins?id=eq.{admin_id}",
                headers=headers,
                timeout=10
            )
            
            if delete_response.status_code in [200, 204]:
                print("🧹 Test admin cleaned up")
            
            return True
        else:
            print(f"❌ Admin creation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Admin creation test error: {e}")
        return False

def main():
    """Main setup verification function"""
    print("🚀 Database Setup Helper")
    print("=" * 50)
    
    # Step 1: Verify connection
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ ERROR: Supabase environment variables not configured!")
        print("Please check your .env file for:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_ROLE_KEY")
        return
    
    print(f"🔗 Connecting to: {SUPABASE_URL}")
    print()
    
    # Step 2: Check tables
    results = verify_database_setup()
    print()
    
    # Step 3: Test functionality if tables exist
    if all(results.values()):
        print("🧪 Testing admin creation...")
        if test_admin_creation():
            print("\n🎉 Database setup is COMPLETE and WORKING!")
            print("✅ You can now use all admin/agent endpoints")
        else:
            print("\n⚠️  Tables exist but admin creation failed")
            print("Check your Supabase permissions and RLS policies")
    else:
        print("\n❌ Database setup incomplete")
        print("Run the supabase_setup.sql script first")

if __name__ == "__main__":
    main()