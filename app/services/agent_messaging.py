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

BUYER_VARIANTS: tuple[str, ...] = ("candid_opener", "peer_reality", "question_first")


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


# Practitioner-grade read on each vertical so Cal speaks like someone who has
# actually watched robots deploy there — not a generalist fishing for a meeting.
# `use` = how robots really get deployed, `edge` = what separates a working
# deployment from a demo, `pain` = where the value actually hides, `pain_q` = the
# same constraint framed as an honest opening question.
_GENERIC_INSIGHT = {
    "use": "the repetitive, hard-to-staff work — moving material and running the same task thousands of times a day",
    "edge": "whether it holds up in your real conditions, not a vendor's demo",
    "pain": "the one job that's actually costing you, rather than a fleet you'll never fully use",
    "pain_q": "is there one repetitive, hard-to-staff job quietly costing you more than the rest",
}

_INDUSTRY_INSIGHT: tuple[tuple[tuple[str, ...], dict[str, str]], ...] = (
    (
        ("logistic", "warehous", "supply chain", "fulfil", "distribution", "3pl"),
        {
            "use": "goods-to-person picking, autonomous case and pallet moves, and keeping product flowing to the pack line",
            "edge": "whether it still holds up at peak volume and mixed SKUs, not just in a clean demo aisle",
            "pain": "the one station — induction, replen, or each-pick — where labor and errors quietly pile up",
            "pain_q": "is one station — induction, replen, or each-pick — quietly eating your labor and error budget",
        },
    ),
    (
        ("hospitality", "hotel", "casino", "gaming", "resort"),
        {
            "use": "room and amenity delivery, back-of-house runs, and autonomous floor cleaning",
            "edge": "whether it can actually work a full building with guests and elevators, not an empty showroom floor",
            "pain": "overnight coverage and the repetitive runs — deliveries, linen, lobby cleaning — that quietly eat staff hours",
            "pain_q": "are the repetitive runs — deliveries, linen, overnight cleaning — where your staff hours disappear",
        },
    ),
    (
        ("health", "medical", "hospital", "clinic", "elder", "senior living"),
        {
            "use": "autonomous transport of supplies, meds, lab samples, linen and waste",
            "edge": "whether it integrates with your elevators, badge access and EVS workflow — the part demos skip",
            "pain": "the hours clinical staff lose fetching and walking material instead of caring for patients",
            "pain_q": "are your clinical staff losing hours fetching and moving supplies instead of caring for patients",
        },
    ),
    (
        ("food", "restaurant", "kitchen", "beverage", "grocery"),
        {
            "use": "repetitive prep and pick-and-place cells — frying, portioning, tray loading, palletizing",
            "edge": "food-safe handling and fast changeover between products, where a lot of cells fall down",
            "pain": "one high-turnover station that's hard to keep staffed, not a wall of machines",
            "pain_q": "is there one high-turnover station you can never keep reliably staffed",
        },
    ),
    (
        ("manufactur", "industrial", "automotive", "assembly", "factory", "cnc", "metal"),
        {
            "use": "machine tending, palletizing, and moving material between cells with cobots and AMRs",
            "edge": "whether it flexes across changeovers instead of only running one part number",
            "pain": "the repetitive tending and transport jobs nobody wants — especially in high-mix runs",
            "pain_q": "is repetitive machine tending and material movement where your labor keeps going",
        },
    ),
    (
        ("retail", "store", "e-commerce", "ecommerce", "apparel", "consumer goods"),
        {
            "use": "shelf-scanning, backroom sortation, and inventory-accuracy robots",
            "edge": "whether the data actually changes what staff do, or just becomes another dashboard",
            "pain": "inventory accuracy and the replenishment labor behind it",
            "pain_q": "are inventory accuracy and replenishment labor the real drain",
        },
    ),
)


def _buyer_insight(industry: str) -> dict[str, str]:
    """Return the practitioner read for an industry (substring match, generic fallback)."""
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


def _variant_candid(name: str, industry: str) -> str:
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        CAL_INTRO,
        "",
        f"I won't pretend to diagnose {name} from the outside — I don't know how you run. But I do know "
        f"{sector}: the robots that earn their place there mostly do {ins['use']}, and the ones that pay "
        f"off get pointed at {ins['pain']}.",
        "",
        f"Where it usually goes wrong is treating this as a fleet decision instead of a fit decision. The "
        f"part that actually decides it is {ins['edge']}.",
        "",
        "If automation's a question you're weighing this year, I'd be glad to compare notes — and if it's "
        "not the right call yet, I'll say so. If it's not on your radar at all, tell me and I'll leave you be.",
        "",
        cal_signature(),
    ])


def _variant_peer(name: str, industry: str) -> str:
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        CAL_INTRO,
        "",
        f"I'll skip the pitch and give you the honest read on {sector}: robots genuinely do good work "
        f"there — {ins['use']} — but what separates the deployments that pay off from the ones that stall "
        f"is almost never the hardware. It's {ins['edge']}.",
        "",
        f"I'm not assuming anything about {name} — you may already have this dialed in, or robots may be "
        f"nowhere near your list. What I actually do is help teams tell working automation from the kind "
        f"that only shines in a demo, and aim it at {ins['pain']}. Sometimes that means telling someone to wait.",
        "",
        "If you've looked at this before, I'd genuinely like to hear what you found. If you haven't, I can "
        "tell you what tends to work for a team like yours — and, just as honestly, when it doesn't.",
        "",
        cal_signature(),
    ])


def _variant_question(name: str, industry: str) -> str:
    sector = _buyer_sector(industry)
    ins = _buyer_insight(industry)
    return "\n".join([
        CAL_INTRO,
        "",
        f"Honest question about {name}: {ins['pain_q']}? Or is that already handled, and automation just "
        f"isn't the priority right now?",
        "",
        f"I ask because in {sector} the robots that actually work come down to {ins['use']}, aimed at one "
        f"real constraint rather than the whole operation. Whether that fits how you run — and whether "
        f"now's even the time — is what I help operations teams think through. Plenty of those talks end "
        f"in \"not yet,\" and that's completely fine.",
        "",
        "If it's worth a short back-and-forth, just reply. If not, no hard feelings — I won't chase you.",
        "",
        cal_signature(),
    ])


def build_buyer_variant_body(name: str, industry: str, variant_id: str) -> str:
    """Assemble the full buyer email body for a given trust-first angle."""
    n = (name or "your team").strip()
    builders = {
        "candid_opener": _variant_candid,
        "peer_reality": _variant_peer,
        "question_first": _variant_question,
    }
    fn = builders.get(variant_id, _variant_candid)
    return fn(n, industry or "your industry")


def buyer_variant_subject(name: str, industry: str, variant_id: str) -> str:
    """Humble, curiosity-driven subject that matches the angle's tone."""
    n = (name or "your team").strip()
    if variant_id == "question_first":
        return f"is automation on the table for {n} this year?"
    if variant_id == "peer_reality":
        return f"{n}: what actually holds up (and what doesn't)"
    return f"an honest read on robots for {n}"


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
