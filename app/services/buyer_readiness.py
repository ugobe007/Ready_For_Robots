"""Buyer readiness — is there an open door to sell this COMPANY robots?

We sell into WORKFLOWS. Robots already bought for one job close that job (unless
the company wants more), not the company. Each company gets a per-category
opportunity map (``opportunity_map.py``): what it is trying to automate, the
status of each category, scored against what we predict that kind of operator
needs. Stages, strongest door first:

  RFP_OPEN    published RFP / RFI / sources sought — budget confirmed
  EXPANDING   has robots in a category and wants more, or a new category
  EXPLORING   exploring / planning / budgeting / piloting, no vendor locked in
  PREPARING   modernizing or under labor pressure (incl. robot owners under
              pressure); predicted needs listed, nothing said yet
  PRIMED      heavy hiring volume for work robots do today, nothing else yet
  COMMITTED   already bought robots, nothing new on record — not a lead now
  WATCH       not enough evidence; robot vendors; junk names
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
    (r"(?:invest\w*|budget\w*|commit\w*|earmark\w*|allocat\w*|[$€£]\s?\d[\d.,]*\s*(?:million|billion|m|bn)\b)\W+(?:\w+\W+){0,8}?" + _R,
     25, "automation investment"),
    (r"(?:new|greenfield|state[- ]of[- ]the[- ]art|highly|fully)\s+automated\s+(?:facility|distribution center|dc|warehouse|plant|fulfillment center|kitchen)", 25, "automated facility"),
    (r"lights[- ]out|industry 4\.0|smart (?:factory|warehouse)", 12, "automation strategy"),
    (r"(?:explor|consider|evaluat|stud(?:y|ies|ying)|assess|look\w* (?:at|into)|weigh)\w*\W+(?:\w+\W+){0,4}?"
     r"(?:robot\w*|automat\w*|autonomous|technology (?:to|that) (?:replace|reduce|assist))", 20, "exploring robots / automation"),
    (r"(?:open|build|construct|break\w* ground on|plan)\w*\W+(?:\w+\W+){0,6}?" + _R, 22, "automated facility"),
)

EXPANDING = (
    (r"(?:maintain|troubleshoot|repair|service|support|operate|monitor|supervise|program)\w*\W+(?:\w+\W+){0,4}?" + _R, 18, "already runs robots"),
    (r"(?:alongside|with|next to)\W+(?:\w+\W+){0,2}?(?:robots?|cobots?|amrs?|agvs?|autonomous)", 18, "already runs robots"),
    (r"\b(?:robot|cobot|amr|agv|asrs|automation) (?:technician|tech|operator|attendant|coordinator|supervisor|specialist)s?\b", 18, "robot ops role"),
)

# Indirect intent: the decision to evaluate robots is forming.
_OPS = (r"(?:operations?|facilit(?:y|ies)|supply chain|distribution|warehous\w*|fulfillment|kitchens?|restaurants?|stores?|"
        r"plants?|factor(?:y|ies)|manufacturing|production|logistics|network|fleet|workforce|labor model|back[- ]of[- ]house|"
        r"housekeeping|laundry|terminals?|airport|hotels?|propert(?:y|ies)|campus|dcs?|processes|workflows?|"
        r"parks?|resorts?|casinos?|ships?|fleet|venues?|stadiums?|arenas?|hospitals?|units?|locations?)")
PREPARING = (
    (r"(?:budget\w*|capital (?:plan|budget|spending|expenditure|investment)s?|capex|allocat\w*|earmark\w*|set aside)"
     r"\W+(?:\w+\W+){0,8}?(?:technology|equipment|efficien\w*|moderni[sz]\w*|upgrad\w*|" + _OPS + r")", 12, "budgeting for operations"),
    (r"(?:moderni[sz]\w*|upgrad\w*|overhaul\w*|transform\w*|retool\w*|refresh\w*|revamp\w*|reinvent\w*|future[- ]proof\w*)"
     r"\W+(?:\w+\W+){0,4}?" + _OPS, 10, "modernizing operations"),
    (r"(?:re-?align\w*|re-?design\w*|re-?engineer\w*|re-?imagin\w*|re-?structur\w*|re-?think\w*|streamlin\w*|optimi[sz]\w*|"
     r"standardi[sz]\w*)\W+(?:\w+\W+){0,4}?" + _OPS, 9, "redesigning workflows"),
    (r"(?:efficiency|productivity|cost[- ](?:reduction|savings?|cutting|out)|margin (?:improvement|expansion)|operational excellence|"
     r"lean|continuous improvement)\W+(?:\w+\W+){0,3}?(?:program|initiative|plan|push|drive|effort|target|goal|strategy)", 10, "efficiency program"),
    (r"(?:reduce|lower|cut|offset|control|manage)\w*\W+(?:\w+\W+){0,3}?(?:labor|labour|staffing|personnel|headcount|wage|payroll)\s*(?:costs?|expenses?|spend|hours)?", 10, "labor cost focus"),
    (r"(?:do more with (?:less|fewer)|fewer (?:workers|employees|people|staff)|smaller (?:workforce|crews?|staff)|"
     r"labor[- ]sav\w*|labor[- ]light|reduce reliance on (?:labor|workers|staff))", 12, "labor-light model"),
    (r"(?:workforce|labor) (?:transformation|planning|strategy|model|optimization)|future of work|reskill\w*|upskill\w*", 8, "workforce transformation"),

    (r"(?:kitchen|store|in-store|warehouse|distribution|fulfillment|operations?|operational|back[- ]of[- ]house|labor|"
     r"housekeeping|guest[- ]service|plant|factory|production|hotel|property|restaurant|frontline)\s+"
     r"(?:technology|tech|automation|equipment)\s+(?:investments?|upgrades?|roadmap|rollout|initiative|spend)", 12,
     "operational technology investment"),
    (r"(?:technology|tech|digital|innovation) (?:investments?|upgrades?|roadmap|transformation|initiative|spend)", 8, "technology investment"),
    (r"(?:smart|connected|next[- ]gen(?:eration)?|store of the future|kitchen of the future|hotel of the future)\s+"
     r"(?:stores?|kitchens?|hotels?|warehouses?|factor(?:y|ies)|plants?|airports?|buildings?|restaurants?)", 10, "next-gen facility"),
    (r"(?:new|additional|second|third|larger|expanded)\s+(?:distribution|fulfillment|cold storage|production|processing|manufacturing|"
     r"central|commissary|laundry)\s+(?:center|facility|plant|kitchen|hub|campus)", 8, "new facility"),
)

# Routine business events: real context, but never enough on their own.
WEAK_PREP_LABELS = frozenset({
    "operations leadership hire", "expansion", "M&A / integration", "new facility", "technology investment",
})

# Labor pressure that pushes companies toward robots.
PRESSURE = (
    (r"(?:labor|labour|staffing|worker|workforce|employee|driver|nurse|kitchen|housekeeping) (?:shortages?|crunch|crisis|challenges?|gap|constraints?|woes)",
     12, "labor shortage"),
    (r"(?:high|record|rising|chronic|elevated)\s+(?:employee\s+|staff\s+|worker\s+)?(?:turnover|attrition|churn)|turnover (?:rates?|of \d+)", 12, "high turnover"),
    (r"(?:can'?t|cannot|unable to|struggl\w* to|hard to|difficult to|difficulty) (?:find|hire|keep|retain|recruit|staff|fill)", 12, "can't staff"),
    (r"(?:minimum wage|wage (?:hikes?|increases?|inflation|pressure|growth)|rising (?:labor|wage) costs?|labor cost (?:pressure|inflation|increases?)|"
     r"higher (?:labor|wage) costs?|\$20 (?:an hour|minimum)|fast food council|ab ?1228)", 10, "wage pressure"),
    (r"(?:union|strike|walkout|labor dispute|collective bargaining|work stoppage)", 6, "labor relations"),
    (r"(?:reduced|cut|limited|shortened) (?:hours|shifts|service|menu)|closed (?:early|dining rooms?)|(?:due to|because of) (?:staffing|labor)", 10, "service cut from staffing"),
    (r"(?:injur\w*|osha|ergonomic\w*|workers'? comp\w*|heat illness|repetitive strain)", 6, "injury / safety"),
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
    "preparing": [(re.compile(p, re.I), w, l) for p, w, l in PREPARING],
    "pressure": [(re.compile(p, re.I), w, l) for p, w, l in PRESSURE],
}

# Industries where labor pressure translates into robot evaluation.
_LABOR_HEAVY_RE = re.compile(
    r"\b(?:restaurants?|food ?service|quick[- ]service|qsr|fast[- ]casual|dining|cafeterias?|catering|kitchens?|"
    r"warehous\w*|logistics|distribution|fulfillment|3pl|supply chain|freight|parcel|trucking|cold (?:chain|storage)|"
    r"retail|grocer\w*|supermarkets?|department stores?|convenience|pharmac\w*|"
    r"janitorial|cleaning|custodial|facilit\w*|building services|property management|"
    r"airports?|aviation|airlines?|"
    r"laundr\w*|linen|uniform|"
    r"hotels?|hospitality|resorts?|casinos?|gaming|cruise|"
    r"factor(?:y|ies)|manufactur\w*|plants?|food processing|meat|poultry|bakery|packaging|bottling|"
    r"hospitals?|health ?care|health system|senior living|nursing|"
    r"agricultur\w*|farms?|growers?|produce|dairy|"
    r"parking|car wash|waste|recycling)\b",
    re.I,
)


def is_labor_heavy(industry: str = "", company_name: str = "") -> bool:
    return bool(_LABOR_HEAVY_RE.search(f"{industry or ''} {company_name or ''}"))

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

STAGES = ("rfp_open", "expanding", "exploring", "preparing", "primed", "committed", "watch")


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
    opportunities: dict = field(default_factory=dict)

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
    # buying now
    "rfp_posted": ("buy_now", 35, "tender / RFP"),
    "government_contract": ("buy_now", 30, "government contract"),
    "vendor_selection": ("buy_now", 35, "vendor selection"),
    "pilot_success": ("buy_now", 30, "pilot / trial"),
    # already running robots
    "robot_installation": ("expanding", 20, "robots installed"),
    "scale_expansion": ("expanding", 20, "scaling robots"),
    "roi_documented": ("expanding", 18, "robot ROI documented"),
    # evaluating
    "automation_intent": ("evaluating", 15, "automation intent"),
    "automation_leadership_hire": ("evaluating", 20, "automation hire"),
    "budget_allocated": ("evaluating", 15, "budget allocated"),
    "factory_automation": ("evaluating", 12, "factory automation"),
    "packaging_automation": ("evaluating", 12, "packaging automation"),
    "automation_interest": ("evaluating", 8, "automation interest"),
    "economics_driven": ("evaluating", 10, "automation economics"),
    "competitive_response": ("evaluating", 10, "competitor automating"),
    "problem_solution": ("evaluating", 10, "automation problem/solution"),
    "equipment_integration": ("evaluating", 8, "equipment integration"),
    # preparing (indirect intent)
    "capex": ("preparing", 12, "capital spending"),
    "warehouse_throughput": ("preparing", 10, "throughput pressure"),
    "production_capacity": ("preparing", 8, "capacity pressure"),
    "quality_bottleneck": ("preparing", 8, "quality bottleneck"),
    "material_handling": ("preparing", 8, "material handling problem"),
    "repetitive_process": ("preparing", 8, "repetitive process"),
    "trade_show_attendance": ("preparing", 8, "automation trade show"),
    "expansion": ("preparing", 6, "expansion"),
    "strategic_hire": ("preparing", 6, "operations leadership hire"),
    "ma_activity": ("preparing", 4, "M&A / integration"),
    # labor pressure
    "labor_shortage": ("pressure", 12, "labor shortage"),
    "labor_pain": ("pressure", 4, "labor pain"),
    "safety_incident": ("pressure", 6, "safety incident"),
    "service_consistency": ("pressure", 4, "service consistency"),
}

def buyer_name_problem(name: str) -> Optional[str]:
    """Why a stored company name can't be a buyer (headline fragment, place, encoded junk, robot vendor), or None."""
    from app.services.company_identity import junk_name_reason

    reason = junk_name_reason(name)
    if reason:
        return reason
    low = (name or "").lower()
    if "robot" in low and not any(w in low for w in ("hotel", "casino", "resort")):
        return "robot vendor (supply side)"
    return None


def assess_company(company_name: str, signals: Iterable[Any], *, now: Optional[datetime] = None,
                   recent_days: int = 180, industry: str = "") -> BuyerReadiness:
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
    prep_labels: Counter = Counter()
    map_signals: list[dict] = []
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
                if kind == "preparing":
                    prep_labels[label] += w if n == 0 else w * 0.15
                if n == 0:
                    evidence.append(Evidence(kind, label, text[:240], getattr(sig, "source_url", None)
                                             if not isinstance(sig, dict) else sig.get("source_url"),
                                             ts.isoformat() if hasattr(ts, "isoformat") else None))
        if ts is not None and getattr(ts, "tzinfo", None) is None:
            ts = ts.replace(tzinfo=timezone.utc)
        recency = 1.0 if (ts is None or ts >= cutoff) else 0.5
        seen = ts.isoformat() if ts else None
        text = _NOT_ROBOT_AUTOMATION_RE.sub(" ", text)
        map_signals.append({"signal_type": stype, "signal_text": text, "source_url": url,
                            "seen_at": ts.isoformat()[:10] if hasattr(ts, "isoformat") else ""})
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
                    map_signals.append({"signal_type": "automation_leadership_hire",
                                        "signal_text": f"Hiring {title} for automation", "source_url": url,
                                        "seen_at": (seen or "")[:10]})
            fams = match_families(title)
            if fams:
                postings += 1
                families[fams[0].family.key] += 1
        elif _VENDOR_STORY_RE.search(text) and vendor:
            continue

        for kind in ("buy_now", "evaluating", "expanding", "preparing", "pressure"):
            if title is not None and kind in ("preparing", "pressure"):
                continue  # posting boilerplate ("optimize workflows") is not company intent
            for rx, w, label in _COMPILED[kind]:
                m = rx.search(blob)
                if not m:
                    continue
                key = (kind, label + "|" + (title or text[:80]).lower())
                if key in seen_labels:
                    if kind in ("preparing", "pressure"):
                        continue
                    break
                seen_labels.add(key)
                weights[kind] += w * recency
                if title is not None and kind == "expanding":
                    map_signals.append({"signal_type": "robot_installation", "signal_text": title,
                                        "source_url": url, "seen_at": (seen or "")[:10]})
                if kind == "preparing":
                    prep_labels[label] += w * recency
                if kind == "pressure":
                    pain_labels[label] += 1
                snippet = text[max(0, m.start() - 60): m.end() + 60].strip() if title is None else title
                evidence.append(Evidence(kind, label, snippet[:240], url, seen))
                if kind not in ("preparing", "pressure"):
                    break  # strong kinds: one credit per item; indirect cues stack
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

    labor_heavy = is_labor_heavy(industry, company_name)
    buy = min(60.0, weights["buy_now"])
    evalu = min(40.0, weights["evaluating"])
    expand = min(30.0, weights["expanding"])
    prep = min(30.0, weights["preparing"])
    # A hire, a new store or a deal alone is routine; it needs a real modernization cue beside it.
    strong_prep = min(30.0, sum(w for lbl, w in prep_labels.items() if lbl not in WEAK_PREP_LABELS))
    distinct_prep = len(prep_labels)
    pressure = min(25.0, weights["pressure"] * (1.0 if labor_heavy else 0.5))
    if labor_heavy:
        primed = min(45.0, primed * 1.2)
    score = min(100.0, buy + evalu + expand + 0.6 * prep + 0.5 * pressure
                + (primed * (0.5 if (buy or evalu or expand) else 1.0)))
    under_pressure = pressure >= 10 or primed >= 24
    labor_focus = any(e.label in ("labor cost focus", "labor-light model", "workforce transformation") for e in evidence)

    name_problem = buyer_name_problem(company_name)

    # Per-category opportunity map: what are they trying to automate, and is the door open?
    from app.services.opportunity_map import OPEN_STATUSES, build_map, summarize

    opp_map = build_map(map_signals, industry=industry, company_name=company_name)
    opps = summarize(opp_map)
    open_obs = [o for o in opp_map.values() if o.status in OPEN_STATUSES]
    deployed = [o for o in opp_map.values() if o.status == "deployed"]
    by_status = {st: [o.label for o in sorted(open_obs, key=lambda o: -o.score) if o.status == st]
                 for st in OPEN_STATUSES}
    predicted_best = max((o.score for o in opp_map.values() if o.status == "predicted"), default=0.0)
    preparing_signal = (
        (strong_prep >= 8 and under_pressure)
        or (prep >= 20 and labor_heavy and labor_focus)
        or (strong_prep >= 10 and (labor_heavy or distinct_prep >= 2)) or (strong_prep >= 8 and prep >= 15)
        or (pressure >= 12 and labor_heavy)
    )

    def _labels(xs: list[str]) -> str:
        return ", ".join(x.split(" / ")[0] for x in xs[:3])

    if open_obs:
        score = min(100.0, opps["best_open_score"] + 5 * (len(open_obs) - 1) + (5 if preparing_signal else 0))
    else:
        score = min(100.0, 0.6 * prep + 0.5 * pressure + primed * 0.8 + predicted_best * 0.3)

    if vendor:
        stage, score, why = "watch", min(score, 10.0), "robot vendor (supply side)"
    elif name_problem:
        stage, score, why = "watch", 0.0, name_problem
    elif open_obs:
        words = {"rfp": "RFP / vendor search", "expanding": "wants more", "exploring": "exploring",
                 "piloting": "piloting"}
        parts = [f"{words[st]}: {_labels(by_status[st])}" for st in OPEN_STATUSES if by_status[st]]
        if deployed:
            parts.append(f"already has {_labels([o.label for o in deployed])}")
        if by_status["rfp"]:
            parts[0] += " (budget confirmed)"
        stage = ("rfp_open" if by_status["rfp"] else "expanding" if by_status["expanding"] else "exploring")
        why = "; ".join(parts)
    elif preparing_signal or (deployed and (strong_prep >= 8 or pressure >= 10)):
        nxt = _labels([p["label"] for p in opps["predicted_next"]])
        lead = "proven robot buyer under pressure" if deployed else "modernizing / labor pressure, no vendor yet"
        stage, why = "preparing", f"{lead} — likely needs {nxt}" if nxt else lead
    elif primed >= 24:
        stage, why = "primed", f"{postings} open postings for work robots do today"
    elif deployed:
        stage, score, why = "committed", min(score, 15.0), (
            f"already has {_labels([o.label for o in deployed])}; no new interest on record")
    else:
        stage, why = "watch", "not enough buying evidence yet"

    order = {"buy_now": 0, "evaluating": 1, "expanding": 2, "preparing": 3, "pressure": 4}
    evidence.sort(key=lambda e: (order.get(e.kind, 9), e.seen_at or ""), reverse=False)
    seen_ev: set[str] = set()
    evidence = [e for e in evidence if not (e.label in seen_ev or seen_ev.add(e.label))]
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
        opportunities=opps,
    )
