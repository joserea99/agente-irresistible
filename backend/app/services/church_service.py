"""
Church Profile Service — the agent's long-term "memory" about THIS church.

Stores a small singleton profile (name, city, size, schedule, current series,
vision, notes) that gets injected into every director's system prompt so the
agent gives advice grounded in the church's real context, not generic answers.
"""

import time
import logging
from typing import Dict, Optional

from .supabase_service import supabase_service

logger = logging.getLogger(__name__)

_FIELDS = [
    "church_name",
    "city",
    "country",
    "size",
    "service_schedule",
    "current_series",
    "vision",
    "notes",
]

_LABELS = {
    "church_name": "Nombre de la iglesia",
    "city": "Ciudad",
    "country": "País",
    "size": "Tamaño / asistencia",
    "service_schedule": "Horario de servicios",
    "current_series": "Serie / predicación actual",
    "vision": "Visión / 'el win'",
    "notes": "Notas adicionales",
}


class ChurchProfileService:
    """Read/write the singleton church profile, with a short in-memory cache."""

    _cache: Optional[Dict] = None
    _cache_ts: float = 0.0
    _ttl: float = 60.0  # seconds

    def get_profile(self, use_cache: bool = True) -> Dict:
        now = time.time()
        if use_cache and ChurchProfileService._cache is not None and (now - ChurchProfileService._cache_ts) < self._ttl:
            return ChurchProfileService._cache

        client = supabase_service.get_client()
        profile: Dict = {}
        if client:
            try:
                res = client.table("church_profile").select("*").eq("id", 1).single().execute()
                profile = res.data or {}
            except Exception as e:
                # Table may not exist yet (migration not applied) — degrade gracefully.
                logger.debug(f"church_profile not available: {e}")
                profile = {}

        ChurchProfileService._cache = profile
        ChurchProfileService._cache_ts = now
        return profile

    def upsert(self, data: Dict) -> bool:
        client = supabase_service.get_client()
        if not client:
            return False
        payload = {k: v for k, v in data.items() if k in _FIELDS}
        payload["id"] = 1
        try:
            client.table("church_profile").upsert(payload).execute()
            ChurchProfileService._cache = None  # invalidate
            return True
        except Exception as e:
            logger.error(f"Error upserting church_profile: {e}")
            return False

    def build_context(self) -> str:
        """Return a formatted prompt block, or '' if nothing meaningful is set."""
        profile = self.get_profile()
        lines = []
        for field in _FIELDS:
            value = (profile.get(field) or "").strip() if isinstance(profile.get(field), str) else profile.get(field)
            if value:
                lines.append(f"- {_LABELS[field]}: {value}")

        if not lines:
            return ""

        return (
            "\n\n## CONTEXTO DE ESTA IGLESIA (memoria — úsalo para personalizar tus respuestas):\n"
            + "\n".join(lines)
            + "\nAdapta tus recomendaciones a este contexto específico cuando sea relevante.\n"
        )


church_profile_service = ChurchProfileService()
