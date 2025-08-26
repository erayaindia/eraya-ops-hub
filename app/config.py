"""
Configuration settings for the application
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from config folder
load_dotenv("config/.env")

# Supabase Configuration - AUTH/LOGIN Project (used by the app right now)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Supabase Configuration - SUPPORT Project (stored for later; NOT used yet)
SUPPORT_SUPABASE_URL = os.getenv("SUPPORT_SUPABASE_URL")
SUPPORT_SUPABASE_ANON_KEY = os.getenv("SUPPORT_SUPABASE_ANON_KEY")
SUPPORT_SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPPORT_SUPABASE_SERVICE_ROLE_KEY")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/eraya_ops.db")

# Application Configuration
APP_TITLE = "Eraya Style Order Processor"
APP_VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# File Upload Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_DIR = "uploads"
BASE_DIR = Path(".")

# Shopify Configuration
SHOPIFY_SHOP = os.getenv("SHOPIFY_SHOP", "")
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN", "")

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "noreply@yourdomain.com")

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
SESSION_EXPIRY_DAYS = int(os.getenv("SESSION_EXPIRY_DAYS", "7"))
REMEMBER_ME_DAYS = int(os.getenv("REMEMBER_ME_DAYS", "30"))

# Feature Flags
USE_JSON = os.getenv("USE_JSON", "false").lower() == "true"
ENABLE_WEBSOCKETS = os.getenv("ENABLE_WEBSOCKETS", "true").lower() == "true"

# Validate required configuration
# Note: Main Supabase connection is optional for support database functionality
if not SUPABASE_URL:
    print("⚠️ SUPABASE_URL environment variable not set. Main app features will be limited.")
    SUPABASE_URL = None

if not SUPABASE_SERVICE_ROLE_KEY:
    print("⚠️ Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_ANON_KEY environment variable is set. Main app features will be limited.")
    SUPABASE_SERVICE_ROLE_KEY = None

# Validate support database configuration (optional for now)
if not SUPPORT_SUPABASE_URL:
    print("⚠️ SUPPORT_SUPABASE_URL environment variable not set. Support features will be limited.")
    SUPPORT_SUPABASE_URL = None

if not SUPPORT_SUPABASE_ANON_KEY:
    print("⚠️ SUPPORT_SUPABASE_ANON_KEY environment variable not set. Support features will be limited.")
    SUPPORT_SUPABASE_ANON_KEY = None

if not SUPPORT_SUPABASE_SERVICE_ROLE_KEY:
    print("⚠️ SUPPORT_SUPABASE_SERVICE_ROLE_KEY environment variable not set. Support features will be limited.")
    SUPPORT_SUPABASE_SERVICE_ROLE_KEY = None

print(f"🔧 Configuration loaded:")
print(f"   AUTH Supabase URL: {SUPABASE_URL or 'Not set'}")
print(f"   AUTH Service Key: {SUPABASE_SERVICE_ROLE_KEY[:20] + '...' if SUPABASE_SERVICE_ROLE_KEY else 'Not set'}")
print(f"   SUPPORT Supabase URL: {SUPPORT_SUPABASE_URL or 'Not set'}")
print(f"   SUPPORT Service Key: {SUPPORT_SUPABASE_SERVICE_ROLE_KEY[:20] + '...' if SUPPORT_SUPABASE_SERVICE_ROLE_KEY else 'Not set'}")
print(f"   Debug Mode: {DEBUG}")
print(f"   Use JSON: {USE_JSON}")
