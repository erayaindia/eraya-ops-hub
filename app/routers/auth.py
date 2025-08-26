"""
Authentication router for login, logout, and user management
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional, Any
import time

from app.deps import get_current_user, require_auth, create_session, require_admin
from app.services import supa
from app.services.auth_service import AuthService  # Import the new AuthService
from app.middleware_pkg.security import login_rate_limit, security_middleware  # Import security features

router = APIRouter()

# Initialize AuthService
auth_service = AuthService()

# Get templates from app state
def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    """Login page with CSRF token"""
    # Check if user is already logged in
    current_user = get_current_user(request.cookies.get("session_id"))
    if current_user:
        return RedirectResponse(url="/hub", status_code=302)
    
    # Generate CSRF token
    csrf_token = security_middleware.generate_csrf_token()
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": "Login",
        "header": "Login",
        "csrf_token": csrf_token
    })

@router.get("/request-password-reset", response_class=HTMLResponse)
async def request_password_reset_page(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    """Password reset request page"""
    return templates.TemplateResponse("request_password_reset.html", {
        "request": request,
        "title": "Request Password Reset",
        "header": "Request Password Reset"
    })

@router.get("/test-logout", response_class=HTMLResponse)
async def test_logout_page(request: Request):
    """Test page for debugging logout functionality"""
    with open('test_logout_simple.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@router.post("/api/auth/login")
@login_rate_limit()  # Apply rate limiting
async def login(
    request: Request,
    email: str = Form(...),  # Changed from username to email
    password: str = Form(...),
    remember_me: bool = Form(False),
    csrf_token: str = Form(...)  # Require CSRF token
):
    """Authenticate user and create session with enhanced security"""
    try:
        # Validate input
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Get client information for security logging
        ip_address = security_middleware.get_client_ip(request)
        user_agent = security_middleware.get_user_agent(request)
        
        # Authenticate user using AuthService with security features
        user = await auth_service.authenticate_user(email, password, ip_address, user_agent)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Update login statistics (temporarily disabled to debug)
        # await auth_service.update_login_stats(user["id"])
        
        # Create session
        session_token = create_session(user["id"], remember_me)
        
        # Create response
        response = JSONResponse(content={
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "status": user["status"]
            }
        })
        
        # Add security headers
        response = security_middleware.add_security_headers(response)
        
        # Set session cookie
        max_age = (30 * 24 * 60 * 60) if remember_me else (7 * 24 * 60 * 60)  # seconds
        response.set_cookie(
            key="session_id",
            value=session_token,
            max_age=max_age,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise # Re-raise FastAPI HTTPExceptions directly
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

@router.get("/api/auth/csrf")
async def get_csrf_token():
    """Get CSRF token for forms"""
    token = security_middleware.generate_csrf_token()
    return {"csrf_token": token}

@router.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user and clear session"""
    try:
        # Get current user for logging (optional)
        current_user = None
        try:
            current_user = get_current_user(request.cookies.get("session_id"))
            if current_user:
                print(f"User {current_user.get('email')} logging out")
        except Exception as e:
            print(f"Warning: Could not get current user for logout: {e}")
        
        # Create response
        response = JSONResponse(content={"message": "Logout successful"})
        
        # Clear session cookie
        response.delete_cookie("session_id")
        
        # Add security headers
        response = security_middleware.add_security_headers(response)
        
        return response
        
    except Exception as e:
        print(f"Logout error: {e}")
        # Still return success response even if there are errors
        response = JSONResponse(content={"message": "Logout successful"})
        response.delete_cookie("session_id")
        return response

@router.get("/api/auth/me")
async def get_current_user_info(current_user: Dict = Depends(require_auth)):
    """Get current logged-in user information"""
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "status": current_user["status"]
    }

@router.post("/api/auth/request-password-reset")
async def request_password_reset(
    request: Request,
    email: str = Form(...),
):
    """Request a password reset email"""
    try:
        # Construct base URL for reset link
        base_url = str(request.base_url).rstrip('/')
        
        success = await auth_service.request_password_reset(email, base_url)
        
        if success:
            return JSONResponse({"message": "If an account with that email exists, a password reset link has been sent."})
        else:
            # Return a generic success message to prevent user enumeration
            return JSONResponse({"message": "If an account with that email exists, a password reset link has been sent."})
    except Exception as e:
        print(f"Error in password reset request endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process password reset request.")

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = None, templates: Jinja2Templates = Depends(get_templates)):
    """Password reset page (where user enters new password)"""
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token is missing.")
    
    # Optionally, you can pre-validate the token here to show a better error message upfront
    # For now, we'll let the POST endpoint handle full validation.
    
    return templates.TemplateResponse("reset_password.html", {
        "request": request,
        "title": "Reset Password",
        "header": "Reset Your Password",
        "token": token
    })

@router.post("/api/auth/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    csrf_token: str = Form(...) # Require CSRF token
):
    """Perform password reset with token"""
    try:
        # Validate CSRF token (if applicable, based on your middleware setup)
        # Note: If your CSRFMiddleware intercepts all POST, it might handle this.
        # For form submissions, we typically rely on the token being in the form data.

        # Get client information for logging
        ip_address = security_middleware.get_client_ip(request)
        user_agent = security_middleware.get_user_agent(request)

        # Validate password strength (optional, but highly recommended)
        from app.services.auth_service import AuthService  # Re-import to avoid circular dependency if needed
        _auth_service = AuthService()

        # It's not ideal to instantiate AuthService here; better to pass it as a dependency or use the existing one.
        # For now, assuming auth_service is globally available or passed.
        
        # Here's where you'd add password strength validation
        # validation_result = _auth_service.validate_password_strength(new_password)
        # if not validation_result["valid"]:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weak password: " + ", ".join(validation_result["errors"])) # type: ignore

        updated_user = await auth_service.reset_password(token, new_password)
        
        if updated_user:
            # Log successful password reset
            await security_middleware.log_security_event(
                user_id=updated_user["id"],
                action="password_reset",
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"email": updated_user["email"]}
            )
            response = JSONResponse({"message": "Password has been reset successfully. You can now log in."})
            response = security_middleware.add_security_headers(response)
            return response
        else:
            # Log failed password reset attempt (if user exists for token, but reset fails)
            # This can be tricky without knowing if the token belongs to a user without validating it fully first.
            # For simplicity, if updated_user is None, it means token was invalid/expired or another error occurred.
            await security_middleware.log_security_event(
                user_id=None, # User ID is unknown or invalid at this point
                action="password_reset",
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"token": token, "reason": "Invalid or expired token, or other error"}
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token, or password update failed.")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in password reset endpoint: {e}")
        await security_middleware.log_security_event(
            user_id=None, # User ID is unknown or invalid at this point
            action="password_reset",
            success=False,
            ip_address=security_middleware.get_client_ip(request),
            user_agent=security_middleware.get_user_agent(request),
            details={"token": token, "reason": f"Server error: {str(e)}"}
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password. Please try again.")

@router.get("/api/auth/navigation")
async def get_current_user_navigation(current_user: Dict = Depends(require_auth)):
    """Get navigation menu for current authenticated user"""
    from app.factory import NAV_ITEMS # Assuming NAV_ITEMS is defined here or imported
    
    # Filter navigation items based on user role if needed
    # For now, return all items if authenticated
    return JSONResponse(content={
        "role": current_user["role"],
        "menu": NAV_ITEMS
    })

@router.get("/api/user/{user_id}/role")
async def get_user_role(user_id: str, current_user: Dict = Depends(require_admin)):
    """Get role for a specific user (admin only)"""
    # This part should ideally use supa.get_user to fetch the actual user's role
    # For simplicity, returning a mock role for now, but in a real app, you'd query Supabase
    user_data = supa.get_user(user_id)
    if user_data:
        return {"role": user_data.get("role", "employee")}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@router.get("/api/auth/security-status")
async def get_security_status(request: Request, email: str = None, current_user: Dict = Depends(require_auth)):
    """Get security status for current user (failed attempts, lockout info)"""
    try:
        # If email is provided, get user by email, otherwise use current user
        if email:
            user = await auth_service.get_user_by_email(email)
        else:
            user = await auth_service.get_user_by_id(current_user["id"])
            
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        security_info = {
            "failed_login_attempts": user.get("failed_login_attempts", 0),
            "max_failed_attempts": auth_service.max_failed_attempts,
            "is_locked": await auth_service.is_account_locked(user["id"]),
            "locked_until": user.get("locked_until"),
            "remaining_attempts": max(0, auth_service.max_failed_attempts - user.get("failed_login_attempts", 0))
        }
        
        return security_info
    except Exception as e:
        print(f"Error getting security status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get security status")
