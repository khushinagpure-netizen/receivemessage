# WhatsApp Business API v4.0

A complete **FastAPI-based WhatsApp Business messaging platform** with lead management, Gemini 2.5 Pro AI integration, real-time message tracking, and Supabase database storage.

##  Table of Contents

- [Features](#features)
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Message Flow](#message-flow)
- [Webhook Integration](#webhook-integration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [File Structure](#file-structure)

---

## ✨ Features

### 📱 WhatsApp Integration
- ✅ **Send Text Messages** - Direct messaging to customers
- ✅ **Send Media** - Images, videos, documents, audio files
- ✅ **Template Messages** - Pre-approved WhatsApp templates with placeholders
- ✅ **Real-time Status Tracking** - Know when messages are sent/delivered/read
- ✅ **Incoming Message Webhook** - Auto-receive and process customer messages
- ✅ **Auto-Reply System** - Automatic responses using Gemini AI

### 🤖 AI-Powered Features
- ✅ **Gemini 2.5 Pro Integration** - Generate professional message templates
- ✅ **Dual Template Modes** - Manual templates + AI-generated templates
- ✅ **Smart Message Processing** - Sentiment analysis and context understanding
- ✅ **Template Categories** - UTILITY, MARKETING, AUTHENTICATION

### 👥 Lead Management & CRM
- ✅ **Lead Creation & Tracking** - Automatic lead creation from conversations
- ✅ **Conversation History** - Complete message timeline per customer
- ✅ **Metadata Storage** - Phone, name, email, timezone, custom fields
- ✅ **Lead Status Management** - NEW, CONTACTED, INTERESTED, CONVERTED, LOST

### 💾 Database Management
- ✅ **Supabase PostgreSQL** - Cloud database with real-time sync
- ✅ **Three-Table Schema** - messages, conversations, leads
- ✅ **Automatic Data Sync** - Real-time updates across all tables
- ✅ **Message History** - Complete audit trail of all communications

### 🔍 Analytics & Monitoring
- ✅ **Message Statistics** - Count by status, type, direction
- ✅ **Conversation Analytics** - Thread analysis and insights
- ✅ **Status Dashboard** - Real-time message status tracking
- ✅ **Export Capabilities** - Conversation export as JSON

---

## 🏗️ Project Overview

This is an **enterprise-grade WhatsApp messaging platform** built with:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | REST API & async processing |
| **Database** | Supabase PostgreSQL | Data storage & real-time sync |
| **AI Engine** | Google Gemini 2.5 Pro | Message generation & processing |
| **WhatsApp API** | Meta Graph API v19.0 | Message sending & receiving |
| **Webhooks** | Meta Business Manager | Real-time message webhook |

### Key Capabilities

```
User/Application
       ↓
   FastAPI Server (port 10000)
   ├── Send Message Endpoint
   ├── Send Media Endpoint
   ├── Send Template Endpoint
   ├── Webhook Receiver
   ├── Message History
   └── Lead Management
       ↓
   WhatsApp Cloud API (Meta)
   └── Customer Phones
       ↓
   Supabase PostgreSQL
   ├── messages table
   ├── conversations table
   └── leads table
```

---

## 📦 Installation & Setup

### Prerequisites

- **Python 3.10+** (3.11 recommended)
- **WhatsApp Business Account** (with phone number verified)
- **Supabase Account** (free tier okay)
- **Google Gemini API Key** (free tier okay)
- **Meta Graph API Credentials** (Access Token, Phone Number ID, WABA ID)

### Step 1: Clone & Setup Environment

```bash
# Navigate to project directory
cd receivemessage

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1

# Mac/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### Step 3: Setup Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your credentials
# Required variables:
# - ACCESS_TOKEN (Meta WhatsApp token)
# - PHONE_NUMBER_ID
# - WABA_ID
# - VERIFY_TOKEN
# - SUPABASE_URL
# - SUPABASE_KEY
# - GEMINI_API_KEY
```

### Step 4: Setup Supabase Database

1. Go to **Supabase Dashboard** → SQL Editor
2. Create new query
3. Copy-paste the SQL from `SUPABASE_COMPLETE_SETUP.sql`
4. Run the query

This creates three tables:
- **messages** - Individual message records
- **conversations** - Grouped conversations with leads
- **leads** - Customer/lead information

### Step 5: Start the Server

```bash
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:10000
INFO:     Press CTRL+C to quit
```

Access API Documentation: **http://localhost:10000/docs**

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Meta WhatsApp Configuration
ACCESS_TOKEN=your_meta_access_token
PHONE_NUMBER_ID=your_phone_number_id
WABA_ID=your_waba_id
VERIFY_TOKEN=your_verify_token

# Supabase PostgreSQL
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Server Configuration
PORT=10000
HOST=0.0.0.0
ENVIRONMENT=development
```

### Getting Meta Credentials

1. **Access Token**: `developers.facebook.com` → Apps → WhatsApp → Configuration → Access Tokens
2. **Phone Number ID**: WhatsApp → Manage Phone Numbers → Use the ID from your number
3. **WABA ID**: WhatsApp → WhatsApp Business Accounts → Your WABA ID
4. **Verify Token**: Generate any random string (e.g., `secure_token_123`)

### Getting Supabase Credentials

1. Create account at **supabase.com**
2. Create new project
3. Go to **Settings** → **API**:
   - `supabase_url` → SUPABASE_URL
   - `anon public` → SUPABASE_KEY
   - `service_role secret` → SUPABASE_SERVICE_KEY

### Getting Gemini API Key

1. Go to **ai.google.dev**
2. Click **Get API Key**
3. Create new API key for your project
4. Copy and paste into .env

---

## 🔌 API Endpoints

All endpoints are documented in **Swagger UI** at `http://localhost:10000/docs`

### Message Sending

#### 1. Send Text Message
```
POST /send-message
Content-Type: application/json

{
  "phone": "1234567890",
  "message": "Hello! How can we help you today?"
}

Response:
{
  "success": true,
  "message_id": "wamid.xxxxx",
  "stored_in_supabase": true,
  "status": "sent"
}
```

#### 2. Send Media
```
POST /send-media
Content-Type: application/json

{
  "phone": "1234567890",
  "media_url": "https://example.com/image.jpg",
  "media_type": "image",
  "caption": "Check out this image!"
}

Response:
{
  "success": true,
  "message_id": "wamid.xxxxx",
  "stored_in_supabase": true,
  "media_type": "image"
}
```

Supported media types: `image`, `video`, `audio`, `document`

#### 3. Send Template
```
POST /send-template
Content-Type: application/json

{
  "phone": "1234567890",
  "template_name": "hello_world",
  "language": "en",
  "parameters": ["John", "Smith"]
}

Response:
{
  "success": true,
  "message_id": "wamid.xxxxx",
  "stored_in_supabase": true,
  "template_used": "hello_world"
}
```

#### 4. Create Template (Manual Mode)
```
POST /template/create
Content-Type: application/json

{
  "name": "welcome_template",
  "category": "UTILITY",
  "language": "en",
  "mode": "manual",
  "body_text": "Hello {{1}}, welcome to {{2}}!",
  "footer_text": "Powered by AI"
}

Response:
{
  "success": true,
  "template_name": "welcome_template",
  "status": "PENDING_REVIEW",
  "mode": "manual"
}
```

#### 5. Create Template (AI Mode)
```
POST /template/create
Content-Type: application/json

{
  "name": "ai_generated_template",
  "category": "MARKETING",
  "language": "en",
  "mode": "ai",
  "context": "Product promotion for new smartphone launch"
}

Response:
{
  "success": true,
  "template_name": "ai_generated_template",
  "status": "PENDING_REVIEW",
  "mode": "ai",
  "generated_body": "Check out our latest smartphone... [AI generated content]"
}
```

#### 6. Send Template (Existing Template)
```
POST /template/send
Content-Type: application/json

{
  "phone": "1234567890",
  "template_name": "welcome_template",
  "language": "en",
  "parameters": ["Alice"]
}

Response:
{
  "success": true,
  "message_id": "wamid.xxxxx",
  "stored_in_supabase": true
}
```

### Message History & Retrieval

#### 7. Get Recent Messages
```
GET /recent-messages?phone=1234567890&limit=20

Response:
{
  "phone": "1234567890",
  "total_messages": 45,
  "messages": [
    {
      "id": "msg_xxx",
      "message": "Thanks for your order!",
      "sender": "Agent",
      "direction": "outbound",
      "status": "delivered",
      "timestamp": "2024-02-20T10:30:00Z"
    }
  ]
}
```

#### 8. Get Conversation
```
GET /get-conversation?phone=1234567890

Response:
{
  "phone": "1234567890",
  "customer_name": "John Doe",
  "status": "INTERESTED",
  "total_messages": 45,
  "conversation_thread": [...]
}
```

#### 9. Get All Leads
```
GET /leads?limit=50&offset=0

Response:
{
  "total_leads": 128,
  "leads": [...]
}
```

### Webhook

#### 10. Incoming Message Webhook
```
POST /webhook
```

Meta sends incoming messages here automatically.

---

## 📊 Database Schema

### Messages Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) NOT NULL,
    message TEXT,
    sender VARCHAR(50),
    direction VARCHAR(10),
    status VARCHAR(20),
    message_id VARCHAR(100) UNIQUE,
    media_url TEXT,
    media_type VARCHAR(20),
    caption TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Conversations Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) UNIQUE NOT NULL,
    lead_id UUID REFERENCES leads(id),
    total_messages INT DEFAULT 1,
    last_message TEXT,
    last_message_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Leads Table
```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    status VARCHAR(20),
    first_contact TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 💬 Message Flow

### Outbound Flow
1. POST /send-message
2. Validate request
3. Check/Create lead in Supabase
4. Send to WhatsApp API (Meta)
5. Receive message_id
6. Store in messages table
7. Update conversations
8. Return stored_in_supabase: true

### Inbound Flow
1. Customer sends WhatsApp message
2. Meta sends webhook to /webhook
3. Verify webhook signature
4. Extract message data
5. Check/Create lead
6. Store message in messages table
7. Update conversations
8. Return 200 OK to Meta

---

## 🔗 Webhook Integration

### Setup Steps

#### 1. Deploy Your App
Get a public URL for your app using:
- **Render.com** (free tier)
- **Railway.app** (free tier)
- **ngrok** (for local testing)

#### 2. Register Webhook in Meta

1. Go to **Meta App Dashboard** → WhatsApp → Configuration
2. Click **Edit** under Webhook URL
3. Enter:
   - **Callback URL**: `https://your-domain.com/webhook`
   - **Verify Token**: (must match VERIFY_TOKEN in .env)
4. Subscribe to webhook fields:
   - `messages`
   - `message_status_updates`
   - `message_template_status_update`

#### 3. Test Webhook
```bash
python webhook_debug.py
```

---

## 🧪 Testing

### Run Tests

```bash
# Test all endpoints
python complete_api_test.py

# Test send message
python test_send_message.py

# Test templates
python test_template_manual.py

# Test webhook
python webhook_debug.py
```

### Manual Testing (Swagger UI)

1. Navigate to **http://localhost:10000/docs**
2. Click any endpoint
3. Click **Try it out**
4. Fill parameters and execute

---

## 🚀 Deployment

### Option 1: Deploy to Render.com (Recommended)

```bash
# 1. Push to GitHub
git add .
git commit -m "Initial commit"
git push -u origin main

# 2. Go to render.com
# 3. Create Web Service
# 4. Connect GitHub repo
# 5. Set Build Command: pip install -r requirements.txt
# 6. Set Start Command: uvicorn main:app --host 0.0.0.0 --port 10000
# 7. Add all .env variables
# 8. Deploy!
```

Your URL: `https://receivemessage.onrender.com`

### Option 2: Deploy to Railway

1. Connect repo to Railway
2. Add environment variables
3. Deploy automatically

### Option 3: Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
```

---

## 🐛 Troubleshooting

### Webhook Not Receiving Messages

1. Verify webhook URL is registered in Meta Business Manager
2. Check VERIFY_TOKEN matches in .env and Meta settings
3. Run `python webhook_debug.py`
4. Check server logs

### Messages Not Storing to Supabase

1. Verify SUPABASE_URL and SUPABASE_KEY are correct
2. Check that database tables exist
3. Verify network connectivity

### Gemini API Not Working

1. Verify GEMINI_API_KEY is correct
2. Check quota limits on Google Cloud
3. Test at **ai.google.dev**

---

## 📁 File Structure

```
receivemessage/
├── main.py                        # FastAPI application
├── models.py                      # Pydantic models
├── utils.py                       # Helper functions
├── config.py                      # Configuration
├── requirements.txt               # Dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Git rules
├── SUPABASE_COMPLETE_SETUP.sql   # Database schema
├── README.md                      # This file
└── tests/
    ├── test_send_message.py
    ├── test_template_manual.py
    └── webhook_debug.py
```

---

## 🔐 Security

1. Never commit `.env` file
2. Use `.env.example` as template
3. Rotate tokens regularly
4. Verify webhook signatures
5. Use HTTPS in production
6. Restrict database access

---

## 📞 Support & Links

- **FastAPI**: https://fastapi.tiangolo.com/
- **Supabase**: https://supabase.com/docs
- **Meta WhatsApp**: https://developers.facebook.com/docs/whatsapp/
- **Gemini API**: https://ai.google.dev/

---

## 📝 License

MIT License

---

## 🎯 Next Steps

1. Setup environment variables in `.env`
2. Create Supabase tables using SQL migration
3. Start server: `python main.py`
4. Access API docs: `http://localhost:10000/docs`
5. Register webhook in Meta Business Manager
6. Deploy to production
7. Test with real WhatsApp messages

---

**Version**: 4.0 | **Status**: ✅ Production Ready | **Last Updated**: February 2026
