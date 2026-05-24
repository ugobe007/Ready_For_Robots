"""StageGate Cal voice — show-ops infrastructure, not buyer-lead matching."""
from __future__ import annotations

from typing import Any, Optional

from app.services.agent_messaging import CAL_INTRO, cal_signature
from app.services.semantic_frame import SemanticFrame, frame_signal_line, parse_news_semantic_frame

STAGEGATE_EXPLANATION = (
    "I track robotics companies heading into major US shows — especially teams with "
    "small on-site crews, cross-border freight, or hardware that needs a real recovery plan "
    "when something fails on the floor."
)

STAGEGATE_LOGIC_LINE = (
    "StageGate is operational infrastructure for show week: receive off the truck, "
    "power-up diagnostics, calibration, battery cycles, and live demo recovery — "
    "so your booth team is not debugging alone at midnight."
)

STAGEGATE_OFFRAMP = (
    "If the timing or show footprint is not real yet, I'll say so. "
    "The point is fewer surprises on the floor, not another vendor pitch."
)

STAGEGATE_CTA = "Worth a short call before your next US show?"


def cal_stagegate_opening() -> str:
    return (
        f"{CAL_INTRO}\n\n"
        f"{STAGEGATE_EXPLANATION}\n\n"
        f"{STAGEGATE_LOGIC_LINE}"
    )


def stagegate_signal_paragraph(frame: SemanticFrame) -> str:
    """One paragraph grounded in parsed actor / topic / goals — not raw headline hype."""
    line = frame_signal_line(frame)
    parts = [line]

    if len(frame.goals) > 1:
        extras = []
        for g in frame.goals[1:3]:
            q = f" by {g.quantifier}" if g.quantifier else ""
            extras.append(f"{g.direction} in {g.metric}{q}")
        parts.append(f"Related outcomes in the same signal: {', '.join(extras)}.")

    if frame.hyperbolic_terms:
        parts.append(
            "The headline leans promotional; I normalized the frame to actor, action, and measurable outcomes."
        )

    if frame.ontology_concepts:
        tags = ", ".join(t.replace("_", " ") for t in frame.ontology_concepts[:4])
        parts.append(f"Ontology tags: {tags}.")

    return " ".join(parts)


def stagegate_outreach_email(
    company_name: str,
    *,
    semantic_frame: Optional[SemanticFrame] = None,
    source_text: str = "",
    trade_show: Optional[str] = None,
) -> dict[str, str]:
    """Cal draft for StageGate OEM / show-ops outreach."""
    frame = semantic_frame or (parse_news_semantic_frame(source_text) if source_text else None)
    signal_block = stagegate_signal_paragraph(frame) if frame else (source_text[:280] or "Recent robotics news caught my eye.")

    show_line = ""
    if trade_show:
        show_line = f"\n\nI noticed {trade_show} on your horizon — that's usually when operational risk peaks for teams without US show support."

    subject = f"Show-week ops for {company_name}"
    if trade_show:
        subject = f"{trade_show} show ops — {company_name}"

    body = f"""Hello {company_name} team,

{cal_stagegate_opening()}

{signal_block}{show_line}

{STAGEGATE_OFFRAMP}

{STAGEGATE_CTA}

{cal_signature()}"""
    return {"subject": subject, "body": body}


def semantic_frame_from_market_intel(market_intelligence: Any) -> Optional[SemanticFrame]:
    """Rehydrate frame stored on robot_companies.market_intelligence."""
    if not isinstance(market_intelligence, dict):
        return None
    raw = market_intelligence.get("semantic_frame")
    if not isinstance(raw, dict):
        oem = market_intelligence.get("stagegate_oem") or {}
        if isinstance(oem, dict):
            raw = oem.get("semantic_frame")
    if not isinstance(raw, dict):
        return None
    try:
        from app.services.semantic_frame import ParsedGoal, SemanticFrame

        goals = [
            ParsedGoal(**g) if isinstance(g, dict) else g
            for g in raw.get("goals") or []
        ]
        return SemanticFrame(
            source_text=raw.get("source_text") or "",
            actor=raw.get("actor"),
            actors=list(raw.get("actors") or []),
            action_verb=raw.get("action_verb"),
            topic=raw.get("topic"),
            description=raw.get("description"),
            goals=goals,
            outcomes=list(raw.get("outcomes") or []),
            descriptors=list(raw.get("descriptors") or []),
            hyperbolic_terms=list(raw.get("hyperbolic_terms") or []),
            confidence=float(raw.get("confidence") or 0),
            ontology_concepts=list(raw.get("ontology_concepts") or []),
            parse_debug=dict(raw.get("parse_debug") or {}),
        )
    except Exception:
        return None
