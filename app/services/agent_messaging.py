"""Shared wording for agent-authored Ready For Robots communication."""
from __future__ import annotations


CAL_INTRO = "I am Cal with Ready For Robots."
BUYER_SIGNAL_EXPLANATION = (
    "We track automation buying signals and help teams decide where robotics might be worth a practical look."
)
VENDOR_SIGNAL_EXPLANATION = (
    "We find automation sales leads and rank them by buying signals, so stronger signals point to warmer accounts."
)


def cal_signature() -> str:
    return "Best,\nCal\nRobot Automation Team\nReady For Robots"


def max_signature() -> str:
    return "Best,\nMax\nTechnical Support Lead\nReady For Robots"


def cal_opening(*, audience: str = "buyer") -> str:
    explanation = VENDOR_SIGNAL_EXPLANATION if audience == "vendor" else BUYER_SIGNAL_EXPLANATION
    return f"{CAL_INTRO}\n\n{explanation}"
