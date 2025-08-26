# app/services/supa.py
from typing import Optional
from supabase import create_client, Client
from app.config import (
    SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY,
    SUPPORT_SUPABASE_URL, SUPPORT_SUPABASE_ANON_KEY, SUPPORT_SUPABASE_SERVICE_ROLE_KEY
)

# AUTH Supabase clients (for user authentication - used by the app right now)
_anon_client: Optional[Client] = None
_service_client: Optional[Client] = None

# SUPPORT Supabase clients (for support tickets, orders, etc. - stored for later)
_support_anon_client: Optional[Client] = None
_support_service_client: Optional[Client] = None

def get_anon_client() -> Client:
    """Get AUTH Supabase anonymous client (for user authentication - used by the app right now)"""
    global _anon_client
    if _anon_client is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY")
        _anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _anon_client

def get_service_client() -> Client:
    """Get AUTH Supabase service client (for user authentication - used by the app right now)"""
    global _service_client
    if _service_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        _service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _service_client

def get_support_anon_client() -> Client:
    """Get SUPPORT Supabase anonymous client (for support tickets, orders, etc. - stored for later)"""
    global _support_anon_client
    if _support_anon_client is None:
        if not SUPPORT_SUPABASE_URL or not SUPPORT_SUPABASE_ANON_KEY:
            raise RuntimeError("Missing SUPPORT_SUPABASE_URL or SUPPORT_SUPABASE_ANON_KEY")
        _support_anon_client = create_client(SUPPORT_SUPABASE_URL, SUPPORT_SUPABASE_ANON_KEY)
    return _support_anon_client

def get_login_service_client() -> Client:
    """Get login Supabase service client (for user authentication)"""
    global _login_service_client
    if _login_service_client is None:
        if not LOGIN_SUPABASE_URL or not LOGIN_SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Missing LOGIN_SUPABASE_URL or LOGIN_SUPABASE_SERVICE_ROLE_KEY")
        _login_service_client = create_client(LOGIN_SUPABASE_URL, LOGIN_SUPABASE_SERVICE_ROLE_KEY)
    return _login_service_client

def get_support_service_client() -> Client:
    """Get SUPPORT Supabase service client (for support tickets, orders, etc. - stored for later)"""
    global _support_service_client
    if _support_service_client is None:
        if not SUPPORT_SUPABASE_URL or not SUPPORT_SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Missing SUPPORT_SUPABASE_URL or SUPPORT_SUPABASE_SERVICE_ROLE_KEY")
        _support_service_client = create_client(SUPPORT_SUPABASE_URL, SUPPORT_SUPABASE_SERVICE_ROLE_KEY)
    return _support_service_client

# Backward compatibility for existing codebase
# This allows existing code to continue using supa.supabase
class _ClientProxy:
    """Lazy proxy that delegates to the AUTH service client.
    This allows existing code to use supa.supabase.table() calls without breaking.
    """
    def __getattr__(self, name):
        # Delegate every attribute access to the real service client
        return getattr(get_service_client(), name)

# Module-level backward compatibility
# This allows existing code to use supa.supabase directly
supabase = _ClientProxy()
