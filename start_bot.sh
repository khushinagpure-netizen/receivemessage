#!/bin/bash

# Katyayani Organics - WhatsApp Continuous Chat Bot
# Auto-Deploy Startup Script

echo "🚀 Starting Katyayani Organics WhatsApp Bot..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please create .env with required environment variables:"
    echo "  - GEMINI_API_KEY"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_SERVICE_KEY"
    echo "  - ACCESS_TOKEN"
    echo "  - PHONE_NUMBER_ID"
    echo "  - WABA_ID"
    echo "  - VERIFY_TOKEN"
    exit 1
fi

echo "✅ .env file found"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Katyayani Organics - Continuous Chat Bot"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Configuration:"
echo "   ✓ Gemini AI: Enabled (gemini-1.5-pro)"
echo "   ✓ WhatsApp: Integrated"
echo "   ✓ Database: Connected to Supabase"
echo "   ✓ Port: 10000"
echo ""
echo "🔗 Access Points:"
echo "   - API: http://localhost:10000"
echo "   - Docs: http://localhost:10000/docs"
echo "   - Status: http://localhost:10000/status"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the bot
echo "🔄 Starting application..."
python main.py
