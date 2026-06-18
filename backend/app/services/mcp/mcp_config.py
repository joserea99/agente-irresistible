"""
MCP Configuration — defines which MCP servers to connect and role-based access.

Inspired by Claw Code's McpClientBootstrap pattern.
Each deployment (church) configures its own servers via env vars or JSON config.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MCP_CONFIG_PATH = os.environ.get(
    "MCP_CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp_servers.json"),
)


@dataclass
class McpServerConfig:
    """Configuration for a single MCP server."""

    name: str
    transport: str = "stdio"  # "stdio" or "http"
    command: Optional[str] = None  # For stdio: executable to spawn
    args: List[str] = field(default_factory=list)  # For stdio: arguments
    env: Dict[str, str] = field(default_factory=dict)  # Extra env vars for the process
    url: Optional[str] = None  # For http: server URL
    credentials_env: Optional[str] = None  # Env var name holding the API key/token
    allowed_roles: List[str] = field(default_factory=lambda: ["*"])  # ["*"] = all roles

    def is_role_allowed(self, user_role: str) -> bool:
        """Check if a user role has access to this server."""
        if "*" in self.allowed_roles:
            return True
        return user_role in self.allowed_roles

    def has_credentials(self) -> bool:
        """Check if required credentials are available in environment."""
        if not self.credentials_env:
            return True  # No credentials required
        return bool(os.environ.get(self.credentials_env))


@dataclass
class McpConfig:
    """Full MCP configuration for this deployment."""

    servers: List[McpServerConfig] = field(default_factory=list)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "McpConfig":
        """Load MCP config from JSON file. Returns empty config if file doesn't exist."""
        path = config_path or MCP_CONFIG_PATH
        if not os.path.exists(path):
            logger.info(f"No MCP config found at {path}. MCP integration disabled.")
            return cls()

        try:
            with open(path) as f:
                data = json.load(f)

            servers = []
            for srv in data.get("servers", []):
                servers.append(
                    McpServerConfig(
                        name=srv["name"],
                        transport=srv.get("transport", "stdio"),
                        command=srv.get("command"),
                        args=srv.get("args", []),
                        env=srv.get("env", {}),
                        url=srv.get("url"),
                        credentials_env=srv.get("credentials_env"),
                        allowed_roles=srv.get("allowed_roles", ["*"]),
                    )
                )

            logger.info(f"Loaded MCP config: {len(servers)} server(s) from {path}")
            return cls(servers=servers)
        except Exception as e:
            logger.error(f"Failed to load MCP config from {path}: {e}")
            return cls()

    def get_servers_for_role(self, user_role: str) -> List[McpServerConfig]:
        """Get servers accessible to a specific user role."""
        return [
            s
            for s in self.servers
            if s.is_role_allowed(user_role) and s.has_credentials()
        ]
