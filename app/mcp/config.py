"""MCP server configuration and tool tier definitions."""
from __future__ import annotations

import os
from typing import FrozenSet

DEFAULT_API_BASE = "https://ready-2-robot.fly.dev"

# Tool names exposed on the MCP server (used in tests and docs).
PUBLIC_READ_TOOLS: FrozenSet[str] = frozenset(
    {
        "humanoid_list_robots",
        "humanoid_get_robot",
        "humanoid_benchmark_report",
        "humanoid_spec_gaps",
        "search_intelligence",
        "search_categories",
        "leads_summary",
        "leads_list",
        "get_lead",
        "trending_signals",
        "analyze_text",
        "analyze_url",
        "robot_ready_match",
        "get_company",
        "list_robot_vendors",
    }
)

# Tools that trigger paid LLM or heavy compute on the backend — gate in production.
PREMIUM_TOOLS: FrozenSet[str] = frozenset({"scout_chat"})


def api_base_url() -> str:
    return (os.getenv("R4R_API_BASE") or DEFAULT_API_BASE).rstrip("/")


def partner_api_key() -> str:
    """Optional key forwarded to the REST API as X-R4R-API-Key."""
    return (os.getenv("R4R_PARTNER_API_KEY") or os.getenv("API_KEY") or "").strip()


def mcp_bearer_token() -> str:
    """When set, MCP HTTP clients must send Authorization: Bearer <token>."""
    return (os.getenv("R4R_MCP_BEARER_TOKEN") or "").strip()


def mcp_enabled() -> bool:
    return os.getenv("R4R_MCP_ENABLED", "").strip().lower() in ("1", "true", "yes")


def premium_tools_enabled() -> bool:
    return os.getenv("R4R_MCP_PREMIUM", "").strip().lower() in ("1", "true", "yes")
