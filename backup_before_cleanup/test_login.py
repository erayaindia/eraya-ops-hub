#!/usr/bin/env python3
"""
Simple script to test login functionality
"""

import os
import sys
import asyncio

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.auth_service import AuthService

async def test_login():
    """Test the login functionality"""
    print("🔐 Testing Login Functionality")
    print("=" * 40)
    
    try:
        auth_service = AuthService()
        
        # Test credentials
        email = "rishav@erayastyle.com"
        password = "123456"
        
        print(f"Testing login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
        # Test authentication
        user = await auth_service.authenticate_user(email, password)
        
        if user:
            print(f"\n✅ Login SUCCESS!")
            print(f"   User ID: {user.get('id')}")
            print(f"   Name: {user.get('name')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Status: {user.get('status')}")
        else:
            print(f"\n❌ Login FAILED!")
            print("   Check the database and password hash")
            
    except Exception as e:
        print(f"❌ Error testing login: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
