"""
Humanoid Robot Benchmark Scraper & Scoring Engine
==================================================
• HEIF scoring: 6 dimensions × 0–4 (HEIR 2026 framework)
• Live index: same dimensions mapped to 0–100 for ranking UI
• Scraper: SERP/news search → OpenAI/Anthropic spec extraction
• Seeder: known specs for major humanoids (no live data needed)
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# ── HEIF (HEIR 2026) ─────────────────────────────────────────────────────────
HEIF_DIMS = (
    "mobility",
    "manipulation",
    "cognition",
    "safety",
    "data_pipeline",
    "production",
)

HEIF_WEIGHTS = {d: 1.0 / len(HEIF_DIMS) for d in HEIF_DIMS}

# Authoritative HEIR 2026 research scores (0–4) — vendor-level overrides.
HEIF_RESEARCH_BY_VENDOR: Dict[str, Dict[str, float]] = {
    "boston dynamics": {
        "mobility": 4.0, "manipulation": 2.5, "cognition": 2.0,
        "safety": 2.5, "data_pipeline": 2.0, "production": 2.0,
    },
    "engineai": {
        "mobility": 3.5, "manipulation": 1.5, "cognition": 1.5,
        "safety": 1.0, "data_pipeline": 2.0, "production": 2.0,
    },
    "agibot": {
        "mobility": 3.0, "manipulation": 3.5, "cognition": 3.0,
        "safety": 2.0, "data_pipeline": 4.0, "production": 3.0,
    },
    "zhiyuan": {
        "mobility": 3.0, "manipulation": 3.5, "cognition": 3.0,
        "safety": 2.0, "data_pipeline": 4.0, "production": 3.0,
    },
    "tesla": {
        "mobility": 3.0, "manipulation": 2.5, "cognition": 3.0,
        "safety": 2.0, "data_pipeline": 3.5, "production": 4.0,
    },
    "figure ai": {
        "mobility": 2.5, "manipulation": 3.0, "cognition": 3.5,
        "safety": 2.0, "data_pipeline": 3.5, "production": 2.0,
    },
    "figure": {
        "mobility": 2.5, "manipulation": 3.0, "cognition": 3.5,
        "safety": 2.0, "data_pipeline": 3.5, "production": 2.0,
    },
    "unitree": {
        "mobility": 3.5, "manipulation": 2.0, "cognition": 1.5,
        "safety": 1.5, "data_pipeline": 2.0, "production": 3.5,
    },
    "unitree robotics": {
        "mobility": 3.5, "manipulation": 2.0, "cognition": 1.5,
        "safety": 1.5, "data_pipeline": 2.0, "production": 3.5,
    },
    "agility robotics": {
        "mobility": 2.5, "manipulation": 2.5, "cognition": 2.0,
        "safety": 2.5, "data_pipeline": 2.0, "production": 3.0,
    },
}


def _normalize_vendor(vendor: str) -> str:
    v = (vendor or "").lower().strip()
    v = re.sub(r"\s+", " ", v)
    if "agibot" in v or "zhiyuan" in v:
        return "agibot"
    if "unitree" in v:
        return "unitree"
    if "figure" in v:
        return "figure ai"
    if "tesla" in v:
        return "tesla"
    if "agility" in v:
        return "agility robotics"
    if "boston dynamics" in v:
        return "boston dynamics"
    if "engineai" in v or "engine ai" in v:
        return "engineai"
    return v


def _clamp_heif(value: float) -> float:
    return round(min(4.0, max(0.0, value)), 1)


def _heif_from_legacy_100(score_0_100: float) -> float:
    return _clamp_heif(float(score_0_100) / 25.0)


def score_mobility(specs: dict) -> float:
    """Walking speed, terrain, stair capability."""
    s = 0.0
    speed = float(specs.get("top_speed_mps") or 0)
    if speed >= 3.0:   s += 55
    elif speed >= 1.5: s += 40
    elif speed >= 0.8: s += 28
    elif speed >= 0.4: s += 16
    else:              s += 5

    if specs.get("can_climb_stairs"):        s += 25
    if specs.get("can_navigate_rough_terrain"): s += 15
    if specs.get("can_run"):                 s += 5
    return min(100.0, round(s, 1))


def score_manipulation(specs: dict) -> float:
    """Payload, hand dexterity, degrees of freedom."""
    s = 0.0
    payload = float(specs.get("payload_kg") or 0)
    if payload >= 20:  s += 45
    elif payload >= 10: s += 35
    elif payload >= 5:  s += 25
    elif payload >= 2:  s += 15
    else:               s += 5

    fingers = int(specs.get("finger_count") or 0)
    if fingers >= 5:   s += 35
    elif fingers >= 3: s += 22
    elif fingers >= 1: s += 10

    if specs.get("has_dexterous_hands"): s += 20
    return min(100.0, round(s, 1))


def score_autonomy(specs: dict) -> float:
    """AI capability, autonomy level, commercial deployments."""
    level = str(specs.get("autonomy_level") or "research").lower()
    base = {"full": 60, "semi": 40, "teleoperated": 20, "research": 10}.get(level, 10)
    s = float(base)

    deployments = int(specs.get("commercial_deployments") or 0)
    if deployments >= 100: s += 30
    elif deployments >= 10: s += 20
    elif deployments >= 1:  s += 12
    elif deployments >= 0:  s += 0

    if specs.get("has_sdk"): s += 10
    return min(100.0, round(s, 1))


def score_safety(specs: dict) -> float:
    """Collision force, e-stop, safety certifications."""
    s = 0.0
    if specs.get("has_estop"):           s += 25
    if specs.get("safety_certified"):    s += 25
    if specs.get("force_limited_joints"): s += 20

    force = float(specs.get("collision_force_n") or 9999)
    # ISO TS 15066 thresholds: <135 N low-force, <265 N acceptable, >500 N dangerous
    if force <= 135:   s += 30
    elif force <= 265: s += 20
    elif force <= 500: s += 10
    else:              s += 0     # exceeds safe thresholds

    return min(100.0, round(s, 1))


def score_endurance(specs: dict) -> float:
    """Battery life, charge time, hot-swap capability."""
    s = 0.0
    batt = float(specs.get("battery_life_h") or 0)
    if batt >= 8:   s += 60
    elif batt >= 4: s += 45
    elif batt >= 2: s += 30
    elif batt >= 1: s += 18
    else:           s += 5

    charge = float(specs.get("charge_time_h") or 99)
    if charge <= 0.5:  s += 25
    elif charge <= 1:  s += 18
    elif charge <= 2:  s += 10
    elif charge <= 3:  s += 5

    if specs.get("hot_swap_battery"): s += 15
    return min(100.0, round(s, 1))


def score_market_readiness(specs: dict) -> float:
    """Commercial availability, pricing transparency, SDK."""
    status = str(specs.get("status") or "research").lower()
    base = {"available": 55, "pilot": 35, "research": 15, "discontinued": 5}.get(status, 15)
    s = float(base)

    if specs.get("price_usd"):    s += 15
    if specs.get("has_sdk"):      s += 15
    if specs.get("has_api"):      s += 10
    if specs.get("has_support_sla"): s += 5
    return min(100.0, round(s, 1))


def infer_heif_mobility(specs: dict) -> float:
    return _heif_from_legacy_100(score_mobility(specs))


def infer_heif_manipulation(specs: dict) -> float:
    return _heif_from_legacy_100(score_manipulation(specs))


def infer_heif_cognition(specs: dict) -> float:
    """Task planning / autonomy maturity — SDK, deployments, autonomy level."""
    level = str(specs.get("autonomy_level") or "research").lower()
    s = {"full": 3.2, "semi": 2.0, "teleoperated": 1.0, "research": 0.6}.get(level, 0.6)
    deployments = int(specs.get("commercial_deployments") or 0)
    if deployments >= 100:
        s += 0.8
    elif deployments >= 20:
        s += 0.5
    elif deployments >= 5:
        s += 0.3
    if specs.get("has_sdk"):
        s += 0.4
    if specs.get("has_api"):
        s += 0.2
    return _clamp_heif(s)


def infer_heif_safety(specs: dict) -> float:
    return _heif_from_legacy_100(score_safety(specs))


def infer_heif_data_pipeline(specs: dict) -> float:
    """Fleet learning infrastructure — teleop data, SDK, sim-to-real signals."""
    s = 0.8
    if specs.get("has_sdk"):
        s += 1.0
    if specs.get("has_api"):
        s += 0.6
    deployments = int(specs.get("commercial_deployments") or 0)
    if deployments >= 100:
        s += 1.2
    elif deployments >= 30:
        s += 0.9
    elif deployments >= 10:
        s += 0.6
    elif deployments >= 1:
        s += 0.3
    level = str(specs.get("autonomy_level") or "research").lower()
    if level == "teleoperated":
        s += 0.4  # teleop-heavy vendors often collect manipulation data
    return _clamp_heif(s)


def infer_heif_production(specs: dict, status: str = "research") -> float:
    """Manufacturing scale and commercial deploy readiness."""
    s = score_market_readiness({**specs, "status": status}) / 25.0
    deployments = int(specs.get("commercial_deployments") or 0)
    if deployments >= 100:
        s = max(s, 3.5)
    elif deployments >= 30:
        s = max(s, 3.0)
    elif deployments >= 10:
        s = max(s, 2.5)
    price = specs.get("price_usd")
    if price and float(price) <= 25000:
        s += 0.3
    return _clamp_heif(s)


def infer_heif_scores(specs: dict, status: str = "research") -> Dict[str, float]:
    return {
        "mobility": infer_heif_mobility(specs),
        "manipulation": infer_heif_manipulation(specs),
        "cognition": infer_heif_cognition(specs),
        "safety": infer_heif_safety(specs),
        "data_pipeline": infer_heif_data_pipeline(specs),
        "production": infer_heif_production(specs, status),
    }


def apply_heif_research(vendor: str, inferred: Dict[str, float]) -> Dict[str, float]:
    """HEIR research overrides authoritative dimensions for known vendors."""
    research = HEIF_RESEARCH_BY_VENDOR.get(_normalize_vendor(vendor))
    if not research:
        return inferred
    merged = dict(inferred)
    for dim in HEIF_DIMS:
        if dim in research:
            merged[dim] = research[dim]
    return merged


def heif_total(heif: Dict[str, float]) -> float:
    return round(sum(heif[d] * HEIF_WEIGHTS[d] for d in HEIF_DIMS), 2)


def compute_scores(
    specs: dict,
    status: str = "research",
    vendor: str = "",
) -> dict[str, float]:
    """
    HEIF-first scoring (0–4) with 0–100 live-index aliases for UI/API.

    Legacy keys score_autonomy / score_endurance / score_market_readiness map to
    cognition / data_pipeline / production for backward compatibility.
    """
    inferred = infer_heif_scores(specs, status=status)
    heif = apply_heif_research(vendor, inferred)
    total_heif = heif_total(heif)
    to_100 = lambda v: round(v * 25.0, 1)

    return {
        "heif_mobility": heif["mobility"],
        "heif_manipulation": heif["manipulation"],
        "heif_cognition": heif["cognition"],
        "heif_safety": heif["safety"],
        "heif_data_pipeline": heif["data_pipeline"],
        "heif_production": heif["production"],
        "heif_total": total_heif,
        "score_mobility": to_100(heif["mobility"]),
        "score_manipulation": to_100(heif["manipulation"]),
        "score_cognition": to_100(heif["cognition"]),
        "score_autonomy": to_100(heif["cognition"]),
        "score_safety": to_100(heif["safety"]),
        "score_data_pipeline": to_100(heif["data_pipeline"]),
        "score_endurance": to_100(heif["data_pipeline"]),
        "score_production": to_100(heif["production"]),
        "score_market_readiness": to_100(heif["production"]),
        "score_total": to_100(total_heif),
    }


# ── Known robot seeds ────────────────────────────────────────────────────────
# Specs sourced from published datasheets, manufacturer sites, and
# Fraunhofer IPA benchmark (May 2026). Marked as estimates where uncertain.

SEED_ROBOTS: list[dict] = [
    {
        "name": "Unitree G1",
        "vendor": "Unitree Robotics",
        "model_slug": "unitree-g1",
        "product_url": "https://www.unitree.com/g1",
        "status": "available",
        "specs": {
            "top_speed_mps": 2.0,
            "payload_kg": 3.0,
            "battery_life_h": 1.75,
            "charge_time_h": 1.5,
            "has_dexterous_hands": False,
            "finger_count": 3,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": False,
            "collision_force_n": 520,
            "safety_certified": False,
            "force_limited_joints": False,
            "price_usd": 16000,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": False,
            "commercial_deployments": 50,
            "height_cm": 127,
            "weight_kg": 35,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Unitree H1",
        "vendor": "Unitree Robotics",
        "model_slug": "unitree-h1",
        "product_url": "https://www.unitree.com/h1",
        "status": "available",
        "specs": {
            "top_speed_mps": 3.3,
            "payload_kg": 30.0,
            "battery_life_h": 1.5,
            "charge_time_h": 2.0,
            "has_dexterous_hands": False,
            "finger_count": 0,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": True,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 400,
            "safety_certified": False,
            "force_limited_joints": False,
            "price_usd": 90000,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": False,
            "commercial_deployments": 30,
            "height_cm": 180,
            "weight_kg": 47,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Figure 01",
        "vendor": "Figure AI",
        "model_slug": "figure-01",
        "product_url": "https://www.figure.ai",
        "status": "research",
        "specs": {
            "top_speed_mps": 0.6,
            "payload_kg": 15.0,
            "battery_life_h": 4.0,
            "charge_time_h": 2.5,
            "has_dexterous_hands": True,
            "finger_count": 4,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": False,
            "can_run": False,
            "autonomy_level": "teleop",
            "has_estop": True,
            "collision_force_n": 280,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": False,
            "commercial_deployments": 0,
            "height_cm": 168,
            "weight_kg": 60,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Figure 02",
        "vendor": "Figure AI",
        "model_slug": "figure-02",
        "product_url": "https://www.figure.ai",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 1.2,
            "payload_kg": 20.0,
            "battery_life_h": 5.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 300,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": True,
            "commercial_deployments": 5,
            "height_cm": 168,
            "weight_kg": 60,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Figure 03",
        "vendor": "Figure AI",
        "model_slug": "figure-03",
        "product_url": "https://www.figure.ai",
        "status": "research",
        "specs": {
            "top_speed_mps": 1.4,
            "payload_kg": 22.0,
            "battery_life_h": 5.5,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 280,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": True,
            "commercial_deployments": 2,
            "height_cm": 170,
            "weight_kg": 58,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Agility Digit",
        "vendor": "Agility Robotics",
        "model_slug": "agility-digit",
        "product_url": "https://www.agilityrobotics.com/solutions",
        "status": "available",
        "specs": {
            "top_speed_mps": 1.5,
            "payload_kg": 16.0,
            "battery_life_h": 4.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": False,
            "finger_count": 0,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 250,
            "safety_certified": True,
            "force_limited_joints": True,
            "price_usd": 250000,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 20,
            "height_cm": 175,
            "weight_kg": 65,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Agility Digit 2",
        "vendor": "Agility Robotics",
        "model_slug": "agility-digit-2",
        "product_url": "https://www.agilityrobotics.com/solutions",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 1.6,
            "payload_kg": 18.0,
            "battery_life_h": 4.5,
            "charge_time_h": 1.8,
            "has_dexterous_hands": False,
            "finger_count": 0,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 240,
            "safety_certified": True,
            "force_limited_joints": True,
            "price_usd": 250000,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 25,
            "height_cm": 175,
            "weight_kg": 63,
            "hot_swap_battery": True,
        },
    },
    {
        "name": "Tesla Optimus Gen 1",
        "vendor": "Tesla",
        "model_slug": "tesla-optimus-gen1",
        "product_url": "https://www.tesla.com/AI",
        "status": "research",
        "specs": {
            "top_speed_mps": 0.5,
            "payload_kg": 10.0,
            "battery_life_h": 4.0,
            "charge_time_h": 3.5,
            "has_dexterous_hands": True,
            "finger_count": 4,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": False,
            "can_run": False,
            "autonomy_level": "teleop",
            "has_estop": True,
            "collision_force_n": 180,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": False,
            "commercial_deployments": 0,
            "height_cm": 172,
            "weight_kg": 57,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Tesla Optimus Gen 2",
        "vendor": "Tesla",
        "model_slug": "tesla-optimus-gen2",
        "product_url": "https://www.tesla.com/AI",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 0.8,
            "payload_kg": 20.0,
            "battery_life_h": 8.0,
            "charge_time_h": 3.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": False,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 200,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": False,
            "commercial_deployments": 0,
            "height_cm": 172,
            "weight_kg": 57,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Boston Dynamics Atlas",
        "vendor": "Boston Dynamics",
        "model_slug": "boston-dynamics-atlas",
        "product_url": "https://bostondynamics.com/atlas",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 2.5,
            "payload_kg": 11.0,
            "battery_life_h": 1.5,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 3,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": True,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 350,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 5,
            "height_cm": 150,
            "weight_kg": 89,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Apptronik Apollo",
        "vendor": "Apptronik",
        "model_slug": "apptronik-apollo",
        "product_url": "https://apptronik.com/apollo",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 1.2,
            "payload_kg": 25.0,
            "battery_life_h": 4.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": False,
            "finger_count": 0,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 200,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 10,
            "height_cm": 173,
            "weight_kg": 73,
            "hot_swap_battery": True,
        },
    },
    {
        "name": "1X NEO",
        "vendor": "1X Technologies",
        "model_slug": "1x-neo",
        "product_url": "https://www.1x.tech/neo",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 1.0,
            "payload_kg": 10.0,
            "battery_life_h": 8.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": False,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 150,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": False,
            "commercial_deployments": 3,
            "height_cm": 165,
            "weight_kg": 30,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Sanctuary Phoenix",
        "vendor": "Sanctuary AI",
        "model_slug": "sanctuary-phoenix",
        "product_url": "https://sanctuary.ai",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 0.5,
            "payload_kg": 25.0,
            "battery_life_h": 8.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": False,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 180,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": False,
            "commercial_deployments": 5,
            "height_cm": 170,
            "weight_kg": 55,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Agibot A2",
        "vendor": "Agibot (Zhiyuan Robotics)",
        "model_slug": "agibot-a2",
        "product_url": "https://agibot.com",
        "status": "available",
        "specs": {
            "top_speed_mps": 1.5,
            "payload_kg": 20.0,
            "battery_life_h": 2.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 250,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": False,
            "commercial_deployments": 20,
            "height_cm": 168,
            "weight_kg": 65,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "UBTECH Walker X",
        "vendor": "UBTECH Robotics",
        "model_slug": "ubtech-walker-x",
        "product_url": "https://www.ubtrobot.com/en/",
        "status": "available",
        "specs": {
            "top_speed_mps": 0.8,
            "payload_kg": 5.0,
            "battery_life_h": 2.5,
            "charge_time_h": 3.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": False,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 200,
            "safety_certified": False,
            "force_limited_joints": False,
            "price_usd": None,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": False,
            "commercial_deployments": 15,
            "height_cm": 170,
            "weight_kg": 77,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Galaxea Kengo",
        "vendor": "Galaxea Dynamics",
        "model_slug": "galaxea-kengo",
        "product_url": "https://humanoid.guide/welcome-kengo/",
        "status": "research",
        "specs": {
            "top_speed_mps": 1.0,
            "payload_kg": 5.0,
            "battery_life_h": 2.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 280,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": False,
            "commercial_deployments": 0,
            "height_cm": 170,
            "weight_kg": 65,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Foundation Phantom",
        "vendor": "Foundation Future Industries",
        "model_slug": "foundation-phantom",
        "product_url": "https://foundation.bot/",
        "status": "research",
        "specs": {
            "top_speed_mps": 0.8,
            "payload_kg": 15.0,
            "battery_life_h": 4.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 250,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": False,
            "commercial_deployments": 0,
            "height_cm": 175,
            "weight_kg": 70,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "High Torque Mini Pi plus",
        "vendor": "High Torque Robotics",
        "model_slug": "high-torque-mini-pi-plus",
        "product_url": "https://www.hightorquerobotics.com/",
        "status": "available",
        "specs": {
            "top_speed_mps": 0.6,
            "payload_kg": 2.0,
            "battery_life_h": 1.5,
            "charge_time_h": 1.5,
            "has_dexterous_hands": False,
            "finger_count": 3,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": False,
            "can_run": False,
            "autonomy_level": "research",
            "has_estop": True,
            "collision_force_n": 120,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": False,
            "commercial_deployments": 10,
            "height_cm": 90,
            "weight_kg": 12,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Andromeda Abi",
        "vendor": "Andromeda Robotics",
        "model_slug": "andromeda-abi",
        "product_url": "https://andromedarobotics.ai/",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 0.5,
            "payload_kg": 2.0,
            "battery_life_h": 6.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 100,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": True,
            "commercial_deployments": 15,
            "height_cm": 140,
            "weight_kg": 45,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Humanoid HMND 01 Alpha Bipedal",
        "vendor": "Humanoid (SKL Robotics)",
        "model_slug": "humanoid-hmnd01-alpha-bipedal",
        "product_url": "https://thehumanoid.ai/",
        "status": "pilot",
        "specs": {
            "top_speed_mps": 1.2,
            "payload_kg": 20.0,
            "battery_life_h": 4.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": True,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 220,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": True,
            "has_api": True,
            "has_support_sla": True,
            "commercial_deployments": 50,
            "height_cm": 175,
            "weight_kg": 75,
            "hot_swap_battery": False,
        },
    },
    {
        "name": "Generalist GEN-1",
        "vendor": "Generalist AI",
        "model_slug": "generalist-gen1",
        "product_url": "https://generalistai.com/",
        "status": "research",
        "specs": {
            "top_speed_mps": 0.5,
            "payload_kg": 5.0,
            "battery_life_h": 4.0,
            "charge_time_h": 2.0,
            "has_dexterous_hands": True,
            "finger_count": 5,
            "can_climb_stairs": False,
            "can_navigate_rough_terrain": True,
            "can_run": False,
            "autonomy_level": "semi",
            "has_estop": True,
            "collision_force_n": 150,
            "safety_certified": False,
            "force_limited_joints": True,
            "price_usd": None,
            "has_sdk": False,
            "has_api": False,
            "has_support_sla": False,
            "commercial_deployments": 0,
            "height_cm": None,
            "weight_kg": None,
            "hot_swap_battery": False,
        },
    },
]


# ── Scraper ──────────────────────────────────────────────────────────────────

def _search_robot_specs(robot_name: str, vendor: str) -> list[dict]:
    """Search for recent spec articles using configured news/SERP APIs."""
    results: list[dict] = []

    gnews_key = os.environ.get("GNEWS_API_KEY")
    if gnews_key:
        try:
            query = f"{vendor} {robot_name} humanoid robot specifications 2025 2026"
            r = requests.get(
                "https://gnews.io/api/v4/search",
                params={"q": query, "lang": "en", "max": 5, "apikey": gnews_key},
                timeout=10,
            )
            if r.ok:
                for art in r.json().get("articles", []):
                    results.append({
                        "url": art.get("url"),
                        "title": art.get("title"),
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    })
        except Exception as exc:
            logger.warning("GNews search failed for %s: %s", robot_name, exc)

    return results


def _extract_specs_with_llm(robot_name: str, vendor: str, articles: list[dict]) -> dict:
    """
    Use Anthropic Claude to extract structured specs from article titles/URLs.
    Returns a partial spec dict — only updates fields it finds evidence for.
    Falls back to empty dict if extraction fails.
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key or not articles:
        return {}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        article_text = "\n".join(
            f"- {a.get('title', '')} ({a.get('url', '')})"
            for a in articles[:5]
        )
        prompt = f"""You are a robotics spec extraction assistant.

Given these article titles about the {vendor} {robot_name} humanoid robot:
{article_text}

Extract any CONFIRMED specs and return ONLY a JSON object with these keys (omit any you are not certain about):
top_speed_mps, payload_kg, battery_life_h, charge_time_h, finger_count,
can_climb_stairs (bool), can_navigate_rough_terrain (bool), can_run (bool),
has_dexterous_hands (bool), has_estop (bool), price_usd,
commercial_deployments (integer estimate), height_cm, weight_kg

Return ONLY the JSON object, no explanation."""

        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            import json
            return json.loads(match.group())
    except Exception as exc:
        logger.warning("LLM spec extraction failed for %s: %s", robot_name, exc)

    return {}


def scrape_and_score_robot(db_session: Any, model_slug: str) -> dict:
    """
    Scrape fresh spec data for one robot, merge with existing, recompute scores.
    Returns the updated row dict.
    """
    from sqlalchemy import text

    row = db_session.execute(
        text("SELECT * FROM humanoid_benchmarks WHERE model_slug = :slug"),
        {"slug": model_slug},
    ).mappings().first()

    if not row:
        return {"error": f"Robot not found: {model_slug}"}

    robot_name = row["name"]
    vendor = row["vendor"]
    existing_specs = dict(row["specs"] or {})

    # Search for recent articles
    articles = _search_robot_specs(robot_name, vendor)

    # Try to extract updated specs via LLM
    fresh_specs = _extract_specs_with_llm(robot_name, vendor, articles)

    # Merge: fresh data wins over seeded data
    from app.services.humanoid_ai_stack import scoring_specs, specs_for_storage

    merged_specs = {**existing_specs, **{k: v for k, v in fresh_specs.items() if v is not None}}
    merged_specs = specs_for_storage(merged_specs, model_slug)

    # Recompute scores
    scores = compute_scores(scoring_specs(merged_specs), status=row["status"], vendor=vendor)

    now = datetime.now(timezone.utc)
    sources = list(row["sources"] or []) + articles

    db_session.execute(
        text("""
            UPDATE humanoid_benchmarks SET
                specs = cast(:specs as jsonb),
                score_mobility = :score_mobility,
                score_manipulation = :score_manipulation,
                score_autonomy = :score_autonomy,
                score_safety = :score_safety,
                score_endurance = :score_endurance,
                score_market_readiness = :score_market_readiness,
                score_total = :score_total,
                heif_mobility = :heif_mobility,
                heif_manipulation = :heif_manipulation,
                heif_cognition = :heif_cognition,
                heif_safety = :heif_safety,
                heif_data_pipeline = :heif_data_pipeline,
                heif_production = :heif_production,
                heif_total = :heif_total,
                sources = cast(:sources as jsonb),
                last_scraped_at = :now,
                updated_at = :now
            WHERE model_slug = :slug
        """),
        {
            "specs": __import__("json").dumps(merged_specs),
            "sources": __import__("json").dumps(sources[-20:]),  # keep last 20
            "now": now,
            "slug": model_slug,
            **scores,
        },
    )
    db_session.commit()
    return {"slug": model_slug, "scores": scores, "sources_found": len(articles)}


def seed_robots(db_session: Any) -> dict:
    """
    Insert all SEED_ROBOTS into humanoid_benchmarks if not already present.
    Computes initial scores from seeded specs.
    """
    from sqlalchemy import text
    import json

    inserted = 0
    updated = 0
    failed: list[str] = []

    from app.services.humanoid_ai_stack import specs_for_storage, scoring_specs

    for robot in SEED_ROBOTS:
        specs = specs_for_storage(robot["specs"], robot["model_slug"], robot.get("ai_stack"))
        scores = compute_scores(
            scoring_specs(specs),
            status=robot["status"],
            vendor=robot["vendor"],
        )
        now = datetime.now(timezone.utc)

        try:
            existing = db_session.execute(
                text("SELECT id FROM humanoid_benchmarks WHERE model_slug = :slug"),
                {"slug": robot["model_slug"]},
            ).first()

            if existing:
                db_session.execute(
                    text("""
                        UPDATE humanoid_benchmarks SET
                            product_url = :product_url,
                            specs = cast(:specs as jsonb),
                            score_mobility = :score_mobility,
                            score_manipulation = :score_manipulation,
                            score_autonomy = :score_autonomy,
                            score_safety = :score_safety,
                            score_endurance = :score_endurance,
                            score_market_readiness = :score_market_readiness,
                            score_total = :score_total,
                            heif_mobility = :heif_mobility,
                            heif_manipulation = :heif_manipulation,
                            heif_cognition = :heif_cognition,
                            heif_safety = :heif_safety,
                            heif_data_pipeline = :heif_data_pipeline,
                            heif_production = :heif_production,
                            heif_total = :heif_total,
                            updated_at = :now
                        WHERE model_slug = :slug
                    """),
                    {"specs": json.dumps(specs), "now": now, "slug": robot["model_slug"], "product_url": robot.get("product_url"), **scores},
                )
                updated += 1
            else:
                db_session.execute(
                    text("""
                        INSERT INTO humanoid_benchmarks
                            (name, vendor, model_slug, product_url, status, specs,
                             score_mobility, score_manipulation, score_autonomy,
                             score_safety, score_endurance, score_market_readiness,
                             score_total,
                             heif_mobility, heif_manipulation, heif_cognition,
                             heif_safety, heif_data_pipeline, heif_production, heif_total,
                             sources, last_scraped_at, created_at, updated_at)
                        VALUES
                            (:name, :vendor, :model_slug, :product_url, :status, cast(:specs as jsonb),
                             :score_mobility, :score_manipulation, :score_autonomy,
                             :score_safety, :score_endurance, :score_market_readiness,
                             :score_total,
                             :heif_mobility, :heif_manipulation, :heif_cognition,
                             :heif_safety, :heif_data_pipeline, :heif_production, :heif_total,
                             cast('[]' as jsonb), :now, :now, :now)
                    """),
                    {
                        "name": robot["name"],
                        "vendor": robot["vendor"],
                        "model_slug": robot["model_slug"],
                        "product_url": robot.get("product_url"),
                        "status": robot["status"],
                        "specs": json.dumps(specs),
                        "now": now,
                        **scores,
                    },
                )
                inserted += 1
            db_session.commit()
        except Exception:
            db_session.rollback()
            failed.append(robot["model_slug"])

    return {"inserted": inserted, "updated": updated, "failed": failed, "total": len(SEED_ROBOTS)}


# ── AI HEIF agent + discovery upsert ─────────────────────────────────────────

HEIF_AGENT_SYSTEM = """You are a humanoid robotics analyst using the HEIR 2026 HEIF framework.

Score each dimension 0.0–4.0 (one decimal):
- mobility: dynamic locomotion, speed, terrain, stairs, recovery
- manipulation: payload, dexterous hands, force-controlled grasping
- cognition: task planning, autonomy level, SDK/API, commercial task execution
- safety: e-stop, force-limited joints, certifications, collision force vs ISO TS 15066
- data_pipeline: teleoperation data, fleet learning, sim-to-real, developer ecosystem
- production: manufacturing scale, price transparency, commercial availability

Reference anchors (HEIR 2026):
Boston Dynamics mobility 4.0; AgiBot manipulation 3.5 / data_pipeline 4.0;
Figure cognition 3.5; Tesla production 4.0; Unitree mobility 3.5 / production 3.5.

Be conservative for research-stage or unverified startups. Use public evidence only.
Return valid JSON only."""


def _parse_json_object(text: str) -> dict:
    import json
    if not text:
        return {}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def agent_assess_humanoid(
    name: str,
    vendor: str,
    *,
    country: str = "",
    status: str = "research",
    product_url: str = "",
    articles: Optional[list] = None,
    existing_specs: Optional[dict] = None,
) -> dict:
    """
    LLM agent assesses specs + HEIF dimensions per HEIR protocol.
    Falls back to rule-based inference when no LLM is configured.
    """
    from app.services.llm_client import llm_json_completion

    article_text = ""
    if articles:
        article_text = "\n".join(
            f"- {a.get('title', '')} ({a.get('url', '')})" for a in articles[:8]
        )

    user_prompt = f"""Assess this humanoid robot for the HEIF benchmark leaderboard.

Robot: {name}
Vendor: {vendor}
Country: {country or 'unknown'}
Status hint: {status}
Product URL: {product_url or 'unknown'}
Known specs: {existing_specs or {}}
Recent news:
{article_text or '(none)'}

Return JSON:
{{
  "status": "available|pilot|research|discontinued",
  "specs": {{
    "top_speed_mps": number|null,
    "payload_kg": number|null,
    "battery_life_h": number|null,
    "finger_count": integer|null,
    "has_dexterous_hands": boolean,
    "can_climb_stairs": boolean,
    "can_navigate_rough_terrain": boolean,
    "can_run": boolean,
    "has_estop": boolean,
    "force_limited_joints": boolean,
    "safety_certified": boolean,
    "collision_force_n": number|null,
    "autonomy_level": "full|semi|teleoperated|research",
    "commercial_deployments": integer,
    "price_usd": number|null,
    "has_sdk": boolean,
    "has_api": boolean,
    "height_cm": number|null,
    "weight_kg": number|null
  }},
  "heif": {{
    "mobility": 0.0-4.0,
    "manipulation": 0.0-4.0,
    "cognition": 0.0-4.0,
    "safety": 0.0-4.0,
    "data_pipeline": 0.0-4.0,
    "production": 0.0-4.0
  }},
  "confidence": 0.0-1.0,
  "evidence_summary": "one sentence"
}}"""

    raw = llm_json_completion(HEIF_AGENT_SYSTEM, user_prompt, max_tokens=1200, temperature=0.2)
    parsed = _parse_json_object(raw or "")

    from app.services.humanoid_ai_stack import scoring_specs, specs_for_storage

    if not parsed:
        specs = specs_for_storage(dict(existing_specs or {}), model_slug)
        scores = compute_scores(scoring_specs(specs), status=status, vendor=vendor)
        return {
            "status": status,
            "specs": specs,
            "scores": scores,
            "confidence": 0.0,
            "evidence_summary": "Rule-based inference (no LLM)",
            "agent_scored": False,
        }

    agent_status = str(parsed.get("status") or status).lower()
    if agent_status not in ("available", "pilot", "research", "discontinued"):
        agent_status = status

    agent_specs = {**(existing_specs or {}), **(parsed.get("specs") or {})}
    agent_specs = {k: v for k, v in agent_specs.items() if v is not None and k != "ai_stack"}
    agent_specs = specs_for_storage(agent_specs, model_slug)

    scores = compute_scores(scoring_specs(agent_specs), status=agent_status, vendor=vendor)

    # Apply agent HEIF when no authoritative HEIR research override exists
    agent_heif = parsed.get("heif") or {}
    confidence = float(parsed.get("confidence") or 0.0)
    research = HEIF_RESEARCH_BY_VENDOR.get(_normalize_vendor(vendor))
    if agent_heif and confidence >= 0.45 and not research:
        score_keys = {
            "mobility": "score_mobility",
            "manipulation": "score_manipulation",
            "cognition": "score_cognition",
            "safety": "score_safety",
            "data_pipeline": "score_data_pipeline",
            "production": "score_production",
        }
        for dim in HEIF_DIMS:
            val = agent_heif.get(dim)
            if val is not None:
                scores[f"heif_{dim}"] = _clamp_heif(float(val))
                scores[score_keys[dim]] = round(scores[f"heif_{dim}"] * 25, 1)
        # Legacy aliases
        scores["score_autonomy"] = scores["score_cognition"]
        scores["score_endurance"] = scores["score_data_pipeline"]
        scores["score_market_readiness"] = scores["score_production"]
        heif_map = {d: scores[f"heif_{d}"] for d in HEIF_DIMS}
        scores["heif_total"] = heif_total(heif_map)
        scores["score_total"] = round(scores["heif_total"] * 25, 1)

    return {
        "status": agent_status,
        "specs": agent_specs,
        "scores": scores,
        "confidence": confidence,
        "evidence_summary": parsed.get("evidence_summary") or "",
        "agent_scored": bool(agent_heif),
    }


def upsert_humanoid_robot(
    db_session: Any,
    robot: dict,
    *,
    source: str = "discovery",
    commit: bool = True,
) -> str:
    """
    Insert or update a humanoid_benchmarks row.
    Returns 'inserted', 'updated', or 'skipped'.
    """
    from sqlalchemy import text
    import json

    from app.services.humanoid_catalog_cleanup import is_junk_humanoid_row

    slug = robot["model_slug"]
    name = robot.get("name") or ""
    vendor = robot.get("vendor") or ""
    if is_junk_humanoid_row(name, vendor, slug):
        logger.info("Skipping junk humanoid upsert: %s (%s)", name[:80], slug)
        return "skipped"
    from app.services.humanoid_ai_stack import specs_for_storage, scoring_specs

    raw_specs = robot.get("specs") or {}
    specs = specs_for_storage(raw_specs, slug, robot.get("ai_stack"))
    status = robot.get("status") or "research"
    scores = robot.get("scores") or compute_scores(
        scoring_specs(specs), status=status, vendor=vendor
    )
    now = datetime.now(timezone.utc)

    sources = robot.get("sources") or []
    if source:
        sources.append({
            "type": source,
            "scraped_at": now.isoformat(),
            "summary": robot.get("evidence_summary", ""),
        })

    existing = db_session.execute(
        text("SELECT id, specs, sources FROM humanoid_benchmarks WHERE model_slug = :slug"),
        {"slug": slug},
    ).mappings().first()

    if existing:
        merged_specs = {**(existing["specs"] or {}), **specs}
        merged_sources = list(existing["sources"] or []) + sources
        db_session.execute(
            text("""
                UPDATE humanoid_benchmarks SET
                    name = :name, vendor = :vendor, product_url = :product_url,
                    status = :status, specs = cast(:specs as jsonb),
                    score_mobility = :score_mobility, score_manipulation = :score_manipulation,
                    score_autonomy = :score_autonomy, score_safety = :score_safety,
                    score_endurance = :score_endurance, score_market_readiness = :score_market_readiness,
                    score_total = :score_total,
                    heif_mobility = :heif_mobility, heif_manipulation = :heif_manipulation,
                    heif_cognition = :heif_cognition, heif_safety = :heif_safety,
                    heif_data_pipeline = :heif_data_pipeline, heif_production = :heif_production,
                    heif_total = :heif_total,
                    sources = cast(:sources as jsonb),
                    last_scraped_at = :now, updated_at = :now
                WHERE model_slug = :slug
            """),
            {
                "name": robot["name"],
                "vendor": vendor,
                "product_url": robot.get("product_url"),
                "status": status,
                "specs": json.dumps(merged_specs),
                "sources": json.dumps(merged_sources[-20:]),
                "now": now,
                "slug": slug,
                **scores,
            },
        )
        if commit:
            db_session.commit()
        return "updated"

    db_session.execute(
        text("""
            INSERT INTO humanoid_benchmarks
                (name, vendor, model_slug, product_url, status, specs,
                 score_mobility, score_manipulation, score_autonomy,
                 score_safety, score_endurance, score_market_readiness, score_total,
                 heif_mobility, heif_manipulation, heif_cognition,
                 heif_safety, heif_data_pipeline, heif_production, heif_total,
                 sources, last_scraped_at, created_at, updated_at)
            VALUES
                (:name, :vendor, :model_slug, :product_url, :status, cast(:specs as jsonb),
                 :score_mobility, :score_manipulation, :score_autonomy,
                 :score_safety, :score_endurance, :score_market_readiness, :score_total,
                 :heif_mobility, :heif_manipulation, :heif_cognition,
                 :heif_safety, :heif_data_pipeline, :heif_production, :heif_total,
                 cast(:sources as jsonb), :now, :now, :now)
        """),
        {
            "name": robot["name"],
            "vendor": vendor,
            "model_slug": slug,
            "product_url": robot.get("product_url"),
            "status": status,
            "specs": json.dumps(specs),
            "sources": json.dumps(sources[-20:]),
            "now": now,
            **scores,
        },
    )
    if commit:
        db_session.commit()
    return "inserted"

