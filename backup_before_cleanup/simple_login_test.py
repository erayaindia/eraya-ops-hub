#!/usr/bin/env python3
"""
Simple script to test password verification directly
"""

import os
import sys

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.supa import supabase

def test_password_directly():
    """Test password verification directly"""
    print("🔐 Testing Password Verification Directly")
    print("=" * 40)
    
    try:
        # Get user directly from database
        response = supabase.table('users').select('*').eq('email', 'rishav@erayastyle.com').execute()
        
        if response.data:
            user = response.data[0]
            print(f"✅ User found in database:")
            print(f"   ID: {user.get('id')}")
            print(f"   Name: {user.get('name')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Password Hash: {user.get('password_hash')[:50]}...")
            
            # Test password verification manually
            from passlib.hash import argon2
            test_password = "123456"
            
            try:
                is_valid = argon2.verify(test_password, user.get('password_hash'))
                if is_valid:
                    print(f"\n✅ Password verification SUCCESS!")
                    print(f"   Password '123456' is correct for user {user.get('email')}")
                    print(f"\n🎉 You can now login with:")
                    print(f"   Email: rishav@erayastyle.com")
                    print(f"   Password: 123456")
                else:
                    print(f"\n❌ Password verification FAILED!")
                    print(f"   Password '123456' is incorrect for user {user.get('email')}")
            except Exception as e:
                print(f"\n❌ Error verifying password: {e}")
                
        else:
            print("❌ User NOT found in database!")
            print("   You need to run the SQL command first.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_password_directly()
