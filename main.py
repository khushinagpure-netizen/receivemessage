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
from fastapi.responses import JSONResponse, PlainTextResponse
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
    ACCESS_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN,
    GEMINI_API_KEY, GEMINI_READY, PORT, HOST, APP_TITLE, APP_DESCRIPTION, APP_VERSION
)
from models import (
    MessageCreate, ReceiveMessage, TemplateCreate, TemplateSend,
    LeadCreate, LeadUpdate, ConversationResponse, RecentMessagesResponse, WebhookMessage
)
from utils import (
    get_supabase_headers, log_api_call, add_to_recent_messages, get_recent_messages,
    store_lead, store_conversation, update_message_status,
    generate_ai_reply, send_whatsapp_message, verify_webhook_token
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

# ============ HEALTH CHECK ENDPOINTS ============

@app.get("/")
async def root():
    """API Documentation - Public endpoint (no authentication required)"""
    return {
        "title": APP_TITLE + " 🚀",
        "version": APP_VERSION,
        "status": "operational",
        "description": APP_DESCRIPTION,
        "features": [
            "📱 WhatsApp Business API Integration",
            "👥 Multi-Agent Team Collaboration",
            "🎯 Lead Management & CRM",
            "🤖 AI-Powered Auto-Replies (Gemini 2.5 Pro)",
            "📊 Analytics & Performance Tracking",
            "⚡ Conversation Tracking with Message Status"
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
    """API Health Check"""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "whatsapp": bool(ACCESS_TOKEN and PHONE_NUMBER_ID),
            "gemini": GEMINI_READY,
            "database": bool(SUPABASE_URL and SUPABASE_KEY)
        }
    }

# ============ WHATSAPP WEBHOOK ENDPOINTS ============

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None),
    hub_challenge: str = Query(None),
    hub_verify_token: str = Query(None)
):
    """Verify WhatsApp webhook with Meta"""
    try:
        if hub_mode == "subscribe":
            if verify_webhook_token(hub_verify_token, VERIFY_TOKEN):
                await log_api_call("/webhook", "GET", None, 200)
                return PlainTextResponse(hub_challenge)
            else:
                await log_api_call("/webhook", "GET", None, 403, "Invalid verify token")
                return JSONResponse({"error": "Invalid verify token"}, status_code=403)
        
        await log_api_call("/webhook", "GET", None, 400, "Invalid mode")
        return JSONResponse({"error": "Invalid mode"}, status_code=400)
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        await log_api_call("/webhook", "GET", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive WhatsApp messages from Meta and auto-generate AI replies"""
    try:
        body = await request.json()
        
        # Verify webhook signature
        x_hub_signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_webhook_signature(await request.body(), x_hub_signature):
            logger.warning("Invalid webhook signature")
        
        # Process messages
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    messages = change.get("value", {}).get("messages", [])
                    statuses = change.get("value", {}).get("statuses", [])
                    
                    # Process incoming messages
                    for message in messages:
                        await process_incoming_message(message)
                    
                    # Process message status updates
                    for status in statuses:
                        await process_message_status(status)
        
        await log_api_call("/webhook", "POST", None, 200)
        return JSONResponse({"status": "received"})
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        await log_api_call("/webhook", "POST", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

async def process_incoming_message(message: Dict[str, Any]):
    """Process incoming WhatsApp message"""
    try:
        phone = message.get("from")
        text = message.get("text", {}).get("body", "")
        
        if not phone or not text:
            return
        
        # Create/update lead
        success, lead = await store_lead(phone)
        if not success:
            logger.warning(f"Could not store lead for {phone}")
            return
        
        # Store conversation
        await store_conversation(
            lead.get("id"),
            phone,
            text,
            "customer",
            direction="inbound",
            status="received"
        )
        
        # Add to recent messages
        add_to_recent_messages(text, phone, phone, "received")
        
        # Generate & send AI reply
        if GEMINI_READY:
            reply = await generate_ai_reply(text, phone)
            success, msg_id = send_whatsapp_message(
                PHONE_NUMBER_ID, ACCESS_TOKEN, phone, reply
            )
            
            if success:
                add_to_recent_messages(reply, "AI Agent", phone, "sent")
                await store_conversation(
                    lead.get("id"),
                    phone,
                    reply,
                    "agent",
                    direction="outbound",
                    status="sent"
                )
        
        logger.info(f"Processed message from {phone}")
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")

async def process_message_status(status: Dict[str, Any]):
    """Process WhatsApp message status update"""
    try:
        phone = status.get("recipient_id")
        msg_status = status.get("status")
        
        logger.info(f"Message status for {phone}: {msg_status}")
        
        # Could store status in database if needed
        await log_api_call("/webhook/status", "POST", phone, 200)
    
    except Exception as e:
        logger.error(f"Error processing status: {e}")

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
    """Send WhatsApp message"""
    try:
        if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
            await log_api_call("/send-message", "POST", request.phone, 503, "WhatsApp not configured")
            return JSONResponse(
                {"error": "WhatsApp not configured"},
                status_code=503
            )
        
        success, msg_id = send_whatsapp_message(
            PHONE_NUMBER_ID,
            ACCESS_TOKEN,
            request.phone,
            request.message
        )
        
        if success:
            add_to_recent_messages(request.message, "Agent", request.phone, "sent")
            await log_api_call("/send-message", "POST", request.phone, 200)
            
            return JSONResponse({
                "status": "success",
                "message_id": msg_id,
                "phone": request.phone
            })
        else:
            await log_api_call("/send-message", "POST", request.phone, 500, "Failed to send")
            return JSONResponse(
                {"error": "Failed to send message"},
                status_code=500
            )
    
    except Exception as e:
        logger.error(f"Send message error: {e}")
        await log_api_call("/send-message", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/receive-simple")
async def receive_simple(request: ReceiveMessage):
    """Simulate receiving a WhatsApp message and generate AI reply"""
    try:
        # Create/update lead
        success, lead = await store_lead(request.phone, request.name)
        if not success:
            return JSONResponse({"error": "Failed to store lead"}, status_code=500)
        
        # Store incoming message
        await store_conversation(
            lead.get("id"),
            request.phone,
            request.message_text,
            request.name or "Customer",
            direction="inbound",
            status="received"
        )
        
        add_to_recent_messages(request.message_text, request.phone, request.phone, "received")
        
        # Generate AI reply
        reply = await generate_ai_reply(request.message_text, request.phone)
        
        # Store and send reply
        await store_conversation(
            lead.get("id"),
            request.phone,
            reply,
            "AI Agent",
            direction="outbound",
            status="sent"
        )
        
        add_to_recent_messages(reply, "AI Agent", request.phone, "sent")
        
        await log_api_call("/receive-simple", "POST", request.phone, 200)
        
        return JSONResponse({
            "status": "success",
            "received": request.message_text,
            "reply": reply,
            "lead_id": lead.get("id")
        })
    
    except Exception as e:
        logger.error(f"Receive simple error: {e}")
        await log_api_call("/receive-simple", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ CONVERSATION ENDPOINTS ============

@app.get("/get-conversation")
async def get_conversation(phone: str):
    """Get conversation history for a specific phone number"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse(
                {"messages": [], "error": "Database not configured"},
                status_code=200
            )
        
        headers = get_supabase_headers()
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conversations?phone=eq.{phone}&order=created_at.asc",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            messages = response.json()
            await log_api_call("/get-conversation", "GET", phone, 200)
            
            return JSONResponse({
                "status": "success",
                "phone": phone,
                "messages": messages,
                "total": len(messages)
            })
        else:
            logger.error(f"Failed to get conversations: {response.text}")
            return JSONResponse(
                {"messages": [], "total": 0, "phone": phone},
                status_code=200
            )
    
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        return JSONResponse(
            {"messages": [], "error": str(e)},
            status_code=200
        )

@app.get("/recent-messages")
async def recent_messages(
    phone: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Get recent sent/received messages with status"""
    try:
        messages = get_recent_messages(phone, limit)
        
        sent = [m for m in messages if m.get("direction") == "sent"]
        received = [m for m in messages if m.get("direction") == "received"]
        
        await log_api_call("/recent-messages", "GET", phone, 200)
        
        return JSONResponse({
            "status": "success",
            "phone": phone or "all",
            "recent_sent": sent[-10:],
            "recent_received": received[-10:],
            "total_sent": len(sent),
            "total_received": len(received),
            "total_messages": len(messages),
            "last_update": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Recent messages error: {e}")
        await log_api_call("/recent-messages", "GET", phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ TEMPLATE ENDPOINTS ============

@app.post("/template/create")
async def template_create(request: TemplateCreate):
    """Create a message template"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({"error": "Database not configured"}, status_code=503)
        
        headers = get_supabase_headers()
        template_data = {
            "name": request.name,
            "content": request.content,
            "title": request.title or request.name,
            "category": request.category,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/message_templates",
            headers={**headers, "Prefer": "return=representation"},
            json=template_data,
            timeout=10
        )
        
        if response.status_code == 201:
            template = response.json()[0]
            await log_api_call("/template/create", "POST", None, 201)
            
            return JSONResponse({
                "status": "success",
                "template": template
            })
        else:
            logger.error(f"Template creation failed: {response.text}")
            await log_api_call("/template/create", "POST", None, 500)
            return JSONResponse({"error": "Failed to create template"}, status_code=500)
    
    except Exception as e:
        logger.error(f"Template create error: {e}")
        await log_api_call("/template/create", "POST", None, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/templates")
async def templates_list():
    """Get all active message templates"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({"templates": [], "count": 0})
        
        headers = get_supabase_headers()
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/message_templates?is_active=eq.true",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            templates = response.json()
            await log_api_call("/templates", "GET", None, 200)
            
            return JSONResponse({
                "status": "success",
                "templates": templates,
                "count": len(templates)
            })
        else:
            return JSONResponse({"templates": [], "count": 0})
    
    except Exception as e:
        logger.error(f"Templates list error: {e}")
        return JSONResponse({"templates": [], "count": 0})

@app.post("/template/send")
async def template_send(request: TemplateSend):
    """Send message from template"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({"error": "Database not configured"}, status_code=503)
        
        headers = get_supabase_headers()
        
        # Get template
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/message_templates?id=eq.{request.template_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200 or not response.json():
            return JSONResponse({"error": "Template not found"}, status_code=404)
        
        template = response.json()[0]
        
        # Replace variables
        message = template["content"]
        for key, value in request.variables.items():
            message = message.replace(f"{{{key}}}", str(value))
        
        # Send message
        success, msg_id = send_whatsapp_message(
            PHONE_NUMBER_ID,
            ACCESS_TOKEN,
            request.phone,
            message
        )
        
        if success:
            add_to_recent_messages(message, "Template", request.phone, "sent")
            await log_api_call("/template/send", "POST", request.phone, 200)
            
            return JSONResponse({
                "status": "success",
                "message_id": msg_id,
                "message": message
            })
        else:
            return JSONResponse({"error": "Failed to send template"}, status_code=500)
    
    except Exception as e:
        logger.error(f"Template send error: {e}")
        await log_api_call("/template/send", "POST", request.phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ LEAD ENDPOINTS ============

@app.post("/leads/create")
async def create_lead(request: LeadCreate):
    """Create a new lead"""
    try:
        success, lead = await store_lead(request.phone, request.name)
        
        if success:
            await log_api_call("/leads/create", "POST", request.phone, 201)
            
            return JSONResponse({
                "status": "success",
                "lead": lead
            }, status_code=201)
        else:
            return JSONResponse({"error": "Failed to create lead"}, status_code=500)
    
    except Exception as e:
        logger.error(f"Create lead error: {e}")
        await log_api_call("/leads/create", "POST", request.phone, 500, str(e))
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
            await log_api_call("/leads", "GET", None, 200)
            
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
    phone: str = Query(...),
    status: str = Query(...)
):
    """Update lead status"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return JSONResponse({"error": "Database not configured"}, status_code=503)
        
        headers = get_supabase_headers()
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/leads?phone=eq.{phone}",
            headers=headers,
            json={"status": status, "updated_at": datetime.now().isoformat()},
            timeout=10
        )
        
        if response.status_code == 200:
            await log_api_call("/leads/status", "POST", phone, 200)
            
            return JSONResponse({
                "status": "success",
                "message": f"Lead status updated to {status}"
            })
        else:
            return JSONResponse({"error": "Failed to update status"}, status_code=500)
    
    except Exception as e:
        logger.error(f"Update status error: {e}")
        await log_api_call("/leads/status", "POST", phone, 500, str(e))
        return JSONResponse({"error": str(e)}, status_code=500)

# ============ STARTUP EVENT ============

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup"""
    logger.info("=" * 70)
    logger.info(f"  {APP_TITLE} v{APP_VERSION}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("✅ Services:")
    logger.info(f"   WhatsApp: {'✓ Configured' if ACCESS_TOKEN and PHONE_NUMBER_ID else '✗ Not Configured'}")
    logger.info(f"   Gemini AI: {'✓ Ready' if GEMINI_READY else '✗ Not Available'}")
    logger.info(f"   Database: {'✓ Connected' if SUPABASE_URL else '✗ Not Configured'}")
    logger.info("")
    logger.info("📚 API Docs:")
    logger.info("   Interactive: http://localhost:8000/docs")
    logger.info("   OpenAPI: http://localhost:8000/openapi.json")
    logger.info("")

# ============ MAIN ============

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Starting server on {HOST}:{PORT}")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
