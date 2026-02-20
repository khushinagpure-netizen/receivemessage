"""
Pydantic Models for Request/Response Validation with comprehensive API coverage
"""

from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

# ============ ENUMS ============

class UserRoleEnum(str, Enum):
    """User role types"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    SENIOR_AGENT = "senior_agent"
    AGENT = "agent"

class UserStatusEnum(str, Enum):
    """User status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"

class LeadStatusEnum(str, Enum):
    """Lead status"""
    NEW = "new"
    CONTACTED = "contacted"
    FOLLOW_UP = "follow-up"
    QUALIFIED = "qualified"
    WON = "won"
    LOST = "lost"
    UNQUALIFIED = "unqualified"

class LeadPriorityEnum(str, Enum):
    """Lead priority"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class MessageTypeEnum(str, Enum):
    """Message types"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    FILE = "file"

class MessageStatusEnum(str, Enum):
    """Message status"""
    SENT = "sent"
    DELIVERED = "delivered"
    SEEN = "seen"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"

class SentimentEnum(str, Enum):
    """Sentiment analysis results"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class TemplateCategoryEnum(str, Enum):
    """WhatsApp template categories (as per Meta API)"""
    UTILITY = "UTILITY"
    MARKETING = "MARKETING"
    AUTHENTICATION = "AUTHENTICATION"

class TemplateModeEnum(str, Enum):
    """Template creation modes"""
    MANUAL = "manual"  # User provides exact template text
    AI = "ai"  # AI generates template from prompt

# ============ ADMIN & AGENT MODELS ============

class AdminCreate(BaseModel):
    """Create new admin"""
    email: str = Field(..., description="Admin email address", example="admin@katyayaniorganics.com")
    name: str = Field(..., description="Admin full name", example="John Doe")
    phone: Optional[str] = Field(None, description="Admin phone number", example="+919876543210")
    password: str = Field(..., min_length=8, description="Admin password (min 8 chars)")
    role: UserRoleEnum = Field(UserRoleEnum.ADMIN, description="Admin role")
    permissions: Optional[Dict[str, Any]] = Field({"all": True}, description="Admin permissions")

class AgentCreate(BaseModel):
    """Create new agent"""
    email: str = Field(..., description="Agent email address", example="agent@katyayaniorganics.com")
    name: str = Field(..., description="Agent full name", example="Jane Smith")
    phone: Optional[str] = Field(None, description="Agent phone number", example="+919876543210")
    password: str = Field(..., min_length=8, description="Agent password (min 8 chars)")
    role: UserRoleEnum = Field(UserRoleEnum.AGENT, description="Agent role")
    assigned_leads_limit: int = Field(50, description="Maximum leads agent can handle", example=50)

class AdminResponse(BaseModel):
    """Admin response model"""
    id: str = Field(..., description="Admin ID")
    email: str = Field(..., description="Admin email")
    name: str = Field(..., description="Admin name")
    phone: Optional[str] = Field(None, description="Admin phone")
    role: UserRoleEnum = Field(..., description="Admin role")
    status: UserStatusEnum = Field(..., description="Admin status")
    permissions: Dict[str, Any] = Field(..., description="Admin permissions")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class AgentResponse(BaseModel):
    """Agent response model"""
    id: str = Field(..., description="Agent ID")
    email: str = Field(..., description="Agent email")
    name: str = Field(..., description="Agent name")
    phone: Optional[str] = Field(None, description="Agent phone")
    role: UserRoleEnum = Field(..., description="Agent role")
    status: UserStatusEnum = Field(..., description="Agent status")
    assigned_leads_limit: int = Field(..., description="Max leads limit")
    current_leads_count: int = Field(..., description="Current leads count")
    is_available: bool = Field(..., description="Is agent available")
    performance_rating: float = Field(..., description="Performance rating (0-5)")
    total_leads_handled: int = Field(..., description="Total leads handled")
    total_conversations: int = Field(..., description="Total conversations")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class AgentMessageSend(BaseModel):
    """Send message from specific agent to lead"""
    agent_id: str = Field(..., description="Agent ID sending the message", example="550e8400-e29b-41d4-a716-446655440000")
    lead_phone: str = Field(..., description="Lead phone number", example="917974734809")
    message: str = Field(..., description="Message content", example="Hello! How can I help you today?")
    message_type: MessageTypeEnum = Field(MessageTypeEnum.TEXT, description="Message type")

class AgentConversationResponse(BaseModel):
    """Agent conversation history response"""
    agent_id: str = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    total_conversations: int = Field(..., description="Total conversations")
    active_conversations: int = Field(..., description="Active conversations")
    recent_conversations: List[Dict[str, Any]] = Field(..., description="Recent conversations")
    performance_stats: Dict[str, Any] = Field(..., description="Performance statistics")

# ============ STANDARD RESPONSE MODELS ============

class ApiResponse(BaseModel):
    """Standard API response wrapper"""
    status: str = Field(..., description="Response status (success/error)")
    message: Optional[str] = Field(None, description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = "error"
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# ============ MESSAGE SEND/RECEIVE MODELS ============

class MessageCreate(BaseModel):
    """Request to send a text WhatsApp message"""
    phone: str = Field(..., example="919876543210", description="Phone number (with country code)")
    message: str = Field(..., description="Message text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "919876543210",
                "message": "Hello! How can I help you?"
            }
        }

class MediaMessageCreate(BaseModel):
    """Request to send media message"""
    phone: str = Field(..., description="Recipient phone number")
    media_url: str = Field(..., description="URL of media file")
    media_type: MessageTypeEnum = Field(..., description="Type of media")
    caption: Optional[str] = Field(None, description="Caption for media")
    filename: Optional[str] = Field(None, description="Filename for document/file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "919876543210",
                "media_url": "https://example.com/image.jpg",
                "media_type": "image",
                "caption": "Check this image!"
            }
        }

class MessageResponse(BaseModel):
    """Response for message send operations"""
    status: str = Field("success", description="Response status")
    message_id: Optional[str] = Field(None, description="WhatsApp message ID")
    phone: str = Field(..., description="Recipient phone")
    message_type: MessageTypeEnum = Field("text")
    sent_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Optional[Dict[str, Any]] = Field(None)

class ReceiveMessage(BaseModel):
    """Request to simulate receiving a message"""
    phone: str = Field(..., description="Sender phone number")
    message_text: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Sender name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "919876543210",
                "message_text": "I have a question",
                "name": "John"
            }
        }

class ReceiveMessageResponse(BaseModel):
    """Response for receiving/simulating message"""
    status: str
    received_message: str
    ai_reply: str
    lead_id: str
    sentiment: SentimentEnum
    timestamp: str

# ============ MESSAGE STATUS MODELS ============

class MessageStatusUpdate(BaseModel):
    """Message status update"""
    message_id: str = Field(..., description="Message ID")
    status: MessageStatusEnum = Field(..., description="New status")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    error_code: Optional[str] = Field(None)
    error_message: Optional[str] = Field(None)

class MessageStatusResponse(BaseModel):
    """Response for message status"""
    status: str
    message_id: str
    current_status: MessageStatusEnum
    updated_at: str

# ============ CONVERSATION MODELS ============

class ConversationMessage(BaseModel):
    """Single message in conversation"""
    id: str
    phone: str
    sender: str
    message: str
    message_type: MessageTypeEnum = "text"
    status: MessageStatusEnum = "sent"
    sentiment: Optional[SentimentEnum] = None
    created_at: str
    media_url: Optional[str] = None

class ConversationResponse(BaseModel):
    """Response for conversation retrieval"""
    status: str
    phone: str
    messages: List[ConversationMessage]
    total_messages: int
    last_message: Optional[ConversationMessage] = None
    updated_at: str

class RecentMessagesResponse(BaseModel):
    """Response for recent messages API"""
    status: str
    phone: Optional[str] = None
    recent_sent: List[ConversationMessage] = []
    recent_received: List[ConversationMessage] = []
    total_sent: int = 0
    total_received: int = 0
    sentiment_summary: Optional[Dict[str, int]] = None
    last_update: str

# ============ LEAD MODELS ============

class LeadCreate(BaseModel):
    """Request to create a lead"""
    phone: str = Field(..., description="Phone number")
    name: Optional[str] = Field(None, description="Lead name")
    email: Optional[str] = Field(None, description="Lead email")
    status: Optional[str] = Field("new", description="Lead status")
    tags: Optional[List[str]] = Field(None, description="Lead tags")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "919876543210",
                "name": "John Doe",
                "email": "john@example.com",
                "status": "new",
                "tags": ["interested", "premium"]
            }
        }

class LeadUpdate(BaseModel):
    """Request to update lead"""
    status: Optional[str] = Field(None, description="Lead status")
    tags: Optional[List[str]] = Field(None, description="Lead tags")
    notes: Optional[str] = Field(None, description="Internal notes")
    email: Optional[str] = Field(None, description="Lead email")

class LeadResponse(BaseModel):
    """Response for lead operations"""
    status: str
    lead: Dict[str, Any]
    message: Optional[str] = None

class LeadListResponse(BaseModel):
    """Response for listing leads"""
    status: str
    leads: List[Dict[str, Any]]
    count: int
    total_pages: Optional[int] = None
    current_page: Optional[int] = None

# ============ SENTIMENT ANALYSIS MODELS ============

class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    phone: str = Field(..., description="Contact phone number")
    sentiment: SentimentEnum = Field(..., description="Overall sentiment")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    positive_count: int
    negative_count: int
    neutral_count: int
    most_recent_sentiment: SentimentEnum
    trend: str = Field(..., description="Sentiment trend (improving/declining/stable)")
    summary: str

class SentimentResponse(BaseModel):
    """Response for sentiment analysis"""
    status: str
    analysis: SentimentAnalysis
    timestamp: str

# ============ TEMPLATE MODELS ============

class TemplateCreate(BaseModel):
    """Request to create a message template
    
    Supports two creation modes:
    - MANUAL: User provides exact template text in 'content' field
    - AI: AI generates template from 'prompt' field using Gemini
    
    Backward compatibility: If no creation_mode is specified, defaults to AI mode.
    
    Valid categories: UTILITY, MARKETING, AUTHENTICATION (from Meta API requirements)
    """
    name: str = Field(..., description="Template name (lowercase, alphanumeric, underscores only)", example="greeting_template")
    mode: TemplateModeEnum = Field(default=TemplateModeEnum.AI, description="Template mode: 'manual' or 'ai'")
    prompt: Optional[str] = Field(default=None, description="Template idea/description for AI to generate content (required for AI mode)")
    content: Optional[str] = Field(default=None, description="Exact template text (required for MANUAL mode, or deprecated field for AI mode)")
    category: TemplateCategoryEnum = Field(default=TemplateCategoryEnum.MARKETING, description="Template category: UTILITY, MARKETING, or AUTHENTICATION")
    title: Optional[str] = Field(default=None, description="Display title for the template")
    
    @model_validator(mode='after')
    def validate_mode_fields(self):
        """Validate fields based on template mode"""
        # Set defaults if None
        if self.mode is None:
            self.mode = TemplateModeEnum.AI
        if self.category is None:
            self.category = TemplateCategoryEnum.MARKETING
        
        # Get string value for comparison
        mode_value = self.mode.value if hasattr(self.mode, 'value') else str(self.mode)
        
        if mode_value.lower() == "manual":
            # Manual mode: content is required
            if not self.content or (isinstance(self.content, str) and not self.content.strip()):
                raise ValueError("For MANUAL mode: 'content' field is required. Provide exact template text.")
        else:  # ai mode
            # AI mode: prompt is required (but support old 'content' for backward compatibility)
            if self.content and not self.prompt:
                self.prompt = self.content  # Backward compatibility
            if not self.prompt or (isinstance(self.prompt, str) and not self.prompt.strip()):
                raise ValueError("For AI mode: 'prompt' field is required. Provide template idea.")
        
        return self
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "greeting_ai",
                    "mode": "ai",
                    "prompt": "Write a professional greeting for new customers interested in organic products",
                    "category": "MARKETING",
                    "title": "AI Generated Greeting"
                },
                {
                    "name": "greeting_manual",
                    "mode": "manual",
                    "content": "Hello {{1}}! Welcome to our organic store. We're excited to serve you!",
                    "category": "MARKETING",
                    "title": "Manual Greeting"
                }
            ]
        }
    )

class TemplateResponse(BaseModel):
    """Response for template creation"""
    status: str
    template_id: str
    template: Dict[str, Any]

class TemplateSend(BaseModel):
    """Request to send message from template"""
    phone: str = Field(..., description="Recipient phone")
    template_id: str = Field(..., description="Template ID")
    variables: Dict[str, str] = Field(default_factory=dict, description="Template variables")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "919876543210",
                "template_id": "greeting_01",
                "variables": {"name": "John"}
            }
        }

class TemplateListResponse(BaseModel):
    """Response for listing templates"""
    status: str
    templates: List[Dict[str, Any]]
    count: int

# ============ WEBHOOK MODELS ============

class WebhookMessage(BaseModel):
    """WhatsApp webhook message structure"""
    object: str
    entry: List[Dict[str, Any]]

class WebhookResponse(BaseModel):
    """Standard webhook response"""
    status: str = "success"
    message: str = "Webhook received"

# ============ ANALYTICS MODELS ============

class MessageStats(BaseModel):
    """Message statistics"""
    total_messages: int
    total_sent: int
    total_received: int
    delivery_rate: float
    read_rate: float
    average_response_time: Optional[float] = None

class AnalyticsResponse(BaseModel):
    """Response for analytics endpoint"""
    status: str
    phone: Optional[str] = None
    stats: MessageStats
    period: str = "all_time"
    timestamp: str

# ============ STATUS MODELS ============

class ServiceStatus(BaseModel):
    """Service health status"""
    whatsapp: bool
    gemini: bool
    database: bool

class ApiStatusResponse(BaseModel):
    """Response for API status"""
    status: str = "healthy"
    version: str
    services: ServiceStatus
    timestamp: str
