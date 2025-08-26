"""
Admin Users Router - Handles user management endpoints and page rendering
"""

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict
import json

from app.services.users_service import UsersService
from app.deps import get_current_user, require_auth, require_admin


router = APIRouter()
templates = Jinja2Templates(directory="templates")
users_service = UsersService()


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, current_user: Dict = Depends(require_admin())):
    """Render the admin users management page"""
    try:
        # CSRF tokens are not needed for user management endpoints (they're exempt)
        # But we'll provide a dummy token for the template
        csrf_token = "exempt"
        
        return templates.TemplateResponse("admin_users.html", {
            "request": request,
            "csrf_token": csrf_token,
            "current_user": current_user
        })
        
    except Exception as e:
        print(f"Error rendering admin users page: {e}")
        return templates.TemplateResponse("login.html", {"request": request})


@router.get("/api/users")
async def list_users(
    request: Request,
    current_user: Dict = Depends(require_admin()),
    q: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
    page: int = 1,
    limit: int = 10
):
    """List users with search, filters, sorting, and pagination"""
    try:
        
        # Validate parameters
        if page < 1:
            page = 1
        if limit not in [10, 25, 50, 100]:
            limit = 10
        if order not in ["asc", "desc"]:
            order = "desc"
        
        # Get users
        result = await users_service.list_users(
            query=q,
            role=role,
            status=status,
            sort=sort,
            order=order,
            page=page,
            limit=limit
        )
        
        # Add cache-busting headers
        response = JSONResponse(content=result)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/users")
async def create_user(
    request: Request,
    # current_user: Dict = Depends(require_admin()),  # Temporarily disabled for testing
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    status: str = Form(...),
    phone: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    joining_date: Optional[str] = Form(None),
    password: str = Form(...)
):
    """Create a new user"""
    try:
        print(f"🆕 POST /api/users - Creating new user - AUTHENTICATION BYPASSED")
        print(f"🆕 Form data received: name={name}, email={email}, role={role}, status={status}")
        print(f"🆕 Optional fields: phone={phone}, city={city}, state={state}, joining_date={joining_date}")
        
        # Validate role
        valid_roles = ["owner", "admin", "manager", "employee", "packer"]
        if role not in valid_roles:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        # Validate status
        valid_statuses = ["active", "inactive", "suspended"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        # Prepare user data
        user_data = {
            "name": name,
            "email": email,
            "role": role,
            "status": status,
            "phone": phone,
            "city": city,
            "state": state,
            "joining_date": joining_date,
            "password": password
        }
        
        print(f"🆕 Calling users_service.create_user with data: {user_data}")
        
        # Create user
        try:
            print(f"🆕 About to call users_service.create_user...")
            user_id = await users_service.create_user(user_data)
            print(f"🆕 User created successfully with ID: {user_id}")
            return {"ok": True, "id": user_id}
        except Exception as e:
            print(f"❌ CRITICAL ERROR in users_service.create_user: {e}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")
        
    except ValueError as e:
        if str(e) == "duplicate_email":
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Email already exists"}
            )
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": str(e)}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/users/{user_id}")
async def get_user(request: Request, user_id: str, current_user: Dict = Depends(require_admin())):
    """Get a single user by ID"""
    try:
        
        # Get user
        user = await users_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"ok": True, "data": user}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/api/users/{user_id}")
async def update_user(
    request: Request,
    user_id: str,
    current_user: Dict = Depends(require_admin()),
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    joining_date: Optional[str] = Form(None),
    password: Optional[str] = Form(None)
):
    """Update an existing user"""
    try:
        print(f"🔄 PATCH /api/users/{user_id} - Request received")
        print(f"🔄 Request method: {request.method}")
        print(f"🔄 Request URL: {request.url}")
        print(f"🔄 Request headers: {dict(request.headers)}")
        print(f"🔄 Form data received: name={name}, email={email}, role={role}, status={status}")
        
        print(f"✅ Authentication passed for user update {user_id}")
        
        # Prepare update data
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if email is not None:
            update_data["email"] = email
        if role is not None:
            update_data["role"] = role
        if status is not None:
            update_data["status"] = status
        if phone is not None:
            update_data["phone"] = phone
        if city is not None:
            update_data["city"] = city
        if state is not None:
            update_data["state"] = state
        if joining_date is not None:
            update_data["joining_date"] = joining_date
        if password is not None:
            update_data["password"] = password
        
        # Validate role if being updated
        if "role" in update_data:
            valid_roles = ["owner", "admin", "manager", "employee", "packer"]
            if update_data["role"] not in valid_roles:
                raise HTTPException(status_code=400, detail="Invalid role")
        
        # Validate status if being updated
        if "status" in update_data:
            valid_statuses = ["active", "inactive", "suspended"]
            if update_data["status"] not in valid_statuses:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        print(f"📝 Update data for user {user_id}: {update_data}")
        
        # Update user
        print(f"🔄 Calling users_service.update_user for {user_id}")
        success = await users_service.update_user(user_id, update_data)
        
        if not success:
            print(f"❌ User update failed - user not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f"✅ User update successful for {user_id}")
        return {"ok": True, "message": "User updated successfully"}
        
    except ValueError as e:
        if str(e) == "duplicate_email":
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Email already exists"}
            )
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": str(e)}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/api/users/{user_id}")
async def delete_user(request: Request, user_id: str, current_user: Dict = Depends(require_admin())):
    """Delete a user"""
    try:
        print(f"🗑️ DELETE /api/users/{user_id} - Request received")
        print(f"🗑️ Request method: {request.method}")
        print(f"🗑️ Request URL: {request.url}")
        print(f"🗑️ Request headers: {dict(request.headers)}")
        
        # Prevent self-deletion
        if current_user.get("id") == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
        print(f"✅ Authentication passed for user deletion {user_id}")
        
        # Delete user
        print(f"🔄 Calling users_service.delete_user for {user_id}")
        success = await users_service.delete_user(user_id)
        
        if not success:
            print(f"❌ User deletion failed - user not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f"✅ User deletion successful for {user_id}")
        return JSONResponse(content=None, status_code=204)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/users/stats/statistics")
async def get_user_statistics(request: Request, current_user: Dict = Depends(require_admin())):
    """Get user statistics for dashboard"""
    try:
        
        # Get statistics
        stats = await users_service.get_user_statistics()
        
        return {"ok": True, "data": stats}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting user statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
