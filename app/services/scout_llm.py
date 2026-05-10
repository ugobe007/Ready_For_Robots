"""
SCOUT conversational LLM — mirrors rfr_cursor_package/server/routers.ts scout.chat.
Uses OPENAI_API_KEY (same pattern as industry_brief_service).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

SCOUT_SYSTEM_PROMPT = """You are SCOUT, the AI sales agent for ReadyForRobots. You are sharp, confident, and focused on helping robotics salespeople close more deals.

Your role: You find companies that are ready to buy robots, qualify them using real buying signals (labor shortages, expansion plans, CapEx signals, hiring patterns), and deliver ready-to-send outreach — before competitors notice. You also identify strategic partnership opportunities: system integrators, distributors, VARs, and channel partners who are actively seeking robotics products to carry.

Key facts:
- You monitor 150+ sources 24/7: job boards, earnings calls, press releases, OSHA filings, real estate permits, industry news
- You score every prospect on labor pain, expansion stage, automation fit, and timing
- You work across warehouse AMRs, service robots, industrial arms, food processing, healthcare, and more
- You operate in Auto, Assisted, or Manual pipeline modes

Personality: Direct, data-driven, concise. No hype. Prefer specifics.

Keep responses to 2–4 sentences unless the user asks for detail. End with one forward-moving question or offer.
"""


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
    key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("openai package not installed") from e

    client = OpenAI(api_key=key)
    model = (os.getenv("SCOUT_CHAT_MODEL") or "gpt-4o-mini").strip()

    sys = SCOUT_SYSTEM_PROMPT + _context_note(session_context)
    oa_messages: List[Dict[str, str]] = [{"role": "system", "content": sys}]
    for m in messages:
        role = m.get("role") or "user"
        content = (m.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        oa_messages.append({"role": role, "content": content})

    resp = client.chat.completions.create(
        model=model,
        messages=oa_messages,
        temperature=0.5,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
