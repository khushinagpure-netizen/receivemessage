"""
Quick diagnostic script - Run this to check all systems
"""

import subprocess
import sys

def check_python():
    print("✓ Python version:", sys.version.split()[0])

def check_dependencies():
    """Check if all required packages are installed"""
    print("\nChecking dependencies...")
    
    required = ['fastapi', 'uvicorn', 'requests', 'pydantic', 'python-dotenv', 'google.generativeai']
    
    for package in required:
        try:
            __import__(package.replace('.', '_') if package == 'google.generativeai' else package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - MISSING (install with: pip install {package})")

def check_env():
    """Check if .env file exists and has required variables"""
    print("\nChecking environment variables...")
    
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        required_vars = {
            'SUPABASE_URL': 'Supabase project URL',
            'SUPABASE_ANON_KEY': 'Supabase anonymous key',
            'ACCESS_TOKEN': 'WhatsApp API token',
            'PHONE_NUMBER_ID': 'WhatsApp phone number ID',
            'GEMINI_API_KEY': 'Google Gemini API key'
        }
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # Show first 10 chars for security
                display = value[:10] + '...' if len(value) > 10 else value
                print(f"  ✓ {var}: {display}")
            else:
                print(f"  ✗ {var}: NOT SET ({description})")
    
    except Exception as e:
        print(f"  ✗ Error reading .env: {e}")

def check_database():
    """Check if database tables exist"""
    print("\nChecking Supabase database...")
    
    try:
        from config import SUPABASE_URL, SUPABASE_KEY
        import requests
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("  ✗ Supabase credentials not configured")
            return
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
        
        required_tables = ['leads', 'conversations', 'messages']
        
        for table in required_tables:
            try:
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/{table}?limit=0",
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  ✓ Table '{table}' exists")
                else:
                    print(f"  ✗ Table '{table}' - Error {response.status_code}")
            except Exception as e:
                print(f"  ✗ Table '{table}' - {str(e)}")
    
    except Exception as e:
        print(f"  ✗ Database check failed: {e}")

def main():
    print("=" * 60)
    print("Multi-Channel Communication API - System Diagnostics")
    print("=" * 60)
    
    check_python()
    check_dependencies()
    check_env()
    check_database()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("""
1. If dependencies are missing, run:
   pip install -r requirements.txt

2. If environment variables are missing, add them to .env file

3. If database tables don't exist, run in Supabase SQL Editor:
   - Open: SUPABASE_COMPLETE_SETUP.sql
   - Copy all content and paste in SQL Editor
   - Click Run

4. Start the server:
   python main.py

5. Test endpoints:
   python complete_api_test.py
    """)

if __name__ == "__main__":
    main()
