# Complete Setup & Troubleshooting Guide

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Setup Environment Variables
Create/Update `.env` file with all required credentials:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# WhatsApp Business API
ACCESS_TOKEN=your-whatsapp-access-token
PHONE_NUMBER_ID=your-phone-number-id
VERIFY_TOKEN=verify_token

# Google Gemini AI
GEMINI_API_KEY=your-gemini-api-key

# API Configuration
API_PORT=10000
API_HOST=0.0.0.0
```

### Step 3: Setup Supabase Database
1. Go to your Supabase Project: https://app.supabase.com
2. Open **SQL Editor**
3. Paste the contents of `SUPABASE_COMPLETE_SETUP.sql`
4. Click **Run** to create all tables and views

### Step 4: Start the Server
```bash
python main.py
```

The server will start on: **http://localhost:10000**

---

## 📡 API Endpoints

### Health & Status
- `GET /` - API information
- `GET /status` - Server health check

### Message Operations
- `POST /send-message` - Send WhatsApp message
  ```json
  {
    "phone": "919876543210",
    "message": "Hello from API"
  }
  ```

- `POST /receive-simple` - Simulate receiving a message
  ```json
  {
    "phone": "919876543210",
    "message_text": "Hello from customer",
    "name": "Customer Name"
  }
  ```

### Analytics & Reporting
- `GET /analytics` - Get all analytics
- `GET /analytics?phone=919876543210` - Get analytics for specific phone

### Conversation Management
- `GET /get-conversation?phone=919876543210` - Get conversation history
- `GET /recent-messages` - Get recent messages across all conversations

### Lead Management
- `GET /leads` - List all leads
- `GET /leads?limit=10` - Get leads with limit

---

## 🐛 Troubleshooting

### Issue: Analytics showing all zeros
**Solution:** 
- Send messages via `/receive-simple` endpoint (doesn't require WhatsApp credentials)
- Or ensure `/send-message` is working (requires valid WhatsApp tokens)
- Messages must be stored in database before analytics work

### Issue: WhatsApp API returns 401 (Invalid Token)
**Solution:**
- Verify ACCESS_TOKEN in .env is correct and not expired
- Check PHONE_NUMBER_ID is correct
- Generate new token from Meta Business Suite if needed
- Test manually with curl to verify credentials work

### Issue: Supabase connection fails
**Solution:**
- Verify SUPABASE_URL format: `https://project-ref.supabase.co`
- Check SUPABASE_ANON_KEY is not empty
- Run the SQL setup script in Supabase SQL Editor
- Ensure tables exist: `leads`, `conversations`, `messages`

### Issue: "Port 10000 already in use"
**Solution:**
```powershell
# Windows
taskkill /F /IM python.exe

# macOS/Linux
killall python
```

### Issue: Gemini API not working
**Solution:**
- Get free API key from: https://ai.google.dev/
- Add to .env: `GEMINI_API_KEY=your-key`
- Restart server

---

## 🔄 Test Workflow

### 1. Test Without WhatsApp API (Recommended for Development)
```bash
# Run the server
python main.py

# In another terminal, run the test script
python complete_api_test.py
```

### 2. Simulate Receiving a Message
```curl
curl -X POST "http://localhost:10000/receive-simple" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "917974734809",
    "message_text": "Hello, this is a test",
    "name": "Test User"
  }'
```

### 3. Check Analytics
```curl
curl "http://localhost:10000/analytics?phone=917974734809"
```

Expected Response:
```json
{
  "status": "success",
  "phone": "917974734809",
  "stats": {
    "total_messages": 2,
    "total_sent": 1,
    "total_received": 1,
    "delivery_rate": 100.0,
    "read_rate": 0.0,
    "failed_count": 0
  },
  "period": "all_time",
  "timestamp": "2026-02-19T17:00:00.000000"
}
```

---

## 📊 Database Schema

### Key Tables
- **leads** - Customer contacts
- **conversations** - Message threads
- **messages** - Individual messages
- **api_logs** - API call history
- **sentiment_tracking** - Message sentiment analysis

### Analytics Views
- `message_stats_view` - Message statistics by phone
- `conversation_stats_view` - Conversation metrics
- `recent_messages_view` - Recent activity
- `lead_activity_view` - Lead engagement metrics

---

## 🔐 Security Notes

### For Development
- All endpoints are publicly accessible (no authentication required)
- Perfect for testing and development

### For Production
- Enable Row-Level Security (RLS) in Supabase
- Implement JWT authentication
- Use service role key only in server
- Restrict API access with API keys

Uncomment the RLS policies in `SUPABASE_COMPLETE_SETUP.sql` for production.

---

## 📝 File Structure

```
receivemessage/
├── main.py                          # FastAPI application
├── models.py                        # Pydantic request/response models
├── utils.py                         # Helper functions
├── config.py                        # Environment configuration
├── .env                             # Environment variables
├── requirements.txt                 # Python dependencies
├── SUPABASE_COMPLETE_SETUP.sql      # Database setup script
├── complete_api_test.py             # Comprehensive test suite
├── send_receive_simple.py           # Simple client for testing
└── docs/
    ├── FEATURES_GUIDE.md            # Complete feature documentation
    ├── IMPLEMENTATION_SUMMARY.md    # Technical implementation details
    └── TROUBLESHOOTING.md           # Troubleshooting guide
```

---

## ✅ Verification Checklist

- [ ] `.env` file created with all required variables
- [ ] Supabase database setup SQL has been run
- [ ] Server starts successfully: `python main.py`
- [ ] API responds to `/status` endpoint
- [ ] Can POST to `/receive-simple` endpoint
- [ ] Analytics endpoint returns data
- [ ] Interactive docs available at `/docs`

---

## 📞 Support

For detailed feature documentation, see:
- `FEATURES_GUIDE.md` - Complete API feature reference
- `IMPLEMENTATION_SUMMARY.md` - Technical architecture details
- `TROUBLESHOOTING.md` - Detailed troubleshooting guide

## 🎯 Next Steps

1. Complete the setup steps above
2. Run `python complete_api_test.py` to test all endpoints
3. Use `/docs` for interactive API documentation
4. Check `FEATURES_GUIDE.md` for advanced usage

Happy coding! 🚀
