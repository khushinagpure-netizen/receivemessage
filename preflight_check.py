#!/usr/bin/env python3
"""
Pre-flight checklist validator for Katyayani Organics WhatsApp Bot
Runs automatic checks before server startup
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def check_env_file(self):
        """Verify .env file exists and has required variables"""
        logger.info("📝 Checking environment configuration...")
        
        if not Path('.env').exists():
            self.errors.append("❌ .env file not found. Create it with environment variables.")
            return False
        
        load_dotenv()
        
        required_vars = {
            'GEMINI_API_KEY': 'Google Gemini API Key',
            'SUPABASE_URL': 'Supabase Database URL',
            'SUPABASE_SERVICE_KEY': 'Supabase Service Role Key',
            'ACCESS_TOKEN': 'WhatsApp Business API Token',
            'PHONE_NUMBER_ID': 'WhatsApp Business Phone Number ID',
            'WABA_ID': 'WhatsApp Business Account ID',
            'VERIFY_TOKEN': 'Webhook Verification Token'
        }
        
        all_present = True
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value or value.startswith('your_'):
                self.errors.append(f"❌ {var}: {description} - Not configured")
                all_present = False
            else:
                logger.info(f"   ✓ {var}: Configured")
                self.success_count += 1
        
        return all_present
    
    def check_dependencies(self):
        """Verify all required packages are installed"""
        logger.info("📦 Checking dependencies...")
        
        required_packages = {
            'fastapi': 'Web Framework',
            'google.generativeai': 'Gemini AI',
            'supabase': 'Database Client',
            'beautifulsoup4': 'Web Scraper',
            'pydantic': 'Data Validation',
            'requests': 'HTTP Client',
            'uvicorn': 'Server'
        }
        
        all_installed = True
        for package, description in required_packages.items():
            try:
                __import__(package)
                logger.info(f"   ✓ {package}: {description}")
                self.success_count += 1
            except ImportError:
                self.errors.append(f"❌ {package}: {description} - Not installed")
                all_installed = False
        
        return all_installed
    
    def check_files(self):
        """Verify essential files exist"""
        logger.info("📂 Checking file structure...")
        
        required_files = [
            'main.py',
            'continuous_chat.py',
            'config.py',
            'models.py',
            'utils.py',
            'requirements.txt',
            'katyayani_products.json'
        ]
        
        all_present = True
        for filename in required_files:
            if Path(filename).exists():
                logger.info(f"   ✓ {filename}")
                self.success_count += 1
            else:
                self.warnings.append(f"⚠️ {filename}: Not found (may be auto-generated)")
                all_present = False
        
        return all_present
    
    def check_python_version(self):
        """Verify Python version"""
        logger.info("🐍 Checking Python version...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            logger.info(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
            self.success_count += 1
            return True
        else:
            self.errors.append(f"❌ Python 3.10+ required, found {version.major}.{version.minor}")
            return False
    
    def check_database_connection(self):
        """Test Supabase connection"""
        logger.info("🗄️  Testing database connection...")
        
        try:
            import supabase
            
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_SERVICE_KEY')
            
            if not url or not key:
                self.warnings.append("⚠️ Supabase credentials not fully configured (will try on startup)")
                return False
            
            client = supabase.create_client(url, key)
            
            # Try to check products table
            response = client.table('products').select('COUNT(*)').execute()
            logger.info("   ✓ Database connection successful")
            self.success_count += 1
            return True
            
        except Exception as e:
            self.warnings.append(f"⚠️ Database connection failed: {str(e)}")
            return False
    
    def check_gemini_api(self):
        """Test Gemini API connection"""
        logger.info("🤖 Testing Gemini API...")
        
        try:
            import google.generativeai as genai
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key or api_key.startswith('your_'):
                self.warnings.append("⚠️ Gemini API Key not configured")
                return False
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info("   ✓ Gemini API configured")
            self.success_count += 1
            return True
            
        except Exception as e:
            self.warnings.append(f"⚠️ Gemini API test failed: {str(e)}")
            return False
    
    def validate_all(self):
        """Run all validation checks"""
        logger.info("\n" + "="*60)
        logger.info("🔍 Katyayani Organics - Pre-flight Checklist")
        logger.info("="*60 + "\n")
        
        checks = [
            self.check_python_version,
            self.check_env_file,
            self.check_dependencies,
            self.check_files,
            self.check_database_connection,
            self.check_gemini_api
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                logger.error(f"Error during check: {e}")
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("📊 Summary")
        logger.info("="*60)
        logger.info(f"✓ Checks passed: {self.success_count}")
        
        if self.errors:
            logger.error(f"❌ Errors: {len(self.errors)}")
            for error in self.errors:
                logger.error(f"   {error}")
        
        if self.warnings:
            logger.warning(f"⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                logger.warning(f"   {warning}")
        
        logger.info("="*60 + "\n")
        
        # Return result
        if self.errors:
            logger.error("❌ Pre-flight check FAILED")
            logger.info("\nFix the errors above and try again.")
            return False
        else:
            logger.info("✅ Pre-flight check PASSED")
            logger.info("\n🚀 Ready to launch! Run: python main.py")
            return True

if __name__ == "__main__":
    validator = BotValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)
