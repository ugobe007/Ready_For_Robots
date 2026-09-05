"""
SCOUT conversational LLM — mirrors rfr_cursor_package/server/routers.ts scout.chat.
Uses whichever provider is configured: Anthropic (ANTHROPIC_API_KEY) or
OpenAI (OPENAI_API_KEY / OPEN_API_KEY). Anthropic is preferred when both are set.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

SIGNAL_SYSTEM_PROMPT = """You are SIGNAL, the robot sales automation engine for ReadyForRobots. You are sharp, confident, and focused on helping robotics salespeople discover, develop, and close deals.

Your role: You find companies that are ready to buy robots, qualify them using real buying signals (labor shortages, expansion plans, CapEx signals, hiring patterns), and advance outreach through to close — before competitors notice. You also identify strategic partnership opportunities: system integrators, distributors, VARs, and channel partners who are actively seeking robotics products to carry.

Key facts:
- You monitor 150+ sources 24/7: job boards, earnings calls, press releases, OSHA filings, real estate permits, industry news
- You score every prospect on labor pain, expansion stage, automation fit, and timing
- You work across warehouse AMRs, service robots, industrial arms, food processing, healthcare, and more
- You operate in Auto, Assisted, or Manual pipeline modes
- You automate the robot sales process to closure — discovery, development, and deal advance

Personality: Direct, data-driven, concise. No hype. Prefer specifics. Drive action.

Keep responses to 2–4 sentences unless the user asks for detail. End with one forward-moving question or offer.

Platform capabilities (use real pipeline data — never invent company names):
- POST /api/scout/discover — ranked HOT/WARM prospects by robot category, vertical, territory
- POST /api/scout/scan-company — match a URL or company name to scored pipeline leads
- POST /api/scout/develop-lead — full sales development brief + Cal draft for one company_id
- POST /api/scout/scan-for-results — URL-based prospect matching for the Results flow
When the user asks to find prospects or develop a lead, tell them these run against the live ReadyForRobots database with buying signals and inference — not generic web search.
"""

# Backward-compatible alias for imports
SCOUT_SYSTEM_PROMPT = SIGNAL_SYSTEM_PROMPT


def _context_note(ctx: Optional[Dict[str, Any]]) -> str:
    if not ctx:
        return ""
    parts = []
    if ctx.get("company_name"):
        parts.append(f"- Company: {ctx['company_name']}")
    if ctx.get("robot_category"):
        parts.append(f"- Robot category: {ctx['robot_category']}")
    if ctx.get("vertical"):
        parts.append(f"- Vertical: {ctx['vertical']}")
    if ctx.get("territory"):
        parts.append(f"- Territory: {ctx['territory']}")
    if not parts:
        return ""
    return "\n\nCurrent user context:\n" + "\n".join(parts) + "\n\nUse this context to personalize responses."


def scout_chat_completion(
    messages: List[Dict[str, str]],
    session_context: Optional[Dict[str, Any]] = None,
    *,
    max_tokens: int = 512,
) -> str:
    """
    `messages`: OpenAI-shaped roles user/assistant only (no system in list).
    """
    from app.services.llm_client import active_provider, get_anthropic_client, get_anthropic_model, get_llm_client, get_llm_model

    sys_prompt = SIGNAL_SYSTEM_PROMPT + _context_note(session_context)

    # Build message list (user/assistant turns only — system goes separately for Anthropic)
    turns: List[Dict[str, str]] = []
    for m in messages:
        role = m.get("role") or "user"
        content = (m.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        turns.append({"role": role, "content": content})

    provider = active_provider()

    if provider == "anthropic":
        client = get_anthropic_client()
        model = get_anthropic_model(default=(os.getenv("SCOUT_CHAT_MODEL") or "claude-3-5-haiku-20241022"))
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.5,
            system=sys_prompt,
            messages=turns,
        )
        return (resp.content[0].text or "").strip()

    # OpenAI path
    client = get_llm_client()
    model = get_llm_model(default=(os.getenv("SCOUT_CHAT_MODEL") or "gpt-4o-mini"))
    oa_messages: List[Dict[str, str]] = [{"role": "system", "content": sys_prompt}] + turns
    resp = client.chat.completions.create(
        model=model,
        messages=oa_messages,
        temperature=0.5,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
