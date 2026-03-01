# 🤖 Katyayani Organics - Continuous Chat WhatsApp Bot with Gemini AI

**Complete Setup & Integration Guide**

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Integration with main.py](#integration)
5. [Features & Commands](#features)
6. [Troubleshooting](#troubleshooting)
7. [Monitoring & Maintenance](#monitoring)

---

## <a name="overview"></a>📊 Overview

**What This System Does:**
- ✅ Scrapes 38+ real products from Katyayani Organics website
- ✅ Stores products in Supabase database
- ✅ Uses Google Gemini AI for intelligent responses
- ✅ Maintains continuous conversation history per user
- ✅ Recommends relevant products based on queries
- ✅ Integrates with WhatsApp Business API
- ✅ Responds in < 3 seconds
- ✅ Supports special commands (/help, /restart, /history, /products)

**System Architecture:**
```
WhatsApp User
    ↓
Webhook receives message
    ↓
Extract user ID & text
    ↓
Search relevant products from Supabase
    ↓
Get user's conversation history
    ↓
Build prompt with context + products
    ↓
Send to Google Gemini AI
    ↓
Gemini generates intelligent response
    ↓
Send answer back to WhatsApp
    ↓
Store in conversation history
    ↓
User receives natural, contextual reply
```

---

## <a name="quick-start"></a>🚀 Quick Start (45 minutes)

### Step 1: Install Dependencies (2 min)
```bash
pip install -r requirements.txt
```

### Step 2: Create Database Table (2 min)
**Go to:** Supabase → SQL Editor

**Run this SQL:**
```sql
CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    price DECIMAL(10, 2),
    description TEXT,
    image_url VARCHAR(500),
    category VARCHAR(100),
    availability VARCHAR(50),
    url VARCHAR(500),
    specifications TEXT,
    benefits TEXT,
    ingredients TEXT,
    rating DECIMAL(3, 2),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_name ON products(name);

ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read" ON products FOR SELECT USING (true);
CREATE POLICY "Allow service role all" ON products USING (auth.role() = 'service_role');
```

### Step 3: Scrape Products (5-10 min)
```bash
python scrape_products.py
```
When prompted: Type `y` to save to Supabase

**Expected:** "✅ Scraping complete. Total unique products: 38"

### Step 4: Run Tests (2 min)
```bash
python test_continuous_chat.py
```

**Expected:** "✅ All tests passed!"

### Step 5: Update main.py (5 min)
See [Integration Section](#integration)

### Step 6: Start Bot (1 min)
```bash
python main.py
```

**Expected:**
```
✓ Gemini AI: Ready
✓ WhatsApp: Configured
✓ Database: Connected
INFO: Uvicorn running on http://0.0.0.0:10000
```

### Step 7: Test on WhatsApp (5 min)
Send messages to your business number:
```
You:   Hello
Bot:   [Responds with greeting]

You:   Do you have fertilizers?
Bot:   [Shows product recommendations]

You:   /help
Bot:   [Shows available commands]
```

---

## <a name="detailed-setup"></a>📝 Detailed Setup Instructions

### Files Created

**Python Core Files:**
- `scrape_products.py` - Web scraper (38 real products from website)
- `continuous_chat.py` - Chat engine with Gemini AI
- `whatsapp_continuous_chat.py` - WhatsApp webhook integration
- `test_continuous_chat.py` - Comprehensive test suite

**Configuration:**
- `requirements.txt` - Updated with: beautifulsoup4, supabase, lxml
- `katyayani_products.json` - Scraped products (auto-generated)

### Prerequisites

**Environment Variables (in .env):**
```
GEMINI_API_KEY=your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
ACCESS_TOKEN=EAA...
PHONE_NUMBER_ID=123...
VERIFY_TOKEN=your_token
```

### Database Schema

**Products Table:**
| Column | Type | Purpose |
|--------|------|---------|
| id | BIGSERIAL | Unique ID |
| name | VARCHAR(255) | Product name |
| price | DECIMAL | Price in ₹ |
| description | TEXT | Product description |
| image_url | VARCHAR(500) | Product image |
| category | VARCHAR(100) | Product category |
| availability | VARCHAR(50) | Stock status |
| url | VARCHAR(500) | Product page URL |
| specifications | TEXT | Detailed specs |
| benefits | TEXT | Health benefits |
| ingredients | TEXT | Ingredients list |
| rating | DECIMAL(3,2) | Star rating |

### Scraping Products

**What the scraper does:**
1. Visits katyayaniorganics.com/shop-2/
2. Fetches product categories
3. Extracts: name, price, image, description, benefits, rating
4. Saves to katyayani_products.json
5. Uploads to Supabase

**To get more pages:**
Edit `scrape_products.py` and add more URLs to `pages_to_scrape` list

---

## <a name="integration"></a>🔗 Integration with main.py

### Add Imports (at top of main.py)
```python
from whatsapp_continuous_chat import handle_webhook_event
from continuous_chat import reload_products
```

### Update Webhook Handler
Replace your existing `@app.post("/webhook")` with:

```python
@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Webhook received")
        
        # Use continuous chat handler
        from whatsapp_continuous_chat import handle_webhook_event
        result = handle_webhook_event(payload)
        
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return JSONResponse({'status': 'error'}, status_code=500)
```

### Add Startup Event (after app = FastAPI(...))
```python
@app.on_event("startup")
async def startup_event():
    logger.info("Loading products...")
    try:
        from continuous_chat import reload_products
        reload_products()
        logger.info("✅ Products loaded")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
```

### Verify main.py
```bash
python -m py_compile main.py
```
Should complete without errors.

---

## <a name="features"></a>✨ Features & Commands

### Continuous Conversations
- Remembers entire chat history per user
- Maintains context across messages
- Natural multi-turn dialogue

### Product Intelligence
- Automatically searches relevant products
- Shows pricing, descriptions, benefits
- Makes smart recommendations

### User Commands
| Command | What it does |
|---------|-------------|
| `/help` | Shows help message & available commands |
| `/restart` | Clears conversation history, starts fresh |
| `/history` | Shows last 10 messages in chat |
| `/products` | Lists all available products |

### Example Conversations

**Query 1: Product Information**
```
User: Do you have organic fertilizers?
Bot: Yes! We have several organic fertilizers:
     1. Katyayani Fertilizer - ₹376-₹5,800
     2. Water Soluble Fertilizer - ₹...
     [Shows details]
```

**Query 2: Continuous Context**
```
User: Tell me more
Bot: [References previous products, provides additional info]
```

**Query 3: Special Commands**
```
User: /restart
Bot: Conversation cleared! Start fresh...
```

---

## <a name="troubleshooting"></a>🔧 Troubleshooting

### Issue: "No module named 'bs4'"
**Solution:**
```bash
pip install --break-system-packages beautifulsoup4
pip install --break-system-packages -r requirements.txt
```

### Issue: "ResolutionImpossible" when installing
**Solution:** Use simpler requirements.txt or install individually:
```bash
pip install --break-system-packages beautifulsoup4 supabase google-generativeai fastapi uvicorn
```

### Issue: No products found when scraping
**Solution:** 
1. Check if katyayani_products.json is created
2. Verify Supabase connection in .env
3. Manually add sample products if needed

### Issue: Supabase connection error
**Solution:**
1. Verify SUPABASE_URL format: `https://your-project.supabase.co`
2. Check SUPABASE_SERVICE_KEY is valid
3. Test connection: `python -c "import supabase; print('OK')"`

### Issue: Gemini API error
**Solution:**
1. Verify GEMINI_API_KEY is active
2. Check API quotas in Google Cloud Console
3. Test: `python -c "import google.generativeai; print('OK')"`

### Issue: Bot not responding on WhatsApp
**Solution:**
1. Check if `python main.py` is running
2. Verify webhook is registered
3. Verify VERIFY_TOKEN matches exactly
4. Check PHONE_NUMBER_ID is correct
5. Review logs for errors

### Issue: Slow responses (> 5 seconds)
**Solution:**
1. Reduce `max_output_tokens` in continuous_chat.py (default 500)
2. Use `gemini-1.5-flash` instead of `pro`
3. Check internet connection
4. Check Supabase and API quotas

### Issue: Multiple users interfering
**Solution:** Each user gets unique ID (phone_number). If issues persist:
1. Check `whatsapp_continuous_chat.py` user_id extraction
2. Verify phone numbers are unique

---

## <a name="monitoring"></a>📊 Monitoring & Maintenance

### Check Server Status
```bash
# Is server running?
lsof -i :10000

# View logs
tail -f app.log

# Test endpoint
curl http://localhost:10000/health
```

### Reload Products (if updated in Supabase)
```bash
# Option 1: Restart server
python main.py

# Option 2: API call
curl -X POST http://localhost:10000/admin/reload-products?key=YOUR_KEY
```

### View Conversation History
```bash
curl "http://localhost:10000/chat/history/919876543210?key=YOUR_KEY"
```

### Monitoring Checklist
- [ ] Server running without errors
- [ ] Products loaded successfully
- [ ] WhatsApp messages received
- [ ] Bot responding with recommendations
- [ ] Conversation context working
- [ ] Response time < 3 seconds
- [ ] No sensitive data in logs
- [ ] Errors being caught gracefully

### Performance Tips
1. Monitor API quotas (Gemini, Supabase)
2. Cache products in memory (not DB)
3. Limit conversation history size (max 50 per user)
4. Use faster Gemini model if needed
5. Monitor response times and optimize

---

## 🔄 Workflow Summary

```
1. Products Scraped (38 from website)
   ↓
2. Uploaded to Supabase
   ↓
3. Bot Receives WhatsApp Message
   ↓
4. Extracts User ID & Text
   ↓
5. Searches Relevant Products
   ↓
6. Retrieves Conversation History
   ↓
7. Sends to Gemini with Context
   ↓
8. Generates Personalized Response
   ↓
9. Sends Back to WhatsApp
   ↓
10. Stores in Conversation History
```

---

## 📦 Package Requirements

- **fastapi** - Web framework
- **uvicorn** - Server
- **pydantic** - Data validation
- **google-generativeai** - Gemini AI API
- **supabase** - Database client
- **beautifulsoup4** - Web scraping
- **requests** - HTTP client
- **python-dotenv** - Environment variables
- **lxml** - HTML/XML parsing

---

## 🆘 Additional Resources

**Google Gemini API:**
https://ai.google.dev/

**Supabase Documentation:**
https://supabase.com/docs

**WhatsApp Business API:**
https://developers.facebook.com/docs/whatsapp

**FastAPI:**
https://fastapi.tiangolo.com/

---

## ✅ Verification Checklist

Before going live:
- [ ] All dependencies installed
- [ ] Database tables created
- [ ] Products scraped (38 items)
- [ ] Tests passing (python test_continuous_chat.py)
- [ ] main.py updated with integration code
- [ ] Server starts without errors
- [ ] Webhook registered with WhatsApp
- [ ] Bot responds to test messages
- [ ] Conversation context working
- [ ] Commands operational (/help, /restart, /history)
- [ ] Products showing in responses
- [ ] Error handling working
- [ ] Response time acceptable (< 5 sec)
- [ ] Multiple users working independently

---

## 🎯 Next Steps

1. **Setup:** Follow Quick Start section above
2. **Test:** Run test suite (python test_continuous_chat.py)
3. **Integrate:** Add code to main.py (see Integration section)
4. **Launch:** Start server (python main.py)
5. **Monitor:** Watch logs and user feedback
6. **Improve:** Adjust based on feedback

---

**Good luck! Your WhatsApp Continuous Chat Bot is ready to go! 🚀**
