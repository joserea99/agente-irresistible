"""
MCP Tool Registry — manages multiple MCP servers with health tracking.

Inspired by Claw Code's McpToolRegistry (mcp_tool_bridge.rs).
Supports graceful degradation: if one server fails, others continue working.
"""

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .mcp_client import McpClient
from .mcp_config import McpConfig, McpServerConfig

logger = logging.getLogger(__name__)


class ServerHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class McpServerState:
    """Runtime state for a connected MCP server."""

    config: McpServerConfig
    client: Optional[McpClient] = None
    internal_server: Any = None  # For embedded servers (e.g., PlanningCenterMcpServer)
    health: ServerHealth = ServerHealth.STOPPED
    tools: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def is_internal(self) -> bool:
        return self.internal_server is not None


class McpToolRegistry:
    """
    Thread-safe registry of MCP servers and their tools.
    Provides role-based access filtering and graceful degradation.
    """

    def __init__(self):
        self._servers: Dict[str, McpServerState] = {}
        self._lock = threading.Lock()

    def initialize(self, config: Optional[McpConfig] = None):
        """Initialize the registry from config, starting all configured servers."""
        mcp_config = config or McpConfig.load()

        if not mcp_config.servers:
            logger.info("No MCP servers configured.")
            return

        for srv_config in mcp_config.servers:
            self.register_server(srv_config)

    def register_internal_server(self, internal_server: Any):
        """
        Register an internal (embedded) MCP server.
        The server must have: SERVER_NAME, ALLOWED_ROLES, get_tool_definitions(), call_tool().
        """
        name = internal_server.SERVER_NAME
        allowed_roles = internal_server.ALLOWED_ROLES

        config = McpServerConfig(
            name=name,
            transport="internal",
            allowed_roles=allowed_roles,
        )

        tools = internal_server.get_tool_definitions()

        with self._lock:
            state = McpServerState(
                config=config,
                internal_server=internal_server,
                health=ServerHealth.HEALTHY,
                tools=tools,
            )
            self._servers[name] = state

        logger.info(f"MCP registry: {name} registered as internal server ({len(tools)} tools)")

    def register_server(self, config: McpServerConfig):
        """Register and start a single MCP server."""
        client = McpClient(config)

        with self._lock:
            state = McpServerState(config=config, client=client)
            self._servers[config.name] = state

        # Try to start
        try:
            if client.start():
                tools = client.discover_tools()
                with self._lock:
                    state.tools = tools
                    state.health = ServerHealth.HEALTHY
                logger.info(
                    f"MCP registry: {config.name} healthy ({len(tools)} tools)"
                )
            else:
                with self._lock:
                    state.health = ServerHealth.FAILED
                    state.error_message = "Failed to start server process"
        except Exception as e:
            with self._lock:
                state.health = ServerHealth.FAILED
                state.error_message = str(e)
            logger.error(f"MCP registry: {config.name} failed: {e}")

    def get_servers_status(self) -> List[Dict[str, Any]]:
        """Get status of all registered servers."""
        with self._lock:
            return [
                {
                    "name": name,
                    "health": state.health.value,
                    "tools_count": len(state.tools),
                    "error": state.error_message,
                    "allowed_roles": state.config.allowed_roles,
                }
                for name, state in self._servers.items()
            ]

    def get_available_tools(self, user_role: str = "*") -> List[Dict[str, Any]]:
        """
        Get all available tools, filtered by user role.
        Returns tools with namespaced names: mcp__{server}__{tool}.
        """
        tools = []
        with self._lock:
            for name, state in self._servers.items():
                if state.health != ServerHealth.HEALTHY:
                    continue
                if not state.config.is_role_allowed(user_role):
                    continue

                for tool in state.tools:
                    tools.append(
                        {
                            "name": f"mcp__{name}__{tool['name']}",
                            "server": name,
                            "original_name": tool["name"],
                            "description": tool.get("description", ""),
                            "input_schema": tool.get("inputSchema", {}),
                        }
                    )
        return tools

    def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any],
        user_role: str = "*",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool on a specific MCP server, with role-based access check.
        For per-user servers (e.g., Planning Center), user_id is used to fetch their tokens.
        """
        with self._lock:
            state = self._servers.get(server_name)

        if not state:
            return {"error": f"MCP server '{server_name}' not found"}

        if state.health != ServerHealth.HEALTHY:
            return {"error": f"MCP server '{server_name}' is {state.health.value}"}

        if not state.config.is_role_allowed(user_role):
            return {"error": f"Access denied: role '{user_role}' cannot use '{server_name}'"}

        try:
            if state.is_internal:
                # For per-user servers (like Planning Center), create fresh instance
                if user_id and hasattr(state.internal_server.__class__, '__init__'):
                    try:
                        fresh_server = state.internal_server.__class__(user_id=user_id)
                        if fresh_server.is_configured():
                            result = fresh_server.call_tool(tool_name, arguments)
                        else:
                            return {"error": f"Servicio '{server_name}' no conectado. Ve a Integraciones para conectarlo."}
                    except TypeError:
                        result = state.internal_server.call_tool(tool_name, arguments)
                else:
                    result = state.internal_server.call_tool(tool_name, arguments)
            else:
                result = state.client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            with self._lock:
                state.health = ServerHealth.DEGRADED
                state.error_message = str(e)
            logger.error(f"MCP tool call failed ({server_name}/{tool_name}): {e}")
            return {"error": str(e)}

    def call_namespaced_tool(
        self, namespaced_name: str, arguments: Dict[str, Any],
        user_role: str = "*",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call a tool using its namespaced name (mcp__{server}__{tool}).
        """
        parts = namespaced_name.split("__")
        if len(parts) != 3 or parts[0] != "mcp":
            return {"error": f"Invalid namespaced tool name: {namespaced_name}"}

        server_name = parts[1]
        tool_name = parts[2]
        return self.call_tool(server_name, tool_name, arguments, user_role, user_id)

    def restart_server(self, server_name: str) -> bool:
        """Restart a failed or degraded server."""
        with self._lock:
            state = self._servers.get(server_name)

        if not state:
            return False

        state.client.stop()

        try:
            if state.client.start():
                tools = state.client.discover_tools()
                with self._lock:
                    state.tools = tools
                    state.health = ServerHealth.HEALTHY
                    state.error_message = None
                return True
        except Exception as e:
            with self._lock:
                state.health = ServerHealth.FAILED
                state.error_message = str(e)
        return False

    def shutdown(self):
        """Stop all MCP servers."""
        with self._lock:
            for name, state in self._servers.items():
                state.client.stop()
                state.health = ServerHealth.STOPPED
            logger.info("MCP registry: all servers stopped.")
