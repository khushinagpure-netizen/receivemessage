#!/usr/bin/env python3
"""Test conversation and message storage"""
import requests
import json
from datetime import datetime
import time

API_BASE = "http://localhost:10000"
SUPABASE_URL = "https://jpdgkorskxfmgkbdbaig.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpwZGdrb3Jza3hmbWdrYmRiYWlnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzOTM3NzUsImV4cCI6MjA4Njk2OTc3NX0.O1nF3paLRgkN6TT-bRMKjznLMM6Jmlqg48jGiu_0H38"

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_unified_storage():
    """Test the unified conversation+message storage"""
    
    print_section("UNIFIED CONVERSATION + MESSAGE STORAGE TEST")
    
    # Test phone number
    test_phone = "919876543210"
    test_message = f"Test message {datetime.now().strftime('%H:%M:%S')}"
    
    # Step 1: Send a test message
    print("\n1. SENDING TEST MESSAGE...")
    print(f"   Phone: {test_phone}")
    print(f"   Message: {test_message}")
    
    payload = {
        "phone": test_phone,
        "message": test_message
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/send-message",
            json=payload,
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            msg_id = data.get("message_id")
            stored = data.get("stored_in_supabase", False)
            print(f"   ✓ Message sent successfully")
            print(f"   Message ID: {msg_id}")
            print(f"   Stored in Supabase: {stored}")
        else:
            print(f"   ✗ Error: {response.text[:200]}")
            return
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return
    
    # Wait for storage to complete
    time.sleep(2)
    
    # Step 2: Check MESSAGES table
    print("\n2. CHECKING MESSAGES TABLE...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/messages?phone=eq.{test_phone}&order=created_at.desc&limit=5",
            headers=get_supabase_headers(),
            timeout=5
        )
        
        if response.status_code in [200, 206]:
            messages = response.json()
            print(f"   Found {len(messages)} messages for {test_phone}")
            
            if messages:
                print(f"   ✓ MESSAGES TABLE HAS DATA")
                for i, msg in enumerate(messages[:3], 1):
                    print(f"   {i}. {msg.get('message', '')[:80]}")
                    print(f"      Direction: {msg.get('direction')}")
                    print(f"      Status: {msg.get('status')}")
                    print(f"      Created: {msg.get('created_at')}")
            else:
                print(f"   ✗ NO DATA IN MESSAGES TABLE")
        else:
            print(f"   ✗ Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Step 3: Check LEADS table
    print("\n3. CHECKING LEADS TABLE...")
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{test_phone}&limit=1",
            headers=get_supabase_headers(),
            timeout=5
        )
        
        if response.status_code in [200, 206]:
            leads = response.json()
            print(f"   Found {len(leads)} leads for {test_phone}")
            
            if leads:
                lead = leads[0]
                lead_id = lead.get("id")
                print(f"   ✓ LEAD EXISTS")
                print(f"   Lead ID: {lead_id}")
                print(f"   Name: {lead.get('name')}")
                print(f"   Status: {lead.get('status')}")
            else:
                print(f"   ✗ NO LEAD FOUND")
                lead_id = None
        else:
            print(f"   ✗ Error: {response.status_code}")
            lead_id = None
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        lead_id = None
    
    # Step 4: Check CONVERSATIONS table
    print("\n4. CHECKING CONVERSATIONS TABLE...")
    try:
        if lead_id:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/conversations?phone=eq.{test_phone}&order=created_at.desc&limit=5",
                headers=get_supabase_headers(),
                timeout=5
            )
            
            if response.status_code in [200, 206]:
                conversations = response.json()
                print(f"   Found {len(conversations)} conversations for {test_phone}")
                
                if conversations:
                    print(f"   ✓ CONVERSATIONS TABLE HAS DATA")
                    for i, conv in enumerate(conversations[:3], 1):
                        print(f"   {i}. {conv.get('message', '')[:80]}")
                        print(f"      Sender: {conv.get('sender')}")
                        print(f"      Direction: {conv.get('direction')}")
                        print(f"      Created: {conv.get('created_at')}")
                else:
                    print(f"   ⚠ NO DATA IN CONVERSATIONS TABLE (but lead exists)")
            else:
                print(f"   ⚠ Error reading conversations: {response.status_code}")
        else:
            print(f"   ✗ Cannot check - no lead_id")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Step 5: Summary
    print_section("TEST SUMMARY")
    print("""
✓ Test script complete!

What to check:
1. Ensure API returned "stored_in_supabase": true
2. Verify MESSAGES table has the test message (outbound, direction=outbound)
3. Verify LEADS table has a record for the phone number
4. Verify CONVERSATIONS table has the message linked to the lead
5. All should have created_at timestamps and be recent

If any table is empty:
- Check Supabase RLS policies (they might be blocking inserts)
- Check the API logs in terminal for error messages
- Run: tail -f api.log  or check console output
    """)

if __name__ == "__main__":
    test_unified_storage()
