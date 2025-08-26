#!/usr/bin/env python3
"""
Create a test user in Supabase for testing authentication
"""
import os
import sys
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.supa import supabase
from app.services.auth_service import AuthService

def create_test_user():
    """Create a test user for authentication testing"""
    try:
        auth_service = AuthService()
        
        # Test user data
        test_user = {
            'id': 'test_user_001',
            'name': 'Test User',
            'email': 'test@example.com',
            'password_hash': auth_service.hash_password('test123'),
            'role': 'admin',
            'status': 'active',
            'phone': '+1234567890',
            'city': 'Test City',
            'state': 'Test State',
            'joining_date': '2024-01-01',
            'login_count': 0,
            'failed_login_attempts': 0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Check if user already exists
        existing_user = supabase.table("users").select("id").eq("email", test_user["email"]).execute()
        
        if existing_user.data:
            print("✅ Test user already exists")
            return True
        
        # Insert test user
        response = supabase.table("users").insert(test_user).execute()
        
        if response.data:
            print("✅ Test user created successfully!")
            print(f"   Email: {test_user['email']}")
            print(f"   Password: test123")
            print(f"   Role: {test_user['role']}")
            return True
        else:
            print("❌ Failed to create test user")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Creating test user for authentication testing...")
    create_test_user()
