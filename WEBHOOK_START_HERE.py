#!/usr/bin/env python3
"""
WEBHOOK NOT WORKING? START HERE!

This script will help you diagnose and fix webhook issues.
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                 WEBHOOK SETUP QUICK START                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

Your webhook URL: https://receivemessage.onrender.com/webhook
Verify Token:     verify_token

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 IF YOU'RE NOT GETTING MESSAGES, DO THIS NOW:

1️⃣  Go to Meta Business Manager:
    https://developers.facebook.com/apps/
    
2️⃣  Click your WhatsApp API app

3️⃣  Go to: Products → WhatsApp Business API → Settings → Webhook

4️⃣  Click "Edit" and enter:
    ✓ Callback URL: https://receivemessage.onrender.com/webhook
    ✓ Verify Token: verify_token
    ✓ Subscribe to: messages, message_status_updates, message_template_status_update
    ✓ Click "Verify and Save"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 THEN TEST YOUR SETUP:

Terminal 1 (Keep running):
    python main.py

Terminal 2 (New - Run once):
    python webhook_debug.py

Expected output:
    ✓ WEBHOOK VERIFICATION WORKING
    ✓ WEBHOOK ACCEPTED MESSAGE
    ✓ Total messages in system: 1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 REAL TEST - Send a message!

1. From ANY WhatsApp client, send a message to your business number
2. Check server logs - you should see:
   
   🔔 WEBHOOK RECEIVED - x.x.x.x
   📨 Processing incoming message from 919876543210
   ✓ Incoming message stored for 919876543210
   ✓ Auto-reply sent and stored

3. Check dashboard:
   curl http://localhost:10000/recent-messages

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  COMMON MISTAKES:

❌ "Connection refused" 
   → Server not running (python main.py)

❌ "Invalid verify token"
   → Token in Meta doesn't match .env (both should be: verify_token)

❌ Webhook URL shows 404
   → URL not registered in Meta Business Manager

❌ Messages sent but not stored
   → Database credentials issue (check .env SUPABASE_*)

❌ No auto-reply sent
   → WhatsApp API credentials expired or invalid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 MORE HELP:

Read: WEBHOOK_DEBUG_GUIDE.md (full documentation)
Test: python webhook_debug.py (automated testing)
Logs: Check your terminal where python main.py is running

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ WHAT HAPPENS WHEN IT WORKS:

1. Customer sends message to your WhatsApp
2. Meta sends webhook to: https://receivemessage.onrender.com/webhook
3. Your server receives it and:
   - Stores incoming message in Supabase
   - Stores in conversations table
   - Sends auto-reply
   - Stores auto-reply in database
4. Status updates automatically tracked
5. All visible in /recent-messages endpoint

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
