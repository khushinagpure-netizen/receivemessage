"""
Simple WhatsApp Message Sender & Receiver
Test script for sending and receiving messages via the Multi-Channel Communication API
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:10000"

# Test phone numbers
TEST_PHONE = "919876543210"  # Change this to your test phone number
RECIPIENT_PHONE = "7974734809"  # Change this to recipient phone

class WhatsAppMessenger:
    """Simple WhatsApp Messenger for testing"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def send_message(self, phone: str, message: str) -> Dict[str, Any]:
        """Send a text message"""
        print(f"\n📤 Sending message to {phone}")
        print(f"   Message: {message}")
        
        payload = {
            "phone": phone,
            "message": message
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/send-message",
                json=payload,
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code in [200, 201]:
                print(f"   ✓ Success! Message ID: {result.get('message_id')}")
                return {"success": True, "data": result}
            else:
                print(f"   ✗ Failed: {result.get('error', 'Unknown error')}")
                if 'details' in result:
                    print(f"   Details: {result['details']}")
                return {"success": False, "error": result}
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def send_media(self, phone: str, media_url: str, media_type: str = "image", caption: str = None) -> Dict[str, Any]:
        """Send media (image, video, document, etc)"""
        print(f"\n📷 Sending {media_type} to {phone}")
        print(f"   URL: {media_url}")
        if caption:
            print(f"   Caption: {caption}")
        
        payload = {
            "phone": phone,
            "media_url": media_url,
            "media_type": media_type,
            "caption": caption or ""
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/send-media",
                json=payload,
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code in [200, 201]:
                print(f"   ✓ Success! Message ID: {result.get('message_id')}")
                return {"success": True, "data": result}
            else:
                print(f"   ✗ Failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result}
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_conversation(self, phone: str) -> Dict[str, Any]:
        """Get conversation history with a phone number"""
        print(f"\n💬 Getting conversation with {phone}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/get-conversation",
                params={"phone": phone},
                timeout=10
            )
            
            result = response.json()
            total = result.get('total', 0)
            
            if response.status_code == 200:
                print(f"   ✓ Found {total} messages")
                
                messages = result.get('messages', [])
                if messages:
                    print("\n   Recent messages:")
                    for i, msg in enumerate(messages[:5], 1):
                        direction = "→" if msg.get('direction') == 'outbound' else "←"
                        sender = msg.get('sender', 'N/A')
                        text = msg.get('message', 'N/A')[:50]
                        print(f"     {i}. {direction} {sender}: {text}")
                
                return {"success": True, "data": result}
            else:
                print(f"   ✗ Failed: {result.get('error')}")
                return {"success": False, "error": result}
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_leads(self, limit: int = 10) -> Dict[str, Any]:
        """Get all leads"""
        print(f"\n👥 Getting leads (limit: {limit})")
        
        try:
            response = self.session.get(
                f"{self.base_url}/leads",
                params={"limit": limit},
                timeout=10
            )
            
            result = response.json()
            leads = result.get('leads', [])
            
            if response.status_code == 200:
                print(f"   ✓ Found {len(leads)} leads")
                
                for i, lead in enumerate(leads[:5], 1):
                    print(f"     {i}. {lead.get('name')} ({lead.get('phone')})")
                
                return {"success": True, "data": result}
            else:
                print(f"   ✗ Failed: {result.get('error')}")
                return {"success": False, "error": result}
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def create_lead(self, name: str, phone: str, email: str = None) -> Dict[str, Any]:
        """Create a new lead"""
        print(f"\n📝 Creating lead: {name} ({phone})")
        
        payload = {
            "name": name,
            "phone": phone,
            "email": email,
            "status": "new"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/leads/create",
                json=payload,
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code in [200, 201]:
                lead_id = result.get('lead', {}).get('id')
                print(f"   ✓ Lead created! ID: {lead_id}")
                return {"success": True, "data": result}
            else:
                print(f"   ✗ Failed: {result.get('error')}")
                return {"success": False, "error": result}
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_sentiment(self, phone: str) -> Dict[str, Any]:
        """Get sentiment analysis for a conversation"""
        print(f"\n😊 Getting sentiment analysis for {phone}")
        
        try:
            response = self.session.get(
                f"{self.base_url}/sentiment",
                params={"phone": phone},
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code == 200:
                analysis = result.get('analysis', {})
                sentiment = analysis.get('overall_sentiment', 'N/A')
                confidence = analysis.get('confidence', 0)
                print(f"   ✓ Sentiment: {sentiment} (Confidence: {confidence:.2%})")
                return {"success": True, "data": result}
            else:
                print(f"   ⚠ No sentiment data: {result.get('error')}")
                return {"success": False, "error": result}
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_analytics(self, phone: str = None) -> Dict[str, Any]:
        """Get analytics for messages"""
        print(f"\n📊 Getting analytics" + (f" for {phone}" if phone else ""))
        
        try:
            response = self.session.get(
                f"{self.base_url}/analytics",
                params={"phone": phone} if phone else {},
                timeout=10
            )
            
            result = response.json()
            
            if response.status_code == 200:
                stats = result.get('stats', {})
                print(f"   ✓ Analytics retrieved:")
                print(f"     Total Messages: {stats.get('total_messages', 0)}")
                print(f"     Sent: {stats.get('total_sent', 0)}")
                print(f"     Received: {stats.get('total_received', 0)}")
                print(f"     Delivery Rate: {stats.get('delivery_rate', 0):.2%}")
                print(f"     Read Rate: {stats.get('read_rate', 0):.2%}")
                return {"success": True, "data": result}
            else:
                print(f"   ✗ Failed: {result.get('error')}")
                return {"success": False, "error": result}
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_server(self) -> bool:
        """Test if server is running"""
        print(f"🔍 Testing server at {self.base_url}")
        
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                services = data.get('services', {})
                print(f"   ✓ Server is healthy!")
                print(f"     WhatsApp: {'✓' if services.get('whatsapp') else '✗'}")
                print(f"     Gemini: {'✓' if services.get('gemini') else '✗'}")
                print(f"     Database: {'✓' if services.get('database') else '✗'}")
                return True
            else:
                print(f"   ✗ Server returned error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ✗ Server not responding: {e}")
            return False


def main():
    """Main test function"""
    
    print("\n" + "=" * 70)
    print("WHATSAPP MESSAGING TEST")
    print("=" * 70)
    
    # Initialize messenger
    messenger = WhatsAppMessenger()
    
    # Test server connection
    if not messenger.test_server():
        print("\n⚠️ Server is not running! Start it with: python main.py")
        return
    
    print("\n" + "=" * 70)
    print("RUNNING TESTS")
    print("=" * 70)
    
    # Test 1: Get existing leads
    print("\n[TEST 1] Get Existing Leads")
    messenger.get_leads(5)
    
    # Test 2: Create a new lead
    print("\n[TEST 2] Create New Lead")
    messenger.create_lead("Test User", "919876543210", "test@example.com")
    
    # Test 3: Send a message
    print("\n[TEST 3] Send Text Message")
    messenger.send_message(RECIPIENT_PHONE, "Hello! This is a test message from the API 🚀")
    
    # Test 4: Send another message
    print("\n[TEST 4] Send Another Message")
    messenger.send_message(RECIPIENT_PHONE, "How are you doing? 😊")
    
    # Test 5: Get conversation
    print("\n[TEST 5] Get Conversation History")
    messenger.get_conversation(RECIPIENT_PHONE)
    
    # Test 6: Get analytics
    print("\n[TEST 6] Get Analytics")
    messenger.get_analytics(RECIPIENT_PHONE)
    
    # Test 7: Get sentiment analysis
    print("\n[TEST 7] Get Sentiment Analysis")
    messenger.get_sentiment(RECIPIENT_PHONE)
    
    # Test 8: Send media
    print("\n[TEST 8] Send Media (Image)")
    messenger.send_media(
        RECIPIENT_PHONE,
        "https://via.placeholder.com/300",
        "image",
        "Check out this image! 🖼️"
    )
    
    print("\n" + "=" * 70)
    print("TESTS COMPLETED")
    print("=" * 70)
    print("\n💡 Tips:")
    print("  - Update RECIPIENT_PHONE to test with actual numbers")
    print("  - Check server logs for detailed information")
    print("  - Use the /docs endpoint for interactive API testing")
    print("  - Run: http://localhost:10000/docs")
    print("\n")


if __name__ == "__main__":
    main()
