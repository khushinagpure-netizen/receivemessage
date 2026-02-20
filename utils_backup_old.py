"""
Utility Functions and Helpers with enhanced features
"""

import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, GEMINI_API_KEY, SERVICE_STATUS

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
            logger.error("Supabase URL or Key is missing")
            return False, {}
        
        headers = get_supabase_headers()
        
        # Check if lead exists
        logger.debug(f"Checking if lead exists for phone: {phone}")
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{phone}&select=*",
            headers=headers,
            timeout=10
        )
        
        logger.debug(f"Check response: {check_response.status_code} - {check_response.text}")
        
        if check_response.status_code == 200 and check_response.json():
            logger.info(f"Lead already exists for {phone}")
            return True, check_response.json()[0]
        
        # Create new lead
        lead_data = {
            "phone": phone,
            "name": name or f"Lead {phone}",
            "status": "new",
            "created_at": datetime.now().isoformat()
        }
        
        logger.debug(f"Creating new lead: {lead_data}")
        
        create_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/leads",
            headers={**headers, "Prefer": "return=representation"},
            json=lead_data,
            timeout=10
        )
        
        logger.debug(f"Create response: {create_response.status_code} - {create_response.text}")
        
        if create_response.status_code == 201:
            logger.info(f"Lead created successfully for {phone}")
            return True, create_response.json()[0]
        else:
            logger.error(f"Failed to create lead: {create_response.status_code} - {create_response.text}")
            return False, {}
    except Exception as e:
        logger.error(f"Error storing lead: {e}", exc_info=True)
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
            logger.error("Supabase URL or Key is missing")
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
        
        logger.debug(f"Storing conversation for {phone}: {sender} ({direction})")
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/conversations",
            headers={**headers, "Prefer": "return=representation"},
            json=conversation_data,
            timeout=10
        )
        
        logger.debug(f"Store response: {response.status_code} - {response.text}")
        
        if response.status_code == 201:
            logger.info(f"Conversation stored for {phone}")
            return True, response.json()[0]
        else:
            logger.error(f"Failed to store conversation: {response.status_code} - {response.text}")
            return False, {}
    except Exception as e:
        logger.error(f"Error storing conversation: {e}", exc_info=True)
        return False, {}

async def update_message_status(
    conversation_id: str,
    status: str
) -> bool:
    """Update conversation message status"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("Supabase URL or Key is missing")
            return False
        
        headers = get_supabase_headers()
        
        update_data = {"status": status, "updated_at": datetime.now().isoformat()}
        logger.debug(f"Updating conversation {conversation_id} status to {status}")
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/conversations?id=eq.{conversation_id}",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        logger.debug(f"Update response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            logger.info(f"Message status updated: {conversation_id} -> {status}")
            return True
        else:
            logger.error(f"Failed to update message status: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating message status: {e}", exc_info=True)
        return False

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
        
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Build conversation context
        context = "You are a helpful customer support agent. Keep responses concise and professional."
        if conversation_history:
            context += "\nPrevious messages:\n" + "\n".join(conversation_history[-5:])
        
        prompt = f"{context}\n\nCustomer: {message}\nAgent:"
        
        logger.debug(f"Generating Gemini reply for phone {phone}")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=150,
                temperature=0.7
            )
        )
        
        ai_reply = response.text if response.text else "Thank you for your message."
        logger.info(f"Generated AI reply for {phone}: {ai_reply[:50]}...")
        return ai_reply
    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
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
        # Validate inputs
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
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        logger.debug(f"Sending WhatsApp message to {phone} via {url}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        logger.debug(f"WhatsApp API response: {response.status_code} - {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"WhatsApp message sent successfully to {phone} (ID: {message_id})")
            return True, message_id
        else:
            logger.error(f"WhatsApp send failed: Status {response.status_code} - {response.text}")
            return False, ""
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}", exc_info=True)
        return False, ""

def verify_webhook_token(token: str, verify_token: str) -> bool:
    """Verify webhook token from Meta"""
    return token == verify_token

# ============ MEDIA MESSAGE HELPERS ============

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
        
        # Convert enum to string if needed
        media_type_str = str(media_type).split(".")[-1].lower() if hasattr(media_type, 'value') else str(media_type).lower()
        
        url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Build media payload based on type
        media_object = {
            "url": media_url
        }
        
        # Add filename for documents/files
        if filename and media_type_str in ["document", "file"]:
            media_object["filename"] = filename
        
        # Add caption if provided (for image/video)
        if caption and media_type_str in ["image", "video"]:
            media_object["caption"] = caption
        
        # Build the complete payload
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": media_type_str,
            media_type_str: media_object
        }
        
        logger.debug(f"Sending {media_type_str} to {phone}: {media_url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        logger.debug(f"WhatsApp media API response: {response.status_code} - {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"WhatsApp media sent successfully to {phone} (ID: {message_id})")
            return True, message_id
        else:
            logger.error(f"WhatsApp media send failed: Status {response.status_code} - {response.text}")
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
    """Send WhatsApp template message using Cloud API"""
    try:
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
                "language": {
                    "code": template_language
                }
            }
        }
        
        # Add components if there are parameters
        if body_parameters:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": body_parameters
                }
            ]
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Sending WhatsApp template to {phone_clean}: {template_name}")
        logger.debug(f"Payload: {json.dumps(payload)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        logger.debug(f"WhatsApp template API response: {response.status_code} - {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"WhatsApp template '{template_name}' sent to {phone_clean} (ID: {message_id})")
            return True, message_id
        else:
            error_msg = response.text
            logger.error(f"WhatsApp template send failed: Status {response.status_code} - {error_msg}")
            return False, ""
    except Exception as e:
        logger.error(f"Error sending WhatsApp template: {e}", exc_info=True)
        return False, ""

def create_whatsapp_template(
    waba_id: str,
    access_token: str,
    template_name: str,
    category: str,
    components: List[Dict[str, Any]],
    language: str = "en_US"
) -> Tuple[bool, Dict[str, Any]]:
    """Create WhatsApp message template using Meta Graph API
    
    Args:
        waba_id: WhatsApp Business Account ID
        access_token: WhatsApp API Access Token
        template_name: Name for the template (no spaces, use underscore)
        category: Template category (MARKETING, TRANSACTIONAL)
        components: List of template components (body, header, footer, buttons)
        language: Language code (default: en_US)
    
    Returns:
        (success: bool, response: dict with template_id or error)
    
    Example:
        components = [
            {
                "type": "BODY",
                "text": "Hello {{1}}, your order {{2}} is {{3}}"
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {
                        "type": "QUICK_REPLY",
                        "text": "Yes"
                    },
                    {
                        "type": "QUICK_REPLY",
                        "text": "No"
                    }
                ]
            }
        ]
    """
    try:
        url = f"https://graph.facebook.com/v19.0/{waba_id}/message_templates"
        
        payload = {
            "name": template_name,
            "language": language,
            "category": category,
            "components": components
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Creating WhatsApp template: {template_name}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        logger.debug(f"Template creation API response: {response.status_code} - {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            template_id = data.get("id", "unknown")
            logger.info(f"✓ WhatsApp template created successfully: {template_name} (ID: {template_id})")
            return True, {
                "template_id": template_id,
                "name": template_name,
                "category": category,
                "language": language,
                "status": "PENDING_REVIEW"
            }
        else:
            error_msg = response.text
            logger.error(f"WhatsApp template creation failed: Status {response.status_code} - {error_msg}")
            return False, {
                "error": "Template creation failed",
                "status_code": response.status_code,
                "details": error_msg
            }
    except Exception as e:
        logger.error(f"Error creating WhatsApp template: {e}", exc_info=True)
        return False, {
            "error": str(e),
            "details": "Exception occurred during template creation"
        }

# ============ MESSAGE STATUS TRACKING ============

async def update_message_status_advanced(
    message_id: str,
    status: str,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    phone: Optional[str] = None
) -> bool:
    """Update message status in database with optional error tracking"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("Supabase not configured")
            return False
        
        headers = get_supabase_headers()
        
        update_data = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        # Add error tracking if provided
        if error_code:
            update_data["error_code"] = error_code
        if error_message:
            update_data["error_message"] = error_message
        
        # Try to update by message ID first
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/messages?message_id=eq.{message_id}",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Message {message_id} status updated to '{status}'")
            if error_code:
                logger.warning(f"Error code {error_code}: {error_message}")
            return True
        else:
            logger.warning(f"Could not update message {message_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating message status: {e}", exc_info=True)
        return False

# ============ SENTIMENT ANALYSIS ============

async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analyze sentiment of a message using Gemini"""
    try:
        if not SERVICE_STATUS.get("gemini", False) or not GEMINI_API_KEY:
            logger.debug("Gemini not available for sentiment analysis")
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "explanation": "Gemini not configured"
            }
        
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        prompt = f"""Analyze the sentiment of this message and respond in JSON format:
        Message: "{text}"
        
        Respond with:
        {{
            "sentiment": "positive" or "negative" or "neutral" or "mixed",
            "confidence": (0.0 to 1.0),
            "explanation": "brief explanation"
        }}"""
        
        response = model.generate_content(prompt)
        
        # Parse the response
        try:
            result = json.loads(response.text)
            logger.debug(f"Sentiment analysis: {result}")
            return result
        except json.JSONDecodeError:
            logger.warning(f"Could not parse Gemini response: {response.text}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "explanation": "Could not parse response"
            }
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}", exc_info=True)
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "explanation": f"Error: {str(e)}"
        }

async def get_conversation_sentiment(phone: str) -> Dict[str, Any]:
    """Analyze overall sentiment from conversation history"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("Supabase not configured")
            return {}
        
        headers = get_supabase_headers()
        
        # Get conversation messages
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conversations?phone=eq.{phone}&order=created_at.desc&limit=50",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return {}
        
        messages = response.json()
        
        if not messages:
            return {
                "sentiment": "neutral",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "most_recent_sentiment": "neutral",
                "trend": "stable",
                "summary": "No messages to analyze"
            }
        
        # Analyze sentiments
        sentiments = {
            "positive": 0,
            "negative": 0,
            "neutral": 0
        }
        
        sentiment_history = []
        
        for msg in messages:
            text = msg.get("message", "")
            if text:
                sentiment_result = await analyze_sentiment(text)
                sentiment = sentiment_result.get("sentiment", "neutral")
                sentiments[sentiment] += 1
                sentiment_history.append(sentiment)
        
        # Determine overall sentiment
        total = sum(sentiments.values())
        if total == 0:
            overall = "neutral"
        else:
            max_sentiment = max(sentiments, key=sentiments.get)
            overall = max_sentiment if sentiments[max_sentiment] / total > 0.4 else "mixed"
        
        # Determine trend
        if len(sentiment_history) > 2:
            recent = sentiment_history[:5]
            older = sentiment_history[-5:]
            recent_positive = recent.count("positive")
            older_positive = older.count("positive")
            
            if recent_positive > older_positive:
                trend = "improving"
            elif recent_positive < older_positive:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        logger.info(f"Sentiment for {phone}: {overall} (P:{sentiments['positive']}, N:{sentiments['negative']}, Neutral:{sentiments['neutral']})")
        
        return {
            "sentiment": overall,
            "positive_count": sentiments["positive"],
            "negative_count": sentiments["negative"],
            "neutral_count": sentiments["neutral"],
            "most_recent_sentiment": sentiment_history[0] if sentiment_history else "neutral",
            "trend": trend,
            "summary": f"{overall.capitalize()} sentiment with {trend} trend"
        }
    except Exception as e:
        logger.error(f"Error analyzing conversation sentiment: {e}", exc_info=True)
        return {}

# ============ ANALYTICS HELPERS ============

async def get_message_stats(phone: Optional[str] = None) -> Dict[str, Any]:
    """Get message statistics for a phone or all"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            # Fallback: Use in-memory recent messages
            logger.warning("Supabase not configured, using in-memory data")
            msgs = recent_messages if not phone else [m for m in recent_messages if m.get("phone") == phone]
            if not msgs:
                return {}
            
            sent = [m for m in msgs if m.get("direction") == "sent"]
            received = [m for m in msgs if m.get("direction") == "received"]
            delivered = [m for m in msgs if m.get("status") in ["delivered", "read", "seen"]]
            failed = [m for m in msgs if m.get("status") == "failed"]
            total = len(msgs)
            
            return {
                "total_messages": total,
                "total_sent": len(sent),
                "total_received": len(received),
                "delivery_rate": (len(delivered) / len(sent)) if sent else 0,
                "read_rate": (len([m for m in sent if m.get("status") in ["read", "seen"]]) / len(sent)) if sent else 0,
                "failed_count": len(failed)
            }
        
        headers = get_supabase_headers()
        
        # Try messages table first (primary source)
        query = f"{SUPABASE_URL}/rest/v1/messages?select=*"
        if phone:
            query += f"&phone=eq.{phone}"
        
        response = requests.get(query, headers=headers, timeout=10)
        
        messages = []
        if response.status_code == 200:
            messages = response.json()
            logger.debug(f"Found {len(messages)} messages in messages table")
        
        # If no messages in messages table, try conversations table
        if not messages:
            query = f"{SUPABASE_URL}/rest/v1/conversations?select=*"
            if phone:
                query += f"&phone=eq.{phone}"
            
            response = requests.get(query, headers=headers, timeout=10)
            
            if response.status_code == 200:
                messages = response.json()
                logger.debug(f"Found {len(messages)} messages in conversations table")
        
        if not messages:
            logger.warning(f"No messages found for phone: {phone}")
            return {}
        
        sent = [m for m in messages if m.get("direction") == "outbound"]
        received = [m for m in messages if m.get("direction") == "inbound"]
        delivered = [m for m in messages if m.get("status") in ["delivered", "read", "seen"]]
        failed = [m for m in messages if m.get("status") == "failed"]
        
        total = len(messages)
        
        return {
            "total_messages": total,
            "total_sent": len(sent),
            "total_received": len(received),
            "delivery_rate": round((len(delivered) / len(sent)) * 100, 2) if sent else 0,
            "read_rate": round((len([m for m in sent if m.get("status") in ["read", "seen"]]) / len(sent)) * 100, 2) if sent else 0,
            "failed_count": len(failed)
        }
    except Exception as e:
        logger.error(f"Error getting message stats: {e}", exc_info=True)
        return {}
