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
