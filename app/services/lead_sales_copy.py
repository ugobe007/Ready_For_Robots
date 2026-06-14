"""
Natural-language intelligence copy for sales leads (share_summary / share_blurb).

Rep-facing prose — grounded in evidence, plain English, no internal jargon.
"""
from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

from app.services.lead_signal_display import pick_primary_sentence, strip_extraction_artifacts
from app.services.lead_project_timing import ProjectTiming, resolve_project_timing

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
    "aviation": "baggage handling staffing and terminal service gaps",
    "airline": "baggage handling staffing and ground-operations labor",
    "airport": "baggage handling staffing and terminal service gaps",
}

_CLEANING_SIGNAL_RE = re.compile(
    r"\b("
    r"clean(?:ing)?\s+aircraft|aircraft\s+clean|clean\s+cabin|cabin\s+clean|"
    r"housekeeping|floor\s+scrub|autonomous\s+scrubber|cleaning\s+robot|"
    r"disinfect(?:ion)?\s+robot|uv[-\s]?c\s+robot"
    r")\b",
    re.I,
)


def _is_aviation_context(industry: str) -> bool:
    low = (industry or "").lower()
    return any(k in low for k in ("aviation", "airline", "airport"))


def _cleaning_signal_present(blob: str) -> bool:
    return bool(_CLEANING_SIGNAL_RE.search(blob or ""))

_JUNK_DISPLAY_RE = re.compile(
    r"(?i)(qualifying factors|active buying indicators in our database|"
    r"signals detected on ready for robots|key evidence\s*—|"
    r"aligns with our signals|signals observed|robot types that fit|"
    r"\[code\]|\[explanation\]|confidence:\s*\d|overall_intent=)",
)

# Plain-English drivers — never expose internal signal taxonomy to reps.
_PLAIN_TRIGGERS: dict[str, str] = {
    "labor_shortage": "staffing pressure",
    "expansion": "new locations or capacity growth",
    "strategic_hire": "leadership moves driving new initiatives",
    "capex": "capital budgets opening up",
    "funding_round": "fresh investment to deploy",
    "ma_activity": "M&A or portfolio moves",
    "job_posting": "automation-related hiring",
    "news": "public automation news",
    "news_signal": "public automation news",
    "automation_interest": "stated interest in automation",
    "automation_intent": "active automation planning",
    "labor_signal": "workforce strain",
    "robot_installation": "robots already going in",
    "rfp_posted": "vendor selection underway",
    "budget_allocated": "budget set aside for automation",
    "scale_expansion": "capacity expansion",
    "automation_hiring": "automation hiring",
}


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
        first = parts[0]
        if len(first) <= max_chars:
            return first if first.endswith((".", "!", "?")) else first + "."
        cut = first[: max_chars - 1].rsplit(" ", 1)[0]
        return (cut or first[:max_chars]).rstrip(",;:") + "…"
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


def _is_food_service_context(industry: str, blob: str) -> bool:
    ind = (industry or "").lower()
    if any(k in ind for k in ("food service", "restaurant", "qsr", "fast casual")):
        return True
    return bool(re.search(r"\b(restaurant|kiosk|kitchen|slider|qsr|dining|chef)\b", blob, re.I))


def _strip_logistics_unless_relevant(types: List[str], *, industry: str, blob: str) -> List[str]:
    """Drop AMR/AGV labels when signals point at kitchen, kiosk, or guest service — not warehouses."""
    ind = (industry or "").lower()
    if any(k in ind for k in ("logistics", "warehouse", "fulfillment", "distribution")):
        return types
    if re.search(r"\b(amr|agv|warehouse|forklift|distribution\s+center|fulfillment)\b", blob, re.I):
        return types
    return [t for t in types if "amr" not in t.lower() and "agv" not in t.lower()]


def _prioritize_robot_opportunities(
    types: List[str],
    *,
    signal_blob: str = "",
    industry: str = "",
) -> List[str]:
    """Surface signal-relevant robot forms ahead of generic industry defaults."""
    blob = (signal_blob or "").lower()
    humanoid_signal = bool(re.search(r"\bhumanoid\b", blob))
    baggage_signal = bool(re.search(r"\bbaggage\b|\bluggage\b", blob))
    cleaning_signal = _cleaning_signal_present(blob)
    kiosk_signal = bool(re.search(r"\bkiosk\b", blob))
    kitchen_signal = bool(
        re.search(r"\b(chef|kitchen|robotic\s+chef|automated\s+kitchen|flippy)\b", blob)
    )
    food_service = _is_food_service_context(industry, blob)

    def rank(label: str) -> tuple[int, int]:
        low = label.lower()
        if humanoid_signal and "humanoid" in low:
            return (0, 0)
        if food_service and kiosk_signal and "humanoid" in low:
            return (1, 0)
        if kitchen_signal and ("chef" in low or "kitchen" in low):
            return (2, 0)
        if food_service and kiosk_signal and ("chef" in low or "kitchen" in low):
            return (2, 1)
        if kiosk_signal and "kiosk" in low:
            return (3, 0)
        if baggage_signal and ("humanoid" in low or "mobile manipulator" in low or "luggage" in low or "baggage" in low):
            return (4, 0)
        if cleaning_signal and "clean" in low:
            return (5, 0)
        if "humanoid" in low:
            return (6, 0)
        if "baggage" in low:
            return (6, 0)
        if "service robot" in low:
            return (7, 0)
        if "cleaning" in low:
            return (14, 0)
        if "mobile manipulator" in low:
            return (8, 0)
        if "amr" in low or "agv" in low:
            return (12, 0)
        if "industrial" in low or "cobot" in low:
            return (10, 0)
        return (9, 0)

    return sorted(types, key=rank)


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

    def add_cleaning(label: str = "cleaning robots") -> None:
        out[:] = [x for x in out if "clean" not in x.lower() and "housekeeping" not in x.lower()]
        seen.difference_update(
            {k for k in seen if "clean" in k or "housekeeping" in k}
        )
        add(label)

    blob = (signal_blob or "").lower()
    ind = (industry or "").lower()
    if re.search(
        r"\b(robotic|automated)\s+chef\b|\brobot\s+chef\b|\bautomated\s+kitchen\b|\bflippy\b",
        blob,
    ):
        add("robotic chefs / automated kitchen systems")
    if re.search(r"\bautomated\s+kiosk\b|\bkiosk\b", blob):
        add("automated restaurant kiosks")
    if re.search(r"\bhumanoid\b", blob):
        add("humanoid robots")
    elif _is_food_service_context(industry, blob) and re.search(
        r"\b(kiosk|automated|automation|slider)\b", blob
    ):
        add("humanoid robots")
        add("robotic chefs / automated kitchen systems")
    if re.search(r"\b(amr|autonomous mobile)\b", blob):
        add("mobile robots (AMRs)")
    if re.search(r"\bpick[-\s]?and[-\s]?place\b", blob):
        add("pick-and-place robots")
    if _cleaning_signal_present(blob):
        add_cleaning("cleaning / housekeeping robots")
    if re.search(r"\b(room service|delivery robot|concierge)\b", blob):
        add("service robots")
    if re.search(r"\b(cobot|collaborative)\b", blob):
        add("collaborative robots (cobots)")
    if re.search(r"\bbaggage\b|\bluggage\b", blob):
        add("mobile manipulators")
        if _is_aviation_context(industry):
            add("baggage handling robots")

    for cat in profile.get("robot_categories") or []:
        add(ROBOT_CATEGORY_LABELS.get(cat, cat.replace("_", " ")))

    for app in profile.get("application_areas") or []:
        hint = APPLICATION_ROBOT_HINTS.get(app)
        if not hint:
            continue
        if "clean" in hint.lower() or "housekeeping" in hint.lower():
            if _cleaning_signal_present(blob):
                add_cleaning(hint)
        else:
            add(hint)

    if not out:
        for key, seeds in (
            ("aviation", ["humanoid robots", "baggage handling robots", "mobile manipulators"]),
            ("airline", ["humanoid robots", "baggage handling robots", "mobile manipulators"]),
            ("airport", ["humanoid robots", "baggage handling robots", "mobile manipulators"]),
            ("logistics", ["mobile robots (AMRs)"]),
            ("warehouse", ["mobile robots (AMRs)", "pick-and-place robots"]),
            ("manufacturing", ["collaborative robots (cobots)", "industrial robotic arms"]),
            ("hospitality", ["service robots", "cleaning robots"]),
            ("hotel", ["service robots", "cleaning robots"]),
            ("healthcare", ["mobile robots (AMRs)", "service robots"]),
            ("food service", ["humanoid robots", "robotic chefs / automated kitchen systems", "service robots"]),
            ("restaurant", ["humanoid robots", "robotic chefs / automated kitchen systems", "service robots"]),
            ("food", ["humanoid robots", "robotic chefs / automated kitchen systems", "kitchen automation robots"]),
        ):
            if key in ind:
                for s in seeds:
                    add(s)
                break
    if not out:
        add("automation robots (confirm on discovery)")
    out = _strip_logistics_unless_relevant(out, industry=industry, blob=blob)
    return _prioritize_robot_opportunities(out, signal_blob=signal_blob, industry=industry)[:5]


def _industry_pain(industry: str, automation_type: str, pain_point: str) -> str:
    low = (industry or "").lower()
    for key, phrase in _INDUSTRY_PAIN.items():
        if key in low:
            return phrase
    if pain_point and "operational efficiency" not in pain_point:
        return pain_point
    return f"pressure on {automation_type}"


def _headline_from_blob(signal_blob: str) -> str:
    """Best-effort news headline — one complete sentence, not a chopped fragment."""
    excerpt = pick_primary_sentence(signal_blob, max_chars=220)
    if excerpt and not is_low_quality_sales_text(excerpt):
        return excerpt
    return ""


def _plain_triggers(signal_types: Sequence[str], limit: int = 3) -> List[str]:
    out: List[str] = []
    for t in signal_types:
        key = (t or "").strip().lower()
        if not key:
            continue
        label = _PLAIN_TRIGGERS.get(key) or key.replace("_", " ").strip()
        if label:
            label = label[0].upper() + label[1:] if len(label) > 1 else label.upper()
        if label and label not in out:
            out.append(label)
        if len(out) >= limit:
            break
    return out


def _format_trigger_list(triggers: List[str]) -> str:
    if not triggers:
        return ""
    if len(triggers) == 1:
        return triggers[0]
    if len(triggers) == 2:
        return f"{triggers[0]} and {triggers[1]}"
    return f"{triggers[0]}, {triggers[1]}, and {triggers[2]}"


def _human_buy_window(timing: ProjectTiming) -> str:
    dmin, dmax = timing.day_min, timing.day_max
    if dmin is not None and dmax is not None:
        if dmax <= 75:
            return f"Outreach window: vendor selection could move in the next {dmin}–{dmax} days."
        if dmax <= 120:
            return f"Outreach window: partner conversations often start within {dmin}–{dmax} days."
        return f"Outreach window: build-out and evaluation cycles typically run {dmin}–{dmax} days."
    label = (timing.label or "").lower()
    if re.fullmatch(r"20\d{2}", label.strip()):
        return ""
    if "procurement" in label or "rfp" in label:
        return "Outreach window: procurement activity suggests they are close to picking a vendor."
    if "deployment" in label or "pilot" in label:
        return "Outreach window: deployment or pilot activity — timing is relatively short."
    if "high-intent" in label:
        return "Outreach window: high-intent account — outreach lands best before an RFP."
    if timing.label and not re.search(r"\b20(3[3-9]|[4-9]\d)\b", timing.label):
        return f"Outreach window: {timing.label}."
    return ""


def _robot_fit_clause(robot_types: List[str]) -> str:
    if not robot_types:
        return ""
    types = robot_types[:3]
    if len(types) == 1:
        return f"Good fit for {types[0]}."
    if len(types) == 2:
        return f"Good fit for {types[0]} and {types[1]}."
    return f"Good fit for {types[0]}, {types[1]}, and {types[2]}."


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
        return f"Worth engaging {parts[0]}."
    return f"Worth engaging {parts[0]} and {parts[1]}."


def _opening_sentence(
    *,
    name: str,
    industry: str,
    automation_type: str,
    pain: str,
    signal_blob: str,
) -> str:
    headline = _headline_from_blob(signal_blob)
    if headline:
        if name.lower() in headline.lower():
            return headline if headline.endswith((".", "!", "?")) else headline + "."
        return f"{name}: {headline.rstrip('.')}."
    excerpt = pick_primary_sentence(signal_blob, max_chars=200)
    if excerpt and not is_low_quality_sales_text(excerpt):
        if name.lower() in excerpt.lower():
            return excerpt if excerpt.endswith((".", "!", "?")) else excerpt + "."
        return f"{name} — {excerpt.rstrip('.')}."

    ind_clause = f" ({industry})" if industry else ""
    return (
        f"{name}{ind_clause} is moving on {automation_type} "
        f"as {pain}."
    )


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
    procurement_hints: Optional[Sequence[str]] = None,
    intent_score: float = 0,
    procurement_strength: float = 0,
) -> Tuple[str, str]:
    """
    Returns (share_blurb ~220 chars, share_summary multi-sentence paragraph).
    """
    name = (company_name or "This company").strip()
    ind = industry if industry and industry.lower() not in ("unknown", "other", "new") else ""
    pain = _industry_pain(ind, automation_type, pain_point)
    triggers = _plain_triggers(signal_types or [], limit=3)
    trigger_phrase = _format_trigger_list(triggers)

    robot_types = humanize_robot_types(
        automation_profile, industry=ind or industry, signal_blob=signal_blob
    )

    project_timing = resolve_project_timing(
        tier=tier,
        crm_metadata=crm_metadata,
        lead_inference=(crm_metadata or {}).get("lead_inference") if isinstance(crm_metadata, dict) else None,
        signal_blob=signal_blob,
        signal_types=signal_types,
        procurement_hints=procurement_hints,
        intent_score=intent_score,
        procurement_strength=procurement_strength,
    )

    sentences: List[str] = []
    sentences.append(
        _opening_sentence(
            name=name,
            industry=ind,
            automation_type=automation_type,
            pain=pain,
            signal_blob=signal_blob,
        )
    )

    if trigger_phrase:
        opener = sentences[0].lower()
        if trigger_phrase.split()[0] not in opener:
            sentences.append(f"What's driving it: {trigger_phrase}.")

    buy_window = _human_buy_window(project_timing)
    if buy_window:
        sentences.append(buy_window)

    robot_clause = _robot_fit_clause(robot_types[:3])
    if robot_clause:
        sentences.append(robot_clause)

    dm = _decision_maker_clause(crm_metadata)
    if dm:
        sentences.append(dm)

    summary = " ".join(sentences)
    blurb = preview_sentences(summary, max_sentences=2, max_chars=220)
    if not blurb:
        blurb = f"{name}: {automation_type}. Ready For Robots."
    return blurb, summary
