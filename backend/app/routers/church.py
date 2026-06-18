from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from ..services.church_service import church_profile_service
from .auth import verify_active_user

router = APIRouter()


class ChurchProfile(BaseModel):
    church_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    size: Optional[str] = None
    service_schedule: Optional[str] = None
    current_series: Optional[str] = None
    vision: Optional[str] = None
    notes: Optional[str] = None


@router.get("/profile")
async def get_church_profile(current_user: dict = Depends(verify_active_user)):
    """Read the church profile (memory) shown to every director."""
    return {"profile": church_profile_service.get_profile(use_cache=False)}


@router.put("/profile")
async def update_church_profile(
    profile: ChurchProfile,
    current_user: dict = Depends(verify_active_user),
):
    """Update the church profile. Admin / lead pastor only."""
    if current_user.get("role") not in ("admin", "pastor_principal"):
        raise HTTPException(status_code=403, detail="Solo el administrador puede editar el perfil de la iglesia.")

    ok = church_profile_service.upsert(profile.model_dump(exclude_none=True))
    if not ok:
        raise HTTPException(status_code=500, detail="No se pudo guardar el perfil (¿migración 003 aplicada?).")

    return {"success": True, "profile": church_profile_service.get_profile(use_cache=False)}
