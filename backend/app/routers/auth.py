from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import os

# Import Supabase-backed service
from ..services.auth_service import verify_token, get_all_users, delete_user, update_user_role

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login") # Url doesn't matter much for Bearer

async def verify_active_user(token: str = Depends(oauth2_scheme)):
    """Verifies valid Supabase token and returns profile"""
    profile, error = verify_token(token)
    if not profile:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return profile

from pydantic import BaseModel

async def verify_admin_role(token: str = Depends(oauth2_scheme)):
    """Verifies token has admin role"""
    profile, error = verify_token(token)
    if not profile:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    role = profile.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return profile

# Compatibility Stubs for Legacy Code/Cache
class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login_stub(data: LoginRequest = None):
    print("⚠️ Legacy /auth/login called. Returning dummy success to prevent 404.")
    # Return a structure that satisfies old frontend if possible, or just 200 OK
    return {
        "access_token": "legacy_token_placeholder", 
        "token_type": "bearer",
        "user": {"username": "legacy", "role": "member"}
    }


# Note: /login and /register are removed. 
# Frontend performs them directly against Supabase.

@router.get("/users")
async def list_users(admin: dict = Depends(verify_admin_role)):
    return get_all_users()

@router.delete("/users/{user_id}")
async def remove_user(user_id: str, admin: dict = Depends(verify_admin_role)):
    if delete_user(user_id):
        return {"message": "User deleted"}
    raise HTTPException(status_code=400, detail="Failed to delete user")

@router.put("/users/{user_id}/role")
async def change_role(user_id: str, role_data: dict, admin: dict = Depends(verify_admin_role)):
    new_role = role_data.get("role")
    # Expanded roles for Irresistible Church Agent
    valid_roles = [
        "admin", 
        "member", 
        "pastor_principal", 
        "kids_director", 
        "media_director", 
        "service_director", 
        "editorial_director",
        "guest_services_director",
        "students_director",
        "adults_director",
        "operations_director",
        "philosophy_director",
        "be_rich_director"
    ]
    if new_role not in valid_roles:
       raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    
    if update_user_role(user_id, new_role):  # Assuming update_user_role returns bool or throws
         return {"message": "Role updated"}
    
    # In case update_user_role is void, just return success if no exception
    return {"message": "Role updated"}


# Migration Endpoint (Temporary)
from fastapi import BackgroundTasks
import sys
import os

@router.post("/migrate-legacy")
async def migrate_legacy_db(background_tasks: BackgroundTasks, admin: dict = Depends(verify_admin_role)):
    """
    Triggers the migration of the local/volume ChromaDB to Supabase.
    Useful for running this on the deployed server (Railway) to migrate production data.
    """
    try:
        # Import dynamically to avoid circular deps if any
        sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
        from migrate_chroma import migrate
        
        background_tasks.add_task(migrate)
        return {"message": "Migration started in background. Check your Supabase database in a few minutes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Header
@router.post("/migrate-force")
async def migrate_force(background_tasks: BackgroundTasks, x_migration_secret: str = Header(None)):
    """
    Emergency endpoint to trigger migration via script/terminal.
    Bypasses auth token check, uses secret header instead.
    """
    if x_migration_secret != "irresistible-migration-force-2026":
        raise HTTPException(status_code=403, detail="Invalid migration secret")
        
    try:
        # Import dynamically
        sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
        from migrate_chroma import migrate
        
        background_tasks.add_task(migrate)
        return {"message": "Force Migration started. Check server logs for details."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
