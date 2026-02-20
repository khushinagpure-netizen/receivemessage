import requests
import json

BASE_URL = "http://localhost:10000"

print("=" * 70)
print("TESTING MESSAGE SENDING")
print("=" * 70)

# Test 1: Send a simple message
print("\n📤 Test 1: Send WhatsApp Message")
print("-" * 70)

payload = {
    "phone": "919876543210",
    "message": "Hello! This is a test message from API"
}

try:
    response = requests.post(
        f"{BASE_URL}/send-message",
        json=payload,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code in [200, 201]:
        print("\n✓ Message sent successfully!")
    else:
        print(f"\n✗ Failed to send message")
        
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Send Media
print("\n\n📷 Test 2: Send Media Message")
print("-" * 70)

payload = {
    "phone": "919876543210",
    "media_type": "image",
    "media_url": "https://via.placeholder.com/300",
    "caption": "Test image from API"
}

try:
    response = requests.post(
        f"{BASE_URL}/send-media",
        json=payload,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Check Conversation/Messages
print("\n\n💬 Test 3: Get Conversation History")
print("-" * 70)

try:
    response = requests.get(
        f"{BASE_URL}/get-conversation?phone=919876543210",
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Messages: {data.get('total', 0)}")
    if data.get('messages'):
        print("\nRecent messages:")
        for msg in data.get('messages', [])[:3]:
            print(f"  - {msg.get('message', 'N/A')}")
    
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Check Leads
print("\n\n👥 Test 4: Get Leads")
print("-" * 70)

try:
    response = requests.get(
        f"{BASE_URL}/leads?limit=3",
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Total Leads: {data.get('count', 0)}")
    print("\nFirst 3 leads:")
    for lead in data.get('leads', [])[:3]:
        print(f"  - {lead.get('name')} ({lead.get('phone')})")
    
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 70)
