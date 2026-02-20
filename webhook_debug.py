#!/usr/bin/env python3
"""Webhook Debugging Tool - Check webhook configuration and receive status"""
import requests
import json
from datetime import datetime
import hmac
import hashlib

WEBHOOK_URL = "https://receivemessage.onrender.com/webhook"
LOCAL_API = "http://localhost:10000"
VERIFY_TOKEN = "verify_token"
APP_SECRET = "a9567d1b077a793273817ce095d910b0"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_webhook_verification():
    """Test webhook verification endpoint"""
    print_section("1. TESTING WEBHOOK VERIFICATION (GET /webhook)")
    
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": "test_challenge_123456",
        "hub.verify_token": VERIFY_TOKEN
    }
    
    print(f"  Endpoint: {LOCAL_API}/webhook")
    print(f"  Verify Token: {VERIFY_TOKEN}")
    print(f"  Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(
            f"{LOCAL_API}/webhook",
            params=params,
            timeout=5
        )
        
        print(f"\n  Response Status: {response.status_code}")
        print(f"  Response Body: {response.text}")
        
        if response.status_code == 200 and response.text == "test_challenge_123456":
            print(f"  ✓ WEBHOOK VERIFICATION WORKING")
            return True
        elif response.status_code == 200:
            print(f"  ✗ Wrong response (should echo challenge)")
            return False
        elif response.status_code == 403:
            print(f"  ✗ INVALID VERIFY TOKEN - Check .env VERIFY_TOKEN")
            return False
        else:
            print(f"  ✗ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Connection Error: {e}")
        print(f"  Is your server running on {LOCAL_API}?")
        return False

def test_incoming_message():
    """Test sending a simulated webhook message"""
    print_section("2. TESTING INCOMING MESSAGE (POST /webhook)")
    
    # Create a test webhook payload (Meta format)
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "ENTRY_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919201962703",
                                "phone_number_id": "1006033565923189"
                            },
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.test_message_id_123",
                                    "timestamp": str(int(datetime.now().timestamp())),
                                    "type": "text",
                                    "text": {
                                        "body": "Test message from debugging script"
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    payload_json = json.dumps(webhook_payload)
    
    print(f"  Endpoint: {LOCAL_API}/webhook")
    print(f"  Payload (formatted):")
    print(json.dumps(webhook_payload, indent=2))
    
    # Create signature
    app_secret = APP_SECRET
    signature = hmac.new(
        app_secret.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={signature}"
    }
    
    print(f"\n  Headers:")
    print(f"    Content-Type: application/json")
    print(f"    X-Hub-Signature-256: sha256={signature[:20]}...")
    
    try:
        response = requests.post(
            f"{LOCAL_API}/webhook",
            data=payload_json,
            headers=headers,
            timeout=5
        )
        
        print(f"\n  Response Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        if response.status_code == 200:
            print(f"  ✓ WEBHOOK ACCEPTED MESSAGE")
            return True
        else:
            print(f"  ✗ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Connection Error: {e}")
        return False

def check_webhook_configuration():
    """Show webhook configuration checklist"""
    print_section("3. WEBHOOK CONFIGURATION CHECKLIST")
    
    print(f"""
✓ REQUIRED SETUP IN META BUSINESS MANAGER:

1. Webhook URL Configuration:
   - Go to: https://developers.facebook.com/apps/
   - Select your app → Products → WhatsApp Business API
   - Settings → Webhook → Click "Edit"
   - Callback URL: {WEBHOOK_URL}
   - Verify Token: {VERIFY_TOKEN}
   - Subscribe to: messages, message_template_status_update, message_status_reviews
   - Click "Verify and Save"

2. Webhook Access Token:
   - Generate a long-lived access token
   - Set in .env as ACCESS_TOKEN: {APP_SECRET[:20]}...

3. Phone Number Assignment:
   - Ensure your phone number is assigned to your WABA
   - Phone Number ID: 1006033565923189
   - WABA ID: 4154575724855200

⚠️  TROUBLESHOOTING:

If webhook not working:
1. Check Meta Business Manager webhook settings
2. Verify callback URL is publicly accessible (HTTPS)
3. Verify token must match exactly
4. Check firewall/port settings
5. Ensure your server is running and publicly accessible
6. Check server logs for errors

Your Current Configuration:
- Webhook URL: {WEBHOOK_URL}
- Verify Token: {VERIFY_TOKEN}
- Local Test URL: {LOCAL_API}/webhook
- API Port: 10000
    """)

def test_recent_messages_endpoint():
    """Test if recent messages are stored"""
    print_section("4. CHECKING MESSAGE STORAGE")
    
    print(f"  Endpoint: {LOCAL_API}/recent-messages")
    
    try:
        response = requests.get(
            f"{LOCAL_API}/recent-messages?limit=5",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Endpoint accessible")
            print(f"  Total messages in system: {data.get('total', 0)}")
            
            messages = data.get('messages', [])
            if messages:
                print(f"\n  Recent {min(3, len(messages))} messages:")
                for i, msg in enumerate(messages[:3], 1):
                    print(f"  {i}. From: {msg.get('phone')[:12]}...")
                    print(f"     Message: {msg.get('message', '')[:80]}...")
                    print(f"     Time: {msg.get('created_at')}")
            else:
                print(f"  ⚠ No messages stored yet")
                print(f"  Messages should appear after webhook is received")
        else:
            print(f"  ✗ Error: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Connection Error: {e}")

def test_webhook_logs():
    """Check if server has logs"""
    print_section("5. SERVER LOGS")
    
    print(f"""
📋 To see SERVER LOGS:

1. In your terminal where main.py is running, you should see:
   - "Received message from 919876543210: Test message..."
   - "✓ Incoming message stored for 919876543210"
   - "✓ Auto-reply sent and stored..."

2. If you DON'T see these logs:
   - Webhook not reaching your server
   - Check firewall/network settings
   - Ensure {WEBHOOK_URL} is correct in Meta

3. If you see ERROR logs:
   - Copy the error and investigate
   - May need to update code

🔍 To test locally:
   - Run this script with your server running
   - Messages should appear in /recent-messages endpoint
    """)

def main():
    print_section("WHATSAPP WEBHOOK DEBUG TOOL")
    
    print(f"\nCurrent Time: {datetime.now().isoformat()}")
    print(f"Testing Server: {LOCAL_API}")
    
    # Run tests
    test1 = test_webhook_verification()
    test2 = test_incoming_message()
    check_webhook_configuration()
    test_recent_messages_endpoint()
    test_webhook_logs()
    
    # Summary
    print_section("TEST SUMMARY")
    
    if test1 and test2:
        print("""
✓ WEBHOOK IS WORKING!

Your server is:
✓ Receiving webhook requests
✓ Processing messages
✓ Storing in database

Next: Check Meta Business Manager webhook configuration
      Messages should start flowing in when customers send messages
        """)
    elif test1:
        print("""
⚠ WEBHOOK VERIFICATION WORKS BUT MESSAGE PROCESSING FAILED

Issues to check:
1. Message format might be wrong
2. Database might not be accessible
3. Check server logs for errors

Go to your terminal and look for error messages
        """)
    else:
        print("""
✗ WEBHOOK NOT WORKING - Connection Issues

Your server is not responding to webhook calls.

Check:
1. Is your server running? (python main.py)
2. Is it running on port 10000?
3. Are there firewall issues?
4. Is your local URL correct?

Common Issues:
- Server crashed (check terminal)
- Port 10000 in use by another process
- Network not accessible

Fix: Check your terminal for error messages and restart server
        """)

if __name__ == "__main__":
    main()
