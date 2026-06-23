"""
crm_extractor.py
================
Extracts CRM-quality descriptors from a company's signal corpus.

Runs after ontological parsing is complete (i.e. signals have been written
and scored).  Produces structured fields that elevate a raw lead into a
sales-ready CRM record:

  budget             — dollar amount or range mentioned in signal text
  timing             — decision window / quarter / year references
  automation_reqs    — specific automation requirements derived from signals
  decision_makers    — people with decision-making titles found in signal text

Results are written to:
  company.crm_metadata   (JSON field — timing, budget, requirements, flags)
  contacts table         (Contact rows for each decision maker found)

Public API
----------
  extract(company, signals, db) -> CRMDescriptors
      Runs all extractors, persists contacts, returns structured result.

  build_crm_metadata_dict(descriptors) -> dict
      Converts CRMDescriptors to the JSON dict stored in crm_metadata.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.company import Company
    from app.models.signal import Signal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Budget extraction
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BudgetSignal:
    raw_text: str          # the matched text snippet
    amount_str: str        # normalized amount string, e.g. "$2.3M"
    amount_usd: float      # approximate USD value
    context: str           # surrounding sentence for verification
    source_url: str = ""


_BUDGET_PATTERNS = [
    # "$2.3 million", "$500M", "$1.2B"
    re.compile(
        r"\$\s*(\d[\d,.]*)\s*(million|billion|M\b|B\b)",
        re.IGNORECASE,
    ),
    # "2.3 million dollars", "500 million USD"
    re.compile(
        r"(\d[\d,.]*)\s*(million|billion)\s+(dollars?|USD|usd)",
        re.IGNORECASE,
    ),
    # "budget of $X", "capex of $X", "investment of $X", "funding of $X"
    re.compile(
        r"(?:budget|capex|capital\s+expenditure|investment|funding|grant|contract)\s+"
        r"of\s+\$?\s*(\d[\d,.]*)\s*(million|billion|M\b|B\b|thousand|K\b)?",
        re.IGNORECASE,
    ),
    # "allocat* $X million", "invest* $X million"
    re.compile(
        r"(?:allocat\w*|invest\w*|spend\w*|commit\w*)\s+"
        r"\$?\s*(\d[\d,.]*)\s*(million|billion|M\b|B\b)",
        re.IGNORECASE,
    ),
]

_MULTIPLIERS = {
    "million": 1_000_000, "m": 1_000_000,
    "billion": 1_000_000_000, "b": 1_000_000_000,
    "thousand": 1_000, "k": 1_000,
}


def _extract_budget(signal_texts: List[tuple[str, str]]) -> List[BudgetSignal]:
    """
    signal_texts: list of (text, source_url) tuples.
    Returns deduplicated BudgetSignal objects.
    """
    found: List[BudgetSignal] = []
    seen_amounts: set = set()

    for text, url in signal_texts:
        for pattern in _BUDGET_PATTERNS:
            for m in pattern.finditer(text):
                raw = m.group(0)
                # Extract numeric part — first capturing group
                groups = [g for g in m.groups() if g]
                num_str = groups[0] if groups else "0"
                unit_str = groups[1].lower() if len(groups) > 1 and groups[1] else ""

                try:
                    num = float(num_str.replace(",", ""))
                except ValueError:
                    continue

                multiplier = _MULTIPLIERS.get(unit_str, 1)
                amount_usd = num * multiplier

                # Normalize display
                if multiplier >= 1_000_000_000:
                    amount_display = f"${num:.1f}B"
                elif multiplier >= 1_000_000:
                    amount_display = f"${num:.1f}M"
                elif multiplier >= 1_000:
                    amount_display = f"${num:.0f}K"
                else:
                    amount_display = f"${num:,.0f}"

                # Deduplicate by approximate amount (±20%)
                key = round(amount_usd / 1_000_000)
                if key in seen_amounts:
                    continue
                seen_amounts.add(key)

                # Grab surrounding context (sentence)
                start = max(0, m.start() - 80)
                end = min(len(text), m.end() + 80)
                context = text[start:end].strip()

                found.append(BudgetSignal(
                    raw_text=raw,
                    amount_str=amount_display,
                    amount_usd=amount_usd,
                    context=context,
                    source_url=url,
                ))

    # Return highest-value signals first
    found.sort(key=lambda b: b.amount_usd, reverse=True)
    return found[:3]  # top 3 budget mentions


# ─────────────────────────────────────────────────────────────────────────────
# Timing extraction
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TimingSignal:
    label: str          # human-readable window label, e.g. "Q3 2025"
    raw_text: str       # matched text
    confidence: float   # 0–1
    context: str        # surrounding sentence


_TIMING_PATTERNS = [
    # Q3 2025, Q4 2026
    (re.compile(r"\b(Q[1-4]\s*20\d\d)\b", re.IGNORECASE), 0.90),
    # H1 2025, H2 2026
    (re.compile(r"\b(H[12]\s*20\d\d)\b", re.IGNORECASE), 0.85),
    # by end of 2025, by 2026, by end of fiscal year 2025
    (re.compile(
        r"\bby\s+(?:end\s+of\s+)?(?:the\s+)?(?:fiscal\s+year\s+)?(20\d\d)\b",
        re.IGNORECASE,
    ), 0.80),
    # in 2025, in fiscal 2026, in early/mid/late 2027
    (re.compile(
        r"\bin\s+(?:fiscal\s+year\s+|fiscal\s+|early\s+|mid[-\s]|late\s+)?(20\d\d)\b",
        re.IGNORECASE,
    ), 0.70),
    # "end of fiscal year 2025" (without leading "by")
    (re.compile(
        r"\bend\s+of\s+(?:the\s+)?(?:fiscal\s+year\s+|fiscal\s+)?(20\d\d)\b",
        re.IGNORECASE,
    ), 0.75),
    # within 6 months, within 12 months
    (re.compile(r"\bwithin\s+(\d+)\s+(months?|weeks?|years?)\b", re.IGNORECASE), 0.75),
    # this quarter / this year / this fiscal year
    (re.compile(
        r"\b(this\s+(?:quarter|year|fiscal\s+year|half))\b", re.IGNORECASE,
    ), 0.65),
    # next quarter / next year
    (re.compile(
        r"\b(next\s+(?:quarter|year|fiscal\s+year|half))\b", re.IGNORECASE,
    ), 0.65),
    # planned for spring/summer/fall/winter 2025
    (re.compile(
        r"\b(?:planned?\s+for\s+|scheduled\s+for\s+|target(?:ed)?\s+for\s+)?"
        r"(spring|summer|fall|winter|autumn)\s+(20\d\d)\b",
        re.IGNORECASE,
    ), 0.72),
    # pilot launch / rollout / deployment + year reference
    (re.compile(
        r"\b(?:pilot\s+launch|full\s+rollout|phase\s+[12]|initial\s+deployment)"
        r"\s+(?:in\s+|by\s+|for\s+)?(20\d\d)\b",
        re.IGNORECASE,
    ), 0.80),
]


def _timing_display_label(m: re.Match) -> str:
    """Human-readable timing label — keep phrase context, not bare years."""
    g0 = (m.group(0) or "").strip().rstrip(".")
    g1 = (m.group(1) or "").strip() if m.lastindex and m.lastindex >= 1 else ""
    if g1 and re.fullmatch(r"20\d{2}", g1, re.I):
        return g0
    if g1 and re.fullmatch(r"Q[1-4]\s*20\d{2}", g1, re.I):
        return re.sub(r"\s+", " ", g1.upper())
    if g1 and re.fullmatch(r"H[12]\s*20\d{2}", g1, re.I):
        return re.sub(r"\s+", " ", g1.upper())
    if g1 and re.fullmatch(r"(spring|summer|fall|winter|autumn)\s+20\d{2}", g1, re.I):
        return g1.title()
    if g1 and re.fullmatch(r"this\s+(quarter|year|fiscal\s+year|half)", g1, re.I):
        return g1.title()
    if g1 and re.fullmatch(r"next\s+(quarter|year|fiscal\s+year|half)", g1, re.I):
        return g1.title()
    if g1 and re.fullmatch(r"\d+\s+(months?|weeks?|years?)", g1, re.I):
        return g1.lower()
    if g1:
        return g1 if len(g1) <= 48 else g0
    return g0


def _extract_timing(signal_texts: List[tuple[str, str]]) -> List[TimingSignal]:
    found: List[TimingSignal] = []
    seen_labels: set = set()

    for text, _url in signal_texts:
        for pattern, conf in _TIMING_PATTERNS:
            for m in pattern.finditer(text):
                label = _timing_display_label(m)
                if label in seen_labels:
                    continue
                seen_labels.add(label)
                start = max(0, m.start() - 60)
                end = min(len(text), m.end() + 60)
                context = text[start:end].strip()
                found.append(TimingSignal(
                    label=label,
                    raw_text=m.group(0),
                    confidence=conf,
                    context=context,
                ))

    found.sort(key=lambda t: t.confidence, reverse=True)
    return found[:5]


def _infer_automation_requirements_fallback(
    company: "Company",
    signal_texts: List[tuple[str, str]],
) -> List[str]:
    """Derive requirement labels from robot-fit inference when signal regex finds nothing."""
    from app.services.lead_sales_copy import humanize_robot_types

    blob = " ".join((text or "")[:2000] for text, _ in signal_texts[:12])
    meta = company.crm_metadata if isinstance(company.crm_metadata, dict) else {}
    profile = meta.get("automation_profile") if isinstance(meta.get("automation_profile"), dict) else {}
    robot_types = humanize_robot_types(
        profile,
        industry=(company.industry or ""),
        signal_blob=blob,
    )
    return [
        label
        for label in robot_types
        if label and "confirm on discovery" not in label.lower()
    ][:5]


# ─────────────────────────────────────────────────────────────────────────────
# Automation requirements extraction
# ─────────────────────────────────────────────────────────────────────────────

# Map from descriptive phrase → normalized requirement label
_AUTOMATION_REQ_PATTERNS: List[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(pallet(?:iz|is)ing|palletizer)\b", re.IGNORECASE), "palletizing"),
    (re.compile(r"\b(case\s+pack(?:ing)?|case\s+erect(?:ing)?)\b", re.IGNORECASE), "case packing"),
    (re.compile(r"\b(pick\s+and\s+place|pick-and-place)\b", re.IGNORECASE), "pick and place"),
    (re.compile(r"\b(material\s+handl(?:ing|er))\b", re.IGNORECASE), "material handling"),
    (re.compile(r"\b(order\s+fulfillment|order\s+pick(?:ing)?)\b", re.IGNORECASE), "order fulfillment"),
    (re.compile(r"\b(warehouse\s+(?:automation|robot(?:ics)?))\b", re.IGNORECASE), "warehouse automation"),
    (re.compile(r"\b(AMRs?|autonomous\s+mobile\s+robots?)\b", re.IGNORECASE), "AMR / mobile robots"),
    (re.compile(r"\b(AGVs?|automated\s+guided\s+vehicles?)\b", re.IGNORECASE), "AGV"),
    (re.compile(r"\b(BOH|back[-\s]of[-\s]house)\s+(?:kitchen\s+)?(?:robot|automat)\b", re.IGNORECASE), "BOH kitchen automation"),
    (re.compile(r"\b(food\s+(?:prep|preparation|processing))\s+(?:robot|automat)\b", re.IGNORECASE), "food prep automation"),
    (re.compile(r"\b(cold\s+stor(?:age|e)|frozen\s+(?:stor|ware))\b", re.IGNORECASE), "cold storage"),
    (re.compile(r"\b(last[-\s]mile\s+deliver(?:y|ies))\b", re.IGNORECASE), "last-mile delivery"),
    (re.compile(r"\b(room\s+(?:service\s+)?delivery|in[-\s]room\s+deliver)\b", re.IGNORECASE), "room delivery robots"),
    (re.compile(r"\b(floor\s+clean(?:ing)?|autonom\w+\s+clean)\b", re.IGNORECASE), "autonomous cleaning"),
    (re.compile(r"\b(surgical|clinical\s+logistic|medication\s+deliver)\b", re.IGNORECASE), "clinical / surgical robotics"),
    (re.compile(r"\b(cobots?|collaborative\s+robots?)\b", re.IGNORECASE), "collaborative robots (cobots)"),
    (re.compile(r"\b(end[-\s]of[-\s]line|EOL)\b", re.IGNORECASE), "end-of-line automation"),
    (re.compile(r"\b(quality\s+(?:control|inspection|check))\s+(?:robot|automat|vision)\b", re.IGNORECASE), "quality inspection"),
    (re.compile(r"\b(vision\s+system|machine\s+vision|computer\s+vision)\b", re.IGNORECASE), "machine vision"),
    (re.compile(r"\b(labor\s+(?:shortage|shortfall|gap))\b", re.IGNORECASE), "labor shortage driver"),
    (re.compile(r"\b(safety\s+(?:incident|hazard|risk)\s+(?:reduction|mitigation))\b", re.IGNORECASE), "safety improvement"),
    (re.compile(r"\b(throughput\s+(?:increas|boost|improv))\b", re.IGNORECASE), "throughput improvement"),
]


def _extract_automation_requirements(signal_texts: List[tuple[str, str]]) -> List[str]:
    """Returns a deduplicated list of identified automation requirement labels."""
    found: List[str] = []
    seen: set = set()
    for text, _url in signal_texts:
        for pattern, label in _AUTOMATION_REQ_PATTERNS:
            if label not in seen and pattern.search(text):
                seen.add(label)
                found.append(label)
    return found


# ─────────────────────────────────────────────────────────────────────────────
# Decision maker extraction
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DecisionMaker:
    first_name: str
    last_name: str
    title: str
    source_url: str = ""
    confidence: float = 0.7


# Pattern: "FirstName LastName, Title" or "Title FirstName LastName"
_DM_AFTER_NAME = re.compile(
    r"\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,25}),?\s+"
    r"((?:(?:VP|SVP|EVP|Chief|Head|Director|President|CEO|COO|CFO|CTO|"
    r"Managing\s+Director|General\s+Manager|Vice\s+President|Senior\s+VP|"
    r"Executive\s+VP)\s*(?:of\s+)?(?:\w+\s*){0,4}))",
)

_DM_BEFORE_NAME = re.compile(
    r"\b(CEO|COO|CFO|CTO|President|Director|VP|Vice\s+President|"
    r"Chief\s+\w+\s+Officer|Head\s+of\s+\w+|General\s+Manager|"
    r"Managing\s+Director)\s+([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,25})\b",
)

# Common first names set (reuse from text_classifier logic)
_FIRST_NAMES_FOR_DM: frozenset = frozenset({
    "james", "john", "robert", "michael", "william", "david", "richard",
    "joseph", "thomas", "charles", "christopher", "daniel", "matthew",
    "anthony", "mark", "paul", "steven", "andrew", "kenneth", "george",
    "joshua", "kevin", "brian", "edward", "jason", "ryan", "jacob",
    "mary", "patricia", "jennifer", "linda", "barbara", "elizabeth", "susan",
    "jessica", "sarah", "karen", "lisa", "nancy", "betty", "margaret",
    "sandra", "ashley", "emily", "donna", "michelle", "carol", "amanda",
    "melissa", "stephanie", "rebecca", "sharon", "laura", "samantha",
    "emma", "nicole", "angela", "anna", "brenda",
})


def _extract_decision_makers(signal_texts: List[tuple[str, str]]) -> List[DecisionMaker]:
    found: List[DecisionMaker] = []
    seen: set = set()

    for text, url in signal_texts:
        # Pattern: "John Smith, VP of Operations" / "John Smith, CEO"
        for m in _DM_AFTER_NAME.finditer(text):
            first, last, title = m.group(1), m.group(2), m.group(3).strip()
            title = re.sub(r"\s+", " ", title).rstrip(",. ")
            if first.lower() not in _FIRST_NAMES_FOR_DM:
                continue
            key = f"{first.lower()} {last.lower()}"
            if key not in seen:
                seen.add(key)
                found.append(DecisionMaker(
                    first_name=first, last_name=last, title=title,
                    source_url=url, confidence=0.80,
                ))

        # Pattern: "CEO John Smith"
        for m in _DM_BEFORE_NAME.finditer(text):
            title, first, last = m.group(1), m.group(2), m.group(3)
            title = re.sub(r"\s+", " ", title).strip()
            if first.lower() not in _FIRST_NAMES_FOR_DM:
                continue
            key = f"{first.lower()} {last.lower()}"
            if key not in seen:
                seen.add(key)
                found.append(DecisionMaker(
                    first_name=first, last_name=last, title=title,
                    source_url=url, confidence=0.75,
                ))

    return found[:5]  # cap at 5 decision makers per company


# ─────────────────────────────────────────────────────────────────────────────
# Main extractor
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CRMDescriptors:
    budget_signals: List[BudgetSignal] = field(default_factory=list)
    timing_signals: List[TimingSignal] = field(default_factory=list)
    automation_requirements: List[str] = field(default_factory=list)
    decision_makers: List[DecisionMaker] = field(default_factory=list)
    extracted_at: Optional[str] = None

    @property
    def has_budget(self) -> bool:
        return bool(self.budget_signals)

    @property
    def has_timing(self) -> bool:
        return bool(self.timing_signals)

    @property
    def top_budget(self) -> Optional[str]:
        return self.budget_signals[0].amount_str if self.budget_signals else None

    @property
    def top_timing(self) -> Optional[str]:
        return self.timing_signals[0].label if self.timing_signals else None


def extract(company: "Company", signals: List["Signal"], db: "Session") -> CRMDescriptors:
    """
    Run all CRM extractors over the company's signals.
    Persists new Contact rows for decision makers.
    Returns CRMDescriptors (caller is responsible for writing crm_metadata to company).
    """
    signal_texts: List[tuple[str, str]] = [
        (s.signal_text or "", s.source_url or "")
        for s in (signals or [])
        if s.signal_text
    ]

    if not signal_texts:
        return CRMDescriptors(extracted_at=_now())

    automation_requirements = _extract_automation_requirements(signal_texts)
    if not automation_requirements:
        automation_requirements = _infer_automation_requirements_fallback(company, signal_texts)

    descriptors = CRMDescriptors(
        budget_signals=_extract_budget(signal_texts),
        timing_signals=_extract_timing(signal_texts),
        automation_requirements=automation_requirements,
        decision_makers=_extract_decision_makers(signal_texts),
        extracted_at=_now(),
    )

    # Persist decision makers as Contact rows
    if descriptors.decision_makers and db is not None:
        _persist_contacts(company, descriptors.decision_makers, db)

    return descriptors


def build_crm_metadata_dict(descriptors: CRMDescriptors) -> dict:
    """Serialise CRMDescriptors to the dict stored in companies.crm_metadata."""
    return {
        "budget": {
            "signals": [
                {
                    "amount": b.amount_str,
                    "amount_usd": b.amount_usd,
                    "context": b.context[:200],
                    "source_url": b.source_url,
                }
                for b in descriptors.budget_signals
            ],
            "top_amount": descriptors.top_budget,
        },
        "timing": {
            "signals": [
                {
                    "label": t.label,
                    "raw": t.raw_text,
                    "context": t.context[:200],
                    "confidence": round(t.confidence, 2),
                }
                for t in descriptors.timing_signals
            ],
            "top_window": descriptors.top_timing,
        },
        "automation_requirements": descriptors.automation_requirements,
        "decision_makers": [
            {
                "name": f"{dm.first_name} {dm.last_name}",
                "title": dm.title,
                "source_url": dm.source_url,
                "confidence": round(dm.confidence, 2),
            }
            for dm in descriptors.decision_makers
        ],
        "quality_flags": {
            "has_budget": descriptors.has_budget,
            "has_timing": descriptors.has_timing,
            "has_decision_makers": bool(descriptors.decision_makers),
            "has_automation_requirements": bool(descriptors.automation_requirements),
            "extracted_at": descriptors.extracted_at,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persist_contacts(
    company: "Company",
    decision_makers: List[DecisionMaker],
    db: "Session",
) -> None:
    """Write Contact rows for decision makers not already in the DB."""
    from app.models.contact import Contact

    try:
        existing_keys = {
            f"{(c.first_name or '').lower()} {(c.last_name or '').lower()}"
            for c in (company.contacts or [])
        }
        for dm in decision_makers:
            key = f"{dm.first_name.lower()} {dm.last_name.lower()}"
            if key in existing_keys:
                continue
            contact = Contact(
                company_id=company.id,
                first_name=dm.first_name,
                last_name=dm.last_name,
                title=dm.title,
                confidence_score=int(dm.confidence * 100),
                linkedin_url=dm.source_url if "linkedin" in dm.source_url else None,
            )
            db.add(contact)
            existing_keys.add(key)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to persist contacts for company %s: %s", company.id, exc)
        db.rollback()
