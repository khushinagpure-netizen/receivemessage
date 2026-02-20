"""
Utility Functions and Helpers with enhanced features
Real-time database operations with proper error handling
"""

import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, GEMINI_API_KEY, SERVICE_STATUS, ACCESS_TOKEN, PHONE_NUMBER_ID

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
    error: Optional[str] = None,
    response_time_ms: int = 0
):
    """Log API call to database"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.debug(f"Supabase not configured, skipping log: {endpoint}")
            return
        
        log_entry = {
            "endpoint": endpoint,
            "method": method,
            "phone": phone,
            "status_code": status_code,
            "error": error,
            "response_time_ms": response_time_ms
        }
        
        requests.post(
            f"{SUPABASE_URL}/rest/v1/api_logs",
            headers=get_supabase_headers(),
            json=log_entry,
            timeout=5
        )
        
        log_msg = f"[API LOG] {method} {endpoint} - {status_code}"
        if phone:
            log_msg += f" - Phone: {phone}"
        if error:
            log_msg += f" - Error: {error}"
        logger.info(log_msg)
        
    except Exception as e:
        logger.debug(f"Could not log API call: {e}")

# ============ MESSAGE STORAGE ============

def add_to_recent_messages(
    message: str,
    sender: str,
    phone: str,
    direction: str = "sent"
):
    """Add message to in-memory recent messages list"""
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
    """Get recent messages from in-memory storage"""
    if phone:
        filtered = [m for m in recent_messages if m.get("phone") == phone]
    else:
        filtered = recent_messages
    
    return filtered[-limit:]

# ============ DATABASE - MESSAGES ============

async def store_message(
    phone: str,
    message: str,
    direction: str = "inbound",
    status: str = "received",
    sender_name: Optional[str] = None,
    sender_type: str = "customer",
    message_id: Optional[str] = None,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None,
    caption: Optional[str] = None
) -> Tuple[bool, str]:
    """Store message in messages table (primary table)"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase not configured")
            return False, ""
        
        headers = get_supabase_headers()
        
        message_data = {
            "phone": phone,
            "message": message,
            "direction": direction,
            "status": status,
            "sender_name": sender_name or "Unknown",
            "sender_type": sender_type,
            "message_id": message_id,
            "media_url": media_url,
            "media_type": media_type,
            "caption": caption
        }
        
        logger.debug(f"Storing message to database: {phone} - {direction} - {status}")
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/messages",
            headers={**headers, "Prefer": "return=representation"},
            json=message_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            if isinstance(result, list) and result:
                msg_id = result[0].get("id", message_id or "unknown")
            else:
                msg_id = message_id or "unknown"
            logger.info(f"✓ Message stored: {phone} ({direction}) - ID: {msg_id}")
            return True, msg_id
        else:
            logger.error(f"Failed to store message: {response.status_code} - {response.text}")
            return False, ""
    
    except Exception as e:
        logger.error(f"Error storing message: {e}", exc_info=True)
        return False, ""

# ============ DATABASE - LEADS ============

async def store_lead(phone: str, name: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """Store or get existing lead in Supabase"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase not configured")
            return False, {}
        
        headers = get_supabase_headers()
        phone_clean = phone.replace("+", "").replace(" ", "")
        
        # Check if lead already exists
        logger.debug(f"Checking for existing lead: {phone_clean}")
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{phone_clean}",
            headers=headers,
            timeout=10
        )
        
        if check_response.status_code == 200:
            existing_leads = check_response.json()
            if existing_leads and len(existing_leads) > 0:
                logger.info(f"Lead already exists: {phone_clean}")
                return True, existing_leads[0]
        
        # Create new lead
        lead_data = {
            "phone": phone_clean,
            "name": name or f"Lead {phone_clean}",
            "status": "new"
        }
        
        logger.debug(f"Creating new lead: {phone_clean}")
        
        create_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/leads",
            headers={**headers, "Prefer": "return=representation"},
            json=lead_data,
            timeout=10
        )
        
        if create_response.status_code in [200, 201]:
            result = create_response.json()
            if isinstance(result, list) and result:
                logger.info(f"✓ Lead created: {phone_clean}")
                return True, result[0]
            return True, lead_data
        else:
            logger.error(f"Failed to create lead: {create_response.status_code} - {create_response.text}")
            return False, {}
    
    except Exception as e:
        logger.error(f"Error storing lead: {e}", exc_info=True)
        return False, {}

async def get_leads(limit: int = 50) -> Tuple[bool, List[Dict[str, Any]]]:
    """Get all leads from Supabase"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase not configured")
            return False, []
        
        headers = get_supabase_headers()
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?limit={limit}&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            leads = response.json()
            logger.info(f"Retrieved {len(leads)} leads")
            return True, leads
        else:
            logger.error(f"Failed to get leads: {response.status_code}")
            return False, []
    
    except Exception as e:
        logger.error(f"Error getting leads: {e}", exc_info=True)
        return False, []

async def update_lead_status(phone: str, status: str) -> bool:
    """Update lead status"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return False
        
        headers = get_supabase_headers()
        phone_clean = phone.replace("+", "").replace(" ", "")
        
        update_data = {"status": status}
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{phone_clean}",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Lead status updated: {phone_clean} -> {status}")
            return True
        else:
            logger.error(f"Failed to update lead status: {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"Error updating lead status: {e}")
        return False

# ============ DATABASE - CONVERSATIONS ============

async def store_conversation(
    lead_id: str,
    phone: str,
    message: str,
    sender: str,
    direction: str = "inbound",
    status: str = "received",
    sender_type: str = "customer",
    message_id: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """Store conversation message in conversations table (grouped by lead)"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase not configured")
            return False, {}
        
        headers = get_supabase_headers()
        
        conversation_data = {
            "lead_id": lead_id,
            "phone": phone,
            "message": message,
            "sender": sender,
            "sender_type": sender_type,
            "direction": direction,
            "status": status,
            "message_id": message_id
        }
        
        logger.debug(f"Storing conversation: {phone} - {sender} ({direction})")
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/conversations",
            headers={**headers, "Prefer": "return=representation"},
            json=conversation_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            if isinstance(result, list) and result:
                logger.info(f"✓ Conversation stored: {phone}")
                return True, result[0]
            return True, conversation_data
        else:
            logger.error(f"Failed to store conversation: {response.status_code} - {response.text}")
            return False, {}
    
    except Exception as e:
        logger.error(f"Error storing conversation: {e}", exc_info=True)
        return False, {}

async def get_conversation(phone: str, limit: int = 50) -> Tuple[bool, List[Dict[str, Any]]]:
    """Get conversation history for a phone number"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return False, []
        
        # Normalize phone - add 91 if not present
        phone_clean = phone.replace("+", "").replace(" ", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean
        
        headers = get_supabase_headers()
        
        logger.debug(f"Fetching conversation for {phone_clean}")
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conversations?phone=eq.{phone_clean}&limit={limit}&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            messages = response.json()
            logger.info(f"✓ Retrieved {len(messages)} conversation messages for {phone_clean}")
            return True, messages
        else:
            logger.error(f"Failed to get conversation: {response.status_code} - {response.text}")
            return False, []
    
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        return False, []

async def store_conversation_with_message(
    phone: str,
    message: str,
    sender: str,
    direction: str = "inbound",
    status: str = "received",
    sender_type: str = "customer",
    message_id: Optional[str] = None,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None,
    caption: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Store message in BOTH messages and conversations tables together
    This ensures complete conversation history is maintained
    
    Args:
    - phone: Customer phone number
    - message: Message text content
    - sender: Name of sender
    - direction: "inbound" or "outbound"
    - status: "sent", "delivered", "read", "received", "failed"  
    - sender_type: "customer", "agent", "template"
    - message_id: Meta message ID (optional, will be generated if not provided)
    - media_url: URL if media message
    - media_type: Image, video, document, etc.
    - caption: Caption for media (optional)
    
    Returns: (success: bool, message_dict: dict)
    """
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase not configured")
            return False, {}
        
        # Normalize phone
        phone_clean = phone.replace("+", "").replace(" ", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean
        
        # Generate message_id if not provided
        if not message_id:
            message_id = str(__import__('uuid').uuid4())
        
        # Step 1: Store message in messages table
        message_data = {
            "phone": phone_clean,
            "message": message,
            "direction": direction,
            "status": status,
            "sender_name": sender,
            "sender_type": sender_type,
            "message_id": message_id,
            "media_url": media_url,
            "media_type": media_type,
            "caption": caption
        }
        
        headers = get_supabase_headers()
        
        logger.debug(f"Storing message+conversation: {phone_clean} - {direction} ({sender})")
        
        msg_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/messages",
            headers={**headers, "Prefer": "return=representation"},
            json=message_data,
            timeout=10
        )
        
        msg_success = msg_response.status_code in [200, 201]
        
        if msg_success:
            logger.info(f"✓ Stored message: {phone_clean} ({direction})")
        else:
            logger.error(f"Failed to store message: {msg_response.status_code} - {msg_response.text[:200]}")
        
        # Step 2: Create/get lead
        lead_data = {
            "phone": phone_clean,
            "name": f"Lead {phone_clean}",
            "status": "active"
        }
        
        # Check if lead exists
        lead_check = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{phone_clean}&limit=1",
            headers=headers,
            timeout=10
        )
        
        lead_id = None
        
        if lead_check.status_code == 200:
            existing_leads = lead_check.json()
            if existing_leads:
                lead_id = existing_leads[0].get("id")
                logger.debug(f"Using existing lead: {lead_id}")
            else:
                # Create new lead
                lead_response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/leads",
                    headers={**headers, "Prefer": "return=representation"},
                    json=lead_data,
                    timeout=10
                )
                
                if lead_response.status_code in [200, 201]:
                    result = lead_response.json()
                    if isinstance(result, list) and result:
                        lead_id = result[0].get("id")
                        logger.debug(f"Created new lead: {lead_id}")
        
        # Step 3: Store conversation if we have a lead_id
        conv_success = False
        if lead_id:
            conversation_data = {
                "lead_id": lead_id,
                "phone": phone_clean,
                "message": message,
                "sender": sender,
                "sender_type": sender_type,
                "direction": direction,
                "status": status,
                "message_id": message_id
            }
            
            conv_response = requests.post(
                f"{SUPABASE_URL}/rest/v1/conversations",
                headers={**headers, "Prefer": "return=representation"},
                json=conversation_data,
                timeout=10
            )
            
            conv_success = conv_response.status_code in [200, 201]
            
            if conv_success:
                logger.info(f"✓ Stored conversation: {phone_clean} (Lead: {lead_id})")
            else:
                logger.error(f"Failed to store conversation: {conv_response.status_code} - {conv_response.text[:200]}")
        else:
            logger.warning(f"Could not store conversation - no lead_id for {phone_clean}")
        
        # Return success if at least message was stored
        return msg_success, message_data if msg_success else {}
    
    except Exception as e:
        logger.error(f"Error storing message+conversation: {e}", exc_info=True)
        return False, {}

# ============ DATABASE - MESSAGE STATUS ============

async def update_message_status(
    message_id: str,
    status: str,
    error_message: Optional[str] = None
) -> bool:
    """Update message status in messages table"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return False
        
        headers = get_supabase_headers()
        
        update_data = {
            "status": status,
            "error_message": error_message
        }
        
        logger.debug(f"Updating message status: {message_id} -> {status}")
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/messages?message_id=eq.{message_id}",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✓ Message status updated: {message_id} -> {status}")
            return True
        else:
            logger.error(f"Failed to update message status: {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"Error updating message status: {e}")
        return False

async def update_message_status_advanced(
    message_id: str,
    status: str,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None
) -> bool:
    """Update message status with error details"""
    return await update_message_status(message_id, status, error_message)

# ============ GEMINI AI HELPERS ============

async def generate_ai_reply(message: str, phone: str, conversation_history: List[str] = None) -> str:
    """Generate AI reply using Gemini 2.5 Pro"""
    try:
        if not SERVICE_STATUS.get("gemini", False):
            logger.debug("Gemini not ready - returning default reply")
            return "Thank you for your message. An agent will respond soon."
        
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not configured")
            return "Thank you for your message. An agent will respond soon."
        
        try:
            import google.generativeai as genai
        except ImportError:
            logger.warning("google.generativeai not installed")
            return "Thank you for your message. An agent will respond soon."
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Build conversation context
        context = f"You are a helpful WhatsApp customer service agent. Answer briefly and professionally."
        if conversation_history:
            context += "\n\nRecent conversation:\n" + "\n".join(conversation_history[-5:])
        
        context += f"\n\nCustomer message: {message}"
        
        logger.debug(f"Generating AI reply for {phone}")
        
        response = model.generate_content(context)
        reply = response.text if response.text else "Thank you for your message."
        
        logger.info(f"✓ AI reply generated for {phone}")
        return reply
    
    except Exception as e:
        logger.error(f"Error generating AI reply: {e}", exc_info=True)
        return "Thank you for your message. An agent will respond soon."

# ============ WHATSAPP API HELPERS ============

def send_whatsapp_message(
    phone_number_id: str,
    access_token: str,
    phone: str,
    message: str
) -> Tuple[bool, str]:
    """Send text message via WhatsApp Cloud API"""
    try:
        if not phone_number_id or not access_token:
            logger.error("Phone number ID or access token is missing")
            return False, ""
        
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message}
        }
        
        logger.debug(f"Sending text message to {phone}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        logger.debug(f"WhatsApp API response: {response.status_code} - {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"✓ WhatsApp text sent to {phone} (ID: {message_id})")
            return True, message_id
        else:
            logger.error(f"WhatsApp API failed: {response.status_code} - {response.text}")
            return False, ""
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}", exc_info=True)
        return False, ""

def send_media_message(
    phone_number_id: str,
    access_token: str,
    phone: str,
    media_url: str,
    media_type: str,
    caption: Optional[str] = None,
    filename: Optional[str] = None
) -> Tuple[bool, str]:
    """Send media (image/video/document/file/audio) via WhatsApp"""
    try:
        if not phone_number_id or not access_token:
            logger.error("Phone number ID or access token is missing")
            return False, ""
        
        # Normalize media type
        media_type_str = str(media_type).split(".")[-1].lower() if hasattr(media_type, 'value') else str(media_type).lower()
        
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Build media object
        media_object = {"url": media_url}
        
        if filename and media_type_str in ["document", "file"]:
            media_object["filename"] = filename
        
        if caption and media_type_str in ["image", "video"]:
            media_object["caption"] = caption
        
        # Build payload
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": media_type_str,
            media_type_str: media_object
        }
        
        logger.debug(f"Sending {media_type_str} to {phone}: {media_url}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        logger.debug(f"WhatsApp media API response: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"✓ WhatsApp media sent to {phone} (ID: {message_id})")
            return True, message_id
        else:
            logger.error(f"WhatsApp media failed: {response.status_code} - {response.text}")
            return False, ""
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp media: {e}", exc_info=True)
        return False, ""

def send_template_message(
    phone_number_id: str,
    access_token: str,
    phone: str,
    template_name: str,
    template_language: str = "en_US",
    variables: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """Send WhatsApp template message"""
    try:
        if not phone_number_id or not access_token:
            logger.error("Phone number ID or access token is missing")
            return False, ""
        
        # Normalize phone
        phone_clean = phone.replace("+", "").replace(" ", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean
        
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        
        # Build template parameters
        body_parameters = []
        if variables:
            for var in variables:
                body_parameters.append({"type": "text", "text": var})
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_clean,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": template_language}
            }
        }
        
        if body_parameters:
            payload["template"]["components"] = [
                {"type": "body", "parameters": body_parameters}
            ]
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Sending template '{template_name}' to {phone_clean}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"✓ Template sent to {phone_clean} (ID: {message_id})")
            return True, message_id
        else:
            logger.error(f"Template send failed: {response.status_code} - {response.text}")
            return False, ""
    
    except Exception as e:
        logger.error(f"Error sending template: {e}")
        return False, ""

# ============ SENTIMENT ANALYSIS ============

async def analyze_sentiment(message: str) -> str:
    """Analyze sentiment using Gemini 2.5 Pro"""
    try:
        if not GEMINI_API_KEY:
            return "neutral"
        
        try:
            import google.generativeai as genai
        except ImportError:
            logger.warning("google.generativeai not installed")
            return "neutral"
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Simple prompt for faster response
        if not message or len(message.strip()) == 0:
            return "neutral"
        
        prompt = f"One word only - is this positive, negative, or neutral? Message: {message[:200]}"
        
        logger.debug(f"Analyzing sentiment for message: {message[:50]}...")
        response = model.generate_content(prompt)
        
        sentiment = response.text.strip().lower()
        logger.debug(f"Gemini response: {sentiment}")
        
        if "positive" in sentiment:
            return "positive"
        elif "negative" in sentiment:
            return "negative"
        else:
            return "neutral"
    
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}", exc_info=True)
        return "neutral"

async def get_conversation_sentiment(phone: str) -> Dict[str, Any]:
    """Get sentiment analysis for a conversation using Gemini 2.5 Pro"""
    try:
        # Normalize phone
        phone_clean = phone.replace("+", "").replace(" ", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean
        
        logger.debug(f"Getting sentiment for {phone_clean}")
        
        success, messages = await get_conversation(phone_clean, limit=20)
        
        if not success or not messages:
            logger.warning(f"No messages found for {phone_clean}")
            return {}
        
        logger.debug(f"Found {len(messages)} messages for sentiment analysis")
        
        sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        
        # Analyze sentiment for each message
        for msg in messages:
            message_text = msg.get("message", "")
            if message_text.strip():
                sentiment = await analyze_sentiment(message_text)
                sentiments[sentiment] += 1
                logger.debug(f"Message: '{message_text[:50]}...' → {sentiment}")
        
        total = sum(sentiments.values())
        overall = max(sentiments, key=sentiments.get) if total > 0 else "neutral"
        
        result = {
            "phone": phone_clean,
            "total_messages": total,
            "sentiment_breakdown": sentiments,
            "overall_sentiment": overall,
            "percentages": {
                "positive": round((sentiments["positive"] / total * 100), 2) if total > 0 else 0,
                "negative": round((sentiments["negative"] / total * 100), 2) if total > 0 else 0,
                "neutral": round((sentiments["neutral"] / total * 100), 2) if total > 0 else 0
            }
        }
        
        logger.info(f"✓ Sentiment analysis complete: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Error getting conversation sentiment: {e}", exc_info=True)
        return {}

async def get_message_stats(phone: Optional[str] = None) -> Dict[str, Any]:
    """Get message statistics from messages table"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase not configured")
            return {}
        
        headers = get_supabase_headers()
        
        # Normalize phone if provided
        if phone:
            phone_clean = phone.replace("+", "").replace(" ", "")
            if not phone_clean.startswith("91"):
                phone_clean = "91" + phone_clean
            url = f"{SUPABASE_URL}/rest/v1/messages?phone=eq.{phone_clean}&select=direction,status"
            logger.debug(f"Getting stats for phone: {phone_clean}")
        else:
            url = f"{SUPABASE_URL}/rest/v1/messages?select=direction,status"
            logger.debug("Getting stats for all messages")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to get messages: {response.status_code} - {response.text}")
            return {}
        
        messages = response.json()
        logger.debug(f"Retrieved {len(messages)} messages for stats")
        
        stats = {
            "total_messages": len(messages),
            "total_sent": sum(1 for m in messages if m.get("direction") == "outbound"),
            "total_received": sum(1 for m in messages if m.get("direction") == "inbound"),
            "delivered_count": sum(1 for m in messages if m.get("status") in ["delivered", "read", "seen"]),
            "failed_count": sum(1 for m in messages if m.get("status") == "failed")
        }
        
        if stats["total_sent"] > 0:
            stats["delivery_rate"] = round((stats["delivered_count"] / stats["total_sent"]) * 100, 2)
            stats["read_rate"] = round((sum(1 for m in messages if m.get("status") in ["read", "seen"]) / stats["total_sent"]) * 100, 2)
        else:
            stats["delivery_rate"] = 0
            stats["read_rate"] = 0
        
        logger.info(f"✓ Stats calculated: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Error getting message stats: {e}", exc_info=True)
        return {}

# ============ WEBHOOK HELPERS ============

def verify_webhook_token(token: str, expected_token: str) -> bool:
    """Verify webhook token"""
    return token == expected_token

# ============ TEMPLATE HELPERS ============

async def create_whatsapp_template(
    waba_id: str,
    access_token: str,
    template_name: str,
    category: str,
    components: List[Dict[str, Any]],
    language: str = "en_US"
) -> Tuple[bool, Dict[str, Any]]:
    """Create WhatsApp template directly on Meta servers using Graph API
    
    Creates a template that WhatsApp will review for approval.
    Status starts as 'PENDING_REVIEW' and updates to 'APPROVED' after review.
    """
    try:
        if not waba_id or not access_token:
            logger.error("WABA ID or Access Token missing")
            return False, {}
        
        # Build template payload for Meta API
        template_payload = {
            "name": template_name,
            "category": category,
            "language": language,
            "components": components
        }
        
        # Call Meta Graph API
        url = f"https://graph.facebook.com/v19.0/{waba_id}/message_templates"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Creating template on Meta: {template_name}")
        logger.info(f"Template payload: {template_payload}")
        logger.info(f"Meta API URL: {url}")
        
        # Try with longer timeout and retry once if timeout occurs
        max_retries = 2
        timeout_seconds = 30
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=template_payload, headers=headers, timeout=timeout_seconds)
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    template_id = result.get("id")
                    
                    logger.info(f"✓ Template created on Meta servers (ID: {template_id})")
                    return True, {
                        "template_id": template_id,
                        "name": template_name,
                        "status": "PENDING_REVIEW",
                        "message": "Template sent to WhatsApp for review. Status will update within 24 hours."
                    }
                else:
                    # Log full error response for debugging
                    error_response = response.json() if response.text else {}
                    error_msg = error_response.get("error", {}).get("message", "Unknown error")
                    error_code = error_response.get("error", {}).get("code")
                    error_type = error_response.get("error", {}).get("type")
                    error_subcode = error_response.get("error", {}).get("error_subcode")
                    
                    logger.error(f"Failed to create template on Meta: {response.status_code}")
                    logger.error(f"Error message: {error_msg}")
                    logger.error(f"Error code: {error_code}, type: {error_type}, subcode: {error_subcode}")
                    logger.error(f"Full error response: {error_response}")
                    
                    return False, {
                        "error": error_msg,
                        "error_code": error_code,
                        "error_type": error_type,
                        "details": error_response
                    }
            
            except requests.exceptions.Timeout as timeout_err:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}. Meta API took >{timeout_seconds}s")
                if attempt < max_retries - 1:
                    logger.info("Retrying...")
                    continue
                else:
                    logger.error(f"Meta API timeout after {max_retries} attempts")
                    return False, {
                        "error": f"Meta API timeout after {timeout_seconds}s. Please try again later.",
                        "details": "WhatsApp servers may be slow. Your template may still be created - check your Meta Business Manager."
                    }
            
            except requests.exceptions.RequestException as req_err:
                logger.error(f"Network error calling Meta API: {req_err}")
                return False, {
                    "error": f"Network error: {str(req_err)}",
                    "details": "Could not connect to Meta servers. Check your internet connection."
                }
    
    except Exception as e:
        logger.error(f"Error creating template on Meta: {e}", exc_info=True)
        return False, {"error": str(e)}

async def get_whatsapp_template_status(
    waba_id: str,
    access_token: str,
    template_id: str
) -> Tuple[bool, str]:
    """Get template approval status from Meta
    
    Returns approval status: PENDING_REVIEW, APPROVED, REJECTED, DISABLED
    """
    try:
        if not waba_id or not access_token or not template_id:
            return False, "UNKNOWN"
        
        url = f"https://graph.facebook.com/v19.0/{template_id}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "UNKNOWN")
            logger.info(f"Template {template_id} status: {status}")
            return True, status
        else:
            logger.warning(f"Could not fetch template status: {response.status_code}")
            return False, "UNKNOWN"
    
    except Exception as e:
        logger.error(f"Error getting template status: {e}")
        return False, "UNKNOWN"

# ============ ADMIN & AGENT MANAGEMENT ============

async def create_admin(admin_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Create a new admin"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase not configured")
            return False, None
        
        headers = get_supabase_headers(use_service_key=True)
        
        # Hash password (in production, use proper bcrypt)
        import hashlib
        password_hash = hashlib.sha256(admin_data.get("password", "").encode()).hexdigest()
        
        admin_record = {
            "email": admin_data.get("email"),
            "name": admin_data.get("name"),
            "phone": admin_data.get("phone"),
            "password_hash": password_hash,
            "role": admin_data.get("role", "admin"),
            "status": "active",
            "permissions": admin_data.get("permissions", {"all": True}),
            "created_at": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/admins",
            headers={**headers, "Prefer": "return=representation"},
            json=admin_record,
            timeout=10
        )
        
        if response.status_code == 201:
            admin = response.json()[0]
            logger.info(f"✅ Admin created: {admin.get('email')}")
            # Remove sensitive data
            admin.pop("password_hash", None)
            return True, admin
        else:
            logger.error(f"Failed to create admin: {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error creating admin: {e}")
        return False, None

async def create_agent(agent_data: Dict[str, Any], created_by: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Create a new agent"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase not configured")
            return False, None
        
        headers = get_supabase_headers(use_service_key=True)
        
        # Hash password (in production, use proper bcrypt)
        import hashlib
        password_hash = hashlib.sha256(agent_data.get("password", "").encode()).hexdigest()
        
        agent_record = {
            "email": agent_data.get("email"),
            "name": agent_data.get("name"),
            "phone": agent_data.get("phone"),
            "password_hash": password_hash,
            "role": agent_data.get("role", "agent"),
            "status": "active",
            "assigned_leads_limit": agent_data.get("assigned_leads_limit", 50),
            "is_available": True,
            "created_by": created_by,
            "created_at": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/agents",
            headers={**headers, "Prefer": "return=representation"},
            json=agent_record,
            timeout=10
        )
        
        if response.status_code == 201:
            agent = response.json()[0]
            logger.info(f"✅ Agent created: {agent.get('email')}")
            # Remove sensitive data
            agent.pop("password_hash", None)
            return True, agent
        else:
            logger.error(f"Failed to create agent: {response.text}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        return False, None

async def get_all_admins() -> Tuple[bool, List[Dict[str, Any]]]:
    """Get all admins"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase not configured")
            return False, []
        
        headers = get_supabase_headers(use_service_key=True)
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/admins?select=*&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            admins = response.json()
            # Remove sensitive data
            for admin in admins:
                admin.pop("password_hash", None)
            return True, admins
        else:
            logger.error(f"Failed to get admins: {response.text}")
            return False, []
            
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return False, []

async def get_all_agents() -> Tuple[bool, List[Dict[str, Any]]]:
    """Get all agents"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase not configured")
            return False, []
        
        headers = get_supabase_headers(use_service_key=True)
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/agents?select=*&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            agents = response.json()
            # Remove sensitive data
            for agent in agents:
                agent.pop("password_hash", None)
            return True, agents
        else:
            logger.error(f"Failed to get agents: {response.text}")
            return False, []
            
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        return False, []

async def send_message_from_agent(agent_id: str, lead_phone: str, message: str) -> Tuple[bool, Optional[str]]:
    """Send message from specific agent to lead"""
    try:
        # Get agent info
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase not configured")
            return False, None
            
        headers = get_supabase_headers(use_service_key=True)
        
        # Get agent details
        agent_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/agents?id=eq.{agent_id}&select=*",
            headers=headers,
            timeout=10
        )
        
        if agent_response.status_code != 200 or not agent_response.json():
            logger.error(f"Agent not found: {agent_id}")
            return False, None
            
        agent = agent_response.json()[0]
        
        # Send WhatsApp message
        success, msg_id = send_whatsapp_message(
            PHONE_NUMBER_ID,
            ACCESS_TOKEN,
            lead_phone,
            message
        )
        
        if success:
            # Store conversation
            success_conv, lead = await store_lead(lead_phone)
            if success_conv:
                await store_conversation(
                    lead.get("id"),
                    lead_phone,
                    message,
                    agent.get("name", "Agent"),
                    direction="outbound",
                    status="sent"
                )
                
                # Update agent activity
                requests.patch(
                    f"{SUPABASE_URL}/rest/v1/agents?id=eq.{agent_id}",
                    headers=headers,
                    json={"last_activity": datetime.now().isoformat()},
                    timeout=10
                )
            
            logger.info(f"✅ Agent {agent.get('name')} sent message to {lead_phone}")
            return True, msg_id
        else:
            logger.error(f"Failed to send message from agent {agent_id}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error sending message from agent: {e}")
        return False, None

async def get_agent_conversations(agent_id: str, limit: int = 50) -> Tuple[bool, Dict[str, Any]]:
    """Get agent conversation history and stats"""
    try:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.warning("Supabase not configured")
            return False, {}
        
        headers = get_supabase_headers(use_service_key=True)
        
        # Get agent info
        agent_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/agents?id=eq.{agent_id}&select=*",
            headers=headers,
            timeout=10
        )
        
        if agent_response.status_code != 200 or not agent_response.json():
            return False, {}
            
        agent = agent_response.json()[0]
        
        # Get leads assigned to agent
        leads_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?assigned_agent_id=eq.{agent_id}&select=*&order=last_contact_at.desc&limit={limit}",
            headers=headers,
            timeout=10
        )
        
        leads = leads_response.json() if leads_response.status_code == 200 else []
        
        # Get recent conversations
        conversations = []
        for lead in leads[:10]:  # Top 10 recent
            conv_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/conversations?phone=eq.{lead.get('phone')}&select=*&order=created_at.desc&limit=5",
                headers=headers,
                timeout=10
            )
            if conv_response.status_code == 200:
                conv_data = conv_response.json()
                if conv_data:
                    conversations.append({
                        "lead": lead,
                        "recent_messages": conv_data
                    })
        
        result = {
            "agent_id": agent_id,
            "agent_name": agent.get("name"),
            "total_conversations": agent.get("total_conversations", 0),
            "active_conversations": len([l for l in leads if l.get("status") not in ["won", "lost"]]),
            "recent_conversations": conversations,
            "performance_stats": {
                "leads_handled": agent.get("total_leads_handled", 0),
                "current_leads": agent.get("current_leads_count", 0),
                "leads_limit": agent.get("assigned_leads_limit", 50),
                "performance_rating": agent.get("performance_rating", 0.0),
                "is_available": agent.get("is_available", True),
                "last_activity": agent.get("last_activity")
            }
        }
        
        return True, result
        
    except Exception as e:
        logger.error(f"Error getting agent conversations: {e}")
        return False, {}
