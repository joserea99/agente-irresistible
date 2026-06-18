"""
OAuth Integration Router — handles OAuth2 flows for external services.
Currently supports: Planning Center Online.

Flow: User clicks "Connect" → redirect to provider → callback with code → exchange for tokens → store in Supabase.
"""

import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse

from ..core.config import settings
from ..services.supabase_service import supabase_service
from .auth import verify_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory state store (short-lived, for CSRF protection)
# In production, use Redis or Supabase for multi-instance support
_oauth_states: dict = {}

PCO_AUTH_URL = "https://api.planningcenteronline.com/oauth/authorize"
PCO_TOKEN_URL = "https://api.planningcenteronline.com/oauth/token"
PCO_API_BASE = "https://api.planningcenteronline.com"


# ── Planning Center OAuth Endpoints ──────────────────────────────


@router.post("/planning-center/authorize")
async def start_pco_oauth(current_user: dict = Depends(verify_active_user)):
    """
    Generate Planning Center OAuth authorization URL.
    Frontend should redirect user to this URL.
    """
    if not settings.planning_center_client_id:
        raise HTTPException(status_code=503, detail="Planning Center OAuth not configured")

    user_id = current_user.get("id")
    state = secrets.token_urlsafe(32)

    # Store state → user_id mapping (expires in 10 min)
    _oauth_states[state] = {
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
    }

    # Clean old states (older than 10 min)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    expired = [k for k, v in _oauth_states.items() if v["created_at"] < cutoff]
    for k in expired:
        del _oauth_states[k]

    params = {
        "client_id": settings.planning_center_client_id,
        "redirect_uri": settings.planning_center_redirect_uri,
        "response_type": "code",
        "scope": "people services check_ins giving groups calendar",
        "state": state,
    }

    auth_url = f"{PCO_AUTH_URL}?{urlencode(params)}"
    return {"auth_url": auth_url, "state": state}


@router.get("/planning-center/callback")
async def pco_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """
    Handle OAuth callback from Planning Center.
    Exchanges authorization code for access/refresh tokens.
    Stores tokens in Supabase and redirects to frontend.
    """
    # Verify state
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    user_id = state_data["user_id"]

    # Exchange code for tokens
    try:
        token_response = requests.post(
            PCO_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.planning_center_client_id,
                "client_secret": settings.planning_center_client_secret,
                "redirect_uri": settings.planning_center_redirect_uri,
            },
            timeout=15,
        )

        if token_response.status_code != 200:
            logger.error(f"PCO token exchange failed: {token_response.status_code} {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

        tokens = token_response.json()
    except requests.RequestException as e:
        logger.error(f"PCO token exchange error: {e}")
        raise HTTPException(status_code=500, detail="Error connecting to Planning Center")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in", 7200)  # Default 2 hours

    if not access_token or not refresh_token:
        raise HTTPException(status_code=400, detail="Invalid token response from Planning Center")

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Fetch church/organization name from Planning Center
    church_name = _fetch_church_name(access_token)

    # Store tokens in Supabase
    try:
        client = supabase_service.get_client()
        # Upsert (insert or update if user already has a connection)
        client.table("planning_center_integrations").upsert(
            {
                "user_id": user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat(),
                "church_name": church_name,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="user_id",
        ).execute()

        logger.info(f"Planning Center connected for user {user_id}: {church_name}")
    except Exception as e:
        logger.error(f"Failed to store PCO tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to save connection")

    # Redirect to frontend settings page
    frontend_url = settings.allowed_origins.split(",")[0].strip()
    if frontend_url == "http://localhost:3000":
        redirect_url = f"http://localhost:3000/settings?pc_connected=true"
    else:
        redirect_url = f"{frontend_url}/settings?pc_connected=true"

    return RedirectResponse(url=redirect_url)


@router.get("/planning-center/status")
async def get_pco_status(current_user: dict = Depends(verify_active_user)):
    """Check if the current user has Planning Center connected."""
    user_id = current_user.get("id")

    try:
        client = supabase_service.get_client()
        result = (
            client.table("planning_center_integrations")
            .select("church_name, connected_at, expires_at")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if result.data:
            expires_at = datetime.fromisoformat(result.data["expires_at"].replace("Z", "+00:00"))
            is_expired = expires_at < datetime.now(timezone.utc)
            return {
                "connected": True,
                "church_name": result.data.get("church_name", ""),
                "connected_at": result.data.get("connected_at"),
                "token_expired": is_expired,
            }
    except Exception:
        pass

    return {"connected": False}


@router.delete("/planning-center/disconnect")
async def disconnect_pco(current_user: dict = Depends(verify_active_user)):
    """Remove Planning Center connection for the current user."""
    user_id = current_user.get("id")

    try:
        client = supabase_service.get_client()
        client.table("planning_center_integrations").delete().eq("user_id", user_id).execute()
        logger.info(f"Planning Center disconnected for user {user_id}")
        return {"success": True, "message": "Planning Center desconectado"}
    except Exception as e:
        logger.error(f"Failed to disconnect PCO: {e}")
        raise HTTPException(status_code=500, detail="Error al desconectar")


# ── Token Management Helpers ─────────────────────────────────────


def get_user_pco_token(user_id: str) -> Optional[str]:
    """
    Get a valid Planning Center access token for a user.
    Auto-refreshes if expired. Returns None if not connected.
    """
    try:
        client = supabase_service.get_client()
        result = (
            client.table("planning_center_integrations")
            .select("access_token, refresh_token, expires_at")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not result.data:
            return None

        access_token = result.data["access_token"]
        refresh_token = result.data["refresh_token"]
        expires_at = datetime.fromisoformat(result.data["expires_at"].replace("Z", "+00:00"))

        # Check if token is expired (with 5 min buffer)
        if expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
            access_token = _refresh_pco_token(user_id, refresh_token)
            if not access_token:
                return None

        return access_token
    except Exception as e:
        logger.error(f"Error getting PCO token for user {user_id}: {e}")
        return None


def _refresh_pco_token(user_id: str, refresh_token: str) -> Optional[str]:
    """Refresh an expired Planning Center token."""
    try:
        response = requests.post(
            PCO_TOKEN_URL,
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.planning_center_client_id,
                "client_secret": settings.planning_center_client_secret,
            },
            timeout=15,
        )

        if response.status_code != 200:
            logger.error(f"PCO token refresh failed: {response.status_code}")
            return None

        tokens = response.json()
        new_access_token = tokens["access_token"]
        new_refresh_token = tokens.get("refresh_token", refresh_token)
        expires_in = tokens.get("expires_in", 7200)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Update in Supabase
        client = supabase_service.get_client()
        client.table("planning_center_integrations").update(
            {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "expires_at": expires_at.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("user_id", user_id).execute()

        logger.info(f"PCO token refreshed for user {user_id}")
        return new_access_token
    except Exception as e:
        logger.error(f"PCO token refresh error: {e}")
        return None


def _fetch_church_name(access_token: str) -> str:
    """Fetch the organization/church name from Planning Center."""
    try:
        response = requests.get(
            f"{PCO_API_BASE}/people/v2",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            name = data.get("data", {}).get("attributes", {}).get("name", "")
            return name or "Planning Center"
    except Exception as e:
        logger.warning(f"Could not fetch church name: {e}")
    return "Planning Center"
