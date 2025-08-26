#!/usr/bin/env python3
"""
Script to check user in database and test login process
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.supa import supabase
from app.services.auth_service import AuthService

def check_user_in_database():
    """Check if user exists in database"""
    print("🔍 Checking User in Database")
    print("=" * 40)
    
    try:
        # Check for user by email
        response = supabase.table('users').select('*').eq('email', 'rishav@erayastyle.com').execute()
        
        if response.data:
            user = response.data[0]
            print(f"✅ User found in database:")
            print(f"   ID: {user.get('id')}")
            print(f"   Name: {user.get('name')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Status: {user.get('status')}")
            print(f"   Password Hash: {user.get('password_hash')[:50]}...")
            print(f"   Created: {user.get('created_at')}")
            return user
        else:
            print("❌ User NOT found in database!")
            print("   You need to run the SQL command first.")
            return None
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return None

def test_password_verification():
    """Test if password verification works"""
    print("\n🔐 Testing Password Verification")
    print("=" * 40)
    
    try:
        auth_service = AuthService()
        
        # Test with the correct password
        test_password = "123456"
        print(f"Testing password: {test_password}")
        
        # Get user from database
        user = auth_service.get_user_by_email('rishav@erayastyle.com')
        
        if user:
            print(f"✅ User retrieved from AuthService")
            print(f"   Password hash exists: {'Yes' if user.get('password_hash') else 'No'}")
            
            # Test password verification
            if auth_service.verify_password(test_password, user.get('password_hash')):
                print("✅ Password verification SUCCESS!")
                return True
            else:
                print("❌ Password verification FAILED!")
                return False
        else:
            print("❌ User not found by AuthService")
            return False
            
    except Exception as e:
        print(f"❌ Error testing password: {e}")
        return False

def create_user_if_missing():
    """Create the user if it doesn't exist"""
    print("\n🚀 Creating User (if missing)")
    print("=" * 40)
    
    try:
        # Check if user exists
        existing = supabase.table('users').select('id').eq('email', 'rishav@erayastyle.com').execute()
        
        if existing.data:
            print("✅ User already exists, skipping creation")
            return True
        
        # Create user
        from passlib.hash import argon2
        password_hash = argon2.hash("123456")
        
        user_data = {
            'id': 'rishav001',
            'name': 'Rishav',
            'email': 'rishav@erayastyle.com',
            'password_hash': password_hash,
            'role': 'admin',
            'status': 'active',
            'phone': '',
            'shift': 'day',
            'joining_date': datetime.now().date().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        response = supabase.table('users').insert(user_data).execute()
        
        if response.data:
            print("✅ User created successfully!")
            print(f"   Email: rishav@erayastyle.com")
            print(f"   Password: 123456")
            return True
        else:
            print("❌ Failed to create user")
            return False
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def main():
    """Main function"""
    print("🔍 User Login Troubleshooting Tool")
    print("=" * 40)
    
    # Step 1: Check if user exists
    user = check_user_in_database()
    
    if not user:
        print("\n💡 User not found. Creating user...")
        if create_user_if_missing():
            print("✅ User created! Now try logging in again.")
        else:
            print("❌ Failed to create user. Check your Supabase connection.")
        return
    
    # Step 2: Test password verification
    if test_password_verification():
        print("\n✅ Everything looks good! Try logging in again.")
    else:
        print("\n❌ Password verification failed. The password hash might be corrupted.")
        print("💡 Try recreating the user with the SQL command.")

if __name__ == "__main__":
    main()
