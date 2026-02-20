"""
Multi-Channel Communication API v4.0
WhatsApp Business API with Lead Management and Gemini 2.5 Pro AI Auto-Replies

Modular structure:
- config.py: Environment and configuration
- models.py: Pydantic request/response models
- utils.py: Helper functions and database operations
- main.py: FastAPI app and endpoints
"""

from fastapi import FastAPI, Request, HTTPException, Query, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import requests
import json
import uuid
import hmac
import hashlib
from typing import Optional, List, Dict, Any

# Import from modular files
from config import (
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY,
    ACCESS_TOKEN, PHONE_NUMBER_ID, WABA_ID, VERIFY_TOKEN,
    GEMINI_API_KEY, GEMINI_READY, PORT, HOST, APP_TITLE, APP_DESCRIPTION, APP_VERSION,
    SERVICE_STATUS
)
import models
import utils
from models import (
    MessageCreate, ReceiveMessage, TemplateCreate, TemplateSend,
    LeadCreate, LeadUpdate, ConversationResponse, RecentMessagesResponse, WebhookMessage,
    MediaMessageCreate, MessageResponse, ReceiveMessageResponse, MessageStatusUpdate,
    MessageStatusResponse, SentimentResponse, AnalyticsResponse, LeadResponse,
    LeadListResponse, TemplateResponse, TemplateListResponse, ApiResponse, ErrorResponse,
    MessageTypeEnum, MessageStatusEnum, SentimentEnum, TemplateModeEnum
)
from utils import (
    get_supabase_headers, log_api_call, add_to_recent_messages, get_recent_messages,
    store_lead, store_conversation, store_message, store_conversation_with_message, update_message_status,
    generate_ai_reply, send_whatsapp_message, verify_webhook_token,
    send_media_message, send_template_message, create_whatsapp_template, update_message_status_advanced, analyze_sentiment,
    get_conversation_sentiment, get_message_stats
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ RESPONSE HEADER MIDDLEWARE ============

@app.middleware("http")
async def add_response_headers(request: Request, call_next):
    """Add standard headers to all responses"""
    response = await call_next(request)
    
    # Add security and standard headers
    response.headers["X-API-Version"] = APP_VERSION
    response.headers["X-API-Name"] = "WhatsApp Business API v4.0"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Log request/response
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Client: {client_host}"
    )
    
    return response

# ============ HEALTH CHECK ENDPOINTS ============

@app.get("/")
async def root():
    """API Documentation - Public endpoint (no authentication required)"""
    return {
        "title": APP_TITLE + " ",
        "version": APP_VERSION,
        "status": "operational",
        "description": APP_DESCRIPTION,
        "features": [
            " WhatsApp Business API Integration",
            " Multi-Agent Team Collaboration",
            " Lead Management & CRM",
            " AI-Powered Auto-Replies (Gemini 2.5 Pro)",
            " Analytics & Performance Tracking",
            " Conversation Tracking with Message Status"
        ],
        "authentication": {
            "status": "disabled",
            "note": "JWT authentication temporarily disabled for development"
        },
        "documentation": {
            "interactive_docs": "/docs",
            "openapi_spec": "/openapi.json"
        }
    }

@app.get("/status")
async def api_status():
    """API Health Check with environment variable debugging"""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whatsapp": bool(ACCESS_TOKEN and PHONE_NUMBER_ID),
            "gemini": SERVICE_STATUS.get("gemini", False),
            "database": bool(SUPABASE_URL and SUPABASE_KEY)
        },
        "environment_debug": {
            "SUPABASE_URL": "SET" if SUPABASE_URL else "MISSING",
            "SUPABASE_ANON_KEY": "SET" if SUPABASE_KEY else "MISSING", 
            "SUPABASE_SERVICE_ROLE_KEY": "SET" if SUPABASE_SERVICE_KEY else "MISSING",
            "ACCESS_TOKEN": "SET" if ACCESS_TOKEN else "MISSING",
            "PHONE_NUMBER_ID": "SET" if PHONE_NUMBER_ID else "MISSING",
            "WABA_ID": "SET" if WABA_ID else "MISSING",
            "VERIFY_TOKEN": "SET" if VERIFY_TOKEN else "MISSING",
            "GEMINI_API_KEY": "SET" if GEMINI_API_KEY else "MISSING"
        }
    }

@app.get("/api/spec", response_class=JSONResponse)
async def get_openapi_spec():
    """Get OpenAPI specification as JSON"""
    return app.openapi()

@app.get("/swagger.json", response_class=JSONResponse)
async def get_swagger_spec():
    """Download Swagger/OpenAPI specification (JSON format)"""
    spec = app.openapi()
    if not spec:
        raise HTTPException(status_code=404, detail="OpenAPI spec not generated")
    return spec

@app.get("/swagger.yaml", response_class=FileResponse)
async def download_swagger_yaml():
    """Download Swagger specification as YAML file"""
    import yaml
    spec = app.openapi()
    if not spec:
        raise HTTPException(status_code=404, detail="OpenAPI spec not generated")
    
    # Create temporary YAML file
    yaml_content = yaml.dump(spec, default_flow_style=False, allow_unicode=True)
    temp_file = "/tmp/swagger.yaml"
    
    try:
        with open(temp_file, 'w') as f:
            f.write(yaml_content)
        return FileResponse(
            temp_file,
            media_type="application/x-yaml",
            filename="swagger.yaml"
        )
    except ImportError:
        return JSONResponse(
            {
                "message": "YAML file download requires PyYAML library",
                "alternative": "Use /swagger.json for JSON format",
                "install": "pip install pyyaml"
            },
            status_code=200
        )

# ============ WHATSAPP WEBHOOK ENDPOINTS ============

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Verify WhatsApp webhook with Meta"""
    try:
        logger.info(f" Webhook verification - Mode: {hub_mode}, Token: {hub_verify_token}")
        
        if hub_mode == "subscribe":
            if verify_webhook_token(hub_verify_token, VERIFY_TOKEN):
                logger.info(f" Webhook verified successfully! Challenge: {hub_challenge}")
                await utils.log_api_call("/webhook", "GET", None, 200)
                return PlainTextResponse(hub_challenge)
            else:
                logger.warning(f" Invalid verify token. Expected: {VERIFY_TOKEN}, Got: {hub_verify_token}")
                await utils.log_api_call("/webhook", "GET", None, 403, "Invalid verify token")
                return JSONResponse({"error": "Invalid verify token"}, status_code=403)
        
        logger.warning(f" Invalid mode: {hub_mode}")
        await utils.log_api_call("/webhook", "GET", None, 400, "Invalid mode")
        return JSONResponse({"error": "Invalid mode"}, status_code=400)
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        await utils.log_api_call("/webhook", "GET", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive WhatsApp messages from Meta and auto-generate AI replies"""
    try:
        # Get raw body first
        raw_body = await request.body()
        
        # Log incoming request
        logger.info(f" WEBHOOK RECEIVED - {request.client.host if request.client else 'unknown'}")
        
        # Handle empty body gracefully
        if not raw_body:
            logger.debug("Empty webhook body received (likely from Swagger test)")
            return JSONResponse({"status": "received"})
        
        # Try to parse JSON
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError as e:
            logger.error(f" Invalid JSON in webhook: {e}")
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
        # Log webhook structure
        logger.debug(f"Webhook object: {body.get('object')}")
        
        # Verify webhook signature
        x_hub_signature = request.headers.get("X-Hub-Signature-256", "")
        if x_hub_signature:
            is_valid = verify_webhook_signature(raw_body, x_hub_signature)
            if not is_valid:
                logger.warning("  Invalid webhook signature - but continuing anyway")
            else:
                logger.debug("✓ Webhook signature verified")
        else:
            logger.debug("No signature provided in webhook (verification skipped)")
        
        # Process messages
        entries_count = 0
        messages_count = 0
        status_updates_count = 0
        template_updates_count = 0
        
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                entries_count += 1
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    statuses = value.get("statuses", [])
                    
                    # Process incoming messages
                    for message in messages:
                        messages_count += 1
                        logger.info(f" Processing incoming message from {message.get('from')}")
                        await process_incoming_message(message)
                    
                    # Process message status updates
                    for status in statuses:
                        status_updates_count += 1
                        logger.info(f" Processing status update for message {status.get('id')}")
                        await process_message_status(status)
                    
                    # Process template status updates (when Meta approves/rejects templates)
                    # Meta sends template updates in `message_template_status_update` field
                    if "message_template_status_update" in value:
                        template_updates_count += 1
                        logger.info(f" Processing template status update")
                        await process_template_status_update(value["message_template_status_update"])
        else:
            logger.warning(f"  Unknown webhook object type: {body.get('object')}")
        
        # Log summary
        logger.info(f"✓ Webhook processed - Entries: {entries_count}, Messages: {messages_count}, Status Updates: {status_updates_count}, Template Updates: {template_updates_count}")
        
        await utils.log_api_call("/webhook", "POST", None, 200)
        return JSONResponse({"status": "received"})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        await utils.log_api_call("/webhook", "POST", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

async def process_incoming_message(message: Dict[str, Any]):
    """Process incoming WhatsApp message and send automatic reply
    
    When customer sends message:
    1. Store incoming message in messages table with status: received
    2. Automatically send default thank you reply
    3. Store reply in messages table with status: sent
    """
    try:
        phone = message.get("from")
        text = message.get("text", {}).get("body", "")
        message_id = message.get("id")
        timestamp = message.get("timestamp")
        
        if not phone or not text:
            logger.warning(f"  Invalid message: phone or text missing")
            return
        
        # Normalize phone
        phone_clean = phone.replace("+", "").replace(" ", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean
        
        logger.info(f" Incoming message from {phone_clean}: {text[:50]}")
        
        # Create/update lead (for conversation grouping)
        success, lead = await utils.store_lead(phone_clean, f"Customer {phone_clean}")
        if not success:
            logger.warning(f" Could not store lead for {phone_clean}")
        else:
            logger.debug(f"✓ Lead created/updated: {phone_clean}")
        
        # Store in BOTH messages and conversations tables using unified function
        db_success, msg_data = await store_conversation_with_message(
            phone=phone_clean,
            message=text,
            sender="Customer",
            direction="inbound",
            status="received",
            sender_type="customer",
            message_id=message_id
        )
        
        # Add to in-memory storage
        utils.add_to_recent_messages(text, phone_clean, phone_clean, "received")
        
        if db_success:
            logger.info(f"✓ Incoming message stored for {phone_clean}")
        else:
            logger.warning(f" Failed to store incoming message for {phone_clean}")
        
        # Send automatic default reply
        default_reply = "Thank you for contacting Katyayani Organics! We will get back to you shortly."
        
        logger.debug(f"Sending auto-reply to {phone_clean}...")
        success, reply_msg_id = utils.send_whatsapp_message(
            PHONE_NUMBER_ID, ACCESS_TOKEN, phone_clean, default_reply
        )
        
        if success:
            # If no msg_id from API, generate UUID
            if not reply_msg_id:
                reply_msg_id = str(uuid.uuid4())
            
            # Store reply using unified function
            reply_success, reply_data = await store_conversation_with_message(
                phone=phone_clean,
                message=default_reply,
                sender="Katyayani Organics",
                direction="outbound",
                status="sent",
                sender_type="agent",
                message_id=reply_msg_id
            )
            
            utils.add_to_recent_messages(default_reply, "Katyayani Organics", phone_clean, "sent")
            
            if reply_success:
                logger.info(f"✓ Auto-reply sent and stored for {phone_clean} (ID: {reply_msg_id})")
            else:
                logger.warning(f" Auto-reply sent but storage failed for {phone_clean}")
        else:
            logger.warning(f" Failed to send auto-reply to {phone_clean}")
        
        await utils.log_api_call("/webhook", "POST", phone_clean, 200)
        
    except Exception as e:
        logger.error(f" Error processing incoming message: {e}", exc_info=True)

async def process_message_status(status: Dict[str, Any]):
    """Process WhatsApp message status update from Meta webhook
    
    Status flow: sent → delivered → read/seen
    Also handles: failed status with error code
    """
    try:
        phone = status.get("recipient_id")
        message_id = status.get("id")
        msg_status = status.get("status")  # Values: sent, delivered, read, failed
        error_code = status.get("errors", [{}])[0].get("code") if status.get("errors") else None
        error_message = status.get("errors", [{}])[0].get("message") if status.get("errors") else None
        
        if not phone or not message_id or not msg_status:
            logger.warning(f"Invalid status update: missing required fields")
            return
        
        # Normalize phone
        phone_clean = phone.replace("+", "").replace(" ", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean
        
        # Map Meta status to our status values
        status_map = {
            "sent": "sent",
            "delivered": "delivered",
            "read": "seen",
            "failed": "failed"
        }
        
        db_status = status_map.get(msg_status, msg_status)
        
        logger.info(f"Message status update: {phone_clean} / {message_id} → {db_status}")
        
        # Update message status in database using message_id
        from utils import update_message_status
        success = await update_message_status(
            message_id=message_id,
            status=db_status,
            error_message=error_message
        )
        
        if success:
            logger.info(f"✓ Message {message_id} status updated to {db_status} in database")
        else:
            logger.warning(f"Could not update status for message {message_id} in database")
        
        await utils.log_api_call("/webhook/status", "POST", phone_clean, 200, f"Status: {db_status}")
        
    except Exception as e:
        logger.error(f"Error processing message status: {e}", exc_info=True)

async def process_template_status_update(template_status: Dict[str, Any]):
    """Process WhatsApp template status update from Meta webhook
    
    When Meta approves/rejects a template, they send webhook with:
    - message_template_id: Template ID
    - message_template_name: Template name
    - event: APPROVED, REJECTED, PAUSED, DISABLED, etc.
    - reason: Reason if rejected
    
    This automatically updates Supabase with the new status.
    """
    try:
        template_name = template_status.get("message_template_name")
        template_id = template_status.get("message_template_id")
        event = template_status.get("event")  # APPROVED, REJECTED, PAUSED, etc.
        reason = template_status.get("reason", "")
        
        if not template_name or not event:
            logger.warning(f"Invalid template status update: missing required fields")
            return
        
        logger.info(f"Template status update: {template_name} → {event}")
        
        # Map Meta events to our status values
        status_map = {
            "APPROVED": "APPROVED",
            "REJECTED": "REJECTED",
            "PENDING": "PENDING",
            "PENDING_DELETION": "PENDING_DELETION",
            "DELETED": "DELETED",
            "DISABLED": "DISABLED",
            "PAUSED": "PAUSED",
            "LIMIT_EXCEEDED": "REJECTED"
        }
        
        db_status = status_map.get(event, event)
        
        # Update template status in Supabase
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                headers = utils.get_supabase_headers()
                
                # Update by template_name
                update_data = {
                    "status": db_status,
                    "updated_at": datetime.now().isoformat()
                }
                
                if reason:
                    update_data["rejection_reason"] = reason
                
                response = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/templates?template_name=eq.{template_name}",
                    headers=headers,
                    json=update_data,
                    timeout=10
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"✓ Template {template_name} status updated to {db_status} in Supabase")
                else:
                    logger.warning(f"Could not update template status: {response.status_code} - {response.text[:200]}")
            
            except Exception as db_error:
                logger.error(f"Database update error for template {template_name}: {db_error}")
        
        await utils.log_api_call("/webhook/template-status", "POST", None, 200, f"Template: {template_name} → {db_status}")
    
    except Exception as e:
        logger.error(f"Error processing template status: {e}", exc_info=True)

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Meta webhook signature"""
    try:
        if not signature or not SUPABASE_KEY:
            return False
        
        # Expected format: sha256=<hash>
        if not signature.startswith("sha256="):
            return False
        
        expected_hash = signature.replace("sha256=", "")
        actual_hash = hmac.new(
            SUPABASE_KEY.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_hash, actual_hash)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False

# ============ MESSAGE ENDPOINTS ============

@app.post("/send-message")
async def send_message(request: MessageCreate):
    """Send WhatsApp message and store in database with live status tracking"""
    try:
        # Normalize phone number
        phone = request.phone.replace("+", "").replace(" ", "")
        if not phone.startswith("91"):
            phone = "91" + phone
        
        if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
            logger.error("WhatsApp not configured: ACCESS_TOKEN or PHONE_NUMBER_ID is missing")
            await utils.log_api_call("/send-message", "POST", phone, 503, "WhatsApp not configured")
            return JSONResponse(
                {"error": "WhatsApp not configured. Please set ACCESS_TOKEN and PHONE_NUMBER_ID in .env"},
                status_code=503
            )
        
        logger.info(f"Sending message to {phone}")
        success, msg_id = utils.send_whatsapp_message(
            PHONE_NUMBER_ID,
            ACCESS_TOKEN,
            phone,
            request.message
        )
        
        if success:
            # If no message_id from API, generate UUID
            if not msg_id:
                msg_id = str(uuid.uuid4())
            
            # Store in both memory and database using unified function
            utils.add_to_recent_messages(request.message, "Agent", phone, "sent")
            
            # Store message and conversation together
            db_success, db_data = await store_conversation_with_message(
                phone=phone,
                message=request.message,
                sender="Agent",
                direction="outbound",
                status="sent",
                sender_type="agent",
                message_id=msg_id
            )
            
            await utils.log_api_call("/send-message", "POST", phone, 200)
            
            if db_success:
                logger.info(f"✓ Message sent to {phone} (ID: {msg_id})")
            else:
                logger.warning(f"Message sent but storage failed for {phone} (ID: {msg_id})")
            
            return JSONResponse({
                "status": "success",
                "message_id": msg_id,
                "phone": phone,
                "message_status": "sent",
                "stored_in_supabase": db_success,
                "sent_at": datetime.now().isoformat(),
                "live_tracking": "You can check status via /message-status or /recent-messages endpoints"
            })
        else:
            error_msg = f"Failed to send WhatsApp message to {phone}. Possible causes: (1) Invalid ACCESS_TOKEN, (2) Invalid PHONE_NUMBER_ID, (3) Recipient not on WhatsApp"
            logger.error(error_msg)
            await utils.log_api_call("/send-message", "POST", phone, 500, error_msg)
            return JSONResponse(
                {"error": "Failed to send message", "details": error_msg},
                status_code=500
            )
    
    except Exception as e:
        logger.error(f"Send message error: {e}", exc_info=True)
        await utils.log_api_call("/send-message", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/send-media")
async def send_media(request: MediaMessageCreate) -> MessageResponse:
    """Send media (image/video/document/file/audio) via WhatsApp"""
    try:
        # Normalize phone number
        phone = request.phone.replace("+", "").replace(" ", "")
        if not phone.startswith("91"):
            phone = "91" + phone
        
        # Convert media_type enum to string
        media_type_str = str(request.media_type).lower()
        if "." in media_type_str:  # Handle enum format like "MessageTypeEnum.IMAGE"
            media_type_str = media_type_str.split(".")[-1].lower()
        
        if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
            logger.error("WhatsApp not configured")
            await utils.log_api_call("/send-media", "POST", phone, 503, "WhatsApp not configured")
            return JSONResponse(
                {"error": "WhatsApp not configured"},
                status_code=503
            )
        
        logger.info(f"Sending {media_type_str} to {phone}")
        logger.debug(f"Media URL: {request.media_url}")
        
        success, msg_id = send_media_message(
            PHONE_NUMBER_ID,
            ACCESS_TOKEN,
            phone,
            request.media_url,
            media_type_str,
            request.caption,
            request.filename
        )
        
        if success:
            media_caption = f"{media_type_str.upper()}: {request.caption or request.media_url}"
            utils.add_to_recent_messages(media_caption, "Agent", phone, "sent")
            
            # If no message_id from API, generate UUID
            if not msg_id:
                msg_id = str(uuid.uuid4())
            
            # Store message and conversation together
            db_success, db_data = await store_conversation_with_message(
                phone=phone,
                message=media_caption,
                sender="Agent",
                direction="outbound",
                status="sent",
                sender_type="agent",
                message_id=msg_id,
                media_url=request.media_url,
                media_type=media_type_str,
                caption=request.caption
            )
            
            await utils.log_api_call("/send-media", "POST", phone, 200)
            
            if db_success:
                logger.info(f"✓ Media sent to {phone} (Type: {media_type_str}, ID: {msg_id})")
            else:
                logger.warning(f"Media sent but storage failed for {phone}")
            
            return JSONResponse({
                "status": "success",
                "message_id": msg_id,
                "phone": phone,
                "message_type": media_type_str,
                "media_url": request.media_url,
                "stored_in_supabase": db_success,
                "sent_at": datetime.now().isoformat()
            })
        else:
            error_msg = f"Failed to send {media_type_str} to {phone}. Possible causes: (1) Invalid ACCESS_TOKEN, (2) Media URL not accessible, (3) Recipient not on WhatsApp"
            logger.error(error_msg)
            await utils.log_api_call("/send-media", "POST", phone, 500, error_msg)
            return JSONResponse(
                {"error": "Failed to send media", "details": error_msg},
                status_code=500
            )
    except Exception as e:
        logger.error(f"Send media error: {e}", exc_info=True)
        await utils.log_api_call("/send-media", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/send-template")
async def send_template(request: TemplateSend) -> MessageResponse:
    """Send WhatsApp template message from Agent Dashboard with automatic message_id generation
    
    If Meta API doesn't return message_id, we generate UUID and store in database
    This ensures all templates have trackable IDs for status updates
    """
    try:
        # Normalize phone number
        phone = request.phone.replace("+", "").replace(" ", "")
        if not phone.startswith("91"):
            phone = "91" + phone
        
        if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
            logger.error("WhatsApp not configured")
            await utils.log_api_call("/send-template", "POST", phone, 503, "WhatsApp not configured")
            return JSONResponse(
                {"error": "WhatsApp not configured"},
                status_code=503
            )
        
        logger.info(f"Sending template '{request.template_id}' to {phone}")
        
        # Convert variables dict to list of values
        variables_list = list(request.variables.values()) if request.variables else []
        
        success, msg_id = send_template_message(
            PHONE_NUMBER_ID,
            ACCESS_TOKEN,
            phone,
            request.template_id,
            "en_US",
            variables_list
        )
        
        if success:
            # If no message_id from API, generate UUID for tracking
            if not msg_id:
                msg_id = str(uuid.uuid4())
                logger.debug(f"Generated UUID for template message: {msg_id}")
            
            template_info = f"TEMPLATE: {request.template_id} with vars: {request.variables or {}}"
            utils.add_to_recent_messages(template_info, "Agent", phone, "sent")
            
            # Store message and conversation together
            db_success, db_data = await store_conversation_with_message(
                phone=phone,
                message=template_info,
                sender="Agent",
                direction="outbound",
                status="sent",
                sender_type="agent",
                message_id=msg_id
            )
            
            await utils.log_api_call("/send-template", "POST", phone, 200)
            
            if db_success:
                logger.info(f"✓ Template sent to {phone} (Template: {request.template_id}, ID: {msg_id})")
            else:
                logger.warning(f"Template sent but storage failed for {phone}")
            
            return JSONResponse({
                "status": "success",
                "message_id": msg_id,
                "phone": phone,
                "message_type": "template",
                "template_id": request.template_id,
                "variables_used": request.variables or {},
                "message_stored": db_success,
                "sent_at": datetime.now().isoformat(),
                "live_tracking": "You can check status via /message-status or /recent-messages endpoints"
            })
        else:
            error_msg = f"Failed to send template '{request.template_id}' to {phone}. Possible causes: (1) Template not found, (2) Invalid variables, (3) Invalid phone number, (4) WhatsApp API error"
            logger.error(error_msg)
            await utils.log_api_call("/send-template", "POST", phone, 500, error_msg)
            return JSONResponse(
                {"error": "Failed to send template", "details": error_msg},
                status_code=500
            )
    except Exception as e:
        logger.error(f"Send template error: {e}", exc_info=True)
        await utils.log_api_call("/send-template", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/message-status")
async def update_message_status_endpoint(request: MessageStatusUpdate) -> MessageStatusResponse:
    """Update message delivery status"""
    try:
        logger.info(f"Updating message {request.message_id} status to '{request.status}'")
        
        success = await update_message_status_advanced(
            request.message_id,
            request.status,
            request.error_code,
            request.error_message
        )
        
        if success:
            await utils.log_api_call("/message-status", "POST", None, 200)
            logger.info(f"✓ Message {request.message_id} status updated to '{request.status}'")
            return JSONResponse({
                "status": "success",
                "message_id": request.message_id,
                "current_status": request.status,
                "updated_at": datetime.now().isoformat()
            })
        else:
            error_msg = f"Message {request.message_id} not found. Ensure database migration was run."
            logger.error(error_msg)
            await utils.log_api_call("/message-status", "POST", None, 404, error_msg)
            return JSONResponse(
                {"error": "Message not found", "details": error_msg},
                status_code=404
            )
    except Exception as e:
        logger.error(f"Update status error: {e}", exc_info=True)
        await utils.log_api_call("/message-status", "POST", None, 500, str(e))
        return JSONResponse({"error": f"Status update failed: {str(e)}", "error_type": type(e).__name__}, status_code=500)

@app.get("/message-status")
async def get_message_status(message_id: str):
    """Get live message status by message ID
    
    Returns current status: sent, delivered, seen, read, failed
    Status updates automatically as Meta webhook sends updates
    """
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            await utils.log_api_call("/message-status", "GET", message_id, 503, "Database not configured")
            return JSONResponse(
                {"error": "Database not configured"},
                status_code=503
            )
        
        headers = utils.get_supabase_headers()
        
        # Query messages table by message_id
        url = f"{SUPABASE_URL}/rest/v1/messages?message_id=eq.{message_id}&select=id,message_id,phone,message,direction,status,created_at,updated_at"
        
        logger.debug(f"Fetching status for message: {message_id}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            messages = response.json()
            
            if not messages or not isinstance(messages, list) or len(messages) == 0:
                logger.warning(f"Message not found: {message_id}")
                await utils.log_api_call("/message-status", "GET", message_id, 404, "Message not found")
                return JSONResponse({
                    "status": "error",
                    "message_id": message_id,
                    "error": "Message not found in database",
                    "code": "NOT_FOUND"
                }, status_code=404)
            
            msg = messages[0]
            current_status = msg.get("status", "unknown")
            
            logger.info(f"✓ Retrieved status for {message_id}: {current_status}")
            await utils.log_api_call("/message-status", "GET", message_id, 200)
            
            return JSONResponse({
                "status": "success",
                "message_id": message_id,
                "current_status": current_status,
                "phone": msg.get("phone"),
                "direction": msg.get("direction"),
                "message": msg.get("message", "").strip()[:100],  # First 100 chars
                "created_at": msg.get("created_at"),
                "updated_at": msg.get("updated_at"),
                "live_tracking": "Status updates automatically from Meta webhook"
            })
        
        elif response.status_code == 401:
            logger.error("Supabase authentication failed")
            return JSONResponse({
                "status": "error",
                "error": "Database authentication failed",
                "code": "AUTH_FAILED"
            }, status_code=401)
        
        else:
            logger.error(f"Failed to get message status: {response.status_code}")
            await utils.log_api_call("/message-status", "GET", message_id, response.status_code, response.text[:100])
            return JSONResponse({
                "status": "error",
                "error": f"Failed to retrieve message status (HTTP {response.status_code})",
                "code": "QUERY_FAILED"
            }, status_code=response.status_code)
    
    except requests.exceptions.Timeout:
        logger.error("Status query timed out")
        return JSONResponse({
            "status": "error",
            "error": "Database query timed out",
            "code": "TIMEOUT"
        }, status_code=504)
    
    except Exception as e:
        logger.error(f"Get status error: {e}", exc_info=True)
        await utils.log_api_call("/message-status", "GET", message_id, 500, str(e)[:100])
        return JSONResponse({
            "status": "error",
            "error": f"Failed to get status: {str(e)[:100]}",
            "code": "INTERNAL_ERROR"
        }, status_code=500)

@app.get("/sentiment")
async def get_sentiment(phone: str):
    """Get sentiment analysis for a phone number"""
    try:
        sentiment_data = await utils.get_conversation_sentiment(phone)
        
        if sentiment_data:
            await utils.log_api_call("/sentiment", "GET", phone, 200)
            return JSONResponse({
                "status": "success",
                "analysis": sentiment_data,
                "timestamp": datetime.now().isoformat()
            })
        else:
            await utils.log_api_call("/sentiment", "GET", phone, 404, "No messages found")
            return JSONResponse(
                {"error": "No messages found for sentiment analysis"},
                status_code=404
            )
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}", exc_info=True)
        await utils.log_api_call("/sentiment", "GET", phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/analytics")
async def get_analytics(phone: Optional[str] = None):
    """Get message analytics"""
    try:
        stats = await utils.get_message_stats(phone)
        
        # Always return stats, even if empty (shows 0 values with no data)
        analytics = stats if stats else {
            "total_messages": 0,
            "total_sent": 0,
            "total_received": 0,
            "delivery_rate": 0,
            "read_rate": 0,
            "failed_count": 0
        }
        
        await utils.log_api_call("/analytics", "GET", phone, 200)
        return JSONResponse({
            "status": "success",
            "phone": phone or "all",
            "stats": analytics,
            "period": "all_time",
            "timestamp": datetime.now().isoformat(),
            "note": "Ensure messages are sent via /send-message or received via /receive-simple for stats to populate"
        })
    except Exception as e:
        logger.error(f"Analytics error: {e}", exc_info=True)
        await utils.log_api_call("/analytics", "GET", phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ CONVERSATION ENDPOINTS ============

@app.get("/get-conversation")
async def get_conversation_endpoint(phone: str):
    """Get conversation history for a specific phone number"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            await utils.log_api_call("/get-conversation", "GET", phone, 503, "Database not configured")
            return JSONResponse(
                {"status": "error", "messages": [], "error": "Database not configured"},
                status_code=503
            )
        
        # Normalize phone
        phone_clean = phone.replace("+", "").replace(" ", "")
        if not phone_clean.startswith("91"):
            phone_clean = "91" + phone_clean
        
        logger.debug(f"Fetching conversation for {phone_clean}")
        
        headers = utils.get_supabase_headers()
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conversations?phone=eq.{phone_clean}&order=created_at.asc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            messages = response.json()
            logger.info(f"✓ Retrieved {len(messages)} messages for {phone_clean}")
            await utils.log_api_call("/get-conversation", "GET", phone_clean, 200)
            
            return JSONResponse({
                "status": "success",
                "phone": phone_clean,
                "messages": messages,
                "total": len(messages),
                "message_types": {
                    "sent": len([m for m in messages if m.get("direction") == "outbound"]),
                    "received": len([m for m in messages if m.get("direction") == "inbound"])
                }
            })
        else:
            logger.error(f"Failed to get conversations: {response.status_code} - {response.text}")
            await utils.log_api_call("/get-conversation", "GET", phone_clean, response.status_code, response.text)
            return JSONResponse(
                {"status": "error", "messages": [], "total": 0, "phone": phone_clean, "error": response.text},
                status_code=response.status_code
            )
    
    except Exception as e:
        logger.error(f"Get conversation error: {e}", exc_info=True)
        await utils.log_api_call("/get-conversation", "GET", phone, 500, str(e))
        return JSONResponse(
            {"status": "error", "messages": [], "error": str(e)},
            status_code=500
        )

@app.get("/recent-messages")
async def recent_messages(
    phone: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Get recent sent/received messages with live status from Supabase
    
    Parameters:
    - phone: Optional phone number to filter by (e.g., 9876543210 or 919876543210)
    - limit: Number of recent messages to return (1-100, default 20)
    
    Returns all recent messages if phone not provided
    Returns messages for specific phone number if phone is provided
    Live message status options: sent, delivered, seen, read, failed
    """
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            # Fallback to in-memory if database not configured
            logger.warning("Supabase not configured, using in-memory storage")
            messages = get_recent_messages(phone, limit)
            sent = [m for m in messages if m.get("direction") == "sent"]
            received = [m for m in messages if m.get("direction") == "received"]
            
            await utils.log_api_call("/recent-messages", "GET", phone, 200)
            
            return JSONResponse({
                "status": "success",
                "phone": phone or "all",
                "source": "in-memory",
                "messages": messages,
                "total": len(messages),
                "sent": len(sent),
                "received": len(received)
            })
        
        headers = get_supabase_headers()
        phone_clean = "all"
        
        # Build query - normalize phone if provided
        if phone:
            phone_clean = phone.replace("+", "").replace(" ", "")
            if not phone_clean.startswith("91"):
                phone_clean = "91" + phone_clean
            # Query with phone filter
            url = f"{SUPABASE_URL}/rest/v1/messages?phone=eq.{phone_clean}&select=*&order=created_at.desc&limit={limit}"
            logger.info(f"Querying Supabase for messages from phone: {phone_clean}")
        else:
            # Query all messages
            url = f"{SUPABASE_URL}/rest/v1/messages?select=*&order=created_at.desc&limit={limit}"
            logger.info(f"Querying Supabase for all recent messages (limit: {limit})")
        
        logger.debug(f"Supabase REST endpoint: {url[:100]}...")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            messages = response.json()
            if not isinstance(messages, list):
                messages = []
            
            logger.info(f"✓ Retrieved {len(messages)} recent messages for {phone_clean}")
            
            # Count by direction
            sent = [m for m in messages if m.get("direction") == "outbound"]
            received = [m for m in messages if m.get("direction") == "inbound"]
            
            # Count by status (for live tracking)
            status_breakdown = {}
            for msg in messages:
                status = msg.get("status", "unknown")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            await utils.log_api_call("/recent-messages", "GET", phone_clean, 200)
            
            return JSONResponse({
                "status": "success",
                "phone": phone_clean,
                "source": "supabase",
                "messages": messages,
                "total": len(messages),
                "sent": len(sent),
                "received": len(received),
                "status_breakdown": status_breakdown,
                "live_status": "Check individual messages for live status: sent, delivered, seen, read, failed",
                "last_update": datetime.now().isoformat()
            })
        elif response.status_code == 401:
            logger.error("Supabase authentication failed - Invalid API key")
            await utils.log_api_call("/recent-messages", "GET", phone_clean, 401, "Invalid Supabase key")
            return JSONResponse({
                "status": "error",
                "messages": [],
                "total": 0,
                "error": "Supabase authentication failed - Check your SUPABASE_KEY",
                "code": "AUTH_FAILED"
            }, status_code=401)
        elif response.status_code == 404:
            logger.info(f"No messages found for {phone_clean}")
            await utils.log_api_call("/recent-messages", "GET", phone_clean, 200)
            return JSONResponse({
                "status": "success",
                "phone": phone_clean,
                "source": "supabase",
                "messages": [],
                "total": 0,
                "sent": 0,
                "received": 0,
                "status_breakdown": {},
                "message": f"No messages found for phone number {phone_clean}" if phone else "No messages in database yet"
            })
        else:
            logger.error(f"Supabase query failed: {response.status_code} - {response.text[:200]}")
            await utils.log_api_call("/recent-messages", "GET", phone_clean, response.status_code, response.text[:100])
            
            return JSONResponse({
                "status": "error",
                "messages": [],
                "total": 0,
                "error": f"Failed to retrieve messages from Supabase: HTTP {response.status_code}",
                "details": response.text[:300] if response.text else "Unknown error"
            }, status_code=response.status_code)
    
    except requests.exceptions.Timeout:
        logger.error(f"Recent messages query timed out")
        await utils.log_api_call("/recent-messages", "GET", phone, 504, "Query timeout")
        return JSONResponse({
            "status": "error",
            "messages": [],
            "error": "Query timed out - Supabase is taking too long to respond",
            "code": "TIMEOUT"
        }, status_code=504)
    
    except Exception as e:
        logger.error(f"Recent messages error: {e}", exc_info=True)
        await utils.log_api_call("/recent-messages", "GET", phone, 500, str(e)[:100])
        return JSONResponse({
            "status": "error",
            "messages": [],
            "error": f"Failed to retrieve messages: {str(e)[:100]}",
            "code": "INTERNAL_ERROR"
        }, status_code=500)

@app.get("/received-messages")
async def received_messages(
    phone: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """Get received messages from webhook with timestamp and sender info
    
    Shows only messages received FROM customers TO your WhatsApp Business Account.
    Stored when webhook processes incoming messages.
    """
    try:
        # Get from Supabase conversations table
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({
                "status": "success",
                "messages": [],
                "total": 0,
                "note": "Database not configured - showing in-memory messages"
            })
        
        headers = get_supabase_headers()
        
        # Build query - get inbound messages only
        query = f"{SUPABASE_URL}/rest/v1/conversations?direction=eq.inbound&select=*"
        
        if phone:
            query += f"&phone=eq.{phone}"
        
        query += "&order=created_at.desc"
        
        response = requests.get(
            query,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            messages = response.json()
            
            # Limit results
            messages = messages[:limit]
            
            # Format for display
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.get("id"),
                    "phone": msg.get("phone"),
                    "sender": msg.get("sender"),
                    "message": msg.get("message"),
                    "timestamp": msg.get("created_at"),
                    "status": msg.get("status"),
                    "lead_id": msg.get("lead_id")
                })
            
            await utils.log_api_call("/received-messages", "GET", phone, 200)
            
            return JSONResponse({
                "status": "success",
                "message": "Received messages from customer",
                "phone_filter": phone or "all",
                "messages": formatted_messages,
                "total_received": len(formatted_messages),
                "limit_applied": limit,
                "last_update": datetime.now().isoformat()
            })
        else:
            logger.warning(f"Failed to fetch received messages: {response.status_code} - {response.text}")
            return JSONResponse({
                "status": "success",
                "messages": [],
                "total": 0,
                "note": "Could not fetch from database"
            })
    
    except Exception as e:
        logger.error(f"Received messages error: {e}", exc_info=True)
        await utils.log_api_call("/received-messages", "GET", phone, 500, str(e))
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "messages": []
        }, status_code=500)

# ============ TEMPLATE ENDPOINTS ============

@app.post("/template/create")
async def template_create(request: TemplateCreate):
    """Create WhatsApp message template using Gemini (backward compatible endpoint)
    
    This is an alias for /create-template for backward compatibility.
    Uses Gemini to generate template content from a prompt, then submits to Meta.
    """
    try:
        if not WABA_ID or not ACCESS_TOKEN:
            logger.error("WhatsApp not fully configured")
            await utils.log_api_call("/template/create", "POST", None, 503, "WhatsApp not configured")
            return JSONResponse(
                {"error": "WhatsApp not configured", "required": ["WABA_ID", "ACCESS_TOKEN"]},
                status_code=503
            )
        
        # Validate and clean template name
        template_name = request.name.replace(" ", "_").lower()
        if not all(c.isalnum() or c == "_" for c in template_name):
            return JSONResponse(
                {"error": "Invalid template name. Use only alphanumeric characters and underscores"},
                status_code=400
            )
        
        # Step 1: Get template content based on template mode
        generated_content = None
        
        if request.mode == TemplateModeEnum.MANUAL:
            # Manual mode: use provided content directly
            generated_content = request.content
            logger.info(f"Using manual template content: {len(generated_content)} chars")
        
        elif request.mode == TemplateModeEnum.AI:
            # AI mode: Use Gemini to generate template content from prompt
            if SERVICE_STATUS.get("gemini", False) and GEMINI_API_KEY:
                try:
                    logger.info(f"Generating template with Gemini from prompt: {request.prompt[:100]}...")
                    import google.generativeai as genai
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel("gemini-2.5-pro")
                    
                    gemini_prompt = f"""Create a professional WhatsApp Business message template.

Rules:
- Under 500 characters
- No spammy words
- No exaggerated claims
- No excessive emojis (max 2-3)
- Professional & engaging tone
- If personalization needed, use {{{{1}}}} format
- Clear and actionable

User Idea:
{request.prompt}

Return ONLY the final template message text, nothing else."""
                    
                    response = model.generate_content(gemini_prompt)
                    if response.text:
                        generated_content = response.text.strip()
                        logger.info(f"✓ Template generated by Gemini: {len(generated_content)} chars")
                    else:
                        logger.warning("Gemini returned empty response")
                
                except Exception as e:
                    logger.error(f"Gemini generation failed: {e}")
            else:
                logger.warning("Gemini not available, cannot generate template")
        
        if not generated_content:
            error_msg = "Could not generate template content."
            if request.mode == TemplateModeEnum.AI:
                error_msg = "Could not generate template. Gemini service may not be available."
            return JSONResponse({
                "status": "error",
                "error": error_msg,
                "troubleshooting": [
                    "1. Verify GEMINI_API_KEY is set in .env (for AI mode)",
                    "2. Check Google Generative AI API is enabled (for AI mode)",
                    "3. Ensure prompt/content is clear and descriptive"
                ]
            }, status_code=400)
        
        # Step 2: Build template component with generated content (Meta API format)
        # According to Meta docs, component type must be lowercase "body" not "BODY"
        component = {
            "type": "body",
            "text": generated_content
        }
        
        # Check if text has variables ({{1}}, {{2}}, etc.) and add examples if needed
        # Meta requires examples for any text with variables
        import re
        variable_pattern = r'\{\{(\d+)\}\}'
        variables = re.findall(variable_pattern, generated_content)
        
        if variables:
            # Has positional parameters - need to provide examples
            # Create example values for each variable
            example_values = [f"example_value_{i}" for i in range(1, len(variables) + 1)]
            component["example"] = {
                "body_text": [example_values]
            }
            logger.info(f"Template has {len(variables)} variables, added examples")
        
        components = [component]
        
        logger.info(f"Submitting template to Meta: {template_name}")
        
        # Validate category - must be UTILITY, MARKETING, or AUTHENTICATION
        category_str = str(request.category.value) if hasattr(request.category, 'value') else str(request.category)
        valid_categories = ["UTILITY", "MARKETING", "AUTHENTICATION"]
        if category_str not in valid_categories:
            logger.error(f"Invalid category: {category_str}. Valid: {valid_categories}")
            await utils.log_api_call("/template/create", "POST", None, 400, f"Invalid category: {category_str}")
            return JSONResponse({
                "status": "error",
                "error": f"Invalid category. Must be: UTILITY, MARKETING, or AUTHENTICATION. Got: {category_str}"
            }, status_code=400)
        
        # Step 3: Submit to Meta Graph API
        success, result = await create_whatsapp_template(
            WABA_ID,
            ACCESS_TOKEN,
            template_name,
            category_str,
            components,
            "en_US"
        )
        
        if success:
            template_id = result.get("template_id")
            
            # Step 4: Store in Supabase for tracking (correct column names)
            if SUPABASE_URL and SUPABASE_KEY:
                try:
                    headers = get_supabase_headers()
                    template_data = {
                        "template_name": template_name,
                        "body": generated_content,
                        "footer": request.title or "",
                        "category": category_str,
                        "language": "en_US",
                        "header_type": None,
                        "header_text": None,
                        "status": "PENDING_REVIEW"
                    }
                    
                    store_response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/templates",
                        headers={**headers, "Prefer": "return=representation"},
                        json=template_data,
                        timeout=10
                    )
                    
                    if store_response.status_code in [200, 201]:
                        logger.info(f"✓ Template {template_name} stored in Supabase with ID {template_id}")
                    else:
                        logger.warning(f"Could not store in Supabase: {store_response.status_code} - {store_response.text[:200]}")
                
                except Exception as e:
                    logger.warning(f"Could not store in Supabase: {e}")
            
            await utils.log_api_call("/template/create", "POST", None, 201)
            
            return JSONResponse({
                "status": "success",
                "message": "Template created and sent to WhatsApp for review",
                "template_name": template_name,
                "template_id": template_id,
                "mode": "manual" if request.mode == TemplateModeEnum.MANUAL else "ai",
                "user_input": request.prompt if request.mode == TemplateModeEnum.AI else request.content,
                "template_content": generated_content,
                "category": category_str,
                "approval_status": "PENDING_REVIEW",
                "next_step": "WhatsApp will review this template within 24 hours. Check status using GET /templates/status",
                "created_at": datetime.now().isoformat()
            }, status_code=201)
        else:
            error_details = result.get("details", result.get("error", "Unknown error"))
            
            # Check for specific error: Template already exists (error_subcode 2388024)
            error_subcode = None
            if isinstance(error_details, dict) and 'error' in error_details:
                error_subcode = error_details['error'].get('error_subcode')
            
            if error_subcode == 2388024:
                # Template name already exists
                await utils.log_api_call("/template/create", "POST", None, 409, error_details)
                return JSONResponse({
                    "status": "error",
                    "error": "Template name already exists",
                    "error_code": "TEMPLATE_ALREADY_EXISTS",
                    "message": f"A template with the name '{template_name}' already exists in your WhatsApp Business Account.",
                    "details": error_details.get('error', {}).get('error_user_msg', ''),
                    "solutions": [
                        "1. Use a different template name (e.g., 'greeting_template_v2')",
                        "2. Delete the existing template from Meta Business Manager first",
                        "3. Check existing templates at: https://business.facebook.com",
                        "4. Or modify the existing template instead of creating a new one"
                    ]
                }, status_code=409)  # 409 Conflict
            else:
                # Other errors
                await utils.log_api_call("/template/create", "POST", None, 500, error_details)
                return JSONResponse({
                    "status": "error",
                    "error": "Failed to create template on WhatsApp",
                    "details": error_details,
                    "troubleshooting": [
                        "1. Verify WABA_ID and ACCESS_TOKEN are valid",
                        "2. Ensure template name follows Meta guidelines (no spaces, max 512 chars)",
                        "3. Template content must be at least 3 characters",
                        "4. Check Meta API documentation for category requirements"
                    ]
                }, status_code=500)
    
    except Exception as e:
        logger.error(f"Template create error: {e}", exc_info=True)
        await utils.log_api_call("/template/create", "POST", None, 500, str(e))
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@app.post("/create-template")
async def create_template_on_meta(request: TemplateCreate):
    """Create WhatsApp message template using Gemini-generated content from a prompt
    
    Flow (based on template_creator.py):
    1. User provides a prompt (template idea)
    2. Gemini generates professional WhatsApp template content from the prompt
    3. Backend submits template to Meta Graph API
    4. WhatsApp reviews template and returns template_id
    5. Template stored in Supabase for tracking
    6. Template awaits WhatsApp approval (usually within 24 hours)
    """
    try:
        if not WABA_ID or not ACCESS_TOKEN:
            logger.error("WhatsApp not fully configured")
            await utils.log_api_call("/create-template", "POST", None, 503, "WhatsApp not configured")
            return JSONResponse(
                {"error": "WhatsApp not configured", "required": ["WABA_ID", "ACCESS_TOKEN"]},
                status_code=503
            )
        
        # Validate and clean template name
        template_name = request.name.replace(" ", "_").lower()
        if not all(c.isalnum() or c == "_" for c in template_name):
            return JSONResponse(
                {"error": "Invalid template name. Use only alphanumeric characters and underscores"},
                status_code=400
            )
        
        # Step 1: Get template content based on template mode
        generated_content = None
        
        if request.mode == TemplateModeEnum.MANUAL:
            # Manual mode: use provided content directly
            generated_content = request.content
            logger.info(f"Using manual template content: {len(generated_content)} chars")
        
        elif request.mode == TemplateModeEnum.AI:
            # AI mode: Use Gemini to generate template content from prompt
            if SERVICE_STATUS.get("gemini", False) and GEMINI_API_KEY:
                try:
                    logger.info(f"Generating template with Gemini from prompt: {request.prompt[:100]}...")
                    import google.generativeai as genai
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel("gemini-2.5-pro")
                    
                    gemini_prompt = f"""Create a professional WhatsApp Business message template.

Rules:
- Under 500 characters
- No spammy words
- No exaggerated claims
- No excessive emojis (max 2-3)
- Professional & engaging tone
- If personalization needed, use {{{{1}}}} format
- Clear and actionable

User Idea:
{request.prompt}

Return ONLY the final template message text, nothing else."""
                    
                    response = model.generate_content(gemini_prompt)
                    if response.text:
                        generated_content = response.text.strip()
                        logger.info(f"✓ Template generated by Gemini: {len(generated_content)} chars")
                    else:
                        logger.warning("Gemini returned empty response")
                
                except Exception as e:
                    logger.error(f"Gemini generation failed: {e}")
            else:
                logger.warning("Gemini not available, cannot generate template")
        
        if not generated_content:
            error_msg = "Could not generate template content."
            if request.mode == TemplateModeEnum.AI:
                error_msg = "Could not generate template. Gemini service may not be available."
            return JSONResponse({
                "status": "error",
                "error": error_msg,
                "troubleshooting": [
                    "1. Verify GEMINI_API_KEY is set in .env (for AI mode)",
                    "2. Check Google Generative AI API is enabled (for AI mode)",
                    "3. Ensure prompt/content is clear and descriptive"
                ]
            }, status_code=400)
        
        # Step 2: Build template component with generated content (lowercase "body" per Meta docs)
        component = {
            "type": "body",
            "text": generated_content
        }
        
        # Auto-detect variables and add required example field
        import re
        variable_pattern = r'\{\{(\d+)\}\}'
        variables = re.findall(variable_pattern, generated_content)
        if variables:
            example_values = [f"example_value_{i}" for i in range(1, len(variables) + 1)]
            component["example"] = {"body_text": [example_values]}
        
        components = [component]
        
        logger.info(f"Submitting template to Meta: {template_name}")
        
        # Validate category - must be UTILITY, MARKETING, or AUTHENTICATION
        category_str = str(request.category.value) if hasattr(request.category, 'value') else str(request.category)
        valid_categories = ["UTILITY", "MARKETING", "AUTHENTICATION"]
        if category_str not in valid_categories:
            logger.error(f"Invalid category: {category_str}. Valid: {valid_categories}")
            await utils.log_api_call("/create-template", "POST", None, 400, f"Invalid category: {category_str}")
            return JSONResponse({
                "status": "error",
                "error": f"Invalid category. Must be: UTILITY, MARKETING, or AUTHENTICATION. Got: {category_str}"
            }, status_code=400)
        
        # Step 3: Submit to Meta Graph API
        success, result = await create_whatsapp_template(
            WABA_ID,
            ACCESS_TOKEN,
            template_name,
            category_str,
            components,
            "en_US"
        )
        
        if success:
            template_id = result.get("template_id")
            
            # Step 4: Store in Supabase for tracking (correct column names)
            if SUPABASE_URL and SUPABASE_KEY:
                try:
                    headers = get_supabase_headers()
                    template_data = {
                        "template_name": template_name,
                        "body": generated_content,
                        "footer": request.title or "",
                        "category": category_str,
                        "language": "en_US",
                        "header_type": None,
                        "header_text": None,
                        "status": "PENDING_REVIEW"
                    }
                    
                    store_response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/templates",
                        headers={**headers, "Prefer": "return=representation"},
                        json=template_data,
                        timeout=10
                    )
                    
                    if store_response.status_code in [200, 201]:
                        logger.info(f"✓ Template {template_name} stored in Supabase with ID {template_id}")
                    else:
                        logger.warning(f"Could not store in Supabase: {store_response.status_code} - {store_response.text[:200]}")
                
                except Exception as e:
                    logger.warning(f"Could not store in Supabase: {e}")
            
            await utils.log_api_call("/create-template", "POST", None, 201)
            
            return JSONResponse({
                "status": "success",
                "message": "Template created and sent to WhatsApp for review",
                "template_name": template_name,
                "template_id": template_id,
                "mode": "manual" if request.mode == TemplateModeEnum.MANUAL else "ai",
                "user_input": request.prompt if request.mode == TemplateModeEnum.AI else request.content,
                "template_content": generated_content,
                "category": category_str,
                "approval_status": "PENDING_REVIEW",
                "next_step": "WhatsApp will review this template within 24 hours. Check status using GET /templates/status",
                "created_at": datetime.now().isoformat()
            }, status_code=201)
        else:
            error_details = result.get("details", result.get("error", "Unknown error"))
            
            # Check for specific error: Template already exists (error_subcode 2388024)
            error_subcode = None
            if isinstance(error_details, dict) and 'error' in error_details:
                error_subcode = error_details['error'].get('error_subcode')
            
            if error_subcode == 2388024:
                # Template name already exists
                await utils.log_api_call("/create-template", "POST", None, 409, error_details)
                return JSONResponse({
                    "status": "error",
                    "error": "Template name already exists",
                    "error_code": "TEMPLATE_ALREADY_EXISTS",
                    "message": f"A template with the name '{template_name}' already exists in your WhatsApp Business Account.",
                    "details": error_details.get('error', {}).get('error_user_msg', ''),
                    "solutions": [
                        "1. Use a different template name (e.g., 'greeting_template_v2')",
                        "2. Delete the existing template from Meta Business Manager first",
                        "3. Check existing templates at: https://business.facebook.com",
                        "4. Or modify the existing template instead of creating a new one"
                    ]
                }, status_code=409)  # 409 Conflict
            else:
                # Other errors
                await utils.log_api_call("/create-template", "POST", None, 500, error_details)
                return JSONResponse({
                    "status": "error",
                    "error": "Failed to create template on WhatsApp",
                    "details": error_details,
                    "troubleshooting": [
                        "1. Verify WABA_ID and ACCESS_TOKEN are valid",
                        "2. Ensure template name follows Meta guidelines (no spaces, max 512 chars)",
                        "3. Template content must be at least 3 characters",
                        "4. Check Meta API documentation for category requirements"
                    ]
                }, status_code=500)
    
    except Exception as e:
        logger.error(f"Create template error: {e}", exc_info=True)
        await utils.log_api_call("/create-template", "POST", None, 500, str(e))
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@app.get("/templates")
async def templates_list():
    """Get all active message templates with Gemini enhancement info"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({"templates": [], "count": 0})
        
        headers = utils.get_supabase_headers()
        
        # Filter by active status using message_templates table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/message_templates?is_active=eq.true&select=*&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            templates = response.json()
            await utils.log_api_call("/templates", "GET", None, 200)
            
            return JSONResponse({
                "status": "success",
                "templates": templates,
                "count": len(templates),
                "message": "Active message templates from database"
            })
        else:
            logger.warning(f"Could not fetch templates: {response.status_code} - {response.text}")
            return JSONResponse({"templates": [], "count": 0, "status": "database_error"})
    
    except Exception as e:
        logger.error(f"Templates list error: {e}")
        return JSONResponse({"templates": [], "count": 0, "error": str(e)})

@app.get("/templates/status")
async def templates_status():
    """Get template status aggregation (approved, pending, rejected counts)
    
    Returns statistics about all templates in the database grouped by status.
    Useful for dashboard and monitoring purposes.
    """
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({
                "status": "error",
                "error": "Database not configured"
            }, status_code=503)
        
        headers = get_supabase_headers()
        
        # Get all templates from Supabase
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/templates?select=status,template_name,created_at,category",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch templates: {response.status_code} - {response.text}")
            return JSONResponse({
                "status": "error",
                "error": "Failed to fetch templates from database"
            }, status_code=500)
        
        templates = response.json()
        
        # Aggregate by status
        status_counts = {}
        category_counts = {}
        templates_by_status = {}
        
        for template in templates:
            status = template.get("status", "UNKNOWN")
            category = template.get("category", "UNKNOWN")
            
            # Count by status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by category
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Group templates by status
            if status not in templates_by_status:
                templates_by_status[status] = []
            templates_by_status[status].append({
                "name": template.get("template_name"),
                "category": category,
                "created_at": template.get("created_at")
            })
        
        await utils.log_api_call("/templates/status", "GET", None, 200)
        
        return JSONResponse({
            "status": "success",
            "total_templates": len(templates),
            "status_breakdown": status_counts,
            "category_breakdown": category_counts,
            "approved": status_counts.get("APPROVED", 0),
            "pending": status_counts.get("PENDING", 0) + status_counts.get("PENDING_REVIEW", 0),
            "rejected": status_counts.get("REJECTED", 0),
            "templates_by_status": templates_by_status,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Templates status error: {e}", exc_info=True)
        await utils.log_api_call("/templates/status", "GET", None, 500, str(e))
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@app.post("/template/send")
async def template_send(request: TemplateSend):
    """Send message from template"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({"error": "Database not configured"}, status_code=503)
        
        headers = utils.get_supabase_headers()
        
        # Get template from message_templates table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/message_templates?id=eq.{request.template_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200 or not response.json():
            return JSONResponse({"error": "Template not found in database"}, status_code=404)
        
        template = response.json()[0]
        
        # Replace variables in template content
        message = template["content"]
        for key, value in request.variables.items():
            message = message.replace(f"{{{{{key}}}}}", str(value))
        
        # Send message
        success, msg_id = utils.send_whatsapp_message(
            PHONE_NUMBER_ID,
            ACCESS_TOKEN,
            request.phone,
            message
        )
        
        if success:
            # If no message_id from API, generate UUID for tracking
            if not msg_id:
                msg_id = str(uuid.uuid4())
                logger.debug(f"Generated UUID for template message: {msg_id}")
            
            # Store in memory
            utils.add_to_recent_messages(message, "Template", request.phone, "sent")
            
            # Store message and conversation together
            db_success, db_data = await utils.store_conversation_with_message(
                phone=request.phone,
                message=message,
                sender="Template",
                direction="outbound",
                status="sent",
                sender_type="template",
                message_id=msg_id
            )
            
            await utils.log_api_call("/template/send", "POST", request.phone, 200)
            
            if db_success:
                logger.info(f"✓ Template sent to {request.phone} (Template ID: {request.template_id}, Message ID: {msg_id})")
            else:
                logger.warning(f"Template sent but storage failed for {request.phone}")
            
            return JSONResponse({
                "status": "success",
                "message_id": msg_id,
                "message": message,
                "template_id": request.template_id,
                "stored_in_supabase": db_success,
                "sent_at": datetime.now().isoformat()
            })
        else:
            return JSONResponse({"error": "Failed to send template"}, status_code=500)
    
    except Exception as e:
        logger.error(f"Template send error: {e}")
        await utils.log_api_call("/template/send", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ LEAD ENDPOINTS ============

@app.post("/leads/create")
async def create_lead(request: LeadCreate):
    """Create a new lead"""
    try:
        success, lead = await utils.store_lead(request.phone, request.name)
        
        if success:
            await utils.log_api_call("/leads/create", "POST", request.phone, 201)
            
            return JSONResponse({
                "status": "success",
                "lead": lead
            }, status_code=201)
        else:
            return JSONResponse({"error": "Failed to create lead"}, status_code=500)
    
    except Exception as e:
        logger.error(f"Create lead error: {e}")
        await utils.log_api_call("/leads/create", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/leads")
async def list_leads(limit: int = Query(100, ge=1, le=1000)):
    """List all leads"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({"leads": [], "count": 0})
        
        headers = get_supabase_headers()
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/leads?limit={limit}&order=created_at.desc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            leads = response.json()
            await utils.log_api_call("/leads", "GET", None, 200)
            
            return JSONResponse({
                "status": "success",
                "leads": leads,
                "count": len(leads)
            })
        else:
            return JSONResponse({"leads": [], "count": 0})
    
    except Exception as e:
        logger.error(f"List leads error: {e}")
        return JSONResponse({"leads": [], "count": 0})

@app.post("/leads/status")
async def update_lead_status(
    phone: str = Query(..., description="Phone number of the lead"),
    status: str = Query("new", description="New status (optional, defaults to 'new')")
):
    """Update lead status - status parameter is optional"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            await utils.log_api_call("/leads/status", "POST", phone, 503, "Database not configured")
            return JSONResponse({"error": "Database not configured"}, status_code=503)
        
        headers = utils.get_supabase_headers()
        
        logger.debug(f"Updating lead status for {phone} to {status}")
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{phone}",
            headers=headers,
            json={"status": status, "updated_at": datetime.now().isoformat()},
            timeout=10
        )
        
        logger.debug(f"Update response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            await utils.log_api_call("/leads/status", "POST", phone, 200)
            
            return JSONResponse({
                "status": "success",
                "message": f"Lead status updated to {status}",
                "phone": phone,
                "new_status": status
            })
        else:
            logger.error(f"Supabase error: {response.status_code} - {response.text}")
            await utils.log_api_call("/leads/status", "POST", phone, response.status_code, response.text)
            return JSONResponse({"error": f"Failed to update status: {response.text}"}, status_code=500)
    
    except Exception as e:
        logger.error(f"Update status error: {e}", exc_info=True)
        await utils.log_api_call("/leads/status", "POST", phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ ADMIN MANAGEMENT ENDPOINTS ============

@app.post("/admin/create")
async def create_admin(request: models.AdminCreate):
    """Create a new admin"""
    try:
        success, admin = await utils.create_admin(request.model_dump())
        
        if success and admin:
            await utils.log_api_call("/admin/create", "POST", None, 201)
            return JSONResponse({
                "status": "success",
                "message": "Admin created successfully",
                "admin": admin
            }, status_code=201)
        else:
            await utils.log_api_call("/admin/create", "POST", None, 500)
            return JSONResponse({
                "status": "error",
                "message": "Failed to create admin"
            }, status_code=500)
    
    except Exception as e:
        logger.error(f"Create admin error: {e}")
        await utils.log_api_call("/admin/create", "POST", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/admin/list")
async def list_admins():
    """Get all admins"""
    try:
        success, admins = await utils.get_all_admins()
        
        if success:
            await utils.log_api_call("/admin/list", "GET", None, 200)
            return JSONResponse({
                "status": "success",
                "admins": admins,
                "count": len(admins)
            })
        else:
            return JSONResponse({
                "status": "error",
                "admins": [],
                "count": 0
            })
    
    except Exception as e:
        logger.error(f"List admins error: {e}")
        await utils.log_api_call("/admin/list", "GET", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ AGENT MANAGEMENT ENDPOINTS ============

@app.post("/agent/create")
async def create_agent(request: models.AgentCreate):
    """Create a new agent"""
    try:
        success, agent = await utils.create_agent(request.model_dump())
        
        if success and agent:
            await utils.log_api_call("/agent/create", "POST", None, 201)
            return JSONResponse({
                "status": "success",
                "message": "Agent created successfully",
                "agent": agent
            }, status_code=201)
        else:
            await utils.log_api_call("/agent/create", "POST", None, 500)
            return JSONResponse({
                "status": "error",
                "message": "Failed to create agent"
            }, status_code=500)
    
    except Exception as e:
        logger.error(f"Create agent error: {e}")
        await utils.log_api_call("/agent/create", "POST", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/agent/list")
async def list_agents():
    """Get all agents"""
    try:
        success, agents = await utils.get_all_agents()
        
        if success:
            await utils.log_api_call("/agent/list", "GET", None, 200)
            return JSONResponse({
                "status": "success",
                "agents": agents,
                "count": len(agents)
            })
        else:
            return JSONResponse({
                "status": "error",
                "agents": [],
                "count": 0
            })
    
    except Exception as e:
        logger.error(f"List agents error: {e}")
        await utils.log_api_call("/agent/list", "GET", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/agent/send-message")
async def agent_send_message(request: models.AgentMessageSend):
    """Send message from specific agent to lead"""
    try:
        success, msg_id = await utils.send_message_from_agent(
            request.agent_id,
            request.lead_phone,
            request.message
        )
        
        if success:
            await utils.log_api_call("/agent/send-message", "POST", request.lead_phone, 200)
            return JSONResponse({
                "status": "success",
                "message": "Message sent successfully",
                "message_id": msg_id,
                "agent_id": request.agent_id,
                "lead_phone": request.lead_phone
            })
        else:
            await utils.log_api_call("/agent/send-message", "POST", request.lead_phone, 500)
            return JSONResponse({
                "status": "error",
                "message": "Failed to send message"
            }, status_code=500)
    
    except Exception as e:
        logger.error(f"Agent send message error: {e}")
        await utils.log_api_call("/agent/send-message", "POST", request.lead_phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/agent/{agent_id}/conversations")
async def get_agent_conversations(agent_id: str, limit: int = Query(50, ge=1, le=100)):
    """Get agent conversation history and performance stats"""
    try:
        success, data = await utils.get_agent_conversations(agent_id, limit)
        
        if success:
            await utils.log_api_call(f"/agent/{agent_id}/conversations", "GET", None, 200)
            return JSONResponse({
                "status": "success",
                "data": data
            })
        else:
            await utils.log_api_call(f"/agent/{agent_id}/conversations", "GET", None, 404)
            return JSONResponse({
                "status": "error",
                "message": "Agent not found or no conversations"
            }, status_code=404)
    
    except Exception as e:
        logger.error(f"Get agent conversations error: {e}")
        await utils.log_api_call(f"/agent/{agent_id}/conversations", "GET", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/agent/{agent_id}/recent-conversations")
async def get_agent_recent_conversations(agent_id: str, limit: int = Query(10, ge=1, le=50)):
    """Get agent recent conversations (simplified)"""
    try:
        success, data = await utils.get_agent_conversations(agent_id, limit)
        
        if success and data:
            recent_conversations = data.get("recent_conversations", [])
            await utils.log_api_call(f"/agent/{agent_id}/recent-conversations", "GET", None, 200)
            
            return JSONResponse({
                "status": "success",
                "agent_id": agent_id,
                "agent_name": data.get("agent_name"),
                "recent_conversations": recent_conversations,
                "total_count": len(recent_conversations)
            })
        else:
            await utils.log_api_call(f"/agent/{agent_id}/recent-conversations", "GET", None, 404)
            return JSONResponse({
                "status": "error",
                "message": "Agent not found or no conversations"
            }, status_code=404)
    
    except Exception as e:
        logger.error(f"Get agent recent conversations error: {e}")
        await utils.log_api_call(f"/agent/{agent_id}/recent-conversations", "GET", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ STARTUP EVENT ============

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup"""
    logger.info("=" * 70)
    logger.info(f"  {APP_TITLE} v{APP_VERSION}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("🔧 Initializing Services:")
    
    # Initialize Gemini
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            # Test the connection by creating a model instance
            model = genai.GenerativeModel("gemini-2.5-pro")
            SERVICE_STATUS["gemini"] = True
            logger.info("   ✓ Gemini AI: Ready (gemini-2.5-pro)")
        except Exception as e:
            logger.error(f"   ✗ Gemini AI: Failed to initialize - {e}")
            SERVICE_STATUS["gemini"] = False
    else:
        logger.warning("   ⚠ Gemini AI: No API key provided - auto-replies disabled")
        SERVICE_STATUS["gemini"] = False
    
    # Log other services
    logger.info(f"   {'✓' if ACCESS_TOKEN and PHONE_NUMBER_ID else '⚠'} WhatsApp: {'Configured' if ACCESS_TOKEN and PHONE_NUMBER_ID else 'Not Configured'}")
    logger.info(f"   {'✓' if SUPABASE_URL else '⚠'} Database: {'Connected' if SUPABASE_URL else 'Not Configured'}")
    logger.info("")
    logger.info(" API Documentation:")
    logger.info(f"   Interactive: http://localhost:{PORT}/docs")
    logger.info(f"   OpenAPI: http://localhost:{PORT}/openapi.json")
    logger.info("")

# ============ MAIN ============

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {HOST}:{PORT}")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )

