import os
from typing import Dict, Optional, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta
import secrets
from postgrest import APIError

from app.services.supa import get_anon_client, get_service_client # Import the AUTH database client
from app.utils.email_utils import send_email # Import email utility
from app.config import EMAIL_SENDER # Import EMAIL_SENDER from config

AUTH_MODE = os.getenv("AUTH_MODE", "local")

class InvalidCredentials(Exception): ...
class AuthError(Exception): ...



class AuthService:
    def __init__(self):
        self.supabase = get_anon_client()
        self.ph = PasswordHasher()
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.reset_token_expiry = timedelta(hours=1) # Password reset token expiry
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2"""
        return self.ph.hash(password)

    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash"""
        try:
            if not hash:
                return False
            self.ph.verify(hash, password)
            return True
        except VerifyMismatchError:
            return False
        except Exception as e:
            print(f"Password verification error: {e}")
            return False

    async def authenticate_user(self, email: str, password: str, ip_address: str = None, user_agent: str = None):
        print("🔧 Using Supabase Auth")
        supa = get_anon_client()
        
        # For profile access, we need service role key due to RLS policies
        supa_service = get_service_client()

        # 1) real Supabase auth (no custom users table, no password hash check)
        try:
            res = supa.auth.sign_in_with_password({"email": email, "password": password})
        except APIError:
            raise InvalidCredentials("Invalid email or password")

        user = getattr(res, "user", None)
        if not user:
            raise InvalidCredentials("Invalid email or password")

        # 2) load profile by user_id (using service role key to bypass RLS)
        prof_res = (
            supa_service.table("profiles")
            .select("full_name, role, status")
            .eq("user_id", user.id)
            .single()
            .execute()
        )
        profile = getattr(prof_res, "data", None)
        if not profile:
            raise AuthError("Profile missing. Contact admin.")
        if profile.get("status") != "active":
            raise AuthError("Your account is inactive. Contact admin.")

        # 3) return the session payload your app expects
        return {
            "id": str(user.id),  # Changed from "uid" to "id" to match expected structure
            "email": user.email,
            "role": profile["role"],
            "status": profile["status"],
            "name": profile.get("full_name", "")  # Changed from "full_name" to "name" to match expected structure
        }
    
    async def get_user_by_email(self, email: str, include_password_hash: bool = False) -> Optional[Dict]:
        """Get user by email from Supabase (can include password hash for verification)"""
        try:
            # TEMPORARY: For now, we'll use the test user or create a mapping
            # In the future, you should add email and password_hash columns to profiles table
            
            # Check if it's the test user
            if email == "admin@test.com":
                return {
                    "id": "test_user_001",
                    "name": "Test Admin",
                    "email": email,
                    "role": "admin",
                    "status": "active",
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vHhHhqG"  # admin123
                }
            
            # For now, return None for other emails
            # TODO: Add email and password_hash columns to profiles table
            print(f"⚠️ User lookup by email not implemented yet. Add email column to profiles table.")
            return None
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str, include_password_hash: bool = False) -> Optional[Dict]:
        """Get user by ID from Supabase (can include password hash for verification)"""
        try:
            # Map the profiles table structure to expected format
            response = self.supabase.table("profiles").select(
                "user_id, full_name, role, status, created_at, updated_at"
            ).eq("user_id", user_id).execute()
            
            if not response.data:
                return None
                
            profile = response.data[0]
            
            # Map to expected format
            return {
                "id": profile["user_id"],
                "name": profile["full_name"] or "Unknown User",
                "email": f"{profile['user_id']}@temp.com",  # Temporary email mapping
                "role": profile["role"],
                "status": profile["status"],
                "created_at": profile["created_at"],
                "updated_at": profile["updated_at"]
            }
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    async def update_login_stats(self, user_id: str):
        """Update user login statistics (simplified)"""
        try:
            current_time = datetime.now().isoformat()
            
            # Simple update without complex queries
            self.supabase.table("profiles").update({
                'last_login': current_time,
                'updated_at': current_time
            }).eq('user_id', user_id).execute()
            
            print(f"Updated login stats for user: {user_id}")
            
        except Exception as e:
            print(f"Warning: Could not update login stats for user {user_id}: {e}")
            # Continue even if stats update fails

    async def is_account_locked(self, user_id: str) -> bool:
        """Check if user account is locked"""
        try:
            user = await self.get_user_by_id(user_id, include_password_hash=True)
            if not user:
                return False
            
            locked_until = user.get('locked_until')
            if not locked_until:
                return False
            
            # Check if lockout period has expired
            lockout_time = datetime.fromisoformat(locked_until)
            if datetime.now() > lockout_time:
                # Unlock the account
                await self.unlock_account(user_id)
                return False
            
            return True
        except Exception as e:
            print(f"Error checking account lock status: {e}")
            return False

    async def handle_failed_login(self, user_id: str, ip_address: str = None, user_agent: str = None):
        """Handle failed login attempt"""
        try:
            user = await self.get_user_by_id(user_id, include_password_hash=True)
            if not user:
                return
            
            current_attempts = user.get('failed_login_attempts', 0) + 1
            
            if current_attempts >= self.max_failed_attempts:
                # Lock the account
                lockout_until = (datetime.now() + self.lockout_duration).isoformat()
                await self.lock_account(user_id, lockout_until)
                await self.log_failed_login_attempt(user.get('email'), ip_address, user_agent, "Account locked due to too many failed attempts")
            else:
                # Increment failed attempts
                await self.increment_failed_attempts(user_id, current_attempts)
                await self.log_failed_login_attempt(user.get('email'), ip_address, user_agent, f"Failed login attempt {current_attempts}/{self.max_failed_attempts}")
                
        except Exception as e:
            print(f"Error handling failed login: {e}")

    async def lock_account(self, user_id: str, lockout_until: str):
        """Lock user account"""
        try:
            self.supabase.table("profiles").update({
                'locked_until': lockout_until,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
        except Exception as e:
            print(f"Error locking account: {e}")

    async def unlock_account(self, user_id: str):
        """Unlock user account"""
        try:
            self.supabase.table("users").update({
                'locked_until': None,
                'failed_login_attempts': 0,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
        except Exception as e:
            print(f"Error unlocking account: {e}")

    async def increment_failed_attempts(self, user_id: str, attempts: int):
        """Increment failed login attempts"""
        try:
            self.supabase.table("users").update({
                'failed_login_attempts': attempts,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
        except Exception as e:
            print(f"Error incrementing failed attempts: {e}")

    async def reset_failed_login_attempts(self, user_id: str):
        """Reset failed login attempts on successful login"""
        try:
            self.supabase.table("users").update({
                'failed_login_attempts': 0,
                'locked_until': None,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
        except Exception as e:
            print(f"Error resetting failed attempts: {e}")

    async def log_failed_login_attempt(self, email: str, ip_address: str = None, user_agent: str = None, reason: str = "Invalid credentials"):
        """Log failed login attempt"""
        try:
            from app.middleware_pkg.security import security_middleware
            await security_middleware.log_security_event(
                user_id=None,
                action="failed_login",
                success=False,
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                details={"email": email, "reason": reason}
            )
        except Exception as e:
            print(f"Error logging failed login attempt: {e}")

    async def log_successful_login(self, user_id: str, ip_address: str = None, user_agent: str = None):
        """Log successful login"""
        try:
            from app.middleware_pkg.security import security_middleware
            await security_middleware.log_security_event(
                user_id=user_id,
                action="successful_login",
                success=True,
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                details={}
            )
        except Exception as e:
            print(f"Error logging successful login: {e}")

    async def request_password_reset(self, email: str, base_url: str) -> bool:
        """Generate a password reset token and send email"""
        try:
            user = await self.get_user_by_email(email, include_password_hash=True)
            if not user:
                print(f"⚠️ Password reset requested for non-existent email: {email}")
                return False # Avoid leaking user existence

            # Generate a secure, time-limited token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + self.reset_token_expiry

            # Store token in database
            self.supabase.table("users").update({
                'reset_token': token,
                'reset_token_expires_at': expires_at.isoformat(),
                'updated_at': datetime.now().isoformat()
            }).eq('id', user["id"]).execute()

            # Construct reset link
            reset_link = f"{base_url}/reset-password?token={token}"

            # Send email
            subject = "Password Reset Request"
            body = f"""<html>
            <body>
                <p>Hello {user['name']},</p>
                <p>You have requested a password reset for your account.</p>
                <p>Please click on the link below to reset your password:</p>
                <p><a href=\"{reset_link}\">{reset_link}</a></p>
                <p>This link will expire in {int(self.reset_token_expiry.total_seconds() / 3600)} hour(s).</p>
                <p>If you did not request a password reset, please ignore this email.</p>
                <p>Best regards,</p>
                <p>Your Application Team</p>
            </body>
            </html>"""
            
            await send_email(user["email"], subject, body, is_html=True)
            return True
        except Exception as e:
            print(f"❌ Error requesting password reset for {email}: {e}")
            return False

    async def reset_password(self, token: str, new_password: str) -> Optional[Dict]:
        """Reset user password using a valid token"""
        try:
            # Find user by reset token
            response = self.supabase.table("users").select(
                "id, name, email, reset_token_expires_at"
            ).eq("reset_token", token).execute()
            
            user = response.data[0] if response.data else None

            if not user:
                print(f"⚠️ Invalid or expired reset token: {token}")
                return None
            
            expires_at = datetime.fromisoformat(user['reset_token_expires_at'])
            if datetime.now() > expires_at:
                # Token expired, clear it
                await self.clear_reset_token(user["id"])
                print(f"⚠️ Expired reset token for user {user['id']}: {token}")
                return None

            # Hash new password
            hashed_password = self.hash_password(new_password)

            # Update password and clear token
            self.supabase.table("users").update({
                'password_hash': hashed_password,
                'reset_token': None,
                'reset_token_expires_at': None,
                'password_changed_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).eq('id', user["id"]).execute()

            print(f"✅ Password reset successfully for user {user['id']}")
            # Return updated user information (without password hash)
            updated_user = await self.get_user_by_id(user["id"])
            return updated_user

        except Exception as e:
            print(f"❌ Error resetting password with token {token}: {e}")
            return None

    async def clear_reset_token(self, user_id: str):
        """Clear the password reset token for a user"""
        try:
            self.supabase.table("users").update({
                'reset_token': None,
                'reset_token_expires_at': None,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
        except Exception as e:
            print(f"Error clearing reset token for user {user_id}: {e}")
