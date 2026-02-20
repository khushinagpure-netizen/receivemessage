import requests
import json
from config import ACCESS_TOKEN, PHONE_NUMBER_ID

print("=" * 70)
print("TESTING WHATSAPP API DIRECTLY")
print("=" * 70)

print(f"\nConfiguration:")
print(f"  PHONE_NUMBER_ID: {PHONE_NUMBER_ID}")
print(f"  ACCESS_TOKEN: {ACCESS_TOKEN[:20]}..." if ACCESS_TOKEN else "  ACCESS_TOKEN: NOT SET")

url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
print(f"\nAPI URL: {url}")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "messaging_product": "whatsapp",
    "to": "919876543210",
    "type": "text",
    "text": {
        "preview_url": False,
        "body": "Hello! Test message"
    }
}

print(f"\nPayload:")
print(json.dumps(payload, indent=2))

print(f"\nSending request...")
try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    print(f"\n✓ Response Received:")
    print(f"  Status Code: {response.status_code}")
    print(f"  Headers: {dict(response.headers)}")
    print(f"  Body:")
    
    try:
        data = response.json()
        print(json.dumps(data, indent=4))
    except:
        print(f"    {response.text}")
    
    if response.status_code not in [200, 201]:
        print(f"\n⚠️ ERROR: WhatsApp API returned error!")
        print(f"\nPossible Issues:")
        print(f"  1. Token might be expired - Check Meta Business Manager")
        print(f"  2. Phone Number ID might be invalid - Verify in WhatsApp Business Account")
        print(f"  3. Recipient phone might not be registered on WhatsApp")
        print(f"  4. Message might be hitting rate limit")
        
except Exception as e:
    print(f"\n✗ Network Error: {e}")

print("\n" + "=" * 70)
