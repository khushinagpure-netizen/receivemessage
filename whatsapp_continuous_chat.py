"""
WhatsApp Webhook Integration for Continuous Chat
Integrates continuous chat handler with WhatsApp webhook for end-to-end conversations

Features:
- Manages WhatsApp user sessions
- Routes messages to continuous chat handler
- Sends responses back to WhatsApp
- Maintains full conversation context
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from continuous_chat import process_user_message, get_user_conversation_history, reload_products
from config import ACCESS_TOKEN, PHONE_NUMBER_ID
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WhatsApp API endpoints
WHATSAPP_API_URL = f"https://graph.instagram.com/v18.0/{PHONE_NUMBER_ID}/messages"


class WhatsAppWebhookHandler:
    
    @staticmethod
    def extract_user_id(message_data: Dict) -> str:
        """Extract unique user ID from WhatsApp message"""
        try:
            phone_number = message_data.get('from', '')
            return f"whatsapp_{phone_number}"
        except:
            return "unknown_user"
    
    @staticmethod
    def extract_message_text(message_data: Dict) -> Optional[str]:
        """Extract text from various message types"""
        try:
            # Text message
            if 'text' in message_data:
                return message_data['text'].get('body')
            
            # Media message with caption
            if 'image' in message_data:
                return message_data['image'].get('caption', 'Image received')
            if 'video' in message_data:
                return message_data['video'].get('caption', 'Video received')
            if 'audio' in message_data:
                return 'Audio message received'
            
            # Button reply
            if 'button' in message_data:
                return message_data['button'].get('text')
            
            # Interactive message
            if 'interactive' in message_data:
                interactive = message_data['interactive']
                if 'button_reply' in interactive:
                    return interactive['button_reply'].get('text')
                if 'list_reply' in interactive:
                    return interactive['list_reply'].get('title')
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting message text: {str(e)}")
            return None
    
    @staticmethod
    def send_whatsapp_response(phone_number: str, response_text: str, 
                              relevant_products: list = None) -> bool:
        """Send response back to WhatsApp user"""
        try:
            # Build message payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": "text",
                "text": {"body": response_text}
            }
            
            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Send the message
            response = requests.post(
                WHATSAPP_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent to {phone_number}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False
    
    @staticmethod
    def send_product_catalog(phone_number: str, products: list) -> bool:
        """Send product cards to WhatsApp user"""
        try:
            if not products or len(products) == 0:
                return False
            
            # For simplicity, send product info as text
            # In production, use WhatsApp catalog/interactive messages
            product_text = "📦 **Recommended Products:**\n\n"
            
            for i, product in enumerate(products[:3], 1):
                product_text += f"{i}. **{product.get('name')}**\n"
                product_text += f"   💰 ₹{product.get('price')}\n"
                product_text += f"   📝 {product.get('description', '')[:80]}...\n\n"
            
            return WhatsAppWebhookHandler.send_whatsapp_response(phone_number, product_text)
            
        except Exception as e:
            logger.error(f"Error sending product catalog: {str(e)}")
            return False


def handle_incoming_message(message_data: Dict) -> Dict[str, Any]:
    """Main handler for incoming WhatsApp messages"""
    
    try:
        logger.info(f"Received message: {json.dumps(message_data, indent=2)}")
        
        # Extract information
        user_id = WhatsAppWebhookHandler.extract_user_id(message_data)
        user_phone = message_data.get('from')
        message_text = WhatsAppWebhookHandler.extract_message_text(message_data)
        
        if not message_text:
            logger.warning("No message text extracted")
            WhatsAppWebhookHandler.send_whatsapp_response(
                user_phone, 
                "I couldn't understand your message. Could you please try again?"
            )
            return {'status': 'error', 'error': 'No message text'}
        
        logger.info(f"Processing message from {user_id}: '{message_text}'")
        
        # Handle special commands
        if message_text.lower() == '/restart':
            return handle_restart_conversation(user_phone, user_id)
        
        if message_text.lower() == '/help':
            return handle_help_command(user_phone)
        
        if message_text.lower() == '/history':
            return handle_history_command(user_phone, user_id)
        
        # Process through continuous chat
        chat_response = process_user_message(user_id, message_text)
        
        if chat_response.get('status') == 'success':
            response_text = chat_response.get('response')
            relevant_products = chat_response.get('relevant_products', [])
            
            # Send main response
            WhatsAppWebhookHandler.send_whatsapp_response(user_phone, response_text)
            
            # Send product recommendations if available
            if relevant_products and len(relevant_products) > 0:
                WhatsAppWebhookHandler.send_product_catalog(user_phone, relevant_products)
            
            return {
                'status': 'success',
                'message': f"Response sent to {user_phone}",
                'user_id': user_id
            }
        else:
            error_msg = "Sorry, I encountered an error. Please try again later."
            WhatsAppWebhookHandler.send_whatsapp_response(user_phone, error_msg)
            return {
                'status': 'error',
                'error': chat_response.get('error', 'Unknown error')
            }
    
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def handle_restart_conversation(phone_number: str, user_id: str) -> Dict[str, Any]:
    """Handle /restart command"""
    try:
        from continuous_chat import chat_handler
        chat_handler.clear_conversation(user_id)
        
        welcome_msg = """🎉 Conversation restarted!

Hi! I'm your Katyayani Organics assistant. I'm here to help you with:

✨ Product information and recommendations
💰 Pricing and availability
🌿 Benefits and ingredients
📦 Delivery and returns
❓ Any other questions

What can I help you with today?"""
        
        WhatsAppWebhookHandler.send_whatsapp_response(phone_number, welcome_msg)
        
        return {'status': 'success', 'message': 'Conversation restarted'}
        
    except Exception as e:
        logger.error(f"Error restarting conversation: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def handle_help_command(phone_number: str) -> Dict[str, Any]:
    """Handle /help command"""
    help_text = """📚 **HELP - Available Commands:**

/help - Show this help message
/restart - Start a new conversation
/history - View your conversation history
/products - List all available products

**How to use:**
✅ Ask about any product
✅ Get product recommendations
✅ Ask about pricing, delivery, returns
✅ Ask about ingredients and benefits
✅ General questions about organic products

Example questions:
- "What products do you have for skincare?"
- "Tell me about your best sellers"
- "How much do your oils cost?"
- "What are the benefits of turmeric?"

Type any question and I'll help! 🌿"""
    
    WhatsAppWebhookHandler.send_whatsapp_response(phone_number, help_text)
    
    return {'status': 'success', 'message': 'Help sent'}


def handle_history_command(phone_number: str, user_id: str) -> Dict[str, Any]:
    """Handle /history command"""
    try:
        history = get_user_conversation_history(user_id)
        
        if not history:
            WhatsAppWebhookHandler.send_whatsapp_response(
                phone_number, 
                "📭 No conversation history yet. Start asking me something!"
            )
            return {'status': 'success'}
        
        history_text = "📜 **Your Conversation History:**\n\n"
        for i, msg in enumerate(history[-10:], 1):  # Show last 10 messages
            role = "You" if msg['role'] == 'user' else "Assistant"
            content = msg['content'][:100]
            history_text += f"{i}. **{role}**: {content}...\n"
        
        WhatsAppWebhookHandler.send_whatsapp_response(phone_number, history_text)
        
        return {'status': 'success'}
        
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def handle_webhook_event(payload: Dict) -> Dict[str, Any]:
    """Handle incoming webhook payload from WhatsApp"""
    
    try:
        # Extract message from webhook payload
        changes = payload.get('entry', [{}])[0].get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        
        if not messages:
            return {'status': 'no_message'}
        
        # Process first message
        message = messages[0]
        
        # Handle the message
        return handle_incoming_message(message)
        
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return {'status': 'error', 'error': str(e)}


if __name__ == "__main__":
    # Test webhook handler
    test_payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "text": {"body": "Hello, do you have any organic skincare products?"}
                    }]
                }
            }]
        }]
    }
    
    result = handle_webhook_event(test_payload)
    print(json.dumps(result, indent=2))
