"""Shared wording for agent-authored Ready For Robots communication."""
from __future__ import annotations


CAL_INTRO = "I am Cal with Ready For Robots."
READYBOT_INTRO = "I am ReadyBot with Ready For Robots."
BUYER_SIGNAL_EXPLANATION = (
    "We track automation buying signals and help teams decide where robotics might be worth a practical look."
)
VENDOR_SIGNAL_EXPLANATION = (
    "We find automation sales leads and rank them by buying signals, so stronger signals point to warmer accounts."
)
READYBOT_DISTRIBUTION_EXPLANATION = (
    "Think of us as a search engine for your sales pipeline: signal capture, hardware matchmaking, and direct channel routing."
)
READYBOT_PIPELINE_LOGIC_LINE = (
    "You built the tech; we build the pipeline and show the exact signal trail behind every lead."
)
VEGAS_DISTRIBUTION_LINE = (
    "In Las Vegas, we use that data to route the right robotics companies toward hotels, casinos, commercial hubs, and enterprise buyers."
)
ONSTAGE_PARTNER_LINE = (
    "If you need physical staging, trade show prep, or showroom space, we hand that off to our trusted logistics partner, onstage.bot."
)
READYBOT_OFFRAMP_LINE = (
    "If the signal logic is weak, we will say so. The point is not more noise; it is a cleaner route to buyers who are already moving."
)
READYBOT_STRATEGY_CALL_CTA = "Open to a Sales Channel & Lead Generation Strategy Call next week?"


def cal_signature() -> str:
    return "Best,\nCal\nRobot Automation Team\nReady For Robots"


def readybot_signature() -> str:
    return "Best,\nReadyBot\nAI Growth & Distribution Strategist\nReady For Robots"


def max_signature() -> str:
    return "Best,\nMax\nTechnical Support Lead\nReady For Robots"


def cal_opening(*, audience: str = "buyer") -> str:
    explanation = VENDOR_SIGNAL_EXPLANATION if audience == "vendor" else BUYER_SIGNAL_EXPLANATION
    return f"{CAL_INTRO}\n\n{explanation}"


def readybot_vendor_opening() -> str:
    return (
        f"{READYBOT_INTRO}\n\n"
        f"{VENDOR_SIGNAL_EXPLANATION}\n\n"
        f"{READYBOT_DISTRIBUTION_EXPLANATION}\n\n"
        f"{READYBOT_PIPELINE_LOGIC_LINE}"
    )
