"""
MCP Client — communicates with MCP servers via stdio or HTTP transport.

Implements the Model Context Protocol for tool discovery and execution.
Inspired by Claw Code's mcp_client.rs multi-transport pattern.
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from .mcp_config import McpServerConfig

logger = logging.getLogger(__name__)


class McpClient:
    """Client for communicating with a single MCP server."""

    def __init__(self, config: McpServerConfig):
        self.config = config
        self.name = config.name
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._tools: List[Dict[str, Any]] = []
        self._resources: List[Dict[str, Any]] = []

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def start(self) -> bool:
        """Start the MCP server process (stdio transport only)."""
        if self.config.transport != "stdio":
            logger.info(f"MCP server {self.name}: HTTP transport, no process to start.")
            return True

        if not self.config.command:
            logger.error(f"MCP server {self.name}: no command specified.")
            return False

        env = {**os.environ, **self.config.env}
        if self.config.credentials_env:
            cred = os.environ.get(self.config.credentials_env, "")
            if cred:
                env[self.config.credentials_env] = cred

        try:
            cmd = [self.config.command] + self.config.args
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )
            logger.info(f"MCP server {self.name}: started (pid={self._process.pid})")

            # Initialize with JSON-RPC
            self._send_initialize()
            return True
        except FileNotFoundError:
            logger.error(f"MCP server {self.name}: command not found: {self.config.command}")
            return False
        except Exception as e:
            logger.error(f"MCP server {self.name}: failed to start: {e}")
            return False

    def stop(self):
        """Stop the MCP server process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
            logger.info(f"MCP server {self.name}: stopped.")

    def _send_jsonrpc(self, method: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Send a JSON-RPC request and read the response."""
        if not self._process or not self._process.stdin or not self._process.stdout:
            return None

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params:
            request["params"] = params

        try:
            msg = json.dumps(request) + "\n"
            self._process.stdin.write(msg)
            self._process.stdin.flush()

            line = self._process.stdout.readline()
            if line:
                return json.loads(line.strip())
        except Exception as e:
            logger.error(f"MCP {self.name} JSON-RPC error ({method}): {e}")
        return None

    def _send_initialize(self):
        """Send the MCP initialize handshake."""
        result = self._send_jsonrpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "irresistible-agent", "version": "1.0.0"},
        })
        if result and "result" in result:
            logger.info(f"MCP {self.name}: initialized successfully")
            # Send initialized notification
            self._send_jsonrpc("notifications/initialized")

    def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from the MCP server."""
        result = self._send_jsonrpc("tools/list")
        if result and "result" in result:
            self._tools = result["result"].get("tools", [])
            logger.info(f"MCP {self.name}: discovered {len(self._tools)} tool(s)")
        return self._tools

    def discover_resources(self) -> List[Dict[str, Any]]:
        """Discover available resources from the MCP server."""
        result = self._send_jsonrpc("resources/list")
        if result and "result" in result:
            self._resources = result["result"].get("resources", [])
        return self._resources

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the MCP server."""
        result = self._send_jsonrpc("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

        if result is None:
            return {"error": f"No response from MCP server {self.name}"}

        if "error" in result:
            return {"error": result["error"].get("message", "Unknown MCP error")}

        if "result" in result:
            return result["result"]

        return {"error": "Unexpected MCP response format"}

    def get_tools_as_gemini_declarations(self) -> List[Dict[str, Any]]:
        """
        Convert MCP tool schemas to Gemini function declarations.
        This allows MCP tools to be used as Gemini tool-use functions.
        """
        declarations = []
        for tool in self._tools:
            decl = {
                "name": f"mcp__{self.name}__{tool['name']}",
                "description": tool.get("description", f"MCP tool: {tool['name']}"),
            }
            if "inputSchema" in tool:
                decl["parameters"] = tool["inputSchema"]
            declarations.append(decl)
        return declarations

    @property
    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None
