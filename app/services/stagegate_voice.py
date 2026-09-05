"""StageGate Cal voice — show-ops infrastructure outreach (not buyer-lead matching)."""
from __future__ import annotations

from typing import Any, Optional

from app.services.semantic_frame import SemanticFrame, frame_signal_line, parse_news_semantic_frame

# ── Cal training rules (StageGate OEM cold outreach) ─────────────────────────
STAGEGATE_OUTREACH_RULES: tuple[str, ...] = (
    "Greet a person by name when known; otherwise use the company name — never a generic bulk greeting.",
    "Name the specific trade show, city, or dates when available — never say 'the upcoming show'.",
    "Lead with StageGate show logistics (warehousing, staging, unpack/test, on-site demo support).",
    "Include one concrete pain line: transit jostle, loose connectors, lab-pass sensors that fail on the floor.",
    "Primary CTA: reply with booth number and move-in dates for a calendar link.",
    "Secondary CTA only: onstage.bot self-serve registration.",
    "Keep under ~130 words; no buzzwords, no ontology tags, no multi-brand signature clutter.",
    "Sign as Cal · StageGate · onstage.bot · Las Vegas — not Ready For Robots.",
)

STAGEGATE_SERVICES_LINE = (
    "I'm Cal with StageGate — we're in Las Vegas and help robotics OEMs with show logistics: "
    "bonded warehousing, staging, unpack/test, and on-site tech support during demos."
)

STAGEGATE_PAIN_LINE = (
    "Robots get jostled in transit — loose connectors, sensors that passed in the lab and won't boot on the floor. "
    "We see it constantly. Our techs expect it and fix it before you hit the aisle."
)

STAGEGATE_CTA_PRIMARY = (
    "If it's useful, reply with your booth number and move-in dates and I'll send a calendar link "
    "to walk through your plan."
)

STAGEGATE_CTA_SECONDARY = "You can also register at onstage.bot if you prefer to self-serve."


def stagegate_signature() -> str:
    return "Thanks,\nCal\nStageGate · onstage.bot\nLas Vegas"


def _greeting(company_name: str, contact_name: Optional[str] = None) -> str:
    name = (contact_name or "").strip()
    if name and "@" not in name:
        return f"Hi {name},"
    company = (company_name or "your team").strip() or "your team"
    return f"Hi {company} team,"


def _show_ask_paragraph(company_name: str, trade_show: Optional[str]) -> str:
    company = (company_name or "your team").strip() or "your team"
    if trade_show:
        show = trade_show.strip()
        return (
            f"I saw {company} is exhibiting at {show} and wanted to ask: "
            f"are you handling staging and pre-floor checks locally, or shipping everything direct to the hall?"
        )
    return (
        f"I saw {company} on the show circuit and wanted to ask: "
        f"are you handling staging and pre-floor checks locally, or shipping everything direct to the hall?"
    )


def _optional_signal_sentence(
    frame: Optional[SemanticFrame],
    source_text: str,
) -> str:
    """One short personalization line — omit if nothing useful."""
    if frame:
        line = frame_signal_line(frame).strip()
        if line and len(line) <= 220:
            return line
    text = (source_text or "").strip()
    if text and len(text) <= 180:
        return text
    return ""


def stagegate_subject(company_name: str, trade_show: Optional[str] = None) -> str:
    company = (company_name or "your team").strip() or "your team"
    if trade_show:
        return f"{company} at {trade_show.strip()} — pre-floor staging & tech check?"
    return f"{company} — show logistics & pre-floor tech check?"


def stagegate_outreach_email(
    company_name: str,
    *,
    semantic_frame: Optional[SemanticFrame] = None,
    source_text: str = "",
    trade_show: Optional[str] = None,
    contact_name: Optional[str] = None,
) -> dict[str, str]:
    """Cal draft for StageGate OEM / show-ops outreach — follows STAGEGATE_OUTREACH_RULES."""
    frame = semantic_frame or (parse_news_semantic_frame(source_text) if source_text else None)
    signal_line = _optional_signal_sentence(frame, source_text)

    paragraphs = [
        _greeting(company_name, contact_name),
        "",
        STAGEGATE_SERVICES_LINE,
        "",
        _show_ask_paragraph(company_name, trade_show),
    ]
    if signal_line:
        paragraphs.extend(["", signal_line])
    paragraphs.extend(
        [
            "",
            STAGEGATE_PAIN_LINE,
            "",
            STAGEGATE_CTA_PRIMARY,
            "",
            STAGEGATE_CTA_SECONDARY,
            "",
            stagegate_signature(),
        ]
    )

    return {
        "subject": stagegate_subject(company_name, trade_show),
        "body": "\n".join(paragraphs),
    }


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
