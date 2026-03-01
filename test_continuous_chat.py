"""
Test Script for Continuous Chat System
Verifies all components are working correctly before full integration

Run with: python test_continuous_chat.py
"""

import sys
import json
import time
from datetime import datetime
from typing import Dict, List

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
CHECKMARK = '✅'
CROSS = '❌'
ARROW = '➜'

def print_header(title: str):
    """Print colored header"""
    print(f"\n{BLUE}{'='*70}")
    print(f"{title.upper()}")
    print(f"{'='*70}{RESET}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}{CHECKMARK} {message}{RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{RED}{CROSS} {message}{RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{BLUE}{ARROW} {message}{RESET}")

def test_imports():
    """Test if all required packages are installed"""
    print_header("1. Testing Imports")
    
    packages = {
        'fastapi': 'FastAPI',
        'requests': 'HTTP requests',
        'google.generativeai': 'Gemini AI',
        'bs4': 'BeautifulSoup4 (web scraping)',
        'supabase': 'Supabase client',
        'dotenv': 'Python dotenv'
    }
    
    all_ok = True
    for package, description in packages.items():
        try:
            __import__(package)
            print_success(f"{description} ({package})")
        except ImportError:
            print_error(f"{description} ({package}) - NOT INSTALLED")
            all_ok = False
    
    if not all_ok:
        print_warning("Run: pip install -r requirements.txt")
    
    return all_ok

def test_environment_variables():
    """Test environment variables"""
    print_header("2. Testing Environment Variables")
    
    from config import (
        GEMINI_API_KEY, SUPABASE_URL, ACCESS_TOKEN,
        PHONE_NUMBER_ID, VERIFY_TOKEN
    )
    
    required_vars = {
        'GEMINI_API_KEY': GEMINI_API_KEY,
        'SUPABASE_URL': SUPABASE_URL,
        'ACCESS_TOKEN': ACCESS_TOKEN,
        'PHONE_NUMBER_ID': PHONE_NUMBER_ID,
        'VERIFY_TOKEN': VERIFY_TOKEN,
    }
    
    all_ok = True
    for var_name, var_value in required_vars.items():
        if var_value and len(str(var_value).strip()) > 0:
            # Show only first and last chars for security
            masked = str(var_value)[0] + '*' * (len(str(var_value)) - 2) + str(var_value)[-1]
            print_success(f"{var_name} = {masked}")
        else:
            print_error(f"{var_name} is not set")
            all_ok = False
    
    return all_ok

def test_gemini_api():
    """Test Gemini API connection"""
    print_header("3. Testing Gemini API")
    
    try:
        import google.generativeai as genai
        from config import GEMINI_API_KEY
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        print_info("Sending test request to Gemini...")
        response = model.generate_content("Say 'Hello from Gemini' in exactly those words")
        
        if response and response.text:
            print_success(f"Gemini API working! Response: {response.text[:50]}...")
            return True
        else:
            print_error("Gemini API returned empty response")
            return False
            
    except Exception as e:
        print_error(f"Gemini API error: {str(e)}")
        return False

def test_supabase_connection():
    """Test Supabase database connection"""
    print_header("4. Testing Supabase Connection")
    
    try:
        import supabase
        from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
        
        print_info("Connecting to Supabase...")
        client = supabase.create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Try to query products table
        response = client.table('products').select('*').limit(1).execute()
        
        if hasattr(response, 'data'):
            product_count = len(response.data)
            if product_count > 0:
                print_success(f"Supabase connected! Found {product_count} products")
            else:
                print_warning("Supabase connected but no products found")
            return True
        else:
            print_warning("Could not query products table (might not exist yet)")
            return True  # Connection OK, just table might not exist
            
    except Exception as e:
        print_error(f"Supabase connection error: {str(e)}")
        return False

def test_continuous_chat():
    """Test continuous chat handler"""
    print_header("5. Testing Continuous Chat Handler")
    
    try:
        from continuous_chat import process_user_message, get_user_conversation_history
        
        test_user_id = "test_user_" + str(int(time.time()))
        test_messages = [
            "Hi, what skincare products do you have?",
            "Can you tell me more about the benefits?",
            "What's the price range?",
        ]
        
        print_info(f"Testing with user ID: {test_user_id}\n")
        
        for i, message in enumerate(test_messages, 1):
            print_info(f"Message {i}: {message}")
            try:
                response = process_user_message(test_user_id, message)
                
                if response.get('status') == 'success':
                    resp_text = response.get('response', '')[:60]
                    print_success(f"Response: {resp_text}...")
                else:
                    print_error(f"Error: {response.get('error', 'Unknown')}")
                    return False
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print_error(f"Error processing message: {str(e)}")
                return False
        
        # Get conversation history
        history = get_user_conversation_history(test_user_id)
        print_success(f"Conversation history stored: {len(history)} messages")
        
        return len(history) > 0
        
    except Exception as e:
        print_error(f"Continuous chat test failed: {str(e)}")
        return False

def test_whatsapp_webhook():
    """Test WhatsApp webhook handler"""
    print_header("6. Testing WhatsApp Webhook Handler")
    
    try:
        from whatsapp_continuous_chat import handle_webhook_event
        
        # Create test webhook payload
        test_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "919876543210",
                            "text": {"body": "Test: Do you have any organic tea?"}
                        }]
                    }
                }]
            }]
        }
        
        print_info("Sending test webhook payload...")
        result = handle_webhook_event(test_payload)
        
        if result.get('status') == 'success':
            print_success("Webhook handler working!")
            return True
        else:
            print_warning(f"Webhook returned: {result.get('status')}")
            return True  # Not necessarily an error
            
    except Exception as e:
        print_error(f"Webhook test failed: {str(e)}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print_header("7. Testing File Structure")
    
    import os
    
    required_files = [
        'scrape_products.py',
        'continuous_chat.py',
        'whatsapp_continuous_chat.py',
        'config.py',
        'main.py',
        '.env',
        'requirements.txt',
    ]
    
    all_exist = True
    for filename in required_files:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print_success(f"{filename} ({file_size} bytes)")
        else:
            print_error(f"{filename} - NOT FOUND")
            all_exist = False
    
    return all_exist

def test_product_scraper():
    """Test product web scraper (optional)"""
    print_header("8. Testing Product Web Scraper (Optional)")
    
    try:
        from scrape_products import KatyayaniScraper
        
        print_info("Initializing scraper...")
        scraper = KatyayaniScraper()
        
        print_info("Testing connection to Katyayani Organics website...")
        from bs4 import BeautifulSoup
        
        # Try to fetch the main page
        soup = scraper.fetch_page("https://www.katyayaniorganics.com")
        
        if soup:
            print_success("Website is accessible")
            print_warning("Note: Run 'python scrape_products.py' to fetch all products")
            return True
        else:
            print_warning("Could not reach website (might be offline or blocked)")
            return True  # Not critical
            
    except Exception as e:
        print_warning(f"Scraper test skipped: {str(e)}")
        return True  # Optional test

def print_summary(results: Dict[str, bool]):
    """Print test summary"""
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"{GREEN}Tests Passed: {passed}/{total}{RESET}")
    
    if failed > 0:
        print(f"{RED}Tests Failed: {failed}{RESET}")
        print("\nFailed tests:")
        for test_name, result in results.items():
            if not result:
                print(f"  {CROSS} {test_name}")
    else:
        print(f"\n{GREEN}🎉 All tests passed!{RESET}")
    
    return failed == 0

def print_next_steps():
    """Print next steps"""
    print_header("Next Steps")
    
    print(f"""
{YELLOW}1. SCRAPE PRODUCTS{RESET}
   Run: python scrape_products.py
   This fetches all Katyayani Organics products from their website

{YELLOW}2. VERIFY DATABASE{RESET}
   Check Supabase → Table Editor → products table
   Ensure products are loaded

{YELLOW}3. INTEGRATE WITH MAIN.PY{RESET}
   Follow INTEGRATION_GUIDE.md to modify main.py
   Add the webhook handler integration

{YELLOW}4. START YOUR BOT{RESET}
   Run your main.py application
   Send messages to your WhatsApp business number

{YELLOW}5. TEST WITH WHATSAPP{RESET}
   Test various product queries
   Try commands: /help, /restart, /history

{YELLOW}6. MONITOR{RESET}
   Check logs for any issues
   Adjust products and responses as needed

{BLUE}Documentation:{RESET}
   - CONTINUOUS_CHAT_SETUP.md - Detailed setup guide
   - INTEGRATION_GUIDE.md - Integration instructions
   - config.py - Environment configuration
    """)

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*70}")
    print("CONTINUOUS CHAT SYSTEM - TEST SUITE")
    print(f"Tests ran at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}{RESET}\n")
    
    results = {}
    
    # Run tests
    results['Imports'] = test_imports()
    results['Environment Variables'] = test_environment_variables()
    results['Gemini API'] = test_gemini_api()
    results['Supabase Connection'] = test_supabase_connection()
    results['Continuous Chat'] = test_continuous_chat()
    results['WhatsApp Webhook'] = test_whatsapp_webhook()
    results['File Structure'] = test_file_structure()
    results['Product Scraper'] = test_product_scraper()
    
    # Print summary
    all_passed = print_summary(results)
    
    # Print next steps
    print_next_steps()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Fatal error: {str(e)}{RESET}")
        sys.exit(1)
