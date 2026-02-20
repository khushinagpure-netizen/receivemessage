#!/usr/bin/env python3
"""Debug conversation storage in Supabase"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:10000"
SUPABASE_URL = "https://jpdgkorskxfmgkbdbaig.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpwZGdrb3Jza3hmbWdrYmRiYWlnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzOTM3NzUsImV4cCI6MjA4Njk2OTc3NX0.O1nF3paLRgkN6TT-bRMKjznLMM6Jmlqg48jGiu_0H38"

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def check_table_exists(table_name):
    """Check if table exists and get row count"""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?limit=1",
            headers=get_supabase_headers(),
            timeout=5
        )
        print(f"  {table_name}: Status {response.status_code}")
        if response.status_code in [200, 206]:
            # Try to count
            response_count = requests.get(
                f"{SUPABASE_URL}/rest/v1/{table_name}?select=count()",
                headers=get_supabase_headers(),
                timeout=5
            )
            print(f"  {table_name}: ✓ EXISTS")
            return True
        else:
            print(f"  {table_name}: ✗ ERROR - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"  {table_name}: ✗ ERROR - {e}")
        return False

def check_data_in_table(table_name, limit=5):
    """Check what data exists in a table"""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?order=created_at.desc&limit={limit}",
            headers=get_supabase_headers(),
            timeout=5
        )
        if response.status_code in [200, 206]:
            data = response.json()
            print(f"  {table_name}: {len(data)} recent records")
            for i, record in enumerate(data[:3], 1):
                print(f"    {i}. {str(record)[:150]}...")
            return data
        else:
            print(f"  {table_name}: Error {response.status_code}")
            return []
    except Exception as e:
        print(f"  {table_name}: Error - {e}")
        return []

def test_send_and_check():
    """Test sending a message and verify storage"""
    print("\n" + "="*70)
    print("CONVERSATION STORAGE DEBUG TEST")
    print("="*70)
    
    # Step 1: Check Supabase tables
    print("\n1. CHECKING SUPABASE TABLES...")
    tables = ["leads", "conversations", "messages"]
    for table in tables:
        check_table_exists(table)
    
    # Step 2: Check current data
    print("\n2. CHECKING CURRENT DATA IN TABLES...")
    for table in tables:
        check_data_in_table(table, 3)
    
    # Step 3: Send a test message
    print("\n3. SENDING TEST MESSAGE...")
    test_phone = "919876543210"
    test_message = f"Test message - {datetime.now().strftime('%H:%M:%S')}"
    
    payload = {
        "phone": test_phone,
        "message": test_message
    }
    
    print(f"  Phone: {test_phone}")
    print(f"  Message: {test_message}")
    
    try:
        response = requests.post(
            f"{API_BASE}/send-message",
            json=payload,
            timeout=10
        )
        print(f"  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Message sent successfully")
            print(f"  Message ID: {data.get('message_id')}")
        else:
            print(f"  ✗ Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    
    # Step 4: Check data again
    print("\n4. CHECKING DATA AFTER SEND...")
    for table in tables:
        print(f"\n  {table.upper()}:")
        data = check_data_in_table(table, 3)
        
        # Look for our test data
        if data and test_phone in str(data):
            print(f"  ✓ TEST DATA FOUND IN {table.upper()}")
        elif data:
            print(f"  ⚠ Data exists but test phone not found")
        else:
            print(f"  ✗ NO DATA IN {table.upper()}")
    
    # Step 5: Direct Supabase query for our phone
    print(f"\n5. SEARCHING FOR TEST PHONE ({test_phone})...")
    for table in tables:
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/{table}?phone=eq.{test_phone}",
                headers=get_supabase_headers(),
                timeout=5
            )
            if response.status_code in [200, 206]:
                data = response.json()
                print(f"  {table}: {len(data)} records found")
                if data:
                    print(f"    Sample: {str(data[0])[:200]}...")
        except Exception as e:
            print(f"  {table}: Error - {e}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_send_and_check()
