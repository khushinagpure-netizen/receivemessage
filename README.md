# Multi-Channel Communication API v4.0

WhatsApp Business API with Lead Management and Gemini AI Auto-Replies.

## Features

-  **WhatsApp Integration** - Send/receive messages via Meta Cloud API
-  **AI Auto-Replies** - Powered by Gemini 2.5 Pro
-  **Lead Management** - Track and manage leads in Supabase
-  **Conversation Tracking** - Store all conversations with message status
-  **Message Analytics** - Recent messages with delivery status
-  **Zero Authentication** - JWT disabled for development

## Quick Start

### 1. Setup Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Database

In [Supabase](https://supabase.com):

```bash
# Run SQL in Supabase SQL editor
cat supabase_setup.sql | psql <your-connection>
```

Or paste content from `supabase_setup.sql` into Supabase dashboard.

### 4. Configure WhatsApp

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create app → Add WhatsApp product
3. Get `PHONE_NUMBER_ID` and create Access Token
4. Update `.env` with your values
5. Set webhook URL to your domain + `/webhook`
6. Set Verify Token (any string, must match `.env`)

### 5. Start Server

```bash
# Development (with reload)
uvicorn main:app --reload

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

Server runs on `http://localhost:8000`

## API Endpoints

### WhatsApp Messaging

- **POST** `/send-message` - Send WhatsApp message
- **POST** `/webhook` - Receive WhatsApp messages (webhook)
- **POST** `/receive-simple` - Simulate receiving message

### Leads

- **POST** `/leads/create` - Create a lead
- **POST** `/leads/assign` - Assign lead to agent
- **POST** `/leads/status` - Update lead status
- **GET** `/leads` - List all leads

### Conversations

- **GET** `/get-conversation` - Get conversation history
- **GET** `/recent-messages` - Get recent sent/received messages with status

### Templates

- **POST** `/template/create` - Create message template
- **GET** `/templates` - List templates
- **POST** `/template/send` - Send from template

### Health

- **GET** `/` - API info
- **GET** `/status` - Health check

## Example Requests

### Send WhatsApp Message

```bash
curl -X POST "http://localhost:8000/send-message" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "1234567890",
    "message": "Hello! How can I help?"
  }'
```

### Receive Message (Test)

```bash
curl -X POST "http://localhost:8000/receive-simple" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "1234567890",
    "message_text": "I have a question",
    "name": "John"
  }'
```

### Create Lead

```bash
curl -X POST "http://localhost:8000/leads/create" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "1234567890",
    "name": "John Doe",
    "status": "new"
  }'
```

### Get Conversation

```bash
curl -X GET "http://localhost:8000/get-conversation?phone=1234567890"
```

### Get Recent Messages

```bash
curl -X GET "http://localhost:8000/recent-messages?limit=20"
```

## Deployment

### Render

1. Push to GitHub
2. Create new Web Service on Render
3. Connect your repo
4. Environment: Python 3.11
5. Build command: `pip install -r requirements.txt`
6. Start command: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
7. Add environment variables from `.env`
8. Deploy

### Railway

1. Connect repo to Railway
2. Add environment variables
3. Railway auto-detects Python
4. Deploy

### Docker

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Project Structure

```
.
├── main.py              # FastAPI app entry point
├── config.py            # Configuration & env vars
├── models.py            # Pydantic request/response models
├── utils.py             # Helper functions
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment file
├── .env                 # Your actual environment (git ignored)
├── supabase_setup.sql   # Database schema
└── venv/                # Virtual environment
```

## Troubleshooting

### WhatsApp messages not sending

- Check `ACCESS_TOKEN` and phone number format
- Verify webhook is receiving messages
- Check logs for API errors

### Gemini not generating replies

- Verify `GEMINI_API_KEY` is valid
- Check API quota at [aistudio.google.com](https://aistudio.google.com)
- Install: `pip install google-generativeai`

### Database not connecting

- Verify `SUPABASE_URL` and keys
- Run `supabase_setup.sql` to create tables
- Check Supabase project is active

## Support

For issues or questions:
1. Check logs: `docker logs <container>`
2. Test endpoint in Swagger: `/docs`
3. Verify `.env` values are correct
4. Check Supabase/Meta dashboards for errors

## License

MIT
