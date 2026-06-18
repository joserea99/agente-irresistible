"""
MCP Router — API endpoints for managing MCP server integrations.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from .auth import verify_active_user
from ..services.mcp import McpToolRegistry

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Global registry instance (initialized in main.py startup)
_registry: Optional[McpToolRegistry] = None


def set_registry(registry: McpToolRegistry):
    """Called from main.py to inject the global registry."""
    global _registry
    _registry = registry


def get_registry() -> McpToolRegistry:
    if _registry is None:
        raise HTTPException(status_code=503, detail="MCP registry not initialized")
    return _registry


class ToolCallRequest(BaseModel):
    tool_name: str  # Namespaced: mcp__{server}__{tool}
    arguments: Dict[str, Any] = {}


@router.get("/servers")
async def list_servers(
    current_user: dict = Depends(verify_active_user),
):
    """List all MCP servers and their status."""
    registry = get_registry()
    return {"servers": registry.get_servers_status()}


@router.get("/tools")
async def list_tools(
    current_user: dict = Depends(verify_active_user),
):
    """List all available MCP tools (filtered by user role)."""
    registry = get_registry()
    user_role = current_user.get("role", "member")
    tools = registry.get_available_tools(user_role=user_role)
    return {"tools": tools, "count": len(tools)}


@router.post("/call")
async def call_tool(
    request: ToolCallRequest,
    current_user: dict = Depends(verify_active_user),
):
    """Execute an MCP tool (with role-based access and per-user token support)."""
    registry = get_registry()
    user_role = current_user.get("role", "member")
    user_id = current_user.get("id")

    result = registry.call_namespaced_tool(
        namespaced_name=request.tool_name,
        arguments=request.arguments,
        user_role=user_role,
        user_id=user_id,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"result": result}


@router.post("/servers/{server_name}/restart")
async def restart_server(
    server_name: str,
    current_user: dict = Depends(verify_active_user),
):
    """Restart a failed or degraded MCP server (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can restart MCP servers")

    registry = get_registry()
    success = registry.restart_server(server_name)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to restart server: {server_name}")

    return {"success": True, "message": f"Server {server_name} restarted"}
