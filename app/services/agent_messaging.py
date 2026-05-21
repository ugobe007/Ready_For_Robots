"""Shared wording for agent-authored Ready For Robots communication."""
from __future__ import annotations

# ── Cal voice: cool, confident, casual, brief, meaningful ─────────────────────
# One paragraph max. No corporate boilerplate. Show the signal. Make one ask.

CAL_INTRO = "Cal here — I run the automation research desk at Ready For Robots."

BUYER_SIGNAL_EXPLANATION = (
    "We track live buying signals across labor, expansion, and CapEx activity "
    "to spot where automation is actually worth a look."
)
VENDOR_SIGNAL_EXPLANATION = (
    "We map automation demand signals across enterprise buyers — labor pressure, "
    "expansion moves, CapEx shifts — and rank them so the warm accounts rise to the top."
)
CAL_VENDOR_PIPELINE_EXPLANATION = (
    "Think of it as a search engine for your sales pipeline: signal capture, "
    "buyer matching, and a clean route to the accounts already moving."
)
CAL_VENDOR_PIPELINE_LOGIC_LINE = (
    "You built the hardware. We find the buyers who are already signaling they need it."
)
VEGAS_DISTRIBUTION_LINE = (
    "We use that signal data to connect the right robot companies with hotels, casinos, "
    "logistics hubs, and enterprise buyers across Las Vegas."
)
CAL_VENDOR_OFFRAMP_LINE = (
    "If the signal is weak, we'll say so — the point is a cleaner route to buyers already moving, not more noise."
)
CAL_VENDOR_STRATEGY_CALL_CTA = "Worth a quick strategy call this week?"


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
        f"{VENDOR_SIGNAL_EXPLANATION}\n\n"
        f"{CAL_VENDOR_PIPELINE_EXPLANATION}\n\n"
        f"{CAL_VENDOR_PIPELINE_LOGIC_LINE}"
    )
