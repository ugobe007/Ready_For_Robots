"""Shared wording for agent-authored Ready For Robots communication."""
from __future__ import annotations

# ── Cal voice: veteran sherpa for robot companies ─────────────────────────────
# Wise, abbreviated, in-the-know. Engineer-led teams, PoC → deployment reality.
# Honesty and trust over hype. Draws on deep robotics industry experience.

CAL_INTRO = "Hi — I'm Cal, with Ready For Robots."

CAL_VENDOR_IDENTITY = (
    "I've spent years inside robot deployments — Anybots, Omron, Panasonic, Mitsubishi, Locus Robotics — "
    "and I've seen the same pattern: great hardware, hard PoCs, harder conversions to paying accounts."
)

CAL_VENDOR_SHERPA_LINE = (
    "Most robot companies are engineer-led, not sales-led. I act as a guide through trials and deployments — "
    "honest readouts, no theater."
)

# Plain, honest, first-person. Say what I do and why I'm writing — no slogans.
BUYER_SIGNAL_EXPLANATION = (
    "I help operations teams figure out which robots would actually fit the way they run, "
    "and which ones aren't worth the trouble. A lot of what I do is talk people out of a pilot "
    "that was never going to work."
)

# Quiet credibility — a plain observation about what makes robots pay off, no bravado.
BUYER_ROI_PROOF = (
    "The teams that get real value out of it usually aren't the ones who bought the most impressive "
    "robot. They're the ones who matched a specific machine to the one job that was actually costing "
    "them. When the fit is right, it tends to pay for itself inside a year or two."
)

BUYER_OUTREACH_CTA = (
    "If it's useful, I'm happy to put together a short list of vendors that have actually deployed in "
    "operations like yours — and flag the couple I'd be careful about. No call, no pitch; just reply "
    "and I'll send it over."
)

# Honest closing beat — builds trust rather than performing confidence.
BUYER_CAL_PERSONALITY = (
    "And if I don't think a robot is the right answer for you yet, I'll tell you that too."
)

VENDOR_SIGNAL_EXPLANATION = (
    "We map buyer demand signals and match them to robot capabilities — "
    "the accounts showing real intent, not list noise."
)

CAL_VENDOR_PIPELINE_EXPLANATION = (
    "I've reviewed your robots and specs against what buyers are asking for right now. "
    "The fit isn't always obvious on paper — ROI, proof points, PoC availability, technical support, "
    "and how your team shows up all factor in."
)

CAL_VENDOR_PIPELINE_LOGIC_LINE = (
    "PoCs fail when capabilities don't match buyer requirements. "
    "Deployments happen when positioning, support, and follow-through align."
)

VEGAS_DISTRIBUTION_LINE = (
    "For teams pushing hospitality or West Coast expansion, we also map buyers across Las Vegas — "
    "hotels, casinos, logistics hubs — where robot trials actually get evaluated."
)

CAL_VENDOR_OFFRAMP_LINE = (
    "If the signal is weak or the fit isn't there, I'll say so. "
    "The point is fewer wasted PoCs, not more pipeline noise."
)

CAL_VENDOR_STRATEGY_CALL_CTA = "Worth 15 minutes to walk through the matches?"

CAL_VENDOR_BUYER_MATCH_CTA = "Want me to send the buyer profiles? I'll flag what fits and what doesn't."

# Customer-facing rep voice (robot sales rep → buyer ops). No Ready For Robots branding.
REP_OUTREACH_CTA = "Worth a quick reply if you're the right person to explore this?"


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


def cal_signature() -> str:
    return "— Cal\nReady For Robots"


def max_signature() -> str:
    return "— Max\nReady For Robots"


# ── Trust-first buyer variants ────────────────────────────────────────────────
# Three genuinely different openers — different premises, not reworded twins.
# All are humble and non-presumptuous: Cal names a real reason for writing, admits
# he doesn't know their context, leaves room for "we already tried robots and it
# flopped," and asks with low commitment plus explicit permission to say no.
# Every variant must (a) mention the company name (assembly gate) and (b) end with
# the Cal sign-off (draft-completeness gate).

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


# Cal is a vendor-neutral deployment advisor, not a salesperson. Each vertical
# gets: `glam` = the workflow everyone automates first (and over-focuses on),
# `hidden` = where labor hours actually disappear, and `opinion` = one strong,
# memorable, deployment-earned point of view. The voice teaches; it doesn't pitch.
_GENERIC_INSIGHT = {
    "glam": "the most visible task",
    "hidden": "the repetitive back-of-house work — moving material and handling the same exceptions over and over",
    "opinion": "The coolest robot in the room is rarely the one that pays for itself.",
}

_INDUSTRY_INSIGHT: tuple[tuple[tuple[str, ...], dict[str, str]], ...] = (
    (
        ("logistic", "warehous", "supply chain", "fulfil", "distribution", "3pl"),
        {
            "glam": "Picking",
            "hidden": "receiving, replenishment, pallet moves, inventory exceptions, and returns",
            "opinion": "The fastest AMR on the floor is rarely the one that survives real peak volume.",
        },
    ),
    (
        ("hospitality", "hotel", "casino", "gaming", "resort"),
        {
            "glam": "The lobby delivery robot",
            "hidden": "linen runs, housekeeping carts, overnight floor cleaning, and room-service logistics",
            "opinion": "A robot that shines in an empty lobby usually stalls the first busy weekend.",
        },
    ),
    (
        ("health", "medical", "hospital", "clinic", "elder", "senior living"),
        {
            "glam": "The robot that gets posted on LinkedIn",
            "hidden": "moving supplies, meds, lab samples, linen, and waste between floors",
            "opinion": "In a hospital the ROI is almost never the flashy robot — it's the miles staff walk every shift.",
        },
    ),
    (
        ("food", "restaurant", "kitchen", "beverage", "grocery"),
        {
            "glam": "The cooking robot",
            "hidden": "prep, portioning, dishwashing, packaging, and product changeovers",
            "opinion": "Most kitchen automation dies on changeover, not on the cook.",
        },
    ),
    (
        ("manufactur", "industrial", "automotive", "assembly", "factory", "cnc", "metal"),
        {
            "glam": "The six-axis arm on the line",
            "hidden": "machine tending, moving material between cells, and end-of-line packaging",
            "opinion": "A cell that only runs one part number looks great until your mix changes.",
        },
    ),
    (
        ("retail", "store", "e-commerce", "ecommerce", "apparel", "consumer goods"),
        {
            "glam": "The shelf-scanning robot",
            "hidden": "backroom sortation, replenishment, and inventory exceptions",
            "opinion": "A robot that just produces another dashboard rarely changes what staff actually do.",
        },
    ),
)


def _buyer_insight(industry: str) -> dict[str, str]:
    """Return Cal's deployment read for an industry (substring match, generic fallback)."""
    ind = (industry or "").strip()
    if "(" in ind:
        ind = ind.split("(", 1)[0].strip()
    low = ind.lower()
    for keys, insight in _INDUSTRY_INSIGHT:
        if any(k in low for k in keys):
            return insight
    return _GENERIC_INSIGHT


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

    Prefers the variant stashed at draft time (``crm_metadata['cal_variant_id']``)
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
    stored = meta.get("cal_variant_id")
    if stored in BUYER_VARIANTS:
        return stored
    return pick_buyer_variant(getattr(company, "id", None))


def _variant_workflow_first(name: str, industry: str) -> str:
    """Flagship teach: most projects automate the wrong workflow first."""
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        "Hi,",
        "",
        "I spend my days looking at where robot deployments actually work — and where they quietly fall apart.",
        "",
        f"One pattern keeps showing up in {sector}.",
        "",
        "Most projects don't struggle because the robot can't do the job. They struggle because the wrong "
        "workflow got automated first.",
        "",
        f"{ins['glam']} gets all the attention. Meanwhile {ins['hidden']} quietly consume thousands of "
        f"labor hours a month. That's usually where I'd start with {name}.",
        "",
        "Ready For Robots isn't tied to any manufacturer. We spend our time working out where automation "
        "creates real ROI — and, just as often, where the answer is \"not yet.\"",
        "",
        f"If robotics is on the roadmap at {name} this year, I'll share what we're seeing across the "
        "market. No presentation, just a practical conversation.",
        "",
        cal_signature(),
    ])


def _variant_what_survives(name: str, industry: str) -> str:
    """Pattern-recognition teach: which deployments are still running at 6 months."""
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        "Hi,",
        "",
        "Part of my job surprises people: I don't track which robots demo well. I track which ones are "
        "still running six months after install.",
        "",
        f"In {sector}, that list is shorter than the sales decks suggest.",
        "",
        ins["opinion"],
        "",
        "What decides it usually isn't the hardware — it's integration, the software layer, and whether the "
        "robot was aimed at the right job in the first place. We're vendor-neutral, so I care about fit, not "
        "about moving any particular box. Sometimes the right call is \"not yet.\"",
        "",
        f"If {name} is weighing robotics this year, I'll tell you what's actually holding up in the field — "
        "and what I'd stay away from. No pitch.",
        "",
        cal_signature(),
    ])


def _variant_bottleneck_first(name: str, industry: str) -> str:
    """Opinionated + curious: start with the bottleneck, not the robot."""
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        "Hi,",
        "",
        f"A question I'd ask before {name} looks at a single robot: which job is actually eating your hours "
        "right now?",
        "",
        f"Most teams start with the coolest machine. I start with the bottleneck — because in {sector} the "
        f"hours usually disappear into {ins['hidden'].lower()}, not {ins['glam'].lower()}.",
        "",
        ins["opinion"],
        "",
        "I'm not tied to any manufacturer. My job is helping teams avoid buying the wrong robot — and "
        "sometimes that means \"not yet.\"",
        "",
        "If it's worth a short exchange, tell me where the hours go and I'll tell you whether a robot is "
        "even the right answer.",
        "",
        cal_signature(),
    ])


def build_buyer_variant_body(name: str, industry: str, variant_id: str) -> str:
    """Assemble the full buyer email body for a given advisor angle."""
    n = (name or "your team").strip()
    builders = {
        "workflow_first": _variant_workflow_first,
        "what_survives": _variant_what_survives,
        "bottleneck_first": _variant_bottleneck_first,
    }
    fn = builders.get(variant_id, _variant_workflow_first)
    return fn(n, industry or "your industry")


def buyer_variant_subject(name: str, industry: str, variant_id: str) -> str:
    """Insight-led subject — a topic Cal is about to teach, not a pitch."""
    sector = _buyer_sector(industry)
    generic_sector = sector == "your line of work"
    if variant_id == "what_survives":
        return (
            "the robots still running six months in"
            if generic_sector
            else f"the {sector} robots still running six months in"
        )
    if variant_id == "bottleneck_first":
        return "start with the bottleneck, not the robot"
    # workflow_first (default)
    return (
        "where automation projects usually go sideways"
        if generic_sector
        else f"where {sector} automation usually goes sideways"
    )


def cal_opening(*, audience: str = "buyer") -> str:
    explanation = VENDOR_SIGNAL_EXPLANATION if audience == "vendor" else BUYER_SIGNAL_EXPLANATION
    return f"{CAL_INTRO}\n\n{explanation}"


def cal_vendor_opening() -> str:
    return (
        f"{CAL_INTRO}\n\n"
        f"{CAL_VENDOR_IDENTITY}\n\n"
        f"{CAL_VENDOR_SHERPA_LINE}\n\n"
        f"{VENDOR_SIGNAL_EXPLANATION}"
    )


def cal_vendor_match_paragraph(company_name: str, *, industry: str = "your space") -> str:
    """Core vendor outreach block — opportunities + PoC realism."""
    name = (company_name or "your team").strip()
    ind = (industry or "your space").strip()
    return (
        f"I've looked at {name}'s robots against active buyer signals in {ind}. "
        f"A few opportunities align with your capabilities — not generic leads, accounts with timing behind them.\n\n"
        f"{CAL_VENDOR_PIPELINE_LOGIC_LINE}"
    )
