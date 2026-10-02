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

from app.mcp.auth import authenticate_mcp_request
from app.mcp.client import R4RApiError, format_json, get_client
from app.mcp.config import mcp_bearer_token, premium_tools_enabled

SERVER_INSTRUCTIONS = """
ReadyForRobots returns catalog records and numeric examples. A result is not a hire, a quote, or approval to install a robot.

Use recommend_robots for a physical task the user describes. Use match_robot_jobs when the user gives a public robot product URL. Use calculate_robot_payback only with a price, a wage, and hours the user entered. Use search_opportunities for buyer records already stored in the catalog.

Use humanoid_list_robots, humanoid_get_robot, humanoid_benchmark_report, and humanoid_spec_gaps for published humanoid index records. Use search_intelligence, search_categories, leads_summary, leads_list, get_lead, trending_signals, get_company, and list_robot_vendors for stored catalog records. Use analyze_text on text the user pasted. Use analyze_url only for a URL the user supplied. Use robot_ready_match only when the user asks to save a robot URL for a customer match.

Ask for missing load, hours, and whether people share the path. Leave a price, a wage, a buyer, or a contact blank when the user did not provide it.
""".strip()

# Closed catalog reads. openWorldHint is false because these tools stay on ReadyForRobots records.
_CATALOG = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": False,
}
# Reads a public page the user named.
_PUBLIC_PAGE = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": True,
}
# Saves a submission that also reads a public URL.
_SUBMIT = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "openWorldHint": True,
}
# Stores a session on this service only.
_SESSION = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "openWorldHint": False,
}


def _job_records(data: Any, key: str = "jobs") -> Any:
    """Drop tracking links and invented roles from a job or opportunity payload."""
    if not isinstance(data, dict):
        return data
    rows = []
    for job in data.get(key) or []:
        if not isinstance(job, dict):
            continue
        rows.append(
            {
                "title": job.get("title"),
                "company_name": job.get("company_name"),
                "location": job.get("location"),
                "industry": job.get("industry"),
                "hourly_wage": job.get("hourly_wage"),
                "task_model_required": job.get("task_model_required"),
            }
        )
    count = data.get("matched_job_count", data.get("opportunity_count", len(rows)))
    return {
        "count": count,
        "records": rows,
        "limit": "Catalog match only. Not a hire and not site approval.",
    }


def _payback_example(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    return {
        "robot_cost_usd": data.get("robot_cost_usd"),
        "hourly_labor_rate_usd": data.get("hourly_labor_rate_usd"),
        "daily_savings_usd": data.get("daily_savings_usd"),
        "annual_savings_usd": data.get("annual_savings_usd"),
        "payback_period_months": data.get("payback_period_months"),
        "annual_return_percent": data.get("annual_roi_percent"),
        "assumptions": (
            "Uses 250 work days. Omits maintenance, downtime, integration, and charging. "
            "This is an example, not a quote."
        ),
    }


def _recommend_records(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    return {
        "task": data.get("task_analyzed"),
        "robot_types": data.get("recommended_robot_types"),
        "limit": "Catalog suggestion only. Not approval to install a robot.",
    }


class MCPBearerAuthMiddleware(BaseHTTPMiddleware):
    """Bearer token or marketplace partner API key for Streamable HTTP."""

    async def dispatch(self, request: Request, call_next):
        ok, partner = authenticate_mcp_request(request)
        if not ok:
            detail = "Unauthorized — send Authorization: Bearer <key> or X-R4R-API-Key"
            if mcp_bearer_token():
                detail += " (global MCP token or marketplace partner key)"
            return JSONResponse({"detail": detail}, status_code=401)
        if partner is not None:
            request.state.partner_api_key = partner
        return await call_next(request)


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

    @mcp.tool(annotations=_CATALOG)
    async def humanoid_list_robots(limit: int = 50) -> str:
        """List published humanoid index records, including scores and specs."""
        try:
            data = await get_client().get("/api/humanoid/robots")
            robots = data if isinstance(data, list) else data.get("robots", data)
            if isinstance(robots, list) and limit > 0:
                robots = robots[: min(limit, 200)]
            return format_json(robots)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def humanoid_get_robot(slug: str) -> str:
        """Return one published humanoid index record by model_slug, such as unitree-g1."""
        try:
            data = await get_client().get(f"/api/humanoid/robots/{slug.strip()}")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def humanoid_benchmark_report() -> str:
        """Return the published humanoid index report, including rankings and summary stats."""
        try:
            data = await get_client().get("/api/humanoid/report")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def humanoid_spec_gaps(sparse_only: bool = False, limit: int = 25) -> str:
        """List humanoid index records that are missing spec fields."""
        try:
            params: dict[str, Any] = {"limit": limit}
            if sparse_only:
                params["sparse_only"] = "true"
            data = await get_client().get("/api/humanoid/gaps", params=params)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    # ── Intelligence search & leads ────────────────────────────────────────────

    @mcp.tool(annotations=_CATALOG)
    async def search_intelligence(
        query: str = "",
        category: str = "",
        limit: int = 20,
    ) -> str:
        """Search stored buyer-signal records by keyword or a preset category."""
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

    @mcp.tool(annotations=_CATALOG)
    async def search_categories() -> str:
        """List the preset categories used by search_intelligence."""
        try:
            data = await get_client().get("/api/search/categories")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def leads_summary() -> str:
        """Summarize stored buyer-lead counts by tier and industry."""
        try:
            data = await get_client().get("/api/leads/summary")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def leads_list(
        tier: str = "ALL",
        industry: str = "",
        min_score: float = 0,
        limit: int = 25,
    ) -> str:
        """List stored buyer-lead records. tier is HOT, WARM, COLD, or ALL."""
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

    @mcp.tool(annotations=_CATALOG)
    async def get_lead(company_id: int) -> str:
        """Return one stored buyer-lead record by company_id."""
        try:
            data = await get_client().get(f"/api/leads/by-id/{company_id}")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def trending_signals(limit: int = 15) -> str:
        """List stored automation-signal records, newest or most frequent first."""
        try:
            data = await get_client().get("/api/trending", params={"limit": min(limit, 50)})
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    # ── Analysis & matching ──────────────────────────────────────────────────

    @mcp.tool(annotations=_CATALOG)
    async def analyze_text(text: str, industry: str = "") -> str:
        """Extract automation-related terms from text the user pasted."""
        try:
            body: dict[str, Any] = {"text": text}
            if industry.strip():
                body["industry"] = industry.strip()
            data = await get_client().post("/api/analyze/text", json_body=body)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_PUBLIC_PAGE)
    async def analyze_url(url: str) -> str:
        """Read a public URL the user supplied and return automation-related terms from that page."""
        try:
            data = await get_client().post("/api/analyze/url", params={"url": url})
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_SUBMIT)
    async def robot_ready_match(
        robot_name: str,
        url: str,
    ) -> str:
        """Save a robot product URL the user asked to submit, and return the customer records the service sends back."""
        try:
            body: dict[str, Any] = {"robot_name": robot_name, "url": url}
            data = await get_client().post("/api/robot-ready/submit", json_body=body)
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_PUBLIC_PAGE)
    async def match_robot_jobs(
        url: str,
        robot_name: str = "",
    ) -> str:
        """Look up catalog jobs for a public robot product URL the user supplied. Return only the jobs the service sends back."""
        try:
            body: dict[str, Any] = {"url": url}
            if robot_name.strip():
                body["robot_name"] = robot_name.strip()
            data = await get_client().post("/api/v1/gpt-actions/match-jobs", json_body=body)
            return format_json(_job_records(data))
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def calculate_robot_payback(
        robot_cost: float,
        hourly_labor_rate: float,
        shift_hours_per_day: float,
    ) -> str:
        """Estimate payback months from a robot price, hourly wage, and hours per day the user entered. The result is an example, not a quote."""
        try:
            body: dict[str, Any] = {
                "robot_cost": robot_cost,
                "hourly_labor_rate": hourly_labor_rate,
                "shift_hours_per_day": shift_hours_per_day,
            }
            data = await get_client().post("/api/v1/gpt-actions/calculate-payback", json_body=body)
            return format_json(_payback_example(data))
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def recommend_robots(
        task_description: str,
        payload_capacity_kg: Optional[float] = None,
        environment: str = "",
    ) -> str:
        """Suggest catalog robot types for a physical task the user describes. A suggestion is not approval to install a robot."""
        try:
            body: dict[str, Any] = {"task_description": task_description}
            if payload_capacity_kg is not None:
                body["payload_capacity_kg"] = payload_capacity_kg
            if environment.strip():
                body["environment"] = environment.strip()
            data = await get_client().post("/api/v1/gpt-actions/recommend-robots", json_body=body)
            return format_json(_recommend_records(data))
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def search_opportunities(
        query: str = "",
        industry: str = "",
    ) -> str:
        """Search stored buyer opportunity records by the words the user provides. Return only records the service sends back."""
        try:
            body: dict[str, Any] = {}
            if query.strip():
                body["query"] = query.strip()
            if industry.strip():
                body["industry"] = industry.strip()
            data = await get_client().post("/api/v1/gpt-actions/search-opportunities", json_body=body)
            return format_json(_job_records(data, key="opportunities"))
        except Exception as exc:
            return _err(exc)

    # ── Reference data ───────────────────────────────────────────────────────

    @mcp.tool(annotations=_CATALOG)
    async def get_company(company_id: int) -> str:
        """Return one stored company profile by id."""
        try:
            data = await get_client().get(f"/api/companies/{company_id}")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    @mcp.tool(annotations=_CATALOG)
    async def list_robot_vendors() -> str:
        """List robot vendors stored in the catalog."""
        try:
            data = await get_client().get("/api/robots/vendors/list")
            return format_json(data)
        except Exception as exc:
            return _err(exc)

    # ── Premium (LLM cost) ───────────────────────────────────────────────────

    if premium_tools_enabled():

        @mcp.tool(annotations=_SESSION)
        async def scout_chat(
            message: str,
            fingerprint: str = "mcp-partner",
            page_context: str = "",
        ) -> str:
            """Send one research question the user wrote and return the service reply. This stores a session."""
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
    http_app = mcp.http_app(path="/", transport="streamable-http")
    http_app.add_middleware(MCPBearerAuthMiddleware)
    return http_app


def run_standalone() -> None:
    transport = (os.getenv("R4R_MCP_TRANSPORT") or "stdio").strip().lower()
    host = os.getenv("R4R_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("R4R_MCP_PORT") or os.getenv("PORT") or "8090")
    path = os.getenv("R4R_MCP_PATH", "/mcp")

    mcp = create_mcp_app()
    if transport in ("http", "streamable-http", "streamable_http"):
        http_app = mcp.http_app(path=path, transport="streamable-http")
        http_app.add_middleware(MCPBearerAuthMiddleware)
        import uvicorn

        uvicorn.run(http_app, host=host, port=port)
    else:
        mcp.run(transport="stdio")
