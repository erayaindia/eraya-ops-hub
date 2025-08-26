"""
Users Service - Handles all user management operations with Supabase
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from argon2 import PasswordHasher

from app.services.supa import supabase


class UsersService:
    def __init__(self):
        self.table_name = "users"
    
    async def list_users(
        self,
        query: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        sort: str = "created_at",
        order: str = "desc",
        page: int = 1,
        limit: int = 10
    ) -> Dict:
        """
        List users with search, filters, sorting, and pagination
        Returns: {items, total, page, pages}
        """
        try:
            # Build the query
            query_builder = supabase.table(self.table_name).select(
                "id,name,email,role,status,phone,city,joining_date,last_login,login_count,created_at,updated_at"
            )
            
            # Apply filters
            if query:
                # Search across name, email, and phone
                query_builder = query_builder.or_(
                    f"name.ilike.%{query}%,email.ilike.%{query}%,phone.ilike.%{query}%"
                )
            
            if role and role != "all":
                query_builder = query_builder.eq("role", role)
            
            if status and status != "all":
                query_builder = query_builder.eq("status", status)
            
            # Get total count for pagination
            count_query = query_builder
            count_result = count_query.execute()
            total = len(count_result.data) if count_result.data else 0
            
            # Apply sorting
            if sort == "name":
                sort_column = "name"
            elif sort == "email":
                sort_column = "email"
            elif sort == "role":
                sort_column = "role"
            elif sort == "status":
                sort_column = "status"
            elif sort == "last_login":
                sort_column = "last_login"
            else:
                sort_column = "created_at"
            
            # Apply pagination
            offset = (page - 1) * limit
            query_builder = query_builder.order(sort_column, desc=(order == "desc"))
            query_builder = query_builder.range(offset, offset + limit - 1)
            
            # Execute query
            result = query_builder.execute()
            
            if not result.data:
                return {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "pages": 0
                }
            
            # Calculate pagination info
            pages = (total + limit - 1) // limit
            
            return {
                "items": result.data,
                "total": total,
                "page": page,
                "pages": pages
            }
            
        except Exception as e:
            print(f"Error listing users: {e}")
            raise Exception(f"Failed to list users: {str(e)}")
    
    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get a single user by ID"""
        try:
            result = supabase.table(self.table_name).select(
                "id,name,email,role,status,phone,city,state,joining_date,last_login,login_count,created_at,updated_at"
            ).eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error getting user {user_id}: {e}")
            raise Exception(f"Failed to get user: {str(e)}")
    
    async def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """Check if email already exists"""
        try:
            query = supabase.table(self.table_name).select("id").eq("email", email.lower())
            
            if exclude_id:
                query = query.neq("id", exclude_id)
            
            result = query.execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error checking email existence: {e}")
            return False
    
    async def create_user(self, data: Dict) -> str:
        """Create a new user"""
        try:
            print(f"🔧 UsersService.create_user called with data: {data}")
            print(f"🔧 Data type: {type(data)}")
            print(f"🔧 Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Validate required fields
            required_fields = ["name", "email", "role", "status", "password"]
            for field in required_fields:
                if not data.get(field):
                    print(f"❌ Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")
            
            print(f"✅ All required fields present")
            
            # Validate role
            valid_roles = ["owner", "admin", "manager", "employee", "packer"]
            if data["role"] not in valid_roles:
                raise ValueError(f"Invalid role: {data['role']}")
            
            # Validate status
            valid_statuses = ["active", "inactive", "suspended"]
            if data["status"] not in valid_statuses:
                raise ValueError(f"Invalid status: {data['status']}")
            
            # Normalize email
            email = data["email"].strip().lower()
            
            # Check for duplicate email
            if await self.email_exists(email):
                raise ValueError("duplicate_email")
            
            # Hash password
            ph = PasswordHasher()
            password_hash = ph.hash(data["password"])
            
            # Prepare user data
            user_data = {
                "id": str(uuid.uuid4()),
                "name": data["name"].strip(),
                "email": email,
                "role": data["role"],
                "status": data["status"],
                "phone": data.get("phone", "").strip(),
                "city": data.get("city", "").strip(),
                "state": data.get("state", "").strip(),
                "joining_date": data.get("joining_date"),
                "password_hash": password_hash,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            print(f"🔧 Preparing to insert user data: {user_data}")
            
            # Insert user
            try:
                print(f"🔧 About to execute Supabase insert...")
                print(f"🔧 Table name: {self.table_name}")
                print(f"🔧 User data to insert: {user_data}")
                
                result = supabase.table(self.table_name).insert(user_data).execute()
                
                print(f"🔧 Supabase insert result: {result}")
                print(f"🔧 Result type: {type(result)}")
                print(f"🔧 Result data: {result.data if hasattr(result, 'data') else 'No data attribute'}")
                
                if not result.data:
                    print(f"❌ No data returned from Supabase insert")
                    raise Exception("Failed to create user")
                
                print(f"✅ User created successfully in Supabase")
                return user_data["id"]
                
            except Exception as e:
                print(f"❌ CRITICAL ERROR during Supabase insert: {e}")
                print(f"❌ Error type: {type(e)}")
                import traceback
                print(f"❌ Full traceback: {traceback.format_exc()}")
                raise
            
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"Error creating user: {e}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    async def update_user(self, user_id: str, data: Dict) -> bool:
        """Update an existing user"""
        try:
            # Get current user to check if email is being changed
            current_user = await self.get_user(user_id)
            if not current_user:
                raise ValueError("User not found")
            
            # Prepare update data
            update_data = {
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Update allowed fields
            allowed_fields = ["name", "role", "status", "phone", "city", "state", "joining_date"]
            for field in allowed_fields:
                if field in data and data[field] is not None:
                    if field in ["name", "phone", "city", "state"]:
                        update_data[field] = data[field].strip()
                    else:
                        update_data[field] = data[field]
            
            # Handle email update separately (with duplicate check)
            if "email" in data and data["email"]:
                new_email = data["email"].strip().lower()
                if new_email != current_user["email"]:
                    if await self.email_exists(new_email, exclude_id=user_id):
                        raise ValueError("duplicate_email")
                    update_data["email"] = new_email
            
            # Handle password update
            if data.get("password") and data["password"].strip():
                ph = PasswordHasher()
                password_hash = ph.hash(data["password"].strip())
                update_data["password_hash"] = password_hash
                update_data["password_changed_at"] = datetime.utcnow().isoformat()
            
            # Validate role if being updated
            if "role" in update_data:
                valid_roles = ["owner", "admin", "manager", "employee", "packer"]
                if update_data["role"] not in valid_roles:
                    raise ValueError(f"Invalid role: {update_data['role']}")
            
            # Validate status if being updated
            if "status" in update_data:
                valid_statuses = ["active", "inactive", "suspended"]
                if update_data["status"] not in valid_statuses:
                    raise ValueError(f"Invalid status: {update_data['status']}")
            
            # Update user
            result = supabase.table(self.table_name).update(update_data).eq("id", user_id).execute()
            
            return len(result.data) > 0
            
        except ValueError as e:
            raise e
        except Exception as e:
            print(f"Error updating user {user_id}: {e}")
            raise Exception(f"Failed to update user: {str(e)}")
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user (hard delete)"""
        try:
            result = supabase.table(self.table_name).delete().eq("id", user_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error deleting user {user_id}: {e}")
            raise Exception(f"Failed to delete user: {str(e)}")
    
    async def get_user_statistics(self) -> Dict:
        """Get user statistics for dashboard"""
        try:
            # Get all users for statistics
            result = supabase.table(self.table_name).select(
                "status,role,last_login"
            ).execute()
            
            if not result.data:
                return {
                    "total": 0,
                    "active": 0,
                    "admins": 0,
                    "recent_logins": 0
                }
            
            users = result.data
            total = len(users)
            active = len([u for u in users if u.get("status") == "active"])
            admins = len([u for u in users if u.get("role") in ["owner", "admin"]])
            
            # Calculate recent logins (last 7 days)
            seven_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            seven_days_ago = seven_days_ago.replace(day=seven_days_ago.day - 7)
            
            recent_logins = 0
            for user in users:
                if user.get("last_login"):
                    try:
                        last_login = datetime.fromisoformat(user["last_login"].replace("Z", "+00:00"))
                        if last_login > seven_days_ago:
                            recent_logins += 1
                    except:
                        continue
            
            return {
                "total": total,
                "active": active,
                "admins": admins,
                "recent_logins": recent_logins
            }
            
        except Exception as e:
            print(f"Error getting user statistics: {e}")
            return {
                "total": 0,
                "active": 0,
                "admins": 0,
                "recent_logins": 0
            }
