#!/usr/bin/env python3
"""
Script to manually add users to Supabase
Run this script to add new users with proper password hashing
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.supa import supabase
from app.services.auth_service import AuthService

def add_user_manually():
    """Add a new user manually to Supabase"""
    print("🔐 Add New User to Supabase")
    print("=" * 40)
    
    # Get user input
    user_id = input("Enter User ID (e.g., user001): ").strip()
    name = input("Enter Full Name: ").strip()
    email = input("Enter Email: ").strip()
    password = input("Enter Password: ").strip()
    role = input("Enter Role (admin/manager/employee) [default: employee]: ").strip() or "employee"
    phone = input("Enter Phone (optional): ").strip() or None
    shift = input("Enter Shift (day/night) [default: day]: ").strip() or "day"
    
    if not all([user_id, name, email, password]):
        print("❌ Error: User ID, Name, Email, and Password are required!")
        return False
    
    try:
        # Hash the password using AuthService
        auth_service = AuthService()
        
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(email)
        if existing_user:
            print(f"❌ Error: User with email {email} already exists!")
            return False
        
        # Hash the password
        from passlib.hash import argon2
        password_hash = argon2.hash(password)
        
        # Prepare user data
        user_data = {
            'id': user_id,
            'name': name,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'status': 'active',
            'phone': phone,
            'shift': shift,
            'joining_date': datetime.now().date().isoformat(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Insert user into Supabase
        response = supabase.table('users').insert(user_data).execute()
        
        if response.data:
            print(f"✅ User '{name}' added successfully!")
            print(f"   ID: {user_id}")
            print(f"   Email: {email}")
            print(f"   Role: {role}")
            print(f"   Status: active")
            print(f"\n🔑 Login credentials:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            return True
        else:
            print("❌ Error: Failed to add user")
            return False
            
    except Exception as e:
        print(f"❌ Error adding user: {e}")
        return False

def list_existing_users():
    """List all existing users"""
    print("\n👥 Existing Users:")
    print("=" * 40)
    
    try:
        response = supabase.table('users').select('id, name, email, role, status').execute()
        
        if response.data:
            for user in response.data:
                status_icon = "🟢" if user.get('status') == 'active' else "🔴"
                print(f"{status_icon} {user.get('name')} ({user.get('email')}) - {user.get('role')}")
        else:
            print("No users found")
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")

def main():
    """Main function"""
    print("🚀 Supabase User Management Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Add new user")
        print("2. List existing users")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            add_user_manually()
        elif choice == '2':
            list_existing_users()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
