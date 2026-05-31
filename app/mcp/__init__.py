"""Ready For Robots MCP server — exposes public API tools to third-party AI clients."""

from app.mcp.server import create_mcp_app

__all__ = ["create_mcp_app"]
