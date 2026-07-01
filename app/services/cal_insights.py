"""Rotating industry insights for Cal's Ready For Robots outreach.

Persona: Cal — veteran robotics sherpa for engineer-led robot companies.
PoC → deployment reality, buyer matching, trade-show timing. Honest, abbreviated, in-the-know.
NOT StageGate logistics (warehousing, staging, on-site repair). Never mention onstage.bot.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_SHOW_ALIASES = {
    "ces": re.compile(r"\bces\b", re.I),
    "automate": re.compile(r"\b(automate|promat|mhi)\b", re.I),
    "nab": re.compile(r"\bnab\b", re.I),
    "imts": re.compile(r"\bimts\b", re.I),
    "hannover": re.compile(r"\b(hannover|hm\s*\d)\b", re.I),
}


@dataclass(frozen=True)
class _Insight:
    id: str
    text: str
    show_key: Optional[str] = None
    robot_pattern: Optional[re.Pattern[str]] = None
    humor: bool = False
    vendor_only: bool = False


_INSIGHTS: list[_Insight] = [
    _Insight(
        id="poc_to_paid",
        text=(
            "Most PoCs stall on integration and support, not hardware specs. "
            "Buyers decide on who shows up when the robot misbehaves on their floor — "
            "not who had the slickest demo video."
        ),
        vendor_only=True,
    ),
    _Insight(
        id="engineer_led_sales",
        text=(
            "Engineer-led robot companies often lose deals in the handoff after the PoC — "
            "when the buyer's ops team asks about uptime, spares, and who fixes it at 2 a.m. "
            "That conversation should start before the trial, not after."
        ),
        vendor_only=True,
    ),
    _Insight(
        id="roi_nuance",
        text=(
            "ROI gets the meeting; proof points, roadmap, and PoC availability get the pilot. "
            "Buyers weigh what you've deployed elsewhere, what ships in the next 12 months, "
            "and whether your leadership team has done this before."
        ),
        vendor_only=True,
    ),
    _Insight(
        id="capability_match",
        text=(
            "The trick isn't listing every sensor — it's matching what your robot does today "
            "(and credibly next year) to what the buyer's workflow actually requires. "
            "Misalignment here is the #1 PoC killer I've seen across AMR and industrial deployments."
        ),
        vendor_only=True,
    ),
    _Insight(
        id="industry_story",
        text=(
            "Buyers in each industry respond to different proof — hospitality cares about guest-facing reliability; "
            "logistics cares about throughput under real aisle conditions. "
            "A story from their vertical beats a generic spec sheet every time."
        ),
    ),
    _Insight(
        id="showroom_not_crate",
        text=(
            "Did you know most robots go back in boxes and crates the minute the booth closes? "
            "Buyers who missed the show never get a second look. "
            "We track who's still actively evaluating — so your team can keep selling after the hall clears."
        ),
    ),
    _Insight(
        id="transit_reality",
        text=(
            "Robots get jostled in transit — loose connectors, misaligned joints, a sensor that worked "
            "in the lab and glitches on the floor. Show week is the wrong time to debug freight damage. "
            "We flag buyers who are planning demos now, not six months from now."
        ),
        humor=True,
    ),
    _Insight(
        id="ces_week",
        text=(
            "CES week in Vegas is when half the robotics industry is in town — including buyers who "
            "never make it to your booth. The off-floor conversations are often where pipeline actually moves."
        ),
        show_key="ces",
    ),
    _Insight(
        id="automate_buyers",
        text=(
            "Automate and ProMat buyers walk in with a checklist: throughput, integration, ROI. "
            "They're not window-shopping — they're comparing vendors who can deploy in their environment, not just on carpet."
        ),
        show_key="automate",
    ),
    _Insight(
        id="nab_crossover",
        text=(
            "NAB pulls broadcast and venue operators who are new to robotics but buying automation for "
            "studios and live production. If you're crossing into that market, timing matters more than a spec sheet."
        ),
        show_key="nab",
    ),
    _Insight(
        id="imts_heavy",
        text=(
            "IMTS is where industrial buyers ask about integration and safety before they ask about cycle time. "
            "The accounts that convert usually started evaluating months before the show — we see those signals early."
        ),
        show_key="imts",
    ),
    _Insight(
        id="hannover_international",
        text=(
            "Hannover draws international OEMs evaluating U.S. expansion. "
            "The ones serious about North America show hiring, distributor, and facility signals long before they land in Germany."
        ),
        show_key="hannover",
    ),
    _Insight(
        id="humanoid_hype",
        text=(
            "Humanoids get the headlines and the foot traffic — and the least patience when a demo hiccups. "
            "Buyers still ask the boring questions: uptime, integration, who fixes it when it breaks."
        ),
        robot_pattern=re.compile(r"\b(humanoid|biped|figure|optimus|digit)\b", re.I),
        humor=True,
    ),
    _Insight(
        id="amr_warehouse",
        text=(
            "AMR deals usually die on the gap between a clean demo lane and a messy warehouse aisle. "
            "We weight signals from operators who've already named throughput or labor pain — not just 'exploring automation.'"
        ),
        robot_pattern=re.compile(r"\b(amr|agv|mobile|autonomous)\b", re.I),
    ),
    _Insight(
        id="hospitality_vegas",
        text=(
            "Vegas hospitality buyers evaluate robots differently — guest experience, labor coverage, "
            "and whether it survives a Friday night on the Strip. We route those accounts separately from warehouse AMR leads."
        ),
    ),
    _Insight(
        id="post_show_momentum",
        text=(
            "The show ends Friday. Pipeline dies Monday if nobody follows up. "
            "We track buyer signals that spike during and right after major events — that's when warm accounts are real."
        ),
    ),
    _Insight(
        id="demo_vs_deploy",
        text=(
            "Trade shows are weird: everyone demos on perfect carpet, then buyers ask if it works on their actual floor. "
            "The vendors who win are the ones talking to accounts already signaling a deployment timeline."
        ),
        humor=True,
    ),
    _Insight(
        id="rfp_timing",
        text=(
            "Most RFP language shows up 6–8 weeks before a vendor conversation — hiring posts, CapEx notes, expansion news. "
            "That's the window we watch, not the week of the press release."
        ),
    ),
    _Insight(
        id="labor_signal",
        text=(
            "Labor pressure is still the quiet driver behind most automation buys — overtime posts, turnover spikes, "
            "new shift schedules. We treat those as first-class signals, not background noise."
        ),
    ),
]


def _hash_seed(key: str) -> int:
    h = 2166136261
    for ch in key:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _show_key(trade_show: Optional[str]) -> Optional[str]:
    if not trade_show:
        return None
    for key, pattern in _SHOW_ALIASES.items():
        if pattern.search(trade_show):
            return key
    return None


def pick_cal_insight(
    *,
    company_name: Optional[str] = None,
    trade_show: Optional[str] = None,
    robot_type: Optional[str] = None,
    seed: Optional[str] = None,
    allow_humor: bool = True,
    audience: str = "any",
) -> str:
    """Pick one insight paragraph. Same seed → same insight.

    audience: "vendor" | "buyer" | "any" — filters vendor-only PoC/deployment insights.
    """
    seed_key = seed or company_name or trade_show or "ready-for-robots"
    show = _show_key(trade_show)
    robot = (robot_type or "").strip()

    pool = [i for i in _INSIGHTS if allow_humor or not i.humor]
    if audience == "buyer":
        pool = [i for i in pool if not i.vendor_only]

    show_matches = [i for i in pool if show and i.show_key == show]
    robot_matches = [
        i for i in pool if i.robot_pattern and robot and i.robot_pattern.search(robot)
    ]

    if show_matches:
        candidates = show_matches
    elif robot_matches:
        candidates = robot_matches
    else:
        candidates = [i for i in pool if not i.show_key and not i.robot_pattern]
        if not candidates:
            candidates = pool

    idx = _hash_seed(seed_key) % len(candidates)
    return candidates[idx].text
