"""Shared wording for agent-authored Ready For Robots communication."""
from __future__ import annotations

# ── Cal voice: veteran sherpa for robot companies ─────────────────────────────
# Wise, abbreviated, in-the-know. Engineer-led teams, PoC → deployment reality.
# Honesty and trust over hype. Draws on deep robotics industry experience.

CAL_INTRO = "Hi, it's Cal at Ready For Robots."

CAL_VENDOR_IDENTITY = (
    "I've spent years inside robot deployments — Anybots, Omron, Panasonic, Mitsubishi, Locus Robotics — "
    "and I've seen the same pattern: great hardware, hard PoCs, harder conversions to paying accounts."
)

CAL_VENDOR_SHERPA_LINE = (
    "Most robot companies are engineer-led, not sales-led. I act as a guide through trials and deployments — "
    "honest readouts, no theater."
)

# Value-first: lead with the outcome the buyer gets, not how we watch them.
BUYER_SIGNAL_EXPLANATION = (
    "I match ops teams with the two or three robotics vendors actually worth a pilot — "
    "and tell you which ones to skip. No brochures, no innovation theater, no 90-day PoC that "
    "quietly dies."
)

# Concrete ROI / proof so the buyer sees a reason to care, not just a pitch.
BUYER_ROI_PROOF = (
    "The teams that get this right see payback in roughly 12–18 months — and it's almost never the "
    "flashiest robot. It's matching the right cell to the one bottleneck that's actually costing you. "
    "I've watched enough pilots stall to know where the money hides."
)

BUYER_OUTREACH_CTA = (
    "Want the shortlist? Reply \"send it\" and I'll send three vendors who've deployed in setups like "
    "yours — plus the one I'd personally avoid. Five-minute read, no call required."
)

# Optional closing beat — confident, a little dry. Used when humor is allowed.
BUYER_CAL_PERSONALITY = (
    "Fair warning: I'm annoyingly picky about fit. It's cheaper than a failed deployment."
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
    """One specific, relatable line: the bottleneck teams like theirs actually hit."""
    n = (name or "your team").strip()
    ind = (industry or "your industry").strip().lower()
    if ind in ("logistics", "warehousing"):
        return (
            f"Warehouses like {n} tend to hit the same wall: labor's tight, volume isn't, and the "
            f"AMRs that crush a carpet demo fall apart in real aisles. The ones that actually hold up "
            f"are a short list — and I keep it."
        )
    if ind in ("hospitality", "hotels", "casinos & gaming"):
        return (
            f"For a property like {n}, the math is usually overnight coverage and turnover — the point "
            f"where service and cleaning automation starts paying for itself instead of sitting in a lobby "
            f"as a gimmick."
        )
    if ind in ("healthcare", "medical technology"):
        return (
            f"Teams like {n} usually reach for robots when clinical ops scale faster than headcount — "
            f"internal logistics and AMRs first, because that's where the hours quietly disappear."
        )
    if ind in ("food service", "food processing & manufacturing"):
        return (
            f"In food ops like {n}, it's throughput and back-of-house strain that make the case — a "
            f"targeted cell on the real bottleneck, not a catalog of robots you'll never run."
        )
    return (
        f"Teams in {industry.strip()} like {n} usually get to robots the same way: one bottleneck gets "
        f"expensive enough that a targeted pilot beats hiring against it."
    )


def cal_signature() -> str:
    return "— Cal\nReady For Robots"


def max_signature() -> str:
    return "— Max\nReady For Robots"


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
