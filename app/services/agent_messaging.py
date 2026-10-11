"""Shared wording for agent-authored Ready For Robots communication."""
from __future__ import annotations

import re

from app.services.phelan_persona import PHELAN_BANNED_PHRASES, PHELAN_ORG, phelan_buyer_email_signature, phelan_signature

# ── Cal voice: veteran sherpa for robot companies ─────────────────────────────
# Wise, abbreviated, in-the-know. Engineer-led teams, PoC → deployment reality.
# Honesty and trust over hype. Draws on deep robotics industry experience.

# External outreach constants (used in phelan_opening, phelan_vendor_opening, sales_agent)
PHELAN_INTRO = (
    "I'm Phelan, Robot Coordinator at ReadyForRobots. ReadyForRobots is recruitment and placement infrastructure for robotic labor. "
    "We evaluate physical task feasibility, cell constraints, payload/throughput requirements, and hardware capabilities "
    "to match qualified robotic labor directly to real, verified job openings at enterprise and industrial facilities."
)

PHELAN_BUYER_ROLE_LINE = (
    "I'm Phelan, Robot Coordinator at ReadyForRobots. ReadyForRobots provides recruitment and placement infrastructure for robotic labor, "
    "evaluating physical task feasibility to match qualified hardware with real production workflows."
)

PHELAN_BUYER_REMINDER_LINE = (
    "This is Phelan again, Robot Coordinator at ReadyForRobots."
)

PHELAN_VENDOR_ROLE_LINE = (
    "Our platform matches enterprise buyer demand with verified robot specifications and turnkey commercial proposals."
)

PHELAN_VENDOR_REMINDER_LINE = (
    "Quick note from ReadyForRobots regarding qualified enterprise buyer matches for your robot lineup."
)

PHELAN_VENDOR_IDENTITY = (
    "ReadyForRobots evaluates physical task feasibility, operating cell geometry, and throughput requirements "
    "to help operators cut through vendor claims and deploy qualified robotic labor."
)

PHELAN_VENDOR_SHERPA_LINE = (
    "We provide independent engineering evaluations and turnkey commercial quotes — "
    "honest readouts and 3D feasibility simulations, zero sales theater."
)

# Plain, honest, first-person. Say what I do and why I'm writing — no slogans.
BUYER_SIGNAL_EXPLANATION = (
    "ReadyForRobots is recruitment and placement infrastructure for robotic labor. "
    "We evaluate physical task feasibility, cell constraints, and hardware capabilities before pitching services, "
    "verifying whether automation belongs in the workflow at all."
)

# Quiet credibility — a plain observation about what makes robots pay off, no bravado.
BUYER_ROI_PROOF = (
    "Most deployments do not fail because the hardware is weak. They fail because the robot "
    "was assigned to the wrong problem, or the workflow, integration, and support were never "
    "scoped. The ones that succeed disappear into daily operations."
)

BUYER_OUTREACH_CTA = (
    "Find Companies Ready For Robots"
)

# Honest closing beat — builds trust rather than performing confidence.
BUYER_CAL_PERSONALITY = (
    "If robotics is not the right solution yet, I will say that directly."
)

VENDOR_SIGNAL_EXPLANATION = (
    "We capture buyer demand signals, score alignment against robot capabilities, and turn that into actionable sales motion — "
    "real intent, not list noise."
)

PHELAN_VENDOR_PIPELINE_EXPLANATION = (
    "I've reviewed your robots and specs against what buyers are asking for right now. "
    "The fit isn't always obvious on paper — ROI, proof points, PoC availability, technical support, "
    "and how your team shows up all factor in."
)

PHELAN_VENDOR_PIPELINE_LOGIC_LINE = (
    "PoCs fail when capabilities don't match buyer requirements. "
    "Deployments happen when positioning, support, and follow-through align."
)

VEGAS_DISTRIBUTION_LINE = (
    "For teams pushing hospitality or West Coast expansion, we also map buyers across Las Vegas — "
    "hotels, casinos, logistics hubs — where robot trials actually get evaluated."
)

PHELAN_VENDOR_OFFRAMP_LINE = (
    "If the signal is weak or the fit isn't there, I'll say so. "
    "The point is fewer wasted PoCs, not more pipeline noise."
)

PHELAN_VENDOR_STRATEGY_CALL_CTA = "If helpful, we can do a short walkthrough after you've reviewed the matches."

PHELAN_VENDOR_BUYER_MATCH_CTA = "Want me to send the buyer profiles? I'll flag what fits and what doesn't."

# Customer-facing rep voice (robot sales rep -> buyer ops). No Ready For Robots branding.
REP_OUTREACH_CTA = "If this belongs with someone else on your ops team, could you point me to the right contact?"


def rep_outreach_signature() -> str:
    return "Best,\n[Your name]"


def buyer_company_hook(name: str, *, industry: str = "your industry") -> str:
    """One grounded, human line about the real problem teams like theirs run into."""
    n = (name or "your team").strip()
    ind = (industry or "your industry").strip().lower()
    if ind in ("logistics", "warehousing"):
        return (
            f"For an operation like {n}, the hard part usually isn't deciding to automate — it's knowing "
            f"which robots still hold up once they're out of a demo and into your real aisles, at your "
            f"real volume. That's the part I can help with."
        )
    if ind in ("hospitality", "hotels", "casinos & gaming"):
        return (
            f"For a property like {n}, it usually comes down to overnight coverage and turnover — where "
            f"service or cleaning robots start earning their keep instead of sitting in the lobby. "
            f"Knowing which ones actually work in a real building is the tricky part."
        )
    if ind in ("healthcare", "medical technology"):
        return (
            f"Teams like {n} tend to look at robots when demand grows faster than they can hire — usually "
            f"internal transport and delivery first, since that's where the hours quietly go. Working out "
            f"which systems fit your floors is where I can help."
        )
    if ind in ("food service", "food processing & manufacturing"):
        return (
            f"In an operation like {n}, it's usually throughput and back-of-house strain that make the "
            f"case — one robot aimed at the real bottleneck, not a shelf of machines you'll never run. "
            f"Picking the right one is the hard part."
        )
    return (
        f"Teams in {industry.strip()} like {n} usually get to robots the same way: one job gets expensive "
        f"or hard to staff, and a focused pilot starts to look smarter than hiring against it. Knowing "
        f"which robot actually fits is where I come in."
    )


def max_signature() -> str:
    return "— Max\nReady For Robots"


# ── Buyer variants (persona: Observation → Interpretation → Next Step) ───────
# Three different premises, same voice: smart, analytical, practical, complete
# sentences. Problems/tasks before robots. Evidence before claims. Room to say
# robotics is not the right move yet. Every variant must (a) mention the company
# name (assembly gate) and (b) end with Cal's sign-off (draft-completeness gate).

BUYER_VARIANTS: tuple[str, ...] = ("workflow_first", "what_survives", "bottleneck_first")


def _buyer_sector(industry: str) -> str:
    """Lowercase, parenthetical-stripped sector that reads naturally after "in ...".

    Falls back to a neutral phrase for missing/junk industries so we never emit
    "in Unknown" or "in your industry teams".
    """
    ind = (industry or "").strip()
    # Drop trailing qualifiers like "Food Service (Restaurants)" -> "food service".
    if "(" in ind:
        ind = ind.split("(", 1)[0].strip()
    low = ind.lower()
    if not low or low in (
        "unknown", "general", "general robotics", "other", "n/a", "none", "your industry",
    ):
        return "your line of work"
    return low


# Per vertical: visible talk-track, short headache beats, people-noun for openers.
_GENERIC_INSIGHT = {
    "visible": "the most visible task",
    "people": "operations teams",
    "look_at": "operations",
    "task": "moving material, handling exceptions, and cleaning up after the process",
    "pressure_para": (
        "A lot of material still has to move between steps, exceptions create work that "
        "doesn't fit the standard process, and people end up filling the gaps."
    ),
    "interpretation": (
        "I've seen demos look great and still fall apart once the work hits real traffic "
        "and exception handling."
    ),
}

_INDUSTRY_INSIGHT: tuple[tuple[tuple[str, ...], dict[str, object]], ...] = (
    (
        ("logistic", "warehous", "supply chain", "fulfill", "distribution", "3pl"),
        {
            "visible": "picking",
            "people": "warehouse and distribution teams",
            "look_at": "warehouse and distribution operations",
            "task": "receiving, replenishment, pallet moves, inventory exceptions, and returns",
            "pressure_para": (
                "Receiving and replenishment involve a lot of material movement, pallets have to move "
                "continuously through the operation, and inventory exceptions and returns create work "
                "that doesn't always fit neatly into the normal warehouse flow. Those are often the "
                "places where people end up filling the gaps."
            ),
            "interpretation": (
                "That usually means more forklift traffic and labor pressure even when everyone "
                "is still debating pick rates."
            ),
        },
    ),
    (
        ("hospitality", "hotel", "casino", "gaming", "resort"),
        {
            "visible": "lobby delivery",
            "people": "hotels and resorts",
            "look_at": "hospitality operations",
            "task": "linen runs, housekeeping carts, overnight floor cleaning, and room-service logistics",
            "pressure_para": (
                "Linen runs, housekeeping carts, overnight floor cleaning, and room-service logistics "
                "keep moving whether the lobby is quiet or packed. Those back-of-house paths are often "
                "where people end up filling the gaps."
            ),
            "interpretation": (
                "Guest-facing demos photograph well. The ones that last are usually chosen for "
                "a full building on a busy weekend."
            ),
        },
    ),
    (
        ("health", "medical", "hospital", "clinic", "elder", "senior living"),
        {
            "visible": "the robot that gets public attention",
            "people": "hospital and clinical ops teams",
            "look_at": "hospital operations",
            "task": "moving supplies, meds, lab samples, linen, and waste between floors",
            "pressure_para": (
                "Supplies, meds, lab samples, linen, and waste still have to move between floors all day. "
                "That transport work often pulls clinical time away from patients, and people end up "
                "filling the gaps when the process breaks down."
            ),
            "interpretation": (
                "The return I keep seeing is staff miles and delayed transport — "
                "not the machine that makes the press release."
            ),
        },
    ),
    (
        ("food", "restaurant", "kitchen", "beverage", "grocery"),
        {
            "visible": "cooking automation",
            "people": "food operations teams",
            "look_at": "food operations",
            "task": "prep, portioning, dishwashing, packaging, and product changeovers",
            "pressure_para": (
                "Prep, portioning, dishwashing, packaging, and product changeovers create a lot of "
                "repetitive work that doesn't always show up in the cooking demo. Those stations are "
                "often where people end up filling the gaps."
            ),
            "interpretation": (
                "Most kitchen automation I've watched fail on changeover and sanitation between "
                "products, not on the cook task that films well."
            ),
        },
    ),
    (
        ("manufactur", "industrial", "automotive", "assembly", "factory", "cnc", "metal"),
        {
            "visible": "the arm on the main line",
            "people": "manufacturing teams",
            "look_at": "manufacturing operations",
            "task": "machine tending, moving material between cells, and end-of-line packaging",
            "pressure_para": (
                "Machine tending, moving material between cells, and end-of-line packaging often create "
                "more day-to-day pressure than the main line itself. Those are frequently the places "
                "where people end up filling the gaps."
            ),
            "interpretation": (
                "A cell tuned to one part number can look excellent until mix or volume changes."
            ),
        },
    ),
    (
        ("retail", "store", "e-commerce", "ecommerce", "apparel", "consumer goods"),
        {
            "visible": "shelf scanning",
            "people": "retail and fulfillment teams",
            "look_at": "retail and fulfillment operations",
            "task": "backroom sortation, replenishment, and inventory exceptions",
            "pressure_para": (
                "Backroom sortation, replenishment, and inventory exceptions keep the floor stocked, "
                "but that work doesn't always fit neatly into the standard process. Those are often "
                "the places where people end up filling the gaps."
            ),
            "interpretation": (
                "Another dashboard rarely changes what staff actually do. "
                "The useful work is usually in the backroom flow that feeds the floor."
            ),
        },
    ),
)



def _buyer_insight(industry: str) -> dict[str, object]:
    """Return Cal's deployment read for an industry (substring match, generic fallback)."""
    ind = (industry or "").strip()
    if "(" in ind:
        ind = ind.split("(", 1)[0].strip()
    low = ind.lower()
    base: dict[str, object] = dict(_GENERIC_INSIGHT)
    for keys, insight in _INDUSTRY_INSIGHT:
        if any(k in low for k in keys):
            base = dict(insight)
            break
    # Food distributors — operator-approved PFG shape.
    if "food" in low and any(k in low for k in ("distribut", "wholesale", "warehouse", "logistic", "3pl")):
        base["people"] = "food distributors"
        base["look_at"] = "food distribution"
        base["visible"] = "picking"
        base["task"] = "receiving, replenishment, pallet moves, inventory exceptions, and returns"
        base["pressure_para"] = (
            "Receiving and replenishment involve a lot of material movement, pallets have to move "
            "continuously through the operation, and inventory exceptions and returns create work "
            "that doesn't always fit neatly into the normal warehouse flow. Those are often the "
            "places where people end up filling the gaps."
        )
    return base


# ── Relationship ladder: teaching follow-ups ──────────────────────────────────
# The follow-up cadence isn't "just bumping this." Each touch teaches ONE thing
# in Cal's advisor voice: a deployment lesson (teach), a market pattern/mistake
# (trend), then an easy, genuine question that invites the buyer's expertise
# (question). No pitch, no AI tells. Company name is added by the wrapper's close
# so every touch clears the assembly gate.
LADDER_TOUCHES: tuple[str, ...] = ("teach", "trend", "question")

_GENERIC_LADDER = {
    "teach_subject": "the workflow most teams automate last",
    "teach": (
        "When a team asks me where to start with automation, they expect me to name a robot. I almost "
        "never do — I start with the workflow.\n\n"
        "The projects with the fastest payback rarely target the most visible task. They target the quiet "
        "process upstream that backs everything else up. Automate the flashy part first — the common "
        "instinct — and the ROI tends not to show."
    ),
    "trend_subject": 'why "evaluating five robots" is usually the wrong question',
    "trend": (
        "I keep a running tally of the deployments still working a year after install, and the ones quietly "
        "unplugged in a corner. The gap between those two lists is most of my week.\n\n"
        "The survivors almost never won on speed. They won on fit — matched to one real bottleneck, with "
        "integration and software actually resourced. The fastest robot in the bake-off is usually the "
        "first one parked."
    ),
    "question_subject": "one question about your operation",
    "question": (
        "I've asked a lot of operators the same question over the years, and the answer tells me more than "
        "any spec sheet.\n\n"
        "If you automated one workflow tomorrow, which would it be? Most name the busiest one. The one that "
        "actually pays back is usually the process quietly creating work everywhere else."
    ),
}

_LADDER_CONTENT: tuple[tuple[tuple[str, ...], dict[str, str]], ...] = (
    (
        ("logistic", "warehous", "supply chain", "fulfil", "distribution", "3pl"),
        {
            "teach_subject": "the workflow most warehouses automate last",
            "teach": (
                "When a logistics team asks me where to start, they expect me to name a robot. I don't — I "
                "start with receiving.\n\n"
                "A slow dock quietly backs up putaway, replenishment, and every downstream pick. Fix the "
                "front of the building and the whole floor speeds up. Automate the flashy pick line first — "
                "which is what most teams do — and you get a great demo and an ROI that never shows up."
            ),
            "trend_subject": 'why "evaluating five robots" is usually the wrong question',
            "trend": (
                "I keep a running tally of the AMRs still working a year after install, and the ones sitting "
                "unplugged in a corner. The gap between those two lists is most of my job.\n\n"
                "The ones that survive almost never won on speed. They won on fit — matched to one specific "
                "bottleneck, with integration and software actually resourced. The fastest robot in the "
                "bake-off is usually the first one parked."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "I've asked a lot of warehouse operators the same question, and the answer tells me more "
                "than any spec sheet.\n\n"
                "If you automated one workflow tomorrow, which would it be? Most people say picking. Nine "
                "times out of ten the one that actually pays back is the quiet one creating work everywhere "
                "else — receiving, replenishment, or returns."
            ),
        },
    ),
    (
        ("hospitality", "hotel", "casino", "gaming", "resort"),
        {
            "teach_subject": "the automation most hotels overlook",
            "teach": (
                "When a property asks me about robots, they're usually picturing the lobby. I steer them to "
                "the back of the house instead.\n\n"
                "The hours and the turnover pile up where guests never look — linen runs, housekeeping "
                "carts, overnight floor cleaning. The lobby delivery robot photographs beautifully and "
                "moves the needle least."
            ),
            "trend_subject": "the robot that demos well and stalls by the weekend",
            "trend": (
                "I keep track of which service robots are still running after the first busy season, and "
                "which got quietly retired. The demo-floor darlings rarely make the first list.\n\n"
                "A robot that glides across an empty showroom often stalls the first packed Saturday — "
                "crowded elevators, guests, tight corridors. The ones that last are chosen for a full "
                "building on a bad day, not for the demo."
            ),
            "question_subject": "one question about your property",
            "question": (
                "I've asked a lot of operators this, and it tells me more than a walkthrough ever could.\n\n"
                "If you automated one task across the property tomorrow, which would it be? Most say "
                "delivery. The one that usually pays back is the repetitive overnight run nobody wants — "
                "linen, cleaning, room service."
            ),
        },
    ),
    (
        ("health", "medical", "hospital", "clinic", "elder", "senior living"),
        {
            "teach_subject": "where hospital automation actually pays back",
            "teach": (
                "When a health system asks me where robots fit, they're often eyeing the machine that makes "
                "the news. I point the other way.\n\n"
                "The ROI is almost always the miles clinical staff walk every shift — supplies, meds, "
                "samples, linen, waste moving between floors. Automate that transport and you hand nurses "
                "time back. Chase the flashy robot and you usually get a press release."
            ),
            "trend_subject": "the part of a robot pilot everyone underestimates",
            "trend": (
                "I've watched enough hospital pilots to know the hardware is rarely why they stall. It's "
                "the integration nobody scoped.\n\n"
                "Elevators, badge access, EVS workflow, EHR hooks — that's what decides whether a transport "
                "robot actually runs or sits charging. The robot is the easy part; the building is the hard "
                "part."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "I ask clinical and ops leaders the same thing, and the answer is more useful than any "
                "demo.\n\n"
                "If you automated one workflow tomorrow, which would it be? Most name a clinical task. The "
                "one that usually pays back first is the internal transport quietly pulling staff away from "
                "patients."
            ),
        },
    ),
    (
        ("food", "restaurant", "kitchen", "beverage", "grocery"),
        {
            "teach_subject": "where kitchen automation usually breaks",
            "teach": (
                "When a food operation asks me about automation, they picture the cooking robot. I ask "
                "about changeover.\n\n"
                "Most kitchen automation doesn't fail on the cook — it fails when the menu shifts three "
                "times a day and the cell can't keep up. What lasts is built around prep, portioning, and "
                "fast changeovers, not the one hero task that films well."
            ),
            "trend_subject": "the robot that looks great and never scales",
            "trend": (
                "I keep a short list of the food robots still earning their spot a year in. The cooking "
                "robot that wowed everyone in the demo usually isn't on it.\n\n"
                "What lasts is the repetitive, food-safe work — portioning, tray loading, packaging — on "
                "equipment that flexes across products without a teardown. Throughput and sanitation "
                "between products quietly retire the flashy ones."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "I've asked a lot of kitchen and plant managers this, and it beats any spec sheet.\n\n"
                "If you automated one station tomorrow, which would it be? Most point at the cook line. The "
                "one that usually pays back is the high-turnover station you can never keep staffed — prep, "
                "portioning, or dish."
            ),
        },
    ),
    (
        ("manufactur", "industrial", "automotive", "assembly", "factory", "cnc", "metal"),
        {
            "teach_subject": "the automation that survives a mix change",
            "teach": (
                "When a plant asks me where to automate, they point at the six-axis arm everyone "
                "photographs. I look between the cells.\n\n"
                "That's where the labor quietly goes — machine tending, moving material, end-of-line "
                "packaging. And a cell built to run one part number looks brilliant right up until your mix "
                "changes."
            ),
            "trend_subject": "why the flexible robot beats the fast one",
            "trend": (
                "I keep track of which cells are still running after a product change, and which got "
                "rebuilt. The ones bought purely for peak speed on one part tend to end up in the second "
                "group.\n\n"
                "The deployments that last are chosen for changeover and reconfiguration, not top-end cycle "
                "time. In high-mix work, flexibility pays back a lot longer than speed."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "I ask plant managers the same question, and the answer tells me more than a line tour.\n\n"
                "If you automated one job tomorrow, which would it be? Most name the bottleneck cell. The "
                "one that usually pays back is the repetitive tending and material movement nobody wants to "
                "staff."
            ),
        },
    ),
    (
        ("retail", "store", "e-commerce", "ecommerce", "apparel", "consumer goods"),
        {
            "teach_subject": "the retail robot that changes nothing",
            "teach": (
                "When a retailer asks me about robots, it's usually the shelf-scanner. I push back "
                "gently.\n\n"
                "A robot that just produces another dashboard rarely changes what staff actually do. The "
                "value shows up behind the shelf — backroom sortation, replenishment, inventory exceptions. "
                "Collecting data is easy; changing the labor is the part that pays back."
            ),
            "trend_subject": "why inventory robots stall after the pilot",
            "trend": (
                "I keep a list of the inventory robots that changed how a store runs, and the ones that "
                "just added a report. The second list is longer.\n\n"
                "The pilots that stall nailed accuracy but never rebuilt a workflow around the data. The "
                "ones that last close the loop — a scan triggers replenishment or a task, not just a "
                "dashboard."
            ),
            "question_subject": "one question about your operation",
            "question": (
                "I've asked a lot of retail ops leaders this, and it's more telling than a store visit.\n\n"
                "If you automated one workflow tomorrow, which would it be? Most say shelf scanning. The one "
                "that usually pays back is the backroom labor behind it — sortation, replenishment, "
                "exceptions."
            ),
        },
    ),
)


def _ladder_content(industry: str) -> dict[str, str]:
    """Return the teaching content for an industry (substring match, generic fallback)."""
    ind = (industry or "").strip()
    if "(" in ind:
        ind = ind.split("(", 1)[0].strip()
    low = ind.lower()
    for keys, content in _LADDER_CONTENT:
        if any(k in low for k in keys):
            return content
    return _GENERIC_LADDER


def ladder_touch_subject(touch: str, name: str, industry: str) -> str:
    """Follow-up subjects stay on the job. No field-note subjects."""
    company = (name or "your team").strip()
    if touch == "teach":
        subject = f"the robots that match the job at {company}"
    elif touch == "trend":
        subject = f"still holding robot matches for {company}"
    else:
        subject = f"may I send the robot matches for {company}"
    return subject[:88]


def build_ladder_touch_body(touch: str, name: str, industry: str) -> str:
    """Follow-up uses the same Robot Coordinator script, not a new essay."""
    body = build_buyer_variant_body(name, industry, "bottleneck_first")
    body = body.replace("nice to meet you. My name is Phelan,", "this is Phelan again.", 1)
    if touch == "trend":
        body = body.replace(
            "I found a few robots that match",
            "I am still holding a few robots that match",
            1,
        )
    elif touch == "question":
        body = body.replace(
            "May I send them to you for review?",
            "May I send them to you for review this week?",
            1,
        )
    return body


def pick_buyer_variant(company_id, *, allowed=None) -> str:
    """Deterministic round-robin so a company's draft and send agree on the angle."""
    pool = [v for v in (allowed or BUYER_VARIANTS) if v in BUYER_VARIANTS]
    if not pool:
        pool = list(BUYER_VARIANTS)
    try:
        idx = int(company_id or 0) % len(pool)
    except (TypeError, ValueError):
        idx = 0
    return pool[idx]


def resolve_buyer_variant(company, acct=None) -> str | None:
    """The angle a send should be tagged with.

    Prefers the variant stashed at draft time (``crm_metadata['phelan_variant_id']``)
    so the tag matches the copy that actually shipped; otherwise falls back to the
    deterministic round-robin. Returns ``None`` for vendors / StageGate accounts,
    which don't use the trust-first buyer angles.
    """
    account_type = getattr(acct, "account_type", None)
    if account_type and account_type != "buyer":
        return None
    meta = getattr(company, "crm_metadata", None) or {}
    if meta.get("outreach_pipeline") == "stagegate":
        return None
    stored = meta.get("phelan_variant_id")
    if stored in BUYER_VARIANTS:
        return stored
    return pick_buyer_variant(getattr(company, "id", None))


def _friendly_sector(industry: str) -> str:
    """Natural sector label — drop slash taxonomies like 'food distribution / wholesale'."""
    sector = _buyer_sector(industry)
    if " / " in sector:
        sector = sector.split(" / ", 1)[0].strip()
    if " & " in sector and len(sector) > 28:
        sector = sector.split(" & ", 1)[0].strip()
    return sector


_KNOWN_TEAM_SHORT = {
    "performance food group": "PFG",
    "united parcel service": "UPS",
    "fedex": "FedEx",
    "dhl": "DHL",
    "medline": "Medline",
    "hellofresh": "HelloFresh",
}


def _short_label(name: str) -> str:
    """Short label for conversational references (PFG, Acme, …)."""
    n = (name or "your team").strip()
    key = n.lower()
    if key in _KNOWN_TEAM_SHORT:
        return _KNOWN_TEAM_SHORT[key]
    words = [w for w in n.replace(",", " ").split() if w]
    if len(words) >= 3 and all(w[:1].isalpha() for w in words[:3]):
        # Prefer a human short name over alphabet soup for ordinary companies.
        return words[0]
    if len(n) <= 18:
        return n
    return words[0] if words else "your team"


def _greeting_name(name: str) -> str:
    """Warm greeting label: 'PFG team' / 'Acme' — not a cold legal entity dump."""
    n = (name or "your team").strip()
    short = _short_label(n)
    if short != n or len(n) > 22:
        return f"{short} team"
    return short


def _cal_intro() -> str:
    """Operator instruction: who Phelan is, then why he is writing. No platform pitch."""
    return (
        "I'm Phelan, Robot Coordinator at ReadyForRobots. I research how companies are using robotics "
        "and help identify jobs where automation could actually make a difference."
    )


def _mission_close() -> str:
    return "I'd be interested in your perspective."


def _pressure_paragraph(insight: dict[str, object]) -> str:
    para = str(insight.get("pressure_para") or "").strip()
    if para:
        return para
    return (
        "A lot of material still has to move between steps, exceptions create work that "
        "doesn't fit the standard process, and people end up filling the gaps."
    )


def _look_at_label(insight: dict[str, object], industry: str) -> str:
    look = str(insight.get("look_at") or "").strip()
    if look:
        return look
    sector = _friendly_sector(industry)
    return sector if sector != "your line of work" else "operations"


def _variant_workflow_first(name: str, industry: str) -> str:
    """Tasks before technology — operator-approved conversational shape."""
    ins = _buyer_insight(industry)
    team = _greeting_name(name)
    short = _short_label(name)
    visible = str(ins.get("visible") or "the most visible task")
    look_at = _look_at_label(ins, industry)
    return "\n".join([
        f"Hi {team},",
        "",
        _cal_intro(),
        "",
        (
            f"I've been looking at {look_at}, and I keep noticing something I wanted to check with you. "
            f"{visible[:1].upper()}{visible[1:]} gets most of the attention, but a lot of the day-to-day "
            "pressure seems to happen elsewhere — often before teams have named the work clearly."
        ),
        "",
        _pressure_paragraph(ins),
        "",
        f"I'm curious if that's true at {short}.",
        "",
        (
            "Where do you see the biggest opportunity to automate today? "
            f"Is it still {visible}, or are there other parts of the operation that cause more problems?"
        ),
        "",
        _mission_close(),
        "",
        phelan_buyer_email_signature(),
    ])


def _variant_what_survives(name: str, industry: str) -> str:
    """Deployment over demos — same conversational shape."""
    ins = _buyer_insight(industry)
    team = _greeting_name(name)
    short = _short_label(name)
    visible = str(ins.get("visible") or "the most visible task")
    look_at = _look_at_label(ins, industry)
    return "\n".join([
        f"Hi {team},",
        "",
        _cal_intro(),
        "",
        (
            f"I've been looking at {look_at}, and I keep noticing something I wanted to check with you. "
            "A demo can look great and still fail once real traffic, exceptions, and support show up."
        ),
        "",
        (
            "The projects that hold up usually start with one clear operational problem — "
            f"not a shortlist of robots. {_pressure_paragraph(ins)}"
        ),
        "",
        f"I'm curious how {short} thinks about that.",
        "",
        (
            f"If you were starting fresh, would you begin with {visible}, "
            "or with the quieter workflow that actually creates more problems?"
        ),
        "",
        _mission_close(),
        "",
        phelan_buyer_email_signature(),
    ])


def _variant_bottleneck_first(name: str, industry: str) -> str:
    """Operator-approved PFG shape — human intro, pressure paragraph, open question."""
    ins = _buyer_insight(industry)
    team = _greeting_name(name)
    short = _short_label(name)
    visible = str(ins.get("visible") or "the most visible task")
    look_at = _look_at_label(ins, industry)
    visible_cap = f"{visible[:1].upper()}{visible[1:]}"
    return "\n".join([
        f"Hi {team},",
        "",
        _cal_intro(),
        "",
        (
            f"I've been looking at {look_at}, and I keep noticing something I wanted to check with you. "
            f"{visible_cap} gets most of the attention, but a lot of the day-to-day pressure seems to happen elsewhere."
        ),
        "",
        _pressure_paragraph(ins),
        "",
        f"I'm curious if that's true at {short}.",
        "",
        (
            "Where do you see the biggest opportunity to automate today? "
            f"Is it still {visible}, or are there other parts of the operation that cause more problems?"
        ),
        "",
        _mission_close(),
        "",
        phelan_buyer_email_signature(),
    ])







# A concrete, external event is the only thing Cal will cite as a reason — an
# opening, expansion, funding round, hire, RFP, deployment. Inferred prose like
# "sits in a sector facing labor shortages" is NOT a verifiable event and reads
# as assumptive/naive, so it is deliberately excluded.
_EVENT_MARKER_RE = re.compile(
    r"(?i)\b("
    r"open(?:s|ed|ing)?\b|launch\w*|expand\w*|expansion|"
    r"new\s+(?:facility|plant|factory|center|centre|distribution|warehouse|"
    r"fulfil?lment|site|hub|line|store|kitchen|campus|dc)\b|"
    r"break(?:s|ing)?\s+ground|ground[-\s]?break\w*|"
    r"fund(?:ing|ed)|raised|raises|series\s+[a-e]\b|funding\s+round|"
    r"invest(?:s|ed|ment|ing)?|acqui(?:re|res|red|sition)|merg(?:er|es|ed)|"
    r"partnership|partner(?:s|ed)\s+with|joint\s+venture|"
    r"contract|awarded|won\s+a\b|rfp|request\s+for\s+proposal|procurement|"
    r"pilot\w*|deploy\w*|install\w*|roll(?:s|ed|ing)?[-\s]?out|rollout|"
    r"hir(?:e|es|ing)|jobs?\b|positions?\b|open\s+roles?|"
    r"\$\s?\d|\d+\s?(?:million|billion|m\b|bn\b)|sq\s?ft|square\s+f(?:ee|oo)t"
    r")\b"
)


def build_context_reason(name: str, signal_blob: str, *, max_chars: int = 200) -> str | None:
    """A single verifiable, humble hook grounded in a concrete company event.

    Cal only names a reason when the company's own signals contain a real,
    external, event-like fact (an opening, expansion, funding round, hire, RFP,
    deployment). Inferred category prose is rejected because reciting it back
    reads as assumptive. Returns ``None`` when there's nothing concrete to stand
    behind, so callers fall back to the clean industry opener. Stays humble: it
    explains *why Cal reached out*, not what the company should buy.
    """
    n = (name or "").strip()
    blob = (signal_blob or "").strip()
    if not n or not blob:
        return None
    try:
        from app.services.lead_sales_copy import is_low_quality_sales_text
        from app.services.lead_signal_display import pick_primary_sentence
    except Exception:
        return None

    fact = (pick_primary_sentence(blob, max_chars=max_chars) or "").strip()
    # A truncated clause ("…") is a fragment, not a fact worth citing.
    if not fact or fact.endswith("…") or is_low_quality_sales_text(fact):
        return None
    if not _EVENT_MARKER_RE.search(fact):
        return None
    if not fact.endswith((".", "!", "?")):
        fact = fact.rstrip(",;:—- ") + "."

    if n.lower() in fact.lower():
        return (
            f"{fact} That's what put you on my radar — I only reach out when there's a "
            "specific reason, not a scraped list."
        )
    return (
        f"A signal tied to {n} is what prompted this — {fact} I keep the list short and "
        "specific, so I'm not writing on spec."
    )


def build_buyer_variant_body(
    name: str,
    industry: str,
    variant_id: str,
    *,
    reason: str | None = None,
    contact_name: str | None = None,
    announced_need: str | None = None,
    automation_tasks: str | None = None,
    skills: str | None = None,
    capabilities: str | None = None,
) -> str:
    """Buyer letter in the operator's Robot Coordinator script.

    The essay angles are not this letter. Unknown contact, job, skills, and
    capabilities stay blank. The company name is filled in when we have it.
    """
    del industry, variant_id, reason  # script does not take an angle or a pitch
    from app.services.oem_job_intro import compose_employer_need_intro

    text = compose_employer_need_intro(
        contact_name=contact_name,
        announced_need=announced_need,
        automation_tasks=automation_tasks,
        skills=skills,
        capabilities=capabilities,
    )
    company = (name or "").strip()
    if company and company.lower() not in {"your team", "your company"}:
        text = text.replace("at your company", f"at {company}", 1)
    return text


def buyer_variant_subject(name: str, industry: str, variant_id: str) -> str:
    """Subject for the Robot Coordinator script. One job, not an essay."""
    del industry, variant_id
    company = (name or "your team").strip()
    subject = f"robots that match the job at {company}"
    return subject[:88]


def phelan_opening(*, audience: str = "buyer") -> str:
    explanation = VENDOR_SIGNAL_EXPLANATION if audience == "vendor" else BUYER_SIGNAL_EXPLANATION
    return f"{PHELAN_INTRO}\n\n{explanation}"


def phelan_vendor_opening(*, reminder: bool = False) -> str:
    if reminder:
        return (
            f"{PHELAN_VENDOR_REMINDER_LINE}\n\n"
            f"{VENDOR_SIGNAL_EXPLANATION}"
        )
    return (
        f"{PHELAN_INTRO}\n\n"
        f"{PHELAN_VENDOR_ROLE_LINE}\n\n"
        f"{PHELAN_VENDOR_IDENTITY}\n\n"
        f"{PHELAN_VENDOR_SHERPA_LINE}\n\n"
        f"{VENDOR_SIGNAL_EXPLANATION}"
    )


def phelan_vendor_match_paragraph(company_name: str, *, industry: str = "your space") -> str:
    """Core vendor outreach block — opportunities + PoC realism."""
    name = (company_name or "your team").strip()
    ind = (industry or "your space").strip()
    return (
        f"I've looked at {name}'s robots against active buyer signals in {ind}. "
        f"A few opportunities align with your capabilities — not generic leads, accounts with timing behind them.\n\n"
        f"{PHELAN_VENDOR_PIPELINE_LOGIC_LINE}"
    )


# Cal → Phelan rename leftovers. Importing app.main must not 502 Fly.
CAL_VENDOR_OFFRAMP_LINE = PHELAN_VENDOR_OFFRAMP_LINE
CAL_VENDOR_STRATEGY_CALL_CTA = PHELAN_VENDOR_STRATEGY_CALL_CTA
CAL_VENDOR_BUYER_MATCH_CTA = PHELAN_VENDOR_BUYER_MATCH_CTA
CAL_VENDOR_SHERPA_LINE = PHELAN_VENDOR_SHERPA_LINE
cal_vendor_match_paragraph = phelan_vendor_match_paragraph
