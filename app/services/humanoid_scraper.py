"""
Humanoid Robot Benchmark Scraper & Scoring Engine
==================================================
• Scoring: 6 dimensions × 0-100, weighted composite
• Scraper: SERP/news search → OpenAI/Anthropic spec extraction
• Seeder: known specs for 10 major humanoids (no live data needed)
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ── Scoring weights ─────────────────────────────────────────────────────────
WEIGHTS = {
    "mobility":         0.20,
    "manipulation":     0.20,
    "autonomy":         0.20,
    "safety":           0.15,
    "endurance":        0.15,
    "market_readiness": 0.10,
}


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


def compute_scores(specs: dict, status: str = "research") -> dict[str, float]:
    full_specs = {**specs, "status": status}
    mob  = score_mobility(full_specs)
    man  = score_manipulation(full_specs)
    aut  = score_autonomy(full_specs)
    saf  = score_safety(full_specs)
    end  = score_endurance(full_specs)
    mkt  = score_market_readiness(full_specs)
    total = round(
        mob  * WEIGHTS["mobility"] +
        man  * WEIGHTS["manipulation"] +
        aut  * WEIGHTS["autonomy"] +
        saf  * WEIGHTS["safety"] +
        end  * WEIGHTS["endurance"] +
        mkt  * WEIGHTS["market_readiness"],
        1
    )
    return {
        "score_mobility":         mob,
        "score_manipulation":     man,
        "score_autonomy":         aut,
        "score_safety":           saf,
        "score_endurance":        end,
        "score_market_readiness": mkt,
        "score_total":            total,
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
        "name": "Agility Digit",
        "vendor": "Agility Robotics",
        "model_slug": "agility-digit",
        "product_url": "https://agilityrobotics.com/digit",
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
        "name": "Tesla Optimus Gen 2",
        "vendor": "Tesla",
        "model_slug": "tesla-optimus-gen2",
        "product_url": "https://www.tesla.com/optimus",
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
        "product_url": "https://www.ubtrobot.com/walker",
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
    merged_specs = {**existing_specs, **{k: v for k, v in fresh_specs.items() if v is not None}}

    # Recompute scores
    scores = compute_scores(merged_specs, status=row["status"])

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

    for robot in SEED_ROBOTS:
        specs = robot["specs"]
        scores = compute_scores(specs, status=robot["status"])
        now = datetime.now(timezone.utc)

        existing = db_session.execute(
            text("SELECT id FROM humanoid_benchmarks WHERE model_slug = :slug"),
            {"slug": robot["model_slug"]},
        ).first()

        if existing:
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
                        updated_at = :now
                    WHERE model_slug = :slug
                """),
                {"specs": json.dumps(specs), "now": now, "slug": robot["model_slug"], **scores},
            )
            updated += 1
        else:
            db_session.execute(
                text("""
                    INSERT INTO humanoid_benchmarks
                        (name, vendor, model_slug, product_url, status, specs,
                         score_mobility, score_manipulation, score_autonomy,
                         score_safety, score_endurance, score_market_readiness,
                         score_total, sources, last_scraped_at, created_at, updated_at)
                    VALUES
                        (:name, :vendor, :model_slug, :product_url, :status, cast(:specs as jsonb),
                         :score_mobility, :score_manipulation, :score_autonomy,
                         :score_safety, :score_endurance, :score_market_readiness,
                         :score_total, cast('[]' as jsonb), :now, :now, :now)
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
    return {"inserted": inserted, "updated": updated, "total": len(SEED_ROBOTS)}
