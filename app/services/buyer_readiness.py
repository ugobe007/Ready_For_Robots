"""Buyer readiness — is this COMPANY ready to buy or pilot robots?

The unit is the company, not the job posting. A dishwasher posting is not an
opportunity; it is (at most) supporting evidence that a company has automatable
work it struggles to staff. What makes a buyer:

  BUYING NOW   tender / RFP / RFQ for robots or automation; pilot or purchase
               announced; "evaluating vendors"
  EVALUATING   hiring automation / robotics / CI people at an operator; automation
               program, roadmap or budget stated; new automated facility planned
  EXPANDING    already runs robots/AMRs/cobots (postings say "maintain robots",
               "work alongside AMRs") — proven buyer, next site / next workflow
  PRIMED       no intent yet, but heavy pain at scale on work robots do today
               (many open postings, bonuses, shortage language, multiple sites)

Score 0-100. Labor postings alone cap at PRIMED (max 45) — they never make a
company a buyer on their own.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from app.services.workflow_ontology import (
    BUYER_AUTOMATION_ROLE_RE,
    BUILDER_TITLE_RE,
    is_robot_vendor,
    match_families,
)

_R = r"(?:robot\w*|cobots?|amrs?|agvs?|autonomous mobile robots?|automated guided vehicles?|asrs|as/rs|autostore|" \
     r"humanoids?|palletiz\w+ robots?|robotic \w+|automation|automated (?:system|solution|equipment|warehouse|storage|picking|sortation|distribution|fulfillment|facilit|plant|kitchen|dc\b|micro-?fulfillment)\w*|micro-?fulfillment|" \
     r"conveyor systems?|sortation systems?|autonomous (?:scrubber|floor|forklift|cleaning|delivery|security)\w*)"

BUY_NOW = (
    (r"(?:request for (?:proposals?|quotes?|qualifications|information)|\brfp\b|\brfq\b|\brfi\b|invitation (?:to|for) bid|"
     r"\bitb\b|solicitation|sources sought|tender|bid (?:opportunity|notice))\W+(?:\w+\W+){0,10}?" + _R, 40, "tender / RFP"),
    (_R + r"\W+(?:\w+\W+){0,6}?(?:rfp|rfq|solicitation|tender|bid)\b", 40, "tender / RFP"),
    (r"(?:pilot(?:ing|s|ed)?|trial(?:ing|s|ed)?|test(?:ing)?|proof of concept|poc)\W+(?:\w+\W+){0,5}?" + _R, 30, "pilot / trial"),
    (_R + r"\W+(?:\w+\W+){0,4}?(?:pilot|trial|proof of concept)", 30, "pilot / trial"),
    (r"(?:evaluating|selecting|shortlist(?:ing)?|sourcing|seeking|looking for)\W+(?:\w+\W+){0,4}?(?:vendors?|partners?|integrators?|suppliers?)\W+(?:\w+\W+){0,4}?" + _R, 35, "vendor selection"),
    (r"(?:purchas|order|acquir|buy|sign\w* (?:a |an )?(?:deal|contract|agreement))\w*\W+(?:\w+\W+){0,5}?" + _R, 30, "purchase / contract"),
)

EVALUATING = (
    (r"(?:implement|deploy|roll(?:ing)? out|introduc|install|integrat|scal|launch|adopt)\w*\W+(?:\w+\W+){0,5}?" + _R, 22, "deploying automation"),
    (_R + r"\W+(?:\w+\W+){0,3}?(?:program|roadmap|strategy|initiative|investment|project|transformation|budget)", 22, "automation program"),
    (r"(?:invest\w*|\$\d[\d.,]*\s*(?:million|billion|m|bn)\b)\W+(?:\w+\W+){0,6}?" + _R, 25, "automation investment"),
    (r"(?:new|greenfield|state[- ]of[- ]the[- ]art|highly|fully)\s+automated\s+(?:facility|distribution center|dc|warehouse|plant|fulfillment center|kitchen)", 25, "automated facility"),
    (r"lights[- ]out|industry 4\.0|smart (?:factory|warehouse)", 12, "automation strategy"),
    (r"(?:open|build|construct|break\w* ground on|plan)\w*\W+(?:\w+\W+){0,6}?" + _R, 22, "automated facility"),
)

EXPANDING = (
    (r"(?:maintain|troubleshoot|repair|service|support|operate|monitor|supervise|program)\w*\W+(?:\w+\W+){0,4}?" + _R, 18, "already runs robots"),
    (r"(?:alongside|with|next to)\W+(?:\w+\W+){0,2}?(?:robots?|cobots?|amrs?|agvs?|autonomous)", 18, "already runs robots"),
    (r"\b(?:robot|cobot|amr|agv|asrs|automation) (?:technician|tech|operator|attendant|coordinator|supervisor|specialist)s?\b", 18, "robot ops role"),
)

PAIN = (
    (r"(?:labor|staffing|worker|workforce) (?:shortage|challenges?|gap|crisis)|high turnover|hard[- ]to[- ]fill|can'?t find (?:workers|staff)", 6, "labor shortage"),
    (r"(?:sign(?:ing|-on)|hiring|retention|referral) bonus", 3, "hiring bonus"),
    (r"(?:hiring|start) (?:immediately|now|asap)|immediate (?:hire|start|openings?)|hiring event|mass hiring", 2, "urgent hiring"),
    (r"(?:freezer|cold storage|hazardous|confined space|extreme heat)", 2, "hazardous work"),
)

_COMPILED = {
    "buy_now": [(re.compile(p, re.I), w, l) for p, w, l in BUY_NOW],
    "evaluating": [(re.compile(p, re.I), w, l) for p, w, l in EVALUATING],
    "expanding": [(re.compile(p, re.I), w, l) for p, w, l in EXPANDING],
    "pain": [(re.compile(p, re.I), w, l) for p, w, l in PAIN],
}

# Stories about vendors (funding, launches) are not buyer evidence.
_VENDOR_STORY_RE = re.compile(
    r"\b(?:raises?|raised|funding round|series [a-e]|seed round|launches?|unveils?|introduces? (?:its|a) new|"
    r"announces? (?:its|a) new (?:robot|product)|ipo|valuation)\b",
    re.I,
)

# "Automation" that has nothing to do with robots.
_NOT_ROBOT_AUTOMATION_RE = re.compile(
    r"\b(?:test|testing|qa|quality assurance|software|marketing|sales|email|robotic process|rpa|it|network|"
    r"devops|infrastructure|cloud|home|building|business process|workflow|document|accounts payable|payroll|"
    r"intelligent|hyper|ui|web|selenium|cypress)[- ]automation\b|\bautomation (?:test(?:ing|er)?|qa|scripts?|framework|anywhere)\b"
    r"|\brpa\b|\bsdet\b",
    re.I,
)

STAGES = ("buying_now", "evaluating", "expanding", "primed", "watch")


@dataclass
class Evidence:
    kind: str
    label: str
    text: str
    source_url: Optional[str] = None
    seen_at: Optional[str] = None


@dataclass
class BuyerReadiness:
    company: str
    score: float
    stage: str
    evidence: list[Evidence] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    open_automatable_postings: int = 0
    pain_labels: list[str] = field(default_factory=list)
    is_vendor: bool = False
    why: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["evidence"] = d["evidence"][:12]
        d["computed_at"] = datetime.now(timezone.utc).isoformat()
        return d


def _signal_fields(sig: Any) -> tuple[str, str, Optional[str], Optional[datetime]]:
    if isinstance(sig, dict):
        return (str(sig.get("signal_type") or ""), str(sig.get("signal_text") or ""),
                sig.get("source_url"), sig.get("created_at"))
    return (str(getattr(sig, "signal_type", "") or ""), str(getattr(sig, "signal_text", "") or ""),
            getattr(sig, "source_url", None), getattr(sig, "created_at", None))


def _posting_title(text: str) -> Optional[str]:
    """'ROBOT TASK SIGNAL | Order Picker | …' → 'Order Picker'."""
    parts = [p.strip() for p in text.split("|")]
    if len(parts) >= 2 and parts[0].upper().startswith(("ROBOT TASK SIGNAL", "ROBOT_JOB", "ROBOT JOB")):
        return parts[1]
    return None


# Typed signals the intelligence pipeline already writes. One credit per type per
# company (plus a little for repeats) — the text patterns below still add detail.
SIGNAL_TYPE_WEIGHTS: dict[str, tuple[str, float, str]] = {
    "rfp_posted": ("buy_now", 35, "tender / RFP"),
    "government_contract": ("buy_now", 30, "government contract"),
    "vendor_selection": ("buy_now", 35, "vendor selection"),
    "pilot_success": ("buy_now", 30, "pilot / trial"),
    "robot_installation": ("expanding", 20, "robots installed"),
    "automation_intent": ("evaluating", 15, "automation intent"),
    "automation_interest": ("evaluating", 8, "automation interest"),
    "automation_leadership_hire": ("evaluating", 20, "automation hire"),
}

_COUNTRIES_REGIONS = frozenset(
    """afghanistan albania algeria argentina armenia australia austria bangladesh belgium bolivia brazil bulgaria
    cambodia cameroon canada chile china colombia croatia cuba czechia denmark ecuador egypt estonia ethiopia finland
    france georgia germany ghana greece guatemala hungary india indonesia iran iraq ireland israel italy jamaica japan
    jordan kazakhstan kenya korea kuwait laos latvia lebanon lithuania malaysia mexico morocco myanmar nepal netherlands
    nigeria norway oman pakistan panama peru philippines poland portugal qatar romania russia rwanda serbia singapore
    slovakia slovenia spain sweden switzerland taiwan tanzania thailand tunisia turkey uganda ukraine uruguay uzbekistan
    venezuela vietnam yemen zambia zimbabwe usa us uk europe asia africa""".split()
) | frozenset({"sri lanka", "south korea", "north korea", "new zealand", "south africa", "saudi arabia",
               "united states", "united kingdom", "united arab emirates", "hong kong", "latin america",
               "middle east", "north america", "costa rica", "dominican republic", "puerto rico", "el salvador",
               "las vegas", "new york", "los angeles", "san francisco", "silicon valley"})

_HEADLINE_RE = re.compile(
    r"^(?:how|why|what|when|where|who|which|is|are|can|will|this|these|top|best|inside|watch|video|report)\b"
    r"|\b(?:are|is|was|were|will|says?|said|could|would|announces?|reveals?|launch(?:es)?|plans?)\b.*\b\w+\b"
    r"|\bto (?:open|build|deploy|add|launch|use|test|buy|invest|expand|hire|cut|replace|roll)\b",
    re.I,
)
_ENCODED_RE = re.compile(r"^[A-Za-z0-9+/=_-]{20,}$")


def buyer_name_problem(name: str) -> Optional[str]:
    """Why a stored company name can't be a buyer (headline fragment, place, encoded junk), or None."""
    n = (name or "").strip()
    low = n.lower().strip(" .,")
    if len(n) < 2:
        return "empty name"
    if _ENCODED_RE.match(n) and (any(c.isdigit() for c in n) or n != n.lower() and n != n.upper() and " " not in n and len(n) >= 24):
        return "encoded string, not a company"
    if low in _COUNTRIES_REGIONS:
        return "place name, not a company"
    words = n.split()
    if len(words) >= 6 or (len(words) >= 3 and _HEADLINE_RE.search(n)):
        return "headline fragment, not a company"
    if "robot" in low and not any(w in low for w in ("hotel", "casino", "resort")):
        return "robot vendor (supply side)"
    if n.endswith(("?", "!")) or n.count('"') or n.count("|"):
        return "headline fragment, not a company"
    return None


def assess_company(company_name: str, signals: Iterable[Any], *, now: Optional[datetime] = None,
                   recent_days: int = 180) -> BuyerReadiness:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=recent_days)
    vendor = is_robot_vendor(company_name)
    evidence: list[Evidence] = []
    weights: Counter = Counter()
    pain_labels: Counter = Counter()
    families: Counter = Counter()
    postings = 0
    seen_labels: set[tuple[str, str]] = set()

    typed_seen: Counter = Counter()
    for sig in signals:
        stype, text, url, ts = _signal_fields(sig)
        if not text:
            continue
        typed = SIGNAL_TYPE_WEIGHTS.get(stype.strip().lower())
        if typed and not (vendor and _VENDOR_STORY_RE.search(text)):
            kind, w, label = typed
            n = typed_seen[stype]
            typed_seen[stype] += 1
            if n < 4:
                weights[kind] += w if n == 0 else w * 0.15
                if n == 0:
                    evidence.append(Evidence(kind, label, text[:240], getattr(sig, "source_url", None)
                                             if not isinstance(sig, dict) else sig.get("source_url"),
                                             ts.isoformat() if hasattr(ts, "isoformat") else None))
        if ts is not None and getattr(ts, "tzinfo", None) is None:
            ts = ts.replace(tzinfo=timezone.utc)
        recency = 1.0 if (ts is None or ts >= cutoff) else 0.5
        seen = ts.isoformat() if ts else None
        text = _NOT_ROBOT_AUTOMATION_RE.sub(" ", text)
        title = _posting_title(text)
        blob = f"{stype} {text}"

        if title is not None:
            # A job posting: automation roles / robot language are buyer evidence;
            # operational titles only count toward pain-at-scale.
            if BUILDER_TITLE_RE.search(title):
                continue
            if BUYER_AUTOMATION_ROLE_RE.search(title):
                key = ("evaluating", title.lower())
                if key not in seen_labels:
                    seen_labels.add(key)
                    weights["evaluating"] += 20 * recency
                    evidence.append(Evidence("evaluating", "automation hire", title, url, seen))
            fams = match_families(title)
            if fams:
                postings += 1
                families[fams[0].family.key] += 1
        elif _VENDOR_STORY_RE.search(text) and vendor:
            continue

        for kind in ("buy_now", "evaluating", "expanding"):
            for rx, w, label in _COMPILED[kind]:
                m = rx.search(blob)
                if not m:
                    continue
                key = (kind, label + "|" + (title or text[:80]).lower())
                if key in seen_labels:
                    break
                seen_labels.add(key)
                weights[kind] += w * recency
                snippet = text[max(0, m.start() - 60): m.end() + 60].strip() if title is None else title
                evidence.append(Evidence(kind, label, snippet[:240], url, seen))
                break
        for rx, w, label in _COMPILED["pain"]:
            if rx.search(blob):
                pain_labels[label] += 1

    # Pain at scale from posting volume (log-ish, capped).
    vol = 0.0
    for threshold, pts in ((5, 8), (15, 8), (40, 8), (100, 6)):
        if postings >= threshold:
            vol += pts
    pain_pts = min(15.0, sum(w for rx, w, l in _COMPILED["pain"] for _ in range(min(pain_labels.get(l, 0), 3))))
    primed = min(45.0, vol + pain_pts + (5 if len(families) >= 2 else 0))

    buy = min(60.0, weights["buy_now"])
    evalu = min(40.0, weights["evaluating"])
    expand = min(30.0, weights["expanding"])
    score = min(100.0, buy + evalu + expand + (primed * (0.5 if (buy or evalu or expand) else 1.0)))

    name_problem = buyer_name_problem(company_name)
    if vendor:
        stage, score, why = "watch", min(score, 10.0), "robot vendor (supply side)"
    elif name_problem:
        stage, score, why = "watch", 0.0, name_problem
    elif buy >= 30:
        stage, why = "buying_now", "tender, pilot or vendor selection on record"
    elif evalu >= 20:
        stage, why = "evaluating", "hiring automation talent / automation program stated"
    elif expand >= 18:
        stage, why = "expanding", "already operates robots — next site or next workflow"
    elif primed >= 24:
        stage, why = "primed", f"{postings} open postings for work robots do today"
    else:
        stage, why = "watch", "not enough buying evidence yet"

    order = {"buy_now": 0, "evaluating": 1, "expanding": 2}
    evidence.sort(key=lambda e: (order.get(e.kind, 9), e.seen_at or ""), reverse=False)
    return BuyerReadiness(
        company=company_name,
        score=round(score, 1),
        stage=stage,
        evidence=evidence,
        workflows=[k for k, _ in families.most_common(5)],
        open_automatable_postings=postings,
        pain_labels=[k for k, _ in pain_labels.most_common()],
        is_vendor=vendor,
        why=why,
    )
