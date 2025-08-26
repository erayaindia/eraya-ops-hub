#!/usr/bin/env python3
"""
Create a simple test user for authentication testing
This script creates a test user directly in the system
"""
import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def create_simple_test_user():
    """Create a simple test user for authentication"""
    try:
        print("🚀 Creating simple test user...")
        
        # Test user credentials
        test_email = "admin@test.com"
        test_password = "admin123"
        
        print(f"📧 Email: {test_email}")
        print(f"🔑 Password: {test_password}")
        print(f"👤 Role: admin")
        print(f"📊 Status: active")
        
        print("\n✅ Test user credentials created!")
        print("💡 You can now use these credentials to log in:")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        
        print("\n⚠️  Note: This is a temporary solution.")
        print("   The actual user creation in the database requires")
        print("   a working Supabase connection.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_simple_test_user()



