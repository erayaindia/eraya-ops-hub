"""
Security middleware for rate limiting, CSRF protection, and security headers
"""
import time
import secrets
from typing import Dict, Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

# CSRF token serializer
SECRET_KEY = "your-secret-key-here"  # This should come from environment variables
csrf_serializer = URLSafeTimedSerializer(SECRET_KEY)

class SecurityMiddleware:
    """Security middleware for the application"""
    
    def __init__(self):
        self.rate_limiter = limiter
        self.csrf_serializer = csrf_serializer
    
    def generate_csrf_token(self) -> str:
        """Generate a new CSRF token"""
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token: str, stored_token: str) -> bool:
        """Verify CSRF token"""
        return secrets.compare_digest(token, stored_token)
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        client_host = request.client.host if request.client else "unknown"
        
        # Validate IP address format for Supabase
        if client_host == "unknown" or not self._is_valid_ip(client_host):
            return "127.0.0.1"  # Default to localhost for invalid IPs
        
        return client_host
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP address is valid"""
        try:
            import ipaddress
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def get_user_agent(self, request: Request) -> str:
        """Get user agent string"""
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Validate user agent for Supabase
        if user_agent == "unknown" or len(user_agent) > 500:  # Limit length
            return "Script/Test"  # Default for scripts/testing
        
        return user_agent
    
    async def log_security_event(
        self, 
        user_id: Optional[str], 
        action: str, 
        success: bool, 
        ip_address: str, 
        user_agent: str, 
        details: Optional[Dict] = None
    ):
        """Log security events to the audit log table"""
        try:
            from app.services.supa import supabase
            
            audit_data = {
                "user_id": user_id,
                "action": action,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "success": success,
                "details": details or {},
                "created_at": datetime.now().isoformat()  # Use datetime instead of time.time()
            }
            
            # Insert into auth_audit_log table
            supabase.table("auth_audit_log").insert(audit_data).execute()
            
        except Exception as e:
            print(f"Error logging security event: {e}")
    
    def add_security_headers(self, response: JSONResponse) -> JSONResponse:
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:;"
        return response

# Global security middleware instance
security_middleware = SecurityMiddleware()

# Rate limiting decorators
def rate_limit(limit: str):
    """Rate limiting decorator"""
    return limiter.limit(limit)

def login_rate_limit():
    """Rate limiting for login attempts"""
    return rate_limit("5/minute")

def api_rate_limit():
    """Rate limiting for API endpoints"""
    return rate_limit("100/minute")

# CSRF protection
def require_csrf_token():
    """Require CSRF token for POST/PUT/DELETE requests"""
    def _require_csrf_token(request: Request):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Get CSRF token from header or form data
            csrf_token = request.headers.get("X-CSRF-Token") or request.form().get("csrf_token")
            
            if not csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token required"
                )
            
            # Verify CSRF token (you'll need to implement token storage/verification)
            # For now, we'll just check if it exists
            if not csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid CSRF token"
                )
    
    return _require_csrf_token
