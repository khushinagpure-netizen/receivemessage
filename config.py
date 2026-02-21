"""
Configuration and Environment Variables
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file explicitly
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

print(f"🔍 Loading .env from: {env_path}")
print(f"✓ .env exists: {env_path.exists()}")

# ============ SUPABASE CONFIG ============
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_KEY)

print(f"✓ SUPABASE_URL loaded: {'✅' if SUPABASE_URL else '❌'}")
print(f"✓ SUPABASE_KEY loaded: {'✅' if SUPABASE_KEY else '❌'}")

# ============ WHATSAPP CONFIG ============
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
WABA_ID = os.getenv("WABA_ID", "")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "verify_token_123")

print(f"✓ ACCESS_TOKEN loaded: {'✅' if ACCESS_TOKEN else '❌'}")
print(f"✓ PHONE_NUMBER_ID loaded: {'✅' if PHONE_NUMBER_ID else '❌'}")
print(f"✓ WABA_ID loaded: {'✅' if WABA_ID else '❌'}")

# ============ GEMINI CONFIG ============
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_READY = False  # Will be set to True after successful initialization in startup event

# Dictionary to track service readiness (mutable global state)
SERVICE_STATUS = {
    "gemini": False,
    "whatsapp": bool(ACCESS_TOKEN and PHONE_NUMBER_ID and WABA_ID),
    "database": bool(os.getenv("SUPABASE_URL", ""))
}

# ============ DEPLOYMENT CONFIG ============
RENDER_WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://receivemessage.onrender.com/webhook")
PORT = int(os.getenv("API_PORT") or os.getenv("PORT") or 8000)
HOST = os.getenv("API_HOST") or os.getenv("HOST") or "0.0.0.0"

# ============ APP CONFIG ============
APP_VERSION = "4.0.0"
APP_TITLE = "Multi-Channel Communication API"
APP_DESCRIPTION = "WhatsApp Business API with Lead Management and AI Auto-Replies"
