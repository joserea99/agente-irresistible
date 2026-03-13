"""
sync.py - Sync Management Router
Provides admin endpoints to manually trigger and monitor the full library sync.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.auth_service import verify_token
from ..services.sync_service import full_sync, get_last_sync_status

router = APIRouter()
security = HTTPBearer()


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    profile, error = verify_token(token)
    if error != "success" or not profile:
        raise HTTPException(status_code=401, detail="Invalid token")
    if profile.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return profile


@router.post("/trigger")
async def trigger_full_sync(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin)
):
    """
    Manually trigger a full Brandfolder library sync.
    Only processes content that hasn't been indexed yet — no duplicates, no data loss.
    """
    background_tasks.add_task(full_sync)
    return {
        "message": "✅ Full library sync started in the background.",
        "note": "Only NEW content will be indexed. Existing memory is preserved. Check /sync/status for progress."
    }


@router.get("/status")
async def get_sync_status(admin: dict = Depends(get_current_admin)):
    """
    Returns the status of the last (or current) sync run.
    """
    status = get_last_sync_status()
    return status
