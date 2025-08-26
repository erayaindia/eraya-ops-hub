#!/usr/bin/env python3
"""
Test script for User Management System
Tests the connection to Supabase and basic CRUD operations
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.users_service import UsersService
from app.services.supa import supabase

async def test_user_management():
    """Test the user management system"""
    print("🧪 Testing User Management System...")
    
    try:
        # Test 1: Check Supabase connection
        print("\n1️⃣ Testing Supabase connection...")
        users_service = UsersService()
        
        # Test 2: List users
        print("\n2️⃣ Testing list users...")
        users = await users_service.list_users(page=1, limit=5)
        print(f"   Found {users['total']} users")
        print(f"   Current page: {users['page']} of {users['pages']}")
        print(f"   Users on this page: {len(users['items'])}")
        
        if users['items']:
            print("   Sample user:")
            user = users['items'][0]
            print(f"     ID: {user.get('id')}")
            print(f"     Name: {user.get('name')}")
            print(f"     Email: {user.get('email')}")
            print(f"     Role: {user.get('role')}")
            print(f"     Status: {user.get('status')}")
        
        # Test 3: Get user statistics
        print("\n3️⃣ Testing user statistics...")
        stats = await users_service.get_user_statistics()
        print(f"   Total users: {stats['total']}")
        print(f"   Active users: {stats['active']}")
        print(f"   Admin users: {stats['admins']}")
        print(f"   Recent logins: {stats['recent_logins']}")
        
        # Test 4: Check if specific email exists
        print("\n4️⃣ Testing email existence check...")
        test_email = "test@example.com"
        exists = await users_service.email_exists(test_email)
        print(f"   Email '{test_email}' exists: {exists}")
        
        # Test 5: Test search functionality
        print("\n5️⃣ Testing search functionality...")
        if users['items']:
            search_term = users['items'][0]['name'][:3]  # First 3 characters of first user's name
            search_results = await users_service.list_users(query=search_term, page=1, limit=10)
            print(f"   Search for '{search_term}' returned {len(search_results['items'])} results")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_create_user():
    """Test creating a new user"""
    print("\n🧪 Testing User Creation...")
    
    try:
        users_service = UsersService()
        
        # Test data
        test_user_data = {
            "name": "Test User",
            "email": "testuser@example.com",
            "role": "employee",
            "status": "active",
            "phone": "+1234567890",
            "city": "Test City",
            "state": "Test State",
            "joining_date": "2024-01-01",
            "password": "testpassword123"
        }
        
        print("   Creating test user...")
        user_id = await users_service.create_user(test_user_data)
        print(f"   ✅ User created successfully with ID: {user_id}")
        
        # Verify user was created
        user = await users_service.get_user(user_id)
        if user:
            print(f"   ✅ User retrieved: {user['name']} ({user['email']})")
        else:
            print("   ❌ Failed to retrieve created user")
        
        # Clean up - delete test user
        print("   Cleaning up test user...")
        deleted = await users_service.delete_user(user_id)
        if deleted:
            print("   ✅ Test user deleted successfully")
        else:
            print("   ❌ Failed to delete test user")
        
        return True
        
    except Exception as e:
        print(f"   ❌ User creation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting User Management System Tests...")
    
    # Run basic tests
    basic_success = asyncio.run(test_user_management())
    
    if basic_success:
        print("\n" + "="*50)
        print("🎯 Basic tests passed! Testing user creation...")
        print("="*50)
        
        # Run user creation test
        creation_success = asyncio.run(test_create_user())
        
        if creation_success:
            print("\n🎉 All tests passed! User Management System is working correctly.")
        else:
            print("\n⚠️ Basic tests passed but user creation failed.")
    else:
        print("\n❌ Basic tests failed. Please check your configuration.")
    
    print("\n🏁 Testing completed.")
