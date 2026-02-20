# Complete API Setup & Fix Guide

## Step 1: Update Supabase Database Schema

Run this SQL in your Supabase SQL Editor (go to SQL Editor in Supabase Dashboard):

```sql
-- Copy the contents from SUPABASE_FIX.sql and run it
```

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" (left sidebar)
4. Click "New Query"
5. Copy entire contents of `SUPABASE_FIX.sql`
6. Click "Run"
7. Wait for success message

**What this does:**
- Creates proper tables: `messages`, `conversations`, `leads`, `templates`, etc.
- Adds real-time subscriptions (Realtime)
- Creates performance indexes
- Sets up auto-update triggers for timestamps

## Step 2: Verify Supabase Configuration in `.env`

Make sure your `.env` file has:

```env
SUPABASE_URL=https://jpdgkorskxfmgkbdbaig.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Step 3: Check WhatsApp Configuration

Verify `.env` has correct WhatsApp credentials:

```env
ACCESS_TOKEN=EAA...  # Your Meta Access Token (from Business App)
PHONE_NUMBER_ID=1006033565923189  # Your WhatsApp Phone Number ID
WABA_ID=158485566934566  # Your WhatsApp Business Account ID
```

## Step 4: Restart API

```bash
# Kill any running processes
Ctrl+C

# Restart API
python main.py
```

## API Endpoints - Testing

### 1. Send Text Message ✅ (Should Work)
```bash
curl -X POST http://localhost:10000/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "7974734809",
    "message": "Hello! This is a test message"
  }'
```

### 2. List All Leads ✅ (Should Work)
```bash
curl http://localhost:10000/leads
```

### 3. Get Conversation History (Fixed)
```bash
curl "http://localhost:10000/get-conversation?phone=917974734809"
```

### 4. Get Recent Messages (Fixed)
```bash
curl http://localhost:10000/recent-messages?phone=917974734809
```

### 5. Get Analytics (Fixed)
```bash
curl "http://localhost:10000/analytics?phone=917974734809"
```

### 6. Send Media/Image
```bash
curl -X POST http://localhost:10000/send-media \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "7974734809",
    "media_url": "https://picsum.photos/400/300",
    "media_type": "image",
    "caption": "Test image"
  }'
```

### 7. Get Sentiment Analysis
```bash
curl "http://localhost:10000/sentiment?phone=917974734809"
```

### 8. Simulate Receive Message & Get AI Reply
```bash
curl -X POST http://localhost:10000/receive-simple \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "917974734809",
    "message_text": "What are your business hours?",
    "name": "Customer Name"
  }'
```

### 9. Create Lead
```bash
curl -X POST http://localhost:10000/leads/create \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "7974734809",
    "name": "John Doe"
  }'
```

### 10. Update Lead Status
```bash
curl -X POST http://localhost:10000/leads/status \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "7974734809",
    "status": "contacted"
  }'
```

### 11. Get Received Messages
```bash
curl http://localhost:10000/received-messages
```

### 12. Create Template
```bash
curl -X POST http://localhost:10000/create-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "greeting_template",
    "category": "MARKETING",
    "body": "Hello {{1}}, welcome to our business!"
  }'
```

### 13. Send Template Message
```bash
curl -X POST http://localhost:10000/send-template \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "7974734809",
    "template_id": "greeting_template",
    "variables": {"name": "John"}
  }'
```

### 14. Update Message Status
```bash
curl -X POST http://localhost:10000/message-status \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "wamid.xxx",
    "status": "delivered",
    "error_code": null,
    "error_message": null
  }'
```

## Real-Time Features

### Enable Real-Time Subscriptions

Your database now has real-time enabled. To subscribe to live updates in your frontend:

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Listen for new messages
const subscription = supabase
  .channel('messages')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'messages' },
    (payload) => {
      console.log('New message:', payload.new)
    }
  )
  .subscribe()

// Listen for lead updates
const leadSubscription = supabase
  .channel('leads')
  .on('postgres_changes',
    { event: '*', schema: 'public', table: 'leads' },
    (payload) => {
      console.log('Lead updated:', payload.new)
    }
  )
  .subscribe()
```

## Database Tables Created

### 1. `messages` (PRIMARY)
- Stores all sent/received messages
- Fields: `id`, `phone`, `message`, `direction` (inbound/outbound), `status`, `message_id`, `sender_name`, `sender_type` (customer/agent/system), `media_url`, `media_type`, `caption`, `sentiment`, `error_message`, `created_at`, `updated_at`
- Indexed by: `phone`, `status`, `direction`, `created_at`
- Real-time: ✅ Yes

### 2. `conversations` (GROUPED BY LEAD)
- Stores messages grouped by lead
- Same fields as messages plus `lead_id`
- Used for conversation threads
- Real-time: ✅ Yes

### 3. `leads` (CRM)
- Stores customer leads
- Fields: `id`, `phone` (unique), `name`, `email`, `status`, `notes`, `created_at`, `updated_at`
- Real-time: ✅ Yes

### 4. `templates`
- Stores WhatsApp message templates
- Fields: `id`, `template_name`, `category`, `status`, `language`, `body`, `footer`, `header_type`, `header_text`, `created_at`, `updated_at`

### 5. `api_logs`
- Stores all API calls for analytics
- Fields: `id`, `endpoint`, `method`, `phone`, `status_code`, `response_time_ms`, `error`, `created_at`

### 6. `sentiment_tracking`
- Stores sentiment analysis results
- Fields: `id`, `lead_id`, `phone`, `sentiment`, `confidence`, `message_content`, `created_at`

## Expected Behavior After Fix

✅ **Send Message**: Message stored in `messages` + `conversations` tables
✅ **Receive Message**: Message stored + AI reply generated + stored
✅ **Send Media**: Media URL + caption stored with direction/status
✅ **List Leads**: Returns all leads with metadata
✅ **Get Conversations**: Returns all messages for a phone
✅ **Analytics**: Calculates delivery rate, read rate, total messages
✅ **Sentiment**: Analyzes conversation sentiment
✅ **Real-Time**: All changes pushed to frontend via WebSocket
✅ **API Logs**: Every call logged for debugging

## Troubleshooting

### "Supabase not configured"
- Check `.env` has `SUPABASE_URL` and `SUPABASE_ANON_KEY`
- Restart the API with `python main.py`

### "Table 'messages' does not exist"
- Run `SUPABASE_FIX.sql` in Supabase SQL Editor
- Make sure you ran the complete script, not just parts

### "Failed to send media"
- Check media URL is publicly accessible (HTTPS)
- Check media is under 5MB
- Try with test URL: `https://picsum.photos/400/300`

### "WhatsApp API error"
- Verify `ACCESS_TOKEN` is valid (doesn't expire)
- Verify `PHONE_NUMBER_ID` is correct
- Check recipient is on WhatsApp

### Messages not storing in database
- Check Supabase connection in `.env`
- Check logs for SQL errors
- Verify tables were created: Go to Supabase Dashboard > Editor > Select table

## Database Optimization Tips

1. **Cleanup old data** (after 90 days):
```sql
DELETE FROM messages WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM conversations WHERE created_at < NOW() - INTERVAL '90 days';
```

2. **View analytics**:
```sql
SELECT phone, total_messages, total_sent, total_received 
FROM message_stats 
ORDER BY total_messages DESC;
```

3. **Get conversation summary**:
```sql
SELECT phone, message_count, unique_leads, last_updated 
FROM conversation_summary;
```

## Next Steps

1. ✅ Run Supabase SQL (`SUPABASE_FIX.sql`)
2. ✅ Replace `utils.py` with new version
3. ✅ Restart API (`python main.py`)
4. ✅ Test each endpoint with curl commands above
5. ✅ Check Supabase tables for data
6. ✅ Enable real-time in frontend

## Support

If API still fails:
1. Check logs in terminal (error messages)
2. Go to Supabase Dashboard > API > Logs
3. Verify `.env` credentials
4. Make sure WhatsApp token is not expired

Run this to see detailed logs:
```bash
python main.py  # Watch terminal for errors
```
