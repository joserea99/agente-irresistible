"""
sync.py - Sync Management Router
Provides admin endpoints to manually trigger and monitor the full library sync.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from ..services.auth_service import verify_token
from ..services.sync_service import (
    full_sync,
    get_last_sync_status,
    coverage_stats,
    reindex_thin,
    diagnose_coverage,
)

router = APIRouter()
security = HTTPBearer()


class ReindexRequest(BaseModel):
    limit: Optional[int] = None  # cap how many name-only docs to re-ingest (batching)


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


@router.get("/coverage")
async def get_coverage(admin: dict = Depends(get_current_admin)):
    """
    Knowledge-base coverage: total documents vs. how many are indexed
    'name-only' (no extracted body). Read-only, safe to call anytime.
    """
    return coverage_stats()


@router.get("/diagnose")
async def get_diagnose(admin: dict = Depends(get_current_admin)):
    """
    Live Brandfolder reachability audit: per-collection reachable count vs. the
    total Brandfolder declares, unique union, truncation flags, and the gap vs.
    the umbrella collection. Read-only. May take several seconds (paginates the
    whole library live).
    """
    return diagnose_coverage()


@router.post("/reindex-thin")
async def trigger_reindex_thin(
    request: ReindexRequest,
    background_tasks: BackgroundTasks,
    admin: dict = Depends(get_current_admin),
):
    """
    Re-ingest documents indexed 'name-only' (Word/PowerPoint that previously
    yielded no text) using the new multi-format extractor. Runs in the background.
    Pass an optional `limit` to process in controlled batches.
    """
    background_tasks.add_task(reindex_thin, request.limit, False)
    return {
        "message": "🧹 Re-indexado de documentos incompletos iniciado en segundo plano.",
        "note": "Borra los 'solo nombre' y los vuelve a ingerir con el extractor nuevo. Revisa /sync/coverage al terminar.",
        "limit": request.limit,
    }
