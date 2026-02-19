"""
Utility Functions and Helpers
"""

import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, GEMINI_API_KEY, GEMINI_READY

logger = logging.getLogger(__name__)

# ============ IN-MEMORY STORAGE ============

recent_messages: List[Dict[str, Any]] = []
MAX_RECENT_MESSAGES = 100

# ============ SUPABASE HELPERS ============

def get_supabase_headers(use_service_key=False) -> Dict[str, str]:
    """Get headers for Supabase API requests"""
    key = SUPABASE_SERVICE_KEY if use_service_key else SUPABASE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

async def log_api_call(
    endpoint: str,
    method: str,
    phone: Optional[str] = None,
    status_code: int = 200,
    error: Optional[str] = None
):
    """Log API call to database or file"""
    try:
        log_entry = {
            "endpoint": endpoint,
            "method": method,
            "phone": phone,
            "status_code": status_code,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                requests.post(
                    f"{SUPABASE_URL}/rest/v1/api_logs",
                    headers=get_supabase_headers(),
                    json=log_entry,
                    timeout=5
                )
            except:
                logger.debug(f"Could not log to database: {log_entry}")
        
        logger.info(f"{method} {endpoint} - {status_code}" + (f" - {phone}" if phone else "") + (f" - {error}" if error else ""))
    except Exception as e:
        logger.error(f"Error logging API call: {e}")

# ============ MESSAGE LOGGING ============

def add_to_recent_messages(
    message: str,
    sender: str,
    phone: str,
    direction: str = "sent"
):
    """Add message to recent messages list"""
    global recent_messages
    
    msg_entry = {
        "message": message,
        "sender": sender,
        "phone": phone,
        "direction": direction,
        "status": "sent" if direction == "sent" else "received",
        "timestamp": datetime.now().isoformat()
    }
    
    recent_messages.append(msg_entry)
    
    if len(recent_messages) > MAX_RECENT_MESSAGES:
        recent_messages = recent_messages[-MAX_RECENT_MESSAGES:]

def get_recent_messages(phone: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent messages, optionally filtered by phone"""
    if phone:
        filtered = [m for m in recent_messages if m.get("phone") == phone]
    else:
        filtered = recent_messages
    
    return filtered[-limit:]

# ============ LEAD OPERATIONS ============

async def store_lead(phone: str, name: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """Store or update a lead in Supabase"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return False, {}
        
        headers = get_supabase_headers()
        
        # Check if lead exists
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{phone}&select=*",
            headers=headers,
            timeout=10
        )
        
        if check_response.status_code == 200 and check_response.json():
            return True, check_response.json()[0]
        
        # Create new lead
        lead_data = {
            "phone": phone,
            "name": name or "Unknown",
            "status": "new",
            "created_at": datetime.now().isoformat()
        }
        
        create_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/leads",
            headers={**headers, "Prefer": "return=representation"},
            json=lead_data,
            timeout=10
        )
        
        if create_response.status_code == 201:
            return True, create_response.json()[0]
        else:
            logger.error(f"Failed to create lead: {create_response.text}")
            return False, {}
    except Exception as e:
        logger.error(f"Error storing lead: {e}")
        return False, {}

async def store_conversation(
    lead_id: str,
    phone: str,
    message: str,
    sender: str,
    direction: str = "inbound",
    status: str = "received"
) -> Tuple[bool, Dict[str, Any]]:
    """Store conversation message in Supabase"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return False, {}
        
        headers = get_supabase_headers()
        
        conversation_data = {
            "lead_id": lead_id,
            "phone": phone,
            "message": message,
            "sender": sender,
            "direction": direction,
            "status": status,
            "created_at": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/conversations",
            headers={**headers, "Prefer": "return=representation"},
            json=conversation_data,
            timeout=10
        )
        
        if response.status_code == 201:
            return True, response.json()[0]
        else:
            logger.error(f"Failed to store conversation: {response.text}")
            return False, {}
    except Exception as e:
        logger.error(f"Error storing conversation: {e}")
        return False, {}

async def update_message_status(
    conversation_id: str,
    status: str
) -> bool:
    """Update conversation message status"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return False
        
        headers = get_supabase_headers()
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/conversations?id=eq.{conversation_id}",
            headers=headers,
            json={"status": status, "updated_at": datetime.now().isoformat()},
            timeout=10
        )
        
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error updating message status: {e}")
        return False

# ============ GEMINI AI HELPERS ============

async def generate_ai_reply(message: str, phone: str, conversation_history: List[str] = None) -> str:
    """Generate AI reply using Gemini 2.5 Pro"""
    try:
        if not GEMINI_READY or not GEMINI_API_KEY:
            return "Thank you for your message. An agent will respond soon."
        
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Build conversation context
        context = "You are a helpful customer support agent. Keep responses concise and professional."
        if conversation_history:
            context += "\nPrevious messages:\n" + "\n".join(conversation_history[-5:])
        
        prompt = f"{context}\n\nCustomer: {message}\nAgent:"
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=150,
                temperature=0.7
            )
        )
        
        return response.text if response.text else "Thank you for your message."
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "We received your message. Please wait for an agent response."

# ============ WHATSAPP HELPERS ============

def send_whatsapp_message(
    phone_number_id: str,
    access_token: str,
    phone: str,
    message: str
) -> Tuple[bool, str]:
    """Send message via WhatsApp Cloud API"""
    try:
        url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            return True, message_id
        else:
            logger.error(f"WhatsApp send failed: {response.text}")
            return False, ""
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False, ""

def verify_webhook_token(token: str, verify_token: str) -> bool:
    """Verify webhook token from Meta"""
    return token == verify_token
