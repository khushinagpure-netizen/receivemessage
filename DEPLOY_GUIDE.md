# 🚀 Auto-Deployment Guide - Katyayani Organics WhatsApp Bot

This guide covers automatic deployment to production platforms.

## 📦 What's Included

- **Procfile** - Heroku deployment configuration
- **runtime.txt** - Python version specification
- **Dockerfile** - Container deployment
- **docker-compose.yml** - Local & cloud deployment
- **.github/workflows/deploy.yml** - GitHub Actions CI/CD
- **start_bot.sh** - Automated startup script

## 🌍 Deployment Options

### Option 1: Heroku (Simplest)

```bash
# 1. Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# 2. Login to Heroku
heroku login

# 3. Create app
heroku create katyayani-whatsapp-bot

# 4. Set environment variables
heroku config:set GEMINI_API_KEY=your_key
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_SERVICE_KEY=your_key
heroku config:set ACCESS_TOKEN=your_token
heroku config:set PHONE_NUMBER_ID=your_id
heroku config:set WABA_ID=your_id
heroku config:set VERIFY_TOKEN=your_token

# 5. Deploy
git push heroku main

# 6. Monitor logs
heroku logs --tail
```

### Option 2: Docker (Recommended)

```bash
# Build image
docker build -t katyayani-bot .

# Run container
docker run -p 10000:10000 \
  -e GEMINI_API_KEY=your_key \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_SERVICE_KEY=your_key \
  -e ACCESS_TOKEN=your_token \
  -e PHONE_NUMBER_ID=your_id \
  -e WABA_ID=your_id \
  -e VERIFY_TOKEN=your_token \
  katyayani-bot

# Or with docker-compose
docker-compose up -d
```

### Option 3: GitHub + Auto-Deploy

1. Push to GitHub repository
2. Add secrets to GitHub (Settings → Secrets)
3. GitHub Actions automatically tests & deploys
4. View deployment status in Actions tab

### Option 4: Local with Script

```bash
# Make script executable
chmod +x start_bot.sh

# Run bot
./start_bot.sh
```

### Option 5: AWS/GCP/Azure

```bash
# AWS Elastic Beanstalk
eb init
eb create katyayani-bot
eb deploy

# Google Cloud Run
gcloud run deploy katyayani-bot --source .

# Azure Container Instances
az containerapp create --name katyayani-bot --image katyayani-bot
```

## 🔐 Environment Variables Required

**Essential (.env):**
```
GEMINI_API_KEY=your_google_gemini_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
ACCESS_TOKEN=EAA...  (WhatsApp API token)
PHONE_NUMBER_ID=123... (Your business phone ID)
WABA_ID=123... (WhatsApp Business Account ID)
VERIFY_TOKEN=your_custom_token
```

## 🧪 Automated Testing

GitHub Actions automatically runs tests on every push:
- ✅ Syntax validation
- ✅ Imports check
- ✅ Dependencies verification
- ✅ Continuous Chat functionality

## 📊 Monitoring Deployment

**Check Service Status:**
```bash
curl http://your-bot-url/status
```

**View Logs:**
- Heroku: `heroku logs --tail`
- Docker: `docker logs katyayani-bot`
- Local: Check terminal output

**Health Check Endpoint:**
```
GET /status
```
Returns: ✓ Gemini AI, ✓ WhatsApp, ✓ Database status

## 🔄 Continuous Deployment Workflow

```
1. Push code to GitHub (main branch)
   ↓
2. GitHub Actions trigger automatically
   ↓
3. Tests run (syntax, imports, functionality)
   ↓
4. If all pass → Deploy to production
   ↓
5. Health checks verify deployment
   ↓
6. Logs available for monitoring
```

## 🛑 Rollback to Previous Version

```bash
# Heroku
git revert HEAD
git push heroku main

# Docker
docker pull katyayani-bot:previous
docker run katyayani-bot:previous
```

## 💡 Tips for Success

1. **Always test locally first** - Run `python test_continuous_chat.py`
2. **Use environment variables** - Never commit secrets to GitHub
3. **Monitor logs regularly** - Catch errors early
4. **Set up alerts** - Get notified of failures
5. **Backup database** - Supabase has auto-backup
6. **Version your API** - Keep backward compatibility

## ❌ Troubleshooting Deployment

**Issue: "ModuleNotFoundError"**
```bash
# Rebuild dependencies
pip install --break-system-packages -r requirements.txt
```

**Issue: "Port already in use"**
```bash
# Change port in main.py or use:
lsof -i :10000
kill -9 <PID>
```

**Issue: "Database connection error"**
1. Verify SUPABASE_URL and SUPABASE_SERVICE_KEY
2. Check Supabase dashboard for table creation
3. Test connection: `python -c "import supabase; print('OK')"`

**Issue: "Gemini API error"**
1. Verify GEMINI_API_KEY is valid
2. Check API quotas in Google Cloud Console
3. Ensure API is enabled

## 📱 Webhook Configuration (Critical!)

After deployment:

1. Go to WhatsApp Business Platform
2. Set Webhook URL to: `https://your-bot-url/webhook`
3. Verify Token: Use your `VERIFY_TOKEN` value
4. Subscribe to messages, message_status events

## ✅ Verify Deployment

```bash
# 1. Check if running
curl http://your-bot-url/status

# 2. Send test message to your WhatsApp number
# You should get an AI response within 3-5 seconds

# 3. Check logs for errors
# Should see: "✓ Incoming message stored" and "✓ AI response sent"
```

## 🎯 Next Steps

1. Deploy to production using any option above
2. Configure WhatsApp webhook with your bot URL
3. Send test messages
4. Monitor logs and refine responses
5. Scale as needed

---

**Questions or Issues?**
- Check DOCUMENTATION.md for API details
- Review logs for error messages
- Verify all environment variables are set
- Test locally before deploying
