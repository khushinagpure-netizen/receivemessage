"""
Pydantic Models for Request/Response Validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# ============ MESSAGE MODELS ============

class MessageCreate(BaseModel):
    """Request to send a WhatsApp message"""
    phone: str = Field(..., example="1234567890", description="Phone number")
    message: str = Field(..., description="Message text")
    
    class Config:
        schema_extra = {
            "example": {
                "phone": "1234567890",
                "message": "Hello! How can I help you today?"
            }
        }

class ReceiveMessage(BaseModel):
    """Request to simulate receiving a message"""
    phone: str = Field(..., description="Sender phone number")
    message_text: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Sender name")
    
    class Config:
        schema_extra = {
            "example": {
                "phone": "1234567890",
                "message_text": "I have a question",
                "name": "John"
            }
        }

class MessageResponse(BaseModel):
    """Response for message operations"""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ============ TEMPLATE MODELS ============

class TemplateCreate(BaseModel):
    """Request to create a message template"""
    name: str = Field(..., description="Template name")
    content: str = Field(..., description="Template content with {variables}")
    title: Optional[str] = Field(None, description="Display title")
    category: Optional[str] = Field("general", description="Template category")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "greeting",
                "content": "Hello {name}, welcome!",
                "title": "Greeting Template",
                "category": "sales"
            }
        }

class TemplateSend(BaseModel):
    """Request to send message from template"""
    phone: str = Field(..., description="Recipient phone")
    template_id: str = Field(..., description="Template ID")
    variables: Dict[str, str] = Field(default_factory=dict, description="Template variables")
    
    class Config:
        schema_extra = {
            "example": {
                "phone": "1234567890",
                "template_id": "greeting_01",
                "variables": {"name": "John"}
            }
        }

# ============ LEAD MODELS ============

class LeadCreate(BaseModel):
    """Request to create a lead"""
    phone: str = Field(..., description="Phone number")
    name: Optional[str] = Field(None, description="Lead name")
    status: Optional[str] = Field("new", description="Lead status")
    
    class Config:
        schema_extra = {
            "example": {
                "phone": "1234567890",
                "name": "John Doe",
                "status": "new"
            }
        }

class LeadUpdate(BaseModel):
    """Request to update lead"""
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "contacted",
                "tags": ["interested", "premium"],
                "notes": "Customer called back"
            }
        }

# ============ CONVERSATION MODELS ============

class ConversationResponse(BaseModel):
    """Response for conversation retrieval"""
    status: str
    phone: str
    messages: List[Dict[str, Any]]
    total_messages: int
    recent_message: Optional[Dict[str, Any]] = None

# ============ MESSAGE TRACKING MODELS ============

class MessageStatus(BaseModel):
    """Message status tracking"""
    message_id: str
    status: str  # sent, delivered, read, failed
    timestamp: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None

class RecentMessagesResponse(BaseModel):
    """Response for recent messages API"""
    status: str
    phone: str
    recent_sent: List[Dict[str, Any]] = []
    recent_received: List[Dict[str, Any]] = []
    total_sent: int = 0
    total_received: int = 0
    last_update: str

# ============ WEBHOOK MODELS ============

class WebhookMessage(BaseModel):
    """WhatsApp webhook message structure"""
    object: str
    entry: List[Dict[str, Any]]

class WebhookStatus(BaseModel):
    """Webhook message status update"""
    message_id: str
    status: str
    timestamp: int
