"""pstack protocol for site agents (How / Act / Critic).

Jobs still come from ontology + POST /api/robot-job-match.
This module routes agent *roles*. It does not pick employers, call Vercel AI
Gateway, resurrect Hermes ingest, or replace ``robot_job_capability_match.py``.
"""

from __future__ import annotations

from typing import Any, Literal

PstackRoleId = Literal["how", "act", "critic"]
SiteAgentRefusal = Literal[
    "vercel_ai_gateway",
    "hermes_ingest",
    "matcher_as_llm",
    "customer_pstack_chat",
    "signal_hop",
    "remove_crm_wall",
]

JOBS_MATCHER_SOURCE: dict[str, str] = {
    "kind": "matcher",
    "method": "POST",
    "path": "/api/robot-job-match",
    "owner": "app/services/robot_job_capability_match.py",
}

ROLES: dict[PstackRoleId, dict[str, str]] = {
    "how": {
        "id": "how",
        "label": "How",
        "job": "Name the owner before anyone edits FIND, Job Cards, or CRM.",
    },
    "act": {
        "id": "act",
        "label": "Act",
        "job": "Change the Jobs path only. Keep the signup wall. Keep step 03 labeled CRM.",
    },
    "critic": {
        "id": "critic",
        "label": "Critic",
        "job": "Prove FIND on /, named employers, the wall, and the matcher.",
    },
}

CRITIC_GATES: tuple[dict[str, str], ...] = (
    {"id": "find", "prove": "FIND is /", "fail": "smoking /experiment as FIND"},
    {"id": "job_cards", "prove": "named employer and real work", "fail": "invented rental dollars"},
    {"id": "wall", "prove": "signup before the CRM desk", "fail": "unsigned /pipeline?src=jobs_activate desk"},
    {"id": "matcher", "prove": "POST /api/robot-job-match", "fail": "LLM as the job source"},
)

FORBIDDEN: dict[SiteAgentRefusal, str] = {
    "vercel_ai_gateway": "Do not call Vercel AI Gateway.",
    "hermes_ingest": "Hermes ingest is retired.",
    "matcher_as_llm": "Do not replace robot_job_capability_match.py with an LLM.",
    "customer_pstack_chat": "pstack is not a customer chatbot.",
    "signal_hop": "Do not hop Jobs traffic onto SIGNAL buyers.",
    "remove_crm_wall": "Keep the signup wall in front of the CRM desk.",
}

CRM_WALL_REQUIRED = True
GATEWAY_PROVIDERS = frozenset({"ai-gateway", "vercel-ai-gateway", "vercel_ai_gateway"})


def jobs_matcher_path() -> str:
    return f"{JOBS_MATCHER_SOURCE['method']} {JOBS_MATCHER_SOURCE['path']}"


def critic_gate_ids() -> list[str]:
    return [gate["id"] for gate in CRITIC_GATES]


def refuse_site_agent(reason: SiteAgentRefusal) -> dict[str, Any]:
    return {"ok": False, "reason": reason, "detail": FORBIDDEN[reason]}


def refuse_gateway(provider: str | None) -> dict[str, Any] | None:
    raw = (provider or "").strip().lower()
    if raw in GATEWAY_PROVIDERS:
        return refuse_site_agent("vercel_ai_gateway")
    return None


def crm_copilot_intent() -> dict[str, Any]:
    """How-check before CRM generate-plan: copilot is not the Jobs matcher."""
    return {
        "ok": True,
        "role": "how",
        "surface": "crm_generate_plan",
        "owner": "app/services/sales_plan_agent.py",
        "not_the_matcher": True,
        "job_source": dict(JOBS_MATCHER_SOURCE),
        "wall_required": CRM_WALL_REQUIRED,
    }


def wrap_site_agent(
    *,
    role: PstackRoleId,
    surface: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tag a site-agent call with a pstack role. Does not invoke a model."""
    if surface == "scout_chat":
        return refuse_site_agent("customer_pstack_chat")
    if role not in ROLES:
        raise ValueError(f"unknown pstack role: {role}")
    return {
        "ok": True,
        "protocol": "pstack",
        "role": role,
        "surface": surface,
        "job_source": dict(JOBS_MATCHER_SOURCE),
        "gates": [dict(gate) for gate in CRITIC_GATES],
        "payload": payload or {},
        "forbids": list(FORBIDDEN),
    }
