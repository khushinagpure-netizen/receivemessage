#!/usr/bin/env python
"""
Test Script for /send-media Endpoint
Send media files properly with correct JSON and phone number format
"""

import requests
import json
from typing import Dict, Any

API_BASE = "http://localhost:10000"

def send_media(phone: str, media_url: str, media_type: str = "image", caption: str = "", filename: str = "") -> Dict[str, Any]:
    """
    Send media via WhatsApp API
    
    Args:
        phone: Phone number with country code (e.g., "917974734809" or "+917974734809")
        media_url: Public URL to media file (e.g., https://example.com/image.png)
        media_type: Type of media - "image", "video", "document", "audio", "file"
        caption: Optional caption for media
        filename: Optional filename (for documents/files)
    
    Returns:
        Response from API
    """
    
    # Ensure phone has country code format
    phone_clean = phone.replace("+", "").replace(" ", "")
    if not phone_clean.startswith("91"):
        print(f"⚠️  Adding country code 91 to phone number...")
        phone_clean = "91" + phone_clean
    
    print(f"\n📤 Sending {media_type} to {phone_clean}")
    print(f"   URL: {media_url}")
    if caption:
        print(f"   Caption: {caption}")
    
    # Build proper JSON payload
    payload = {
        "phone": phone_clean,
        "media_url": media_url,
        "media_type": media_type,
        "caption": caption or ""
    }
    
    if filename:
        payload["filename"] = filename
    
    try:
        response = requests.post(
            f"{API_BASE}/send-media",
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        
        if response.status_code in [200, 201]:
            print(f"   ✓ Success!")
            print(f"   Message ID: {result.get('message_id')}")
            print(json.dumps(result, indent=2))
            return {"success": True, "data": result}
        else:
            print(f"   ✗ Failed: {response.status_code}")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return {"success": False, "error": result}
    
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return {"success": False, "error": str(e)}


def send_text_message(phone: str, message: str) -> Dict[str, Any]:
    """
    Send text message via WhatsApp API
    
    Args:
        phone: Phone number with country code
        message: Message text
    
    Returns:
        Response from API
    """
    
    phone_clean = phone.replace("+", "").replace(" ", "")
    if not phone_clean.startswith("91"):
        phone_clean = "91" + phone_clean
    
    print(f"\n📤 Sending text to {phone_clean}")
    print(f"   Message: {message}")
    
    payload = {
        "phone": phone_clean,
        "message": message
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/send-message",
            json=payload,
            timeout=10
        )
        
        result = response.json()
        
        if response.status_code in [200, 201]:
            print(f"   ✓ Success!")
            print(f"   Message ID: {result.get('message_id')}")
            return {"success": True, "data": result}
        else:
            print(f"   ✗ Failed: {response.status_code}")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return {"success": False, "error": result}
    
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("="*60)
    print("WhatsApp Media & Message Testing")
    print("="*60)
    
    # Test phone numbers
    PHONE_1 = "7974734809"      # Will be auto-formatted to 917974734809
    PHONE_2 = "917974734809"    # Already has country code
    
    print("\n[EXAMPLE 1] Send Text Message")
    # send_text_message(PHONE_1, "Hello! This is a test message 🚀")
    
    print("\n[EXAMPLE 2] Send Image with Caption")
    # Using a free placeholder image service
    result = send_media(
        phone=PHONE_1,
        media_url="https://via.placeholder.com/300x300?text=Test+Image",
        media_type="image",
        caption="This is a test image from the API"
    )
    
    print("\n[EXAMPLE 3] Send Document")
    # Note: You'll need to provide a real document URL
    # result = send_media(
    #     phone=PHONE_1,
    #     media_url="https://example.com/document.pdf",
    #     media_type="document",
    #     filename="document.pdf"
    # )
    
    print("\n" + "="*60)
    print("VALID MEDIA URLs (Test)")
    print("="*60)
    print("""
    Image: https://via.placeholder.com/300
    Video: https://media.w3.org/2010/05/sintel/trailer.mp4
    
    For local files, start a Python server:
        python -m http.server 8080
    
    Then use: http://localhost:8080/your-file-name
    """)
    
    print("\n[PHONE NUMBER FORMAT]")
    print("✓ Valid: 7974734809 (auto-formatted to 917974734809)")
    print("✓ Valid: 917974734809")
    print("✓ Valid: +917974734809 (+ removed automatically)")
    print("✗ Invalid: 07974734809 (leading zero)")
