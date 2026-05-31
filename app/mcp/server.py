"""
Ready For Robots MCP server.

Exposes curated tools over the public REST API so third-party sites, marketplaces,
and AI clients can integrate without hand-rolling HTTP calls.

Run standalone (stdio — local dev):
  python -m app.mcp

Run standalone (Streamable HTTP — remote partners):
  R4R_MCP_TRANSPORT=streamable-http python -m app.mcp

Mounted on FastAPI (production):
  R4R_MCP_ENABLED=1  →  https://ready-2-robot.fly.dev/mcp
"""
from __future__ import annotations

import os
from typing import Any, Optional

from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.mcp.client import R4RApiError, format_json, get_client
from app.mcp.config import mcp_bearer_token, premium_tools_enabled

SERVER_INSTRUCTIONS = """
Ready For Robots MCP — robotics buyer-intent intelligence and humanoid benchmarks.

Use humanoid_* tools for the HEIF humanoid robot index (scores, specs, vendor catalog).
Use search_* and leads_* for automation buyer signals and pipeline summaries.
Use robot_ready_match to match a robot product URL to ideal customer companies.
Use analyze_* for ontological signal extraction from text or URLs.

Data source: Ready For Robots REST API (readyforrobots.com).
Do not call admin, scraper, or purge endpoints through this server.
""".strip()


class MCPBearerAuthMiddleware(BaseHTTPMiddleware):
    """Optional bearer token gate for Streamable HTTP / mounted deployments."""

    async def dispatch(self, request: Request, call_next):
        required = mcp_bearer_token()
        if not required:
            return await call_next(request)
        auth = request.headers.get("authorization", "")
        if auth == f"Bearer {required}":
            return await call_next(request)
        return JSONResponse({"detail": "Unauthorized — send Authorization: Bearer <R4R_MCP_BEARER_TOKEN>"}, status_code=401)


def _err(exc: Exception) -> str:
    if isinstance(exc, R4RApiError):
        return f"API error {exc.status_code}: {exc.detail}"
    return f"Request failed: {exc}"


def create_mcp_app() -> FastMCP:
    mcp = FastMCP(
        name="Ready For Robots",
        instructions=SERVER_INSTRUCTIONS,
    )

    # ── Humanoid benchmark ───────────────────────────────────────────────────

    @mcp.tool()
    async def humanoid_list_robots(limit: int = 50) -> str:
        """List humanoid robots with HEIF scores, specs, and commercial status."""
        try:
            data = await get_client().get("/api/humanoid/robots")
            robots = data if isinstance(data, list) else data.get("robots", data)
            if isinstance(robots, list) and limit > 0:
                robots = robots[: min(limit, 200)]
            return format_json(robots)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def humanoid_get_robot(slug: str) -> str:
        """Get one humanoid robot by model_slug (e.g. fourier-gr3, unitree-g1)."""
        try:
            data = await get_client().get(f"/api/humanoid/robots/{slug.strip()}")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def humanoid_benchmark_report() -> str:
        """Formatted humanoid benchmark report — rankings, leaders, and summary stats."""
        try:
            data = await get_client().get("/api/humanoid/report")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def humanoid_spec_gaps(sparse_only: bool = False, limit: int = 25) -> str:
        """List humanoid models missing spec fields needed for HEIF scoring."""
        try:
            params: dict[str, Any] = {"limit": limit}
            if sparse_only:
                params["sparse_only"] = "true"
            data = await get_client().get("/api/humanoid/gaps", params=params)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    # ── Intelligence search & leads ────────────────────────────────────────────

    @mcp.tool()
    async def search_intelligence(
        query: str = "",
        category: str = "",
        limit: int = 20,
    ) -> str:
        """Search buyer-intent signals and companies by keyword or preset category."""
        try:
            params: dict[str, Any] = {"limit": min(limit, 100)}
            if query.strip():
                params["q"] = query.strip()
            if category.strip():
                params["category"] = category.strip()
            data = await get_client().get("/api/search", params=params)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def search_categories() -> str:
        """List preset intelligence search categories (manufacturing, logistics, etc.)."""
        try:
            data = await get_client().get("/api/search/categories")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def leads_summary() -> str:
        """Pipeline summary — HOT/WARM/COLD counts, top industries, signal mix."""
        try:
            data = await get_client().get("/api/leads/summary")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def leads_list(
        tier: str = "ALL",
        industry: str = "",
        min_score: float = 0,
        limit: int = 25,
    ) -> str:
        """List scored buyer leads. tier: HOT, WARM, COLD, or ALL."""
        try:
            params: dict[str, Any] = {
                "tier": tier.upper(),
                "min_score": min_score,
                "limit": min(limit, 50),
            }
            if industry.strip():
                params["industry"] = industry.strip()
            data = await get_client().get("/api/leads", params=params)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def get_lead(company_id: int) -> str:
        """Get a single lead by company_id with signals and scoring detail."""
        try:
            data = await get_client().get(f"/api/leads/by-id/{company_id}")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def trending_signals(limit: int = 15) -> str:
        """Top trending automation signals across all tracked companies."""
        try:
            data = await get_client().get("/api/trending", params={"limit": min(limit, 50)})
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    # ── Analysis & matching ──────────────────────────────────────────────────

    @mcp.tool()
    async def analyze_text(text: str, industry: str = "") -> str:
        """Run ontological NLP analysis on text — automation intent, concepts, rules."""
        try:
            body: dict[str, Any] = {"text": text}
            if industry.strip():
                body["industry"] = industry.strip()
            data = await get_client().post("/api/analyze/text", json_body=body)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def analyze_url(url: str) -> str:
        """Scrape and analyze a company or product URL for automation signals."""
        try:
            data = await get_client().post("/api/analyze/url", params={"url": url})
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def robot_ready_match(
        robot_name: str,
        url: str,
        email: str = "",
    ) -> str:
        """Submit a robot product URL and get matched ideal customer companies."""
        try:
            body: dict[str, Any] = {"robot_name": robot_name, "url": url}
            if email.strip():
                body["email"] = email.strip()
            data = await get_client().post("/api/robot-ready/submit", json_body=body)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    # ── Reference data ───────────────────────────────────────────────────────

    @mcp.tool()
    async def get_company(company_id: int) -> str:
        """Get company profile by id."""
        try:
            data = await get_client().get(f"/api/companies/{company_id}")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool()
    async def list_robot_vendors() -> str:
        """List robot vendors from the supply-side catalog."""
        try:
            data = await get_client().get("/api/robots/vendors/list")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    # ── Premium (LLM cost) ───────────────────────────────────────────────────

    if premium_tools_enabled():

        @mcp.tool()
        async def scout_chat(
            message: str,
            fingerprint: str = "mcp-partner",
            page_context: str = "",
        ) -> str:
            """Chat with the Ready For Robots Scout assistant (uses server-side LLM)."""
            try:
                await get_client().post("/api/scout/session", json_body={"fingerprint": fingerprint})
                body: dict[str, Any] = {
                    "fingerprint": fingerprint,
                    "messages": [{"role": "user", "content": message}],
                }
                if page_context.strip():
                    body["session_context"] = {"page_context": page_context.strip()}
                data = await get_client().post("/api/scout/chat", json_body=body)
                return format_json(data)
            except Exception as exc:
                return _err(exc)

    return mcp


def mcp_http_app():
    """Starlette ASGI app for mounting on FastAPI at /mcp."""
    mcp = create_mcp_app()
    middleware = [MCPBearerAuthMiddleware] if mcp_bearer_token() else None
    return mcp.http_app(path="/", middleware=middleware, transport="streamable-http")


def run_standalone() -> None:
    transport = (os.getenv("R4R_MCP_TRANSPORT") or "stdio").strip().lower()
    host = os.getenv("R4R_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("R4R_MCP_PORT") or os.getenv("PORT") or "8090")
    path = os.getenv("R4R_MCP_PATH", "/mcp")

    mcp = create_mcp_app()
    if transport in ("http", "streamable-http", "streamable_http"):
        middleware = [MCPBearerAuthMiddleware] if mcp_bearer_token() else None
        http_app = mcp.http_app(path=path, middleware=middleware, transport="streamable-http")
        import uvicorn

        uvicorn.run(http_app, host=host, port=port)
    else:
        mcp.run(transport="stdio")
