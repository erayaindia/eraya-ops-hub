#!/usr/bin/env python3
"""
Simple script to generate Argon2 password hash for SQL insertion
"""

from passlib.hash import argon2

# Generate hash for password: 123456
password = "123456"
password_hash = argon2.hash(password)

print("🔐 Password Hash Generated")
print("=" * 40)
print(f"Password: {password}")
print(f"Hash: {password_hash}")
print("\n📋 SQL Command to run in Supabase:")
print("=" * 40)
print(f"""
-- First, add the missing columns if they don't exist:
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP DEFAULT NOW();

-- Then insert the user:
INSERT INTO users (
    id, 
    name, 
    email, 
    password_hash, 
    role, 
    status,
    phone,
    shift,
    joining_date,
    created_at,
    updated_at
) VALUES (
    'rishav001',
    'Rishav',
    'rishav@erayastyle.com',
    '{password_hash}',
    'admin',
    'active',
    '',
    'day',
    CURRENT_DATE,
    NOW(),
    NOW()
);
""")
