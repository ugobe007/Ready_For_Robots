"""Opportunity map — what is this company trying to automate, and is the door open?

We sell robots into WORKFLOWS, not companies. Disney already running cleaning
robots does not close Disney: it may want more cleaning robots, restroom /
sanitizing robots, food-prep robots, room-service delivery, entertainment robots.

For every company we build a map  {robot category → status, evidence}:

  status        meaning                                               open?
  ───────────── ───────────────────────────────────────────────────── ──────
  rfp           RFP / RFI / sources sought / tender — budget confirmed   yes ★
  expanding     has robots in this category AND wants more/next sites    yes
  exploring     exploring / considering / planning / budgeting / seeking yes
  piloting      pilot or trial under way — decision still pending         yes
  deployed      deployed / installed / purchased / vendor awarded         no
  predicted     no statement yet, but our industry model expects it       maybe

…then score it against our own prediction of what that kind of company needs
(PREDICTIONS below). Intent that matches the prediction scores higher; a
company that already bought robots in one category is a proven buyer, so its
other predicted categories score higher too.
"""
from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

_ROOT = Path(__file__).resolve().parents[2]

# ─── Robot categories (what is being automated) ──────────────────────────────

CATEGORIES: dict[str, tuple[str, str]] = {
    # key: (label, regex of category language)
    "general": ("Automation (unspecified)", r""),
    "restroom_sanitizing": ("Restroom / sanitizing / disinfection",
        r"restrooms?|bathrooms?|toilets?|saniti[sz]\w*|disinfect\w*|uv-?c|uv (?:light|robot)\w*|germ[- ]killing"),
    "cleaning": ("Floor & surface cleaning",
        r"floor[- ](?:scrub|clean|care)\w*|scrubb\w*|vacuum\w*|sweep\w*|cleaning robots?|robotic clean\w*|"
        r"autonomous clean\w*|janitorial robot\w*|clean(?:s|ed)? (?:the )?floors?|window[- ]clean\w*|pool[- ]clean\w*|"
        r"housekeeping (?:robot|automation)\w*|housekeeping\W+(?:\w+\W+){0,2}(?:robot|automat)\w*"),
    "delivery_service": ("Delivery / room service / serving",
        r"room[- ]service|food delivery|meal delivery|delivery robots?|delivering (?:food|meals|amenities|towels|orders)|"
        r"serving robots?|server robots?|robot (?:servers?|waiters?|runners?)|runner robots?|tray\w*|cocktail\w*|bussing|"
        r"butler robots?|amenity deliver\w*|in-?room deliver\w*|autonomous deliver\w*"),
    "food_prep": ("Food prep / kitchen / beverage",
        r"kitchen robot\w*|robotic kitchen\w*|food[- ]prep\w*|fry(?:er|ing)? robot\w*|robotic fry\w*|burger robot\w*|"
        r"robot(?:ic)? (?:chef|cook|barista|bartender|pizza|salad|bowl)\w*|(?:pizza|salad|bowl|coffee|drink|beverage|"
        r"cocktail|noodle|wok) robot\w*|automated kitchen\w*|cooking robot\w*|dish(?:washing)? robot\w*"),
    "entertainment": ("Entertainment / guest experience",
        r"animatronic\w*|entertainment robot\w*|show robot\w*|stunt(?:ronic)?\w*|character robot\w*|"
        r"guest experiences?|interactive robot\w*|performing robot\w*|robot (?:show|performer|character)s?"),
    "concierge": ("Concierge / greeting / wayfinding",
        r"concierge\w*|greeter robot\w*|reception robot\w*|check-?in robot\w*|wayfinding|guide robots?|"
        r"information robots?|robot (?:host|greeter|guide)s?|humanoid host\w*"),
    "security": ("Security / patrol",
        r"security robots?|patrol\w*|surveillance robot\w*|guard robots?|robot(?:ic)? (?:guard|security)\w*"),
    "warehouse_amr": ("Warehouse AMR / goods-to-person",
        r"\bamrs?\b|autonomous mobile robots?|\bagvs?\b|goods[- ]to[- ]person|\basrs\b|as/rs|autostore|"
        r"(?:picking|pick) robots?|robotic picking|sortation|tote\w*|micro[- ]fulfillment|fulfillment robots?|warehouse robots?|"
        r"warehouse automation|(?:distribution|fulfillment) (?:center )?automation|automated (?:distribution|fulfillment|"
        r"warehouse)\w*|robots? (?:at|in|across) (?:its |all |the |\d+ )?(?:dcs?|distribution centers?|warehouses?|"
        r"fulfillment centers?)"),
    "palletizing": ("Palletizing / truck unloading / handling",
        r"palleti[sz]\w*|depalleti[sz]\w*|truck[- ]unload\w*|trailer[- ]unload\w*|case[- ]pick\w*|robotic arms?|parcel handling robot\w*"),
    "forklift": ("Autonomous forklift / pallet movement",
        r"autonomous forklifts?|robotic forklifts?|driverless forklifts?|pallet movers?|autonomous (?:tugger|pallet)\w*"),
    "inventory": ("Inventory / shelf scanning",
        r"shelf[- ]scann\w*|inventory robots?|inventory drones?|robots? (?:that )?scan shelves|out[- ]of[- ]stock"),
    "laundry": ("Laundry / linen",
        r"laundry robot\w*|folding robot\w*|robotic (?:folding|laundry)\w*|linen (?:robot|automation)\w*"),
    "manufacturing": ("Manufacturing cells (cobots, welding, tending)",
        r"cobots?|collaborative robots?|welding robot\w*|robotic welding|machine tending|robotic assembly|industrial robots?"),
    "healthcare_logistics": ("Hospital logistics / pharmacy / lab",
        r"hospital deliver\w*|medication deliver\w*|pharmacy (?:robot|automation)\w*|\btugs?\b|lab(?:oratory)? automation|"
        r"specimen\w*|nursing robots?|patient[- ](?:lift|transport) robot\w*|moxi"),
    "outdoor": ("Outdoor / grounds / facade",
        r"robotic (?:mower|lawn)\w*|robot(?:ic)? mowers?|lawn robots?|snow[- ]remov\w* robot\w*|facade\w*|drone inspection\w*"),
    "last_mile": ("Last-mile / campus delivery",
        r"sidewalk (?:delivery )?robots?|delivery drones?|drone deliver\w*|last[- ]mile robot\w*|campus delivery"),
    "humanoid": ("Humanoid / general-purpose",
        r"humanoids?"),
}
_CAT_RE = {k: re.compile(r"\b(?:" + rx + r")", re.I) for k, (_, rx) in CATEGORIES.items() if rx}
_GENERAL_RE = re.compile(r"\b(?:robot\w*|cobots?|automat\w*|autonomous)\b", re.I)

# ─── Status language ─────────────────────────────────────────────────────────

_STATUS = (  # evaluated in order; first match wins for a sentence
    ("rfp", re.compile(
        r"request for (?:proposals?|quotes?|qualifications|information)|\brfp\b|\brfq\b|\brfi\b|sources sought|"
        r"solicitation|invitation (?:to|for) bid|\bitb\b|tender\w*|bid (?:notice|opportunity)|issued? (?:a )?bids?|"
        r"accepting (?:bids|proposals)|evaluating (?:vendors|suppliers|partners|integrators|providers)|vendor selection process|"
        r"selecting (?:a |an )?(?:vendor|supplier|partner|integrator|provider)|shortlist\w*|seeking (?:vendors|suppliers|"
        r"partners|integrators|proposals|bids)|request(?:ing|s)? (?:bids|proposals|quotes)", re.I)),
    ("expanding", re.compile(
        r"\b(?:expand\w*|more|additional|another|second|scal(?:e|es|ing)|next phase|phase two|other (?:locations|"
        r"properties|parks|stores|hotels|sites|facilities|resorts|ships)|across (?:all|its|the)|rest of|"
        r"add(?:s|ing)? (?:more|another)|roll(?:s|ing)? out to|extend\w*|broaden\w*|fleet of)\b", re.I)),
    ("exploring", re.compile(
        r"\b(?:explor\w*|consider\w*|evaluat\w*|interested|interest in|looking (?:at|into|to|for)|plans? to|planning|"
        r"intends?|aims? to|wants? to|hopes? to|seek\w*|budget\w*|allocat\w*|earmark\w*|stud(?:y|ying|ies)|assess\w*|"
        r"weigh\w*|eyes?|eyeing|could (?:use|add|bring)|may (?:use|add|bring)|would like|in talks|"
        r"feasibility|request(?:ing)? (?:demos?|information)|future of|plans?|invest\w*|commit(?:s|ting)?\b|"
        r"spend(?:s|ing)?|capital (?:plan|program|budget|project)s?)\b|[$€£]\s?\d[\d.,]*\s*(?:million|billion|m\b|bn\b)", re.I)),
    ("piloting", re.compile(
        r"\b(?:pilot\w*|trial\w*|test(?:s|ing|ed)?|proof[- ]of[- ]concept|\bpoc\b|beta)\b", re.I)),
    ("deployed", re.compile(
        r"\b(?:deploy\w*|install\w*|roll(?:s|ed)? out|rollout|launch\w*|introduc\w*|uses?|using|now has|has (?:added|"
        r"rolled)|added|unveil\w*|implement\w*|operat(?:es|ing)|employ\w*|award\w*|select(?:s|ed)|chose|chosen|"
        r"signs?|signed|partner\w*|purchas\w*|order(?:s|ed)|acquir\w*|bought|buys|debut\w*|welcom\w*|meet|"
        r"opens?|opening|to open|alongside|maintain\w*|troubleshoot\w*|servic(?:e|es|ing))\b", re.I)),
)
OPEN_STATUSES = ("rfp", "expanding", "exploring", "piloting")
# Typed signals trusted even when the text has no robot words (strong, specific types only;
# the classifier emits automation_interest on thousands of loosely related articles).
TYPED_TRUSTED = frozenset({"rfp_posted", "vendor_selection", "pilot_success", "robot_installation",
                           "scale_expansion", "budget_allocated", "roi_documented"})
STATUS_SCORE = {"rfp": 1.0, "expanding": 0.85, "exploring": 0.75, "piloting": 0.65, "deployed": 0.0}
STATUS_LABEL = {"rfp": "RFP / vendor search (budget confirmed)", "expanding": "expanding — wants more",
                "exploring": "exploring / planning", "piloting": "piloting — decision pending",
                "deployed": "already has", "predicted": "predicted need"}

# Typed signals → status (category still read from the text).
TYPED_STATUS = {
    "rfp_posted": "rfp", "budget_allocated": "exploring", "automation_intent": "exploring",
    "automation_interest": "exploring", "economics_driven": "exploring", "competitive_response": "exploring",
    "problem_solution": "exploring", "automation_leadership_hire": "exploring", "pilot_success": "piloting",
    "scale_expansion": "expanding", "robot_installation": "deployed", "vendor_selection": "deployed",
    "roi_documented": "deployed", "government_contract": "deployed",
}

# ─── Predictions: what each kind of operator is trying to automate ───────────

PREDICTIONS: tuple[tuple[str, dict[str, float]], ...] = (
    (r"theme park|amusement|parks? (?:&|and) resorts|disney|universal (?:parks|studios|orlando)|six flags|cedar fair|"
     r"seaworld|merlin|legoland|great wolf|water ?park|zoo|aquarium|entertainment",
     {"cleaning": .9, "restroom_sanitizing": .85, "delivery_service": .8, "food_prep": .75, "entertainment": .85,
      "security": .6, "concierge": .6}),
    (r"casino|gaming|resorts? world|wynn|caesars|mgm|sands|station casinos|boyd|red rock|fontainebleau|circa|venetian",
     {"cleaning": .9, "delivery_service": .9, "restroom_sanitizing": .7, "security": .75, "concierge": .65,
      "food_prep": .6, "entertainment": .5}),
    (r"cruise|carnival|royal caribbean|norwegian cruise",
     {"delivery_service": .85, "cleaning": .85, "food_prep": .7, "restroom_sanitizing": .7, "entertainment": .6,
      "laundry": .6, "concierge": .5}),
    (r"hotel|hospitality|resort|inn\b|suites|lodg|marriott|hilton|hyatt|ihg|wyndham|whitbread|accor|four seasons",
     {"delivery_service": .9, "cleaning": .85, "restroom_sanitizing": .6, "laundry": .65, "concierge": .6,
      "food_prep": .5, "security": .4}),
    (r"restaurant|food ?service|quick[- ]service|qsr|fast[- ]casual|dining|cafeteria|catering|pizza|burger|"
     r"chicken|taco|coffee|bakery|diner|grill|kitchen|sodexo|aramark|compass group|delaware north",
     {"food_prep": .9, "delivery_service": .8, "cleaning": .6, "restroom_sanitizing": .4}),
    (r"warehous|logistics|distribution|fulfil|3pl|supply chain|freight|parcel|courier|cold (?:chain|storage)|"
     r"trucking|wholesale|foodservice distribution",
     {"warehouse_amr": .9, "palletizing": .9, "forklift": .85, "inventory": .6, "cleaning": .5, "security": .45}),
    (r"grocer|supermarket|retail|department store|convenience|pharmac|home improvement|big[- ]box|stores",
     {"inventory": .85, "cleaning": .85, "warehouse_amr": .6, "security": .55, "delivery_service": .35,
      "last_mile": .4}),
    (r"hospitals?\b|health ?(?:care|system)|medical center|clinic|senior living|nursing|long[- ]term care",
     {"healthcare_logistics": .9, "restroom_sanitizing": .9, "cleaning": .8, "delivery_service": .7,
      "security": .4, "concierge": .35}),
    (r"airport|aviation|airline|terminal",
     {"cleaning": .9, "restroom_sanitizing": .85, "security": .75, "concierge": .75, "delivery_service": .45}),
    (r"janitorial|cleaning|custodial|facilit|building services|property management|real estate|office",
     {"cleaning": .9, "restroom_sanitizing": .85, "outdoor": .45, "security": .45}),
    (r"laundr|linen|uniform|textile rental",
     {"laundry": .9, "palletizing": .5, "warehouse_amr": .55}),
    (r"manufactur|factory|plant|industrial|automotive|aerospace|food processing|meat|poultry|bottling|packaging|"
     r"beverage|cpg|chemical",
     {"manufacturing": .9, "palletizing": .9, "warehouse_amr": .7, "forklift": .6, "security": .35}),
    (r"universit|college|campus|school district|education",
     {"last_mile": .7, "cleaning": .75, "security": .5, "food_prep": .5, "delivery_service": .5}),
    (r"stadium|arena|convention|venue|event center",
     {"cleaning": .85, "food_prep": .65, "delivery_service": .6, "security": .7, "restroom_sanitizing": .7}),
    (r"agricultur|farm|grower|produce|dairy|nursery",
     {"outdoor": .6, "palletizing": .55, "manufacturing": .4}),
)
_PRED_RE = [(re.compile(r"\b(?:" + rx + r")", re.I), cats) for rx, cats in PREDICTIONS]


def predicted_categories(industry: str = "", company_name: str = "") -> dict[str, float]:
    blob = f"{industry or ''} {company_name or ''}"
    out: dict[str, float] = {}
    for rx, cats in _PRED_RE:
        if rx.search(blob):
            for k, p in cats.items():
                out[k] = max(out.get(k, 0.0), p)
    return out


# ─── Incumbent vendors named in the text (useful for displacement / expansion) ─

@lru_cache(maxsize=1)
def _vendor_re() -> Optional[re.Pattern]:
    path = _ROOT / "docs" / "calibration" / "vendor_seed_sheets" / "vendors.csv"
    names: list[str] = []
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                n = re.sub(r"\s*\(.*?\)", "", row.get("company_name") or "").strip()
                if len(n) >= 4:
                    names.append(re.escape(n))
    except OSError:
        return None
    names += [re.escape(x) for x in ("Brain Corp", "Avidbots", "Knightscope", "Pudu", "Keenon", "Bear Robotics",
                                     "Richtech", "Miso Robotics", "Starship", "Serve Robotics", "Locus", "Symbotic",
                                     "Simbe", "Diligent", "Aethon", "Relay Robotics", "Savioke", "Boston Dynamics",
                                     "Agility Robotics", "Figure", "Tennant", "Nilfisk", "SoftBank Robotics")]
    names.sort(key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(names) + r")\b") if names else None


_VENDOR_CATEGORY = {
    "amr_agv_material_transport": "warehouse_amr", "autonomous_forklift_pallet": "forklift",
    "picking_manipulation_palletizing": "palletizing", "industrial_robot_arms": "manufacturing",
    "cobots": "manufacturing", "humanoids_general_purpose": "humanoid", "cleaning_robots": "cleaning",
    "hospitality_foodservice_delivery": "delivery_service", "inspection_security_quadrupeds": "security",
    "healthcare_hospital_service": "healthcare_logistics", "last_mile_outdoor_delivery": "last_mile",
    "agriculture": "outdoor",
}
_EXTRA_VENDOR_CATEGORY = {
    "Brain Corp": "cleaning", "Avidbots": "cleaning", "Tennant": "cleaning", "Nilfisk": "cleaning",
    "Knightscope": "security", "Pudu": "delivery_service", "Keenon": "delivery_service",
    "Bear Robotics": "delivery_service", "Relay Robotics": "delivery_service", "Savioke": "delivery_service",
    "Miso Robotics": "food_prep", "Starship": "last_mile", "Serve Robotics": "last_mile", "Locus": "warehouse_amr",
    "Symbotic": "warehouse_amr", "Simbe": "inventory", "Diligent": "healthcare_logistics",
    "Aethon": "healthcare_logistics", "Boston Dynamics": "palletizing", "Agility Robotics": "humanoid",
    "Figure": "humanoid",
}


@lru_cache(maxsize=1)
def _vendor_categories() -> dict[str, str]:
    out = dict(_EXTRA_VENDOR_CATEGORY)
    path = _ROOT / "docs" / "calibration" / "vendor_seed_sheets" / "vendors.csv"
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                n = re.sub(r"\s*\(.*?\)", "", row.get("company_name") or "").strip()
                cat = _VENDOR_CATEGORY.get(row.get("robot_category") or "")
                if n and cat:
                    out.setdefault(n, cat)
    except OSError:
        pass
    return out


def vendors_named(text: str) -> list[str]:
    rx = _vendor_re()
    return sorted(set(rx.findall(text or ""))) if rx else []


# ─── Map building ────────────────────────────────────────────────────────────

@dataclass
class CategoryOpportunity:
    category: str
    label: str
    status: str                 # rfp | expanding | exploring | piloting | deployed | predicted
    score: float = 0.0          # 0-100 for this category
    predicted: float = 0.0      # our prior for this kind of company
    evidence: list[dict] = field(default_factory=list)
    vendors: list[str] = field(default_factory=list)

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES or self.status == "predicted"


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+|\s+[–—-]\s+|\s*\|\s*")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT.split(text or "") if len(s.strip()) > 8]


_CLAUSE_SPLIT = re.compile(
    r",?\s+(?:and|while|but|as well as)\s+(?=(?:is|are|was|will|also|plans?|explor\w*|consider\w*|test\w*|"
    r"pilot\w*|has|have|evaluat\w*|looking|now|recently|it)\b)", re.I)


def classify_clauses(sentence: str) -> list[tuple[list[str], Optional[str]]]:
    """Split 'adds more cleaning robots and is exploring restroom robots' so each part keeps its own status."""
    parts = [p for p in _CLAUSE_SPLIT.split(sentence) if p.strip()]
    if len(parts) <= 1:
        return [classify_sentence(sentence)]
    sentence_status = classify_sentence(sentence)[1]
    out = []
    for part in parts:
        cats, status = classify_sentence(part)
        if cats:
            out.append((cats, status or sentence_status))
    return out or [classify_sentence(sentence)]


def classify_sentence(sentence: str) -> tuple[list[str], Optional[str]]:
    """→ (categories mentioned, status). Status None when no robot/automation language."""
    cats = [k for k, rx in _CAT_RE.items() if rx.search(sentence)]
    vendor_cats = _vendor_categories()
    for v in vendors_named(sentence):
        c = vendor_cats.get(v)
        if c and c not in cats:
            cats.append(c)
    if not cats and not _GENERAL_RE.search(sentence):
        return [], None
    status = None
    for name, rx in _STATUS:
        if rx.search(sentence):
            status = name
            break
    if status == "expanding" and not cats:
        status = "exploring"   # "more automation" with no category is interest, not expansion
    if status is None and vendors_named(sentence):
        status = "deployed"    # "... with AutoStore": a vendor is already chosen
    return (cats or ["general"]), status


def build_map(signals: Iterable[dict], *, industry: str = "", company_name: str = "") -> dict[str, CategoryOpportunity]:
    """signals: [{signal_type, signal_text, source_url, seen_at}] → {category: CategoryOpportunity}."""
    rank = {"rfp": 0, "expanding": 1, "exploring": 2, "piloting": 3, "deployed": 4}
    found: dict[str, CategoryOpportunity] = {}
    deployed_any = False
    for sig in signals:
        text = sig.get("signal_text") or ""
        stype = (sig.get("signal_type") or "").lower()
        if text.upper().startswith(("ROBOT TASK SIGNAL", "ROBOT_JOB")):
            continue  # labor postings are pain evidence, not intent
        typed = TYPED_STATUS.get(stype)
        clauses = [(sent, c, st) for sent in (_sentences(text) or [text]) for c, st in classify_clauses(sent)]
        if typed and stype in TYPED_TRUSTED and not any(c for _, c, _ in clauses):
            clauses = [(text, ["general"], typed)]   # typed signal: trust the type even without robot words
        for sentence, cats, status in clauses:
            if not cats:
                continue
            if typed and (status is None or rank.get(typed, 9) < rank.get(status, 9)):
                status = typed
            if status is None:
                continue
            for cat in cats:
                label = CATEGORIES.get(cat, ("Automation (unspecified)", ""))[0]
                cur = found.get(cat)
                ev = {"status": status, "text": sentence[:240], "url": sig.get("source_url") or "",
                      "seen_at": sig.get("seen_at") or ""}
                vendors = vendors_named(sentence)
                if cur is None:
                    found[cat] = CategoryOpportunity(cat, label, status, evidence=[ev], vendors=vendors)
                else:
                    cur.evidence.append(ev)
                    cur.vendors = sorted(set(cur.vendors) | set(vendors))
                    # deployed + later "more/next" = expanding; otherwise strongest status wins
                    if cur.status == "deployed" and status in OPEN_STATUSES:
                        cur.status = "expanding" if status in ("expanding", "exploring") else status
                    elif rank.get(status, 9) < rank.get(cur.status, 9):
                        cur.status = status
                if status == "deployed":
                    deployed_any = True
    return _score(found, predicted_categories(industry, company_name), deployed_any)


def _score(found: dict[str, CategoryOpportunity], pred: dict[str, float], proven_buyer: bool,
           ) -> dict[str, CategoryOpportunity]:
    for cat, opp in found.items():
        opp.predicted = pred.get(cat, 0.0)
        base = STATUS_SCORE.get(opp.status, 0.0)
        # Intent that matches what we expect this company to need is worth more.
        opp.score = round(100 * base * (0.7 + 0.3 * opp.predicted), 1) if base else 0.0
        opp.evidence = sorted(opp.evidence, key=lambda e: (e["status"] != opp.status, e["seen_at"]), reverse=False)[:3]
    for cat, p in pred.items():
        if cat in found:
            continue
        # Whitespace: predicted need, nothing said yet. Proven robot buyers are likelier to buy again.
        found[cat] = CategoryOpportunity(cat, CATEGORIES[cat][0], "predicted", predicted=p,
                                         score=round(100 * 0.3 * p * (1.3 if proven_buyer else 1.0), 1))
    return found


def summarize(opps: dict[str, CategoryOpportunity]) -> dict[str, Any]:
    open_obs = [o for o in opps.values() if o.status in OPEN_STATUSES]
    deployed = [o for o in opps.values() if o.status == "deployed"]
    predicted = sorted((o for o in opps.values() if o.status == "predicted"), key=lambda o: -o.score)
    open_obs.sort(key=lambda o: -o.score)
    matched = [o for o in open_obs if o.predicted >= 0.5]
    return {
        "open": [asdict(o) for o in open_obs],
        "already_has": [{"category": o.category, "label": o.label, "vendors": o.vendors,
                         "evidence": o.evidence[:1]} for o in deployed],
        "predicted_next": [{"category": o.category, "label": o.label, "score": o.score} for o in predicted[:4]],
        "matches_prediction": [o.category for o in matched],
        "best_open_score": open_obs[0].score if open_obs else 0.0,
    }
