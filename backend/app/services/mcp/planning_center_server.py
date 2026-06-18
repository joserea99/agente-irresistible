"""
Planning Center MCP Server — internal MCP server wrapping Planning Center Online API.

Reutilizes patterns from the user's existing code at:
/Users/joserea/iCloud Drive (archivo)/Desktop/mi_asistente_planning_center/

API: https://api.planningcenteronline.com/services/v2
Auth: Bearer token via PLANNING_CENTER_API_TOKEN env var
"""

import logging
import requests
from typing import Any, Dict, List, Optional

from ...core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.planningcenteronline.com"


class PlanningCenterMcpServer:
    """
    Internal MCP server for Planning Center Online.
    Exposes church management data as MCP tools.
    Uses per-user OAuth2 tokens stored in Supabase.
    """

    SERVER_NAME = "planning_center"
    ALLOWED_ROLES = ["*"]  # Any director can use if they've connected their PC

    def __init__(self, user_id: Optional[str] = None, access_token: Optional[str] = None):
        self.user_id = user_id
        self.access_token = access_token

        # If user_id provided but no token, fetch from Supabase
        if user_id and not access_token:
            from ...routers.oauth_integration import get_user_pco_token
            self.access_token = get_user_pco_token(user_id)

    def is_configured(self) -> bool:
        """Check if we have a valid access token."""
        return bool(self.access_token)

    # ── API Helpers ──────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        """Build authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get(self, path: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a GET request to the Planning Center API using OAuth Bearer token."""
        if not self.access_token:
            return None
        url = f"{BASE_URL}{path}"
        try:
            response = requests.get(url, headers=self._headers(), params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Planning Center API {response.status_code}: {path}")
            return None
        except requests.RequestException as e:
            logger.error(f"Planning Center API error: {e}")
            return None

    def _get_paginated(self, path: str, params: Optional[Dict] = None, max_pages: int = 5) -> List[Dict]:
        """Fetch all paginated results from a Planning Center endpoint."""
        if not self.access_token:
            return []
        all_results = []
        url = f"{BASE_URL}{path}"
        page = 0

        while url and page < max_pages:
            try:
                response = requests.get(url, headers=self._headers(), params=params, timeout=15)
                if response.status_code != 200:
                    break
                data = response.json()
                all_results.extend(data.get("data", []))
                url = data.get("links", {}).get("next")
                params = None  # params only for first request
                page += 1
            except requests.RequestException as e:
                logger.error(f"Planning Center pagination error: {e}")
                break

        return all_results

    def _format_person(self, person: Dict) -> Dict:
        """Extract useful fields from a person record."""
        attrs = person.get("attributes", {})
        return {
            "id": person.get("id"),
            "name": f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip(),
            "email": attrs.get("primary_email_address", ""),
            "phone": attrs.get("primary_phone_number", ""),
            "status": attrs.get("status", ""),
            "created_at": attrs.get("created_at", ""),
        }

    def _format_service(self, service: Dict) -> Dict:
        """Extract useful fields from a service type record."""
        attrs = service.get("attributes", {})
        return {
            "id": service.get("id"),
            "name": attrs.get("name", ""),
            "frequency": attrs.get("frequency", ""),
            "last_plan_from": attrs.get("last_plan_from", ""),
        }

    def _format_plan(self, plan: Dict) -> Dict:
        """Extract useful fields from a plan record."""
        attrs = plan.get("attributes", {})
        return {
            "id": plan.get("id"),
            "title": attrs.get("title", ""),
            "dates": attrs.get("dates", ""),
            "sort_date": attrs.get("sort_date", ""),
            "series_title": attrs.get("series_title", ""),
            "items_count": attrs.get("items_count", 0),
        }

    def _format_song(self, song: Dict) -> Dict:
        """Extract useful fields from a song record."""
        attrs = song.get("attributes", {})
        return {
            "id": song.get("id"),
            "title": attrs.get("title", ""),
            "author": attrs.get("author", ""),
            "ccli_number": attrs.get("ccli_number", ""),
            "last_scheduled_at": attrs.get("last_scheduled_at", ""),
        }

    def _format_team_member(self, member: Dict) -> Dict:
        """Extract useful fields from a team member record."""
        attrs = member.get("attributes", {})
        return {
            "id": member.get("id"),
            "name": attrs.get("name", ""),
            "status": attrs.get("status", ""),
            "team_position_name": attrs.get("team_position_name", ""),
        }

    # ── MCP Tool Definitions ────────────────────────────────────

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions for this server."""
        return [
            {
                "name": "search_people",
                "description": "Buscar personas/miembros de la iglesia por nombre en Planning Center. Devuelve nombre, email, teléfono y estado.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Nombre o parte del nombre de la persona a buscar",
                        }
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_services",
                "description": "Listar todos los tipos de servicio de la iglesia (ej: Servicio Dominical, Servicio de Jóvenes, etc.) desde Planning Center.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_service_plans",
                "description": "Obtener los planes de servicio más recientes para un tipo de servicio específico. Incluye fecha, título y serie.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service_type_id": {
                            "type": "string",
                            "description": "ID del tipo de servicio (obtenido de get_services). Si no se provee, usa el primer servicio disponible.",
                        }
                    },
                },
            },
            {
                "name": "get_songs",
                "description": "Listar canciones del repertorio de la iglesia en Planning Center. Incluye título, autor y número CCLI.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Filtrar canciones por título (opcional)",
                        }
                    },
                },
            },
            {
                "name": "get_plan_team",
                "description": "Ver el equipo/voluntarios asignados a un plan de servicio específico. Incluye nombre, posición y estado de confirmación.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service_type_id": {
                            "type": "string",
                            "description": "ID del tipo de servicio",
                        },
                        "plan_id": {
                            "type": "string",
                            "description": "ID del plan específico (obtenido de get_service_plans)",
                        },
                    },
                    "required": ["service_type_id", "plan_id"],
                },
            },
        ]

    # ── MCP Tool Execution ──────────────────────────────────────

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool by name."""
        handlers = {
            "search_people": self._tool_search_people,
            "get_services": self._tool_get_services,
            "get_service_plans": self._tool_get_service_plans,
            "get_songs": self._tool_get_songs,
            "get_plan_team": self._tool_get_plan_team,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return handler(**arguments)
        except Exception as e:
            logger.error(f"Planning Center tool {tool_name} failed: {e}")
            return {"error": str(e)}

    def _tool_search_people(self, query: str) -> Dict:
        """Search for people by name."""
        data = self._get("/people/v2/people", params={"where[search_name]": query, "per_page": 10})
        if not data:
            return {"results": [], "message": "No se pudo conectar con Planning Center."}

        people = [self._format_person(p) for p in data.get("data", [])]
        return {
            "results": people,
            "total": data.get("meta", {}).get("total_count", len(people)),
            "message": f"Se encontraron {len(people)} persona(s) con '{query}'.",
        }

    def _tool_get_services(self) -> Dict:
        """List all service types."""
        results = self._get_paginated("/services/v2/service_types")
        if not results:
            return {"results": [], "message": "No se encontraron tipos de servicio."}

        services = [self._format_service(s) for s in results]
        return {
            "results": services,
            "message": f"La iglesia tiene {len(services)} tipo(s) de servicio.",
        }

    def _tool_get_service_plans(self, service_type_id: str = "") -> Dict:
        """Get recent plans for a service type."""
        # If no service type provided, get the first one
        if not service_type_id:
            service_types = self._get_paginated("/services/v2/service_types")
            if not service_types:
                return {"results": [], "message": "No hay tipos de servicio configurados."}
            service_type_id = service_types[0]["id"]

        data = self._get(
            f"/services/v2/service_types/{service_type_id}/plans",
            params={"order": "-sort_date", "per_page": 5},
        )
        if not data:
            return {"results": [], "message": "No se encontraron planes."}

        plans = [self._format_plan(p) for p in data.get("data", [])]
        return {
            "results": plans,
            "service_type_id": service_type_id,
            "message": f"Últimos {len(plans)} plan(es) de servicio.",
        }

    def _tool_get_songs(self, query: str = "") -> Dict:
        """List songs, optionally filtered by title."""
        params = {"per_page": 20}
        if query:
            params["where[title]"] = query

        results = self._get_paginated("/services/v2/songs", params=params, max_pages=2)
        songs = [self._format_song(s) for s in results]
        return {
            "results": songs,
            "message": f"Se encontraron {len(songs)} canción(es)." + (f" Filtro: '{query}'" if query else ""),
        }

    def _tool_get_plan_team(self, service_type_id: str, plan_id: str) -> Dict:
        """Get team members for a specific plan."""
        data = self._get(f"/services/v2/service_types/{service_type_id}/plans/{plan_id}/team_members")
        if not data:
            return {"results": [], "message": "No se pudo obtener el equipo."}

        members = [self._format_team_member(m) for m in data.get("data", [])]
        confirmed = sum(1 for m in members if m.get("status") == "C")
        return {
            "results": members,
            "total": len(members),
            "confirmed": confirmed,
            "message": f"Equipo del plan: {len(members)} miembros ({confirmed} confirmados).",
        }
