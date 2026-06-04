"""
Natural-language intelligence copy for sales leads (share_summary / share_blurb).

Avoids robotic phrasing, raw scraper quotes, and database-style qualifiers.
"""
from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence, Tuple

from app.services.lead_signal_display import pick_primary_sentence, strip_extraction_artifacts

# Internal automation_profile ids → rep-friendly robot labels
ROBOT_CATEGORY_LABELS: dict[str, str] = {
    "humanoid": "humanoid robots",
    "amr_amr_forklift": "mobile robots (AMRs)",
    "agv": "automated guided vehicles (AGVs)",
    "mobile_manipulator": "mobile manipulators",
    "articulated_industrial_arm": "industrial robotic arms",
    "scara": "SCARA pick-and-place robots",
    "delta": "delta pick-and-place robots",
    "cartesian_gantry": "gantry / cartesian robots",
    "cobot": "collaborative robots (cobots)",
    "service_robot": "service robots",
    "personal_assistant_robot": "personal assistant robots",
    "drone_indoor": "indoor drones",
    "mining_heavy_robot": "heavy-duty / mining robots",
}

APPLICATION_ROBOT_HINTS: dict[str, str] = {
    "pick_and_place": "pick-and-place robots",
    "palletizing": "palletizing robots",
    "depalletizing": "depalletizing automation",
    "goods_to_person": "goods-to-person AMRs",
    "food_delivery_mobile": "delivery robots",
    "room_service_delivery": "room-service robots",
    "housekeeping_support": "cleaning / housekeeping robots",
    "food_prep_automation": "kitchen automation robots",
    "autonomous cleaning": "cleaning robots",
}

_INDUSTRY_PAIN: dict[str, str] = {
    "logistics": "labor shortages and throughput pressure in distribution",
    "warehouse": "picking bottlenecks and staffing gaps",
    "fulfillment": "order fulfillment speed and labor cost",
    "manufacturing": "labor costs and line consistency",
    "hospitality": "housekeeping and guest-service staffing gaps",
    "hotel": "housekeeping labor and service consistency",
    "healthcare": "staff walking time and logistics load",
    "food service": "kitchen labor and order accuracy",
    "restaurant": "staff turnover and back-of-house pressure",
    "food & beverage": "packaging throughput and labor on the line",
    "casino": "housekeeping labor and high-traffic facility coverage",
    "gaming": "facility service consistency and labor pressure",
}

_JUNK_DISPLAY_RE = re.compile(
    r"(?i)(qualifying factors|active buying indicators in our database|"
    r"signals detected on ready for robots|key evidence\s*—|"
    r"\[code\]|\[explanation\]|confidence:\s*\d|overall_intent=)",
)
_PCT_RE = re.compile(r"(\d{1,2})\s*(?:%|percent)", re.I)
_POC_RE = re.compile(
    r"(?i)\b(pilot|proof of concept|poc|trial)\b.*?"
    r"(?:\d{1,2})\s*(?:-|to)\s*(?:\d{1,2})?\s*weeks?",
)
_INITIATIVE_RE = re.compile(
    r"(?i)\b(automation (?:initiative|program|investment|rollout)|"
    r"robotics (?:program|deployment)|digital transformation|"
    r"warehouse automation (?:project|program))\b",
)


def preview_sentences(text: Optional[str], *, max_sentences: int = 3, max_chars: int = 520) -> str:
    """Card/newsletter preview — complete sentences only, never mid-word."""
    t = (text or "").strip()
    if not t:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", t)
    parts = [p.strip() for p in parts if len(p.strip()) > 12]
    if not parts:
        if len(t) <= max_chars:
            return t
        cut = t[: max_chars - 1].rsplit(" ", 1)[0]
        return (cut or t[:max_chars]).rstrip(",;:") + "…"
    out: List[str] = []
    for part in parts[:max_sentences]:
        candidate = " ".join(out + [part]) if out else part
        if len(candidate) > max_chars:
            break
        out.append(part)
    if not out:
        return preview_sentences(t, max_sentences=1, max_chars=max_chars)
    joined = " ".join(out)
    if not joined.endswith((".", "!", "?")):
        joined += "."
    return joined


def is_low_quality_sales_text(text: Optional[str]) -> bool:
    """True when text should not be shown to reps or in share copy."""
    t = (text or "").strip()
    if not t or len(t) < 18:
        return True
    if _JUNK_DISPLAY_RE.search(t):
        return True
    if t.count("http") >= 2 and len(t) < 120:
        return True
    alpha = sum(1 for c in t if c.isalpha())
    if alpha < 12:
        return True
    return False


def humanize_robot_types(
    automation_profile: Optional[dict],
    *,
    industry: str = "",
    signal_blob: str = "",
) -> List[str]:
    """Ordered, deduped customer-facing robot type labels."""
    profile = automation_profile or {}
    out: List[str] = []
    seen: set[str] = set()

    def add(label: str) -> None:
        key = label.lower()
        if key not in seen:
            seen.add(key)
            out.append(label)

    for cat in profile.get("robot_categories") or []:
        add(ROBOT_CATEGORY_LABELS.get(cat, cat.replace("_", " ")))

    for app in profile.get("application_areas") or []:
        hint = APPLICATION_ROBOT_HINTS.get(app)
        if hint:
            add(hint)

    blob = (signal_blob or "").lower()
    if re.search(r"\bhumanoid\b", blob):
        add("humanoid robots")
    if re.search(r"\b(amr|autonomous mobile)\b", blob):
        add("mobile robots (AMRs)")
    if re.search(r"\bpick[-\s]?and[-\s]?place\b", blob):
        add("pick-and-place robots")
    if re.search(r"\b(clean|scrub|housekeeping|floor)\b", blob):
        add("cleaning robots")
    if re.search(r"\b(room service|delivery robot|concierge)\b", blob):
        add("service robots")
    if re.search(r"\b(cobot|collaborative)\b", blob):
        add("collaborative robots (cobots)")

    if not out:
        ind = (industry or "").lower()
        for key, seeds in (
            ("logistics", ["mobile robots (AMRs)"]),
            ("warehouse", ["mobile robots (AMRs)", "pick-and-place robots"]),
            ("manufacturing", ["collaborative robots (cobots)", "industrial robotic arms"]),
            ("hospitality", ["service robots", "cleaning robots"]),
            ("hotel", ["service robots", "cleaning robots"]),
            ("healthcare", ["mobile robots (AMRs)", "service robots"]),
            ("food", ["kitchen automation robots", "pick-and-place robots"]),
        ):
            if key in ind:
                for s in seeds:
                    add(s)
                break
    if not out:
        add("automation robots (type to confirm on discovery)")
    return out[:5]


def _industry_pain(industry: str, automation_type: str, pain_point: str) -> str:
    low = (industry or "").lower()
    for key, phrase in _INDUSTRY_PAIN.items():
        if key in low:
            return phrase
    if pain_point and "operational efficiency" not in pain_point:
        return pain_point
    return f"pressure on {automation_type}"


def _initiative_clause(name: str, signal_blob: str, signal_types: Sequence[str]) -> str:
    if _INITIATIVE_RE.search(signal_blob):
        return (
            f"The company has publicly discussed a new automation initiative in response."
        )
    st = {t.lower() for t in signal_types if t}
    if st & {"capex", "funding_round", "robot_installation", "automation_hiring"}:
        return (
            f"{name} has announced capital or hiring moves that point to an active automation program."
        )
    if "expansion" in st or "scale_expansion" in st:
        return f"{name} is expanding capacity, which typically pulls forward robotics evaluations."
    return ""


def _timing_clause(tier: str, crm_meta: Optional[dict]) -> str:
    meta = crm_meta if isinstance(crm_meta, dict) else {}
    timing = meta.get("timing") if isinstance(meta.get("timing"), dict) else {}
    top = timing.get("top_window") if timing else None
    if top and str(top).strip():
        window = str(top).strip()
        if re.search(r"(?i)q[1-4]|quarter|month|week|fy|fiscal", window):
            return f"The timing of the project looks like {window}."
        return f"The timing of the project is {window}."
    days = "60 to 90" if tier == "HOT" else "90 to 120"
    return f"The timing of the project is {days} days."


def _decision_maker_clause(crm_meta: Optional[dict]) -> str:
    meta = crm_meta if isinstance(crm_meta, dict) else {}
    dms = meta.get("decision_makers") or []
    if not isinstance(dms, list) or not dms:
        return ""
    parts: List[str] = []
    for dm in dms[:2]:
        if not isinstance(dm, dict):
            continue
        title = (dm.get("title") or "").strip()
        name = (dm.get("name") or "").strip()
        if name and title:
            parts.append(f"{name}, {title}")
        elif title:
            parts.append(title)
        elif name:
            parts.append(name)
    if not parts:
        return ""
    if len(parts) == 1:
        return f"Key decision makers to engage include {parts[0]}."
    return f"Key decision makers include {parts[0]} and {parts[1]}."


def _poc_clause(name: str, signal_blob: str) -> str:
    if not _POC_RE.search(signal_blob) and "pilot" not in signal_blob.lower():
        return (
            f"{name} often runs proof-of-concept trials for two to three weeks "
            f"(eight-hour shifts) before scaling — confirm savings targets on the discovery call."
        )
    pct = _PCT_RE.search(signal_blob)
    savings = f"{pct.group(1)}%" if pct else "double-digit"
    return (
        f"{name} runs PoC trials for two to three weeks with eight-hour shifts, "
        f"with an expectation of saving about {savings} in costs while improving operational workflows."
    )


def _signals_observed_phrase(labels: List[str]) -> str:
    if not labels:
        return "automation interest"
    cleaned = [lb.lower() for lb in labels[:4]]
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def build_lead_intelligence_copy(
    *,
    company_name: str,
    industry: str,
    tier: str,
    signal_labels: List[str],
    signal_types: Optional[Sequence[str]] = None,
    automation_type: str,
    pain_point: str,
    automation_profile: Optional[dict],
    crm_metadata: Optional[dict],
    signal_blob: str = "",
) -> Tuple[str, str]:
    """
    Returns (share_blurb ~220 chars, share_summary multi-sentence paragraph).
    """
    name = (company_name or "This company").strip()
    ind = industry if industry and industry.lower() not in ("unknown", "other", "new") else ""
    observed = _signals_observed_phrase(signal_labels)
    pain = _industry_pain(ind, automation_type, pain_point)

    robot_types = humanize_robot_types(
        automation_profile, industry=ind or industry, signal_blob=signal_blob
    )
    robots_str = ", ".join(robot_types[:3])

    sentences: List[str] = []

    sentences.append(
        f"Signals observed: {observed}. {name} is looking for automation to help with {pain}."
    )

    initiative = _initiative_clause(name, signal_blob, signal_types or [])
    if initiative:
        sentences.append(initiative)

    sentences.append(_timing_clause(tier, crm_metadata))

    sentences.append(f"Robot types that fit this account: {robots_str}.")

    dm = _decision_maker_clause(crm_metadata)
    if dm:
        sentences.append(dm)

    sentences.append(_poc_clause(name, signal_blob))

    summary = " ".join(sentences)
    blurb = (
        f"{name}: {observed}. {robots_str}. "
        f"Window: {'60–90' if tier == 'HOT' else '90–120'} days. Ready For Robots."
    )
    blurb_cut = blurb[:220].rsplit(" ", 1)[0] if len(blurb) > 220 else blurb
    return blurb_cut.rstrip(",;:"), summary
