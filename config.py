"""
Configuration and Environment Variables
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============ SUPABASE CONFIG ============
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_KEY)

# ============ WHATSAPP CONFIG ============
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "verify_token_123")

# ============ GEMINI CONFIG ============
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_READY = False  # Set to True after Gemini initialization

# ============ DEPLOYMENT CONFIG ============
RENDER_WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://receivemessage.onrender.com/webhook")
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# ============ APP CONFIG ============
APP_VERSION = "4.0.0"
APP_TITLE = "Multi-Channel Communication API"
APP_DESCRIPTION = "WhatsApp Business API with Lead Management and AI Auto-Replies"
