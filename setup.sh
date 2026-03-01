#!/bin/bash

# Katyayani Organics - Automated Setup Script
# This script sets up everything automatically

echo "🚀 Katyayani Organics - Automated Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track errors
ERRORS=0

# ============ STEP 1: Check Python ============
echo "📝 Step 1: Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# ============ STEP 2: Create Virtual Environment ============
echo ""
echo "📝 Step 2: Setting up Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# ============ STEP 3: Upgrade pip ============
echo ""
echo "📝 Step 3: Upgrading pip..."
pip install --quiet --upgrade pip setuptools wheel 2>/dev/null
echo -e "${GREEN}✓${NC} pip upgraded"

# ============ STEP 4: Install Dependencies ============
echo ""
echo "📝 Step 4: Installing Dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --quiet -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All dependencies installed"
    else
        echo -e "${RED}✗${NC} Failed to install dependencies"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "${RED}✗${NC} requirements.txt not found"
    ERRORS=$((ERRORS+1))
fi

# ============ STEP 5: Verify Environment Variables ============
echo ""
echo "📝 Step 5: Checking Environment Variables..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file found"
    
    # Check required variables
    REQUIRED_VARS=("GEMINI_API_KEY" "SUPABASE_URL" "SUPABASE_SERVICE_KEY" "ACCESS_TOKEN" "PHONE_NUMBER_ID" "WABA_ID" "VERIFY_TOKEN")
    
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            echo -e "${GREEN}  ✓${NC} $var configured"
        else
            echo -e "${YELLOW}  ⚠${NC} $var missing"
        fi
    done
else
    echo -e "${YELLOW}⚠${NC} .env file not found. Creating template..."
    cat > .env << 'EOF'
# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# WhatsApp API
ACCESS_TOKEN=EAA...your_token_here
PHONE_NUMBER_ID=your_phone_number_id
WABA_ID=your_waba_id
VERIFY_TOKEN=your_custom_verify_token

# Server
PORT=10000
HOST=0.0.0.0
EOF
    echo -e "${YELLOW}⚠${NC} Template .env created. Please填充 with real values."
fi

# ============ STEP 6: Check Database ============
echo ""
echo "📝 Step 6: Checking Database..."
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

try:
    import supabase
    print("✓ Supabase library available")
except ImportError:
    print("✗ Supabase library not found")

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if SUPABASE_URL and SUPABASE_KEY:
    print("✓ Supabase credentials found")
else:
    print("⚠ Supabase credentials incomplete")
EOF

# ============ STEP 7: Verify File Structure ============
echo ""
echo "📝 Step 7: Verifying File Structure..."
FILES=("main.py" "continuous_chat.py" "config.py" "models.py" "utils.py" "requirements.txt")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓${NC} $file"
    else
        echo -e "${RED}  ✗${NC} $file missing"
        ERRORS=$((ERRORS+1))
    fi
done

# ============ STEP 8: Syntax Check ============
echo ""
echo "📝 Step 8: Checking Python Syntax..."
for file in main.py continuous_chat.py config.py models.py utils.py; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${GREEN}  ✓${NC} $file syntax OK"
        else
            echo -e "${RED}  ✗${NC} $file has syntax errors"
            ERRORS=$((ERRORS+1))
        fi
    fi
done

# ============ STEP 9: Test Imports ============
echo ""
echo "📝 Step 9: Testing Critical Imports..."
python3 << 'EOF'
try:
    import fastapi
    print("✓ FastAPI")
except ImportError:
    print("✗ FastAPI")

try:
    import google.generativeai
    print("✓ Google Generative AI")
except ImportError:
    print("✗ Google Generative AI")

try:
    import supabase
    print("✓ Supabase")
except ImportError:
    print("✗ Supabase")

try:
    import bs4
    print("✓ BeautifulSoup")
except ImportError:
    print("✗ BeautifulSoup")
EOF

# ============ STEP 10: Summary ============
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Setup Complete!${NC}"
    echo ""
    echo "📊 Configured Services:"
    echo "   • Gemini AI: gemini-1.5-pro"
    echo "   • WhatsApp: Business API"
    echo "   • Database: Supabase"
    echo "   • Server: FastAPI on port 10000"
    echo ""
    echo "🚀 To start the bot, run:"
    echo "   python main.py"
    echo ""
    echo "📱 To test webhook, run:"
    echo "   python test_continuous_chat.py"
    echo ""
    echo "🌐 Access:"
    echo "   API: http://localhost:10000"
    echo "   Docs: http://localhost:10000/docs"
    echo "   Status: http://localhost:10000/status"
    echo ""
else
    echo -e "${RED}✗ Setup encountered $ERRORS errors${NC}"
    echo ""
    echo "Please fix the errors above and run again."
    echo ""
    exit 1
fi
