#!/usr/bin/env python
"""
Test media sending with proper URLs
"""
import requests
import json

API_BASE = "http://localhost:10000"

# Test with different media URLs
test_cases = [
    {
        "name": "Unsplash Image (Properly formatted)",
        "payload": {
            "phone": "7974734809",
            "media_url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=800&h=600&fit=crop&q=80",
            "media_type": "image",
            "caption": "Check this image!"
        }
    },
    {
        "name": "Placeholder Image",
        "payload": {
            "phone": "7974734809",
            "media_url": "https://via.placeholder.com/600x400.png",
            "media_type": "image",
            "caption": "Test image from placeholder"
        }
    },
    {
        "name": "Direct Image URL",
        "payload": {
            "phone": "7974734809",
            "media_url": "https://picsum.photos/800/600",
            "media_type": "image",
            "caption": "Random test image"
        }
    }
]

def test_media_send(test_case):
    """Test sending media with a specific payload"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_case['name']}")
    print(f"{'='*60}")
    print(f"Payload: {json.dumps(test_case['payload'], indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE}/send-media",
            json=test_case['payload'],
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
        else:
            print("❌ FAILED!")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MEDIA SEND TESTING - Multiple URLs")
    print("="*60)
    
    # Test each case
    for test_case in test_cases:
        test_media_send(test_case)
        print("\n")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS FOR MEDIA URLs:")
    print("="*60)
    print("""
    ✅ WORKING URLs:
    - https://via.placeholder.com/600x400.png
    - https://picsum.photos/800/600
    - https://images.unsplash.com/photo-ID?w=800&h=600&fit=crop&q=80
    
    ❌ PROBLEMATIC URLs:
    - https://images.unsplash.com/photo-ID (missing parameters)
    - http://localhost/image.png (not publicly accessible)
    - https://example.com/protected-image.png (authentication required)
    
    📝 NOTES:
    - URLs must be publicly accessible (no authentication)
    - URLs must use HTTPS (not HTTP)
    - Images should be under 5MB for WhatsApp
    - Supported formats: JPG, PNG (for images)
    """)
