"""
Curated AI / cognition stacks for humanoid benchmark robots.

Stored inside ``humanoid_benchmarks.specs`` as ``ai_stack`` and exposed at the
API top level as ``ai_stack`` for the robots UI. Physical scoring fields are
unchanged — ``compute_scores`` ignores this nested object.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# model_family: vla | world_model | physics_fm | hybrid | fleet_platform | research_stack
AI_STACK_BY_SLUG: Dict[str, Dict[str, Any]] = {
    "unitree-g1": {
        "primary_model": "Unitree onboard policy + NVIDIA GR00T (ecosystem)",
        "model_family": "hybrid",
        "stack_layers": ["locomotion policy", "manipulation policy"],
        "compute": "On-robot edge compute",
        "third_party": ["NVIDIA Isaac GR00T", "NVIDIA Jetson"],
        "unique_claim": "Mass-market hardware with open SDK; GR00T post-training path for G1 embodiment.",
    },
    "unitree-h1": {
        "primary_model": "Unitree onboard policy + NVIDIA GR00T (ecosystem)",
        "model_family": "hybrid",
        "stack_layers": ["locomotion", "manipulation"],
        "compute": "On-robot edge compute",
        "third_party": ["NVIDIA Isaac GR00T"],
        "unique_claim": "Full-size biped platform used in NVIDIA humanoid training sets.",
    },
    "figure-02": {
        "primary_model": "Helix",
        "model_family": "vla",
        "stack_layers": ["S2 planning", "S1 control @ 200 Hz"],
        "compute": "Dual embedded GPUs per robot",
        "third_party": [],
        "unique_claim": "Proprietary VLA for upper-body dexterity; ended OpenAI partnership to own full stack.",
    },
    "agility-digit": {
        "primary_model": "Agility Arc + learned manipulation policies",
        "model_family": "fleet_platform",
        "stack_layers": ["Arc fleet orchestration", "simulation-trained skills"],
        "compute": "Cloud Arc + on-robot control",
        "third_party": ["NVIDIA Isaac (ecosystem partner)"],
        "unique_claim": "First humanoid with documented production tote-moving deployments; WMS/MES-native fleet layer.",
    },
    "tesla-optimus-gen2": {
        "primary_model": "Tesla FSD-derived vision + in-house manipulation",
        "model_family": "hybrid",
        "stack_layers": ["vision backbone", "manipulation policy"],
        "compute": "Tesla Dojo / in-house training",
        "third_party": [],
        "unique_claim": "Reuses automotive perception at scale; factory data flywheel for training.",
    },
    "boston-dynamics-atlas": {
        "primary_model": "Boston Dynamics control stack",
        "model_family": "hybrid",
        "stack_layers": ["model-based locomotion", "learning-assisted manipulation"],
        "compute": "Onboard hydraulic/electric control",
        "third_party": ["NVIDIA Isaac (ecosystem)", "Google DeepMind (Hyundai group)"],
        "unique_claim": "Decades of dynamic locomotion expertise; electric Atlas for real-world pilots.",
    },
    "apptronik-apollo": {
        "primary_model": "Apptronik autonomy stack",
        "model_family": "hybrid",
        "stack_layers": ["manipulation", "locomotion"],
        "compute": "On-robot + cloud",
        "third_party": ["NVIDIA Isaac GR00T (ecosystem partner)"],
        "unique_claim": "Industrial Apollo with hot-swap battery; NVIDIA humanoid platform partner.",
    },
    "1x-neo": {
        "primary_model": "Redwood AI + 1X World Model",
        "model_family": "world_model",
        "stack_layers": ["world model", "built-in LLM", "Redwood VLA"],
        "compute": "NVIDIA Jetson Thor (NEO Cortex)",
        "third_party": ["NVIDIA robotics platform", "OpenAI Startup Fund (investor)"],
        "unique_claim": "Human-like embodiment so internet-scale video transfers; novel tasks from voice/text without prior demos.",
    },
    "sanctuary-phoenix": {
        "primary_model": "Carbon",
        "model_family": "hybrid",
        "stack_layers": ["symbolic reasoning", "LLM", "deep RL", "Large Behavior Models"],
        "compute": "Microsoft Azure training; NVIDIA Isaac Lab simulation",
        "third_party": ["Microsoft Azure", "NVIDIA Isaac"],
        "unique_claim": "Explainable hybrid cognition — audit-friendly plans for regulated manufacturing.",
    },
    "agibot-a2": {
        "primary_model": "Agibot embodied AI + industry datasets",
        "model_family": "vla",
        "stack_layers": ["VLA manipulation", "locomotion"],
        "compute": "On-robot + cloud training",
        "third_party": ["NVIDIA GR00T ecosystem (Genie-1 / Agibot in GR00T training)"],
        "unique_claim": "Strong data-pipeline scale in China deployments; dexterous five-finger hands.",
    },
    "ubtech-walker-x": {
        "primary_model": "UBTECH humanoid AI stack",
        "model_family": "hybrid",
        "stack_layers": ["navigation", "manipulation"],
        "compute": "On-robot",
        "third_party": [],
        "unique_claim": "Commercial Walker line with stair climbing and service-robot heritage.",
    },
    "galaxea-kengo": {
        "primary_model": "Galaxea embodied AI brain",
        "model_family": "hybrid",
        "stack_layers": ["ROS stack", "proprietary motion / AI layer"],
        "compute": "Linux + ROS; Ethernet / Wi-Fi",
        "third_party": [],
        "unique_claim": "Two-module actuator design for scalable manufacturing; fall-tolerant structure for service tasks.",
    },
    "foundation-phantom": {
        "primary_model": "Cortex",
        "model_family": "physics_fm",
        "stack_layers": ["encode", "Bayesian inference", "decode"],
        "compute": "PHANTOM-MK1 onboard",
        "third_party": [],
        "unique_claim": "Physics-informed AI (DVBF-style latent dynamics) vs imitation-only VLAs.",
    },
    "high-torque-mini-pi-plus": {
        "primary_model": "High Torque open robotics stack",
        "model_family": "research_stack",
        "stack_layers": ["sim-to-real pipeline", "community policies"],
        "compute": "Desktop / lab edge",
        "third_party": [],
        "unique_claim": "Open-core lab humanoid; sim-to-real in 24 hours positioning for researchers.",
    },
    "high-torque-mini-pi": {
        "primary_model": "High Torque open robotics stack",
        "model_family": "research_stack",
        "stack_layers": ["sim-to-real pipeline"],
        "compute": "Desktop / lab edge",
        "third_party": [],
        "unique_claim": "Bipedal Mini Pi platform for education and developer experimentation.",
    },
    "andromeda-abi": {
        "primary_model": "Abi companion AI",
        "model_family": "hybrid",
        "stack_layers": ["conversational AI", "social engagement", "mobile base nav"],
        "compute": "On-robot",
        "third_party": [],
        "unique_claim": "Semi-humanoid companion for aged care — personality and empathy, not industrial VLA.",
    },
    "humanoid-hmnd01-alpha-bipedal": {
        "primary_model": "KinetIQ",
        "model_family": "vla",
        "stack_layers": ["S3 fleet", "S2 omni-modal LM", "S1 VLA @ 5–10 Hz", "S0 RL whole-body @ 50 Hz"],
        "compute": "On-robot + cloud fleet layer",
        "third_party": ["NVIDIA GR00T N1.7 (adopter)", "Schaeffler (actuators)"],
        "unique_claim": "Cross-embodiment fleet orchestration; Schaeffler-scale manufacturing rollout.",
    },
    "humanoid-hmnd01-alpha-wheeled": {
        "primary_model": "KinetIQ",
        "model_family": "vla",
        "stack_layers": ["S3 fleet", "S2 planning", "S1 VLA", "S0 RL locomotion"],
        "compute": "On-robot + cloud",
        "third_party": ["NVIDIA GR00T N1.7 (adopter)", "Schaeffler (actuators)"],
        "unique_claim": "Same KinetIQ brain as bipedal variant; industrial wheeled HMND for logistics cells.",
    },
    "generalist-gen1": {
        "primary_model": "GEN-1",
        "model_family": "research_stack",
        "stack_layers": ["embodied foundation model"],
        "compute": "Cloud training + on-robot inference",
        "third_party": [],
        "unique_claim": "Trained from scratch beyond standard VLA/world-model recipes for physical mastery.",
    },
    # ── Common catalog slugs (discovery / backfill) ─────────────────────────
    "figure-01": {
        "primary_model": "Helix (predecessor) / OpenAI-era stack",
        "model_family": "vla",
        "stack_layers": ["S2", "S1"],
        "compute": "Embedded GPUs",
        "third_party": ["OpenAI (former partner)"],
        "unique_claim": "Early Figure stack before full proprietary Helix 02 whole-body control.",
    },
    "nvidia-gr00t-humanoid": {
        "primary_model": "NVIDIA Isaac GR00T N1.7",
        "model_family": "vla",
        "stack_layers": ["Cosmos-Reason VLM", "DiT action head"],
        "compute": "NVIDIA Jetson Thor",
        "third_party": [],
        "unique_claim": "Open, commercially licensed humanoid foundation model; EgoScale human-video pre-training.",
    },
    "pi-humanoid-research": {
        "primary_model": "π0.7",
        "model_family": "vla",
        "stack_layers": ["flow-matching action head"],
        "compute": "Partner robot hardware",
        "third_party": [],
        "unique_claim": "Hardware-agnostic brain; compositional generalization to unseen tasks.",
    },
    "skild-humanoid-stack": {
        "primary_model": "Skild Brain",
        "model_family": "hybrid",
        "stack_layers": ["omni-bodied policy"],
        "compute": "Commercial edge deployments",
        "third_party": [],
        "unique_claim": "Commercial omni-bodied stack with reported $30M early revenue vs research-only peers.",
    },
    "engineai-pm01": {
        "primary_model": "EngineAI onboard AI",
        "model_family": "hybrid",
        "stack_layers": ["locomotion", "manipulation"],
        "compute": "On-robot",
        "third_party": [],
        "unique_claim": "Chinese biped startup platform (PM01) with dynamic motion demos.",
    },
    "fourier-gr3": {
        "primary_model": "Fourier GR-series AI + GR00T path",
        "model_family": "vla",
        "stack_layers": ["manipulation", "locomotion"],
        "compute": "On-robot",
        "third_party": ["NVIDIA Isaac GR00T"],
        "unique_claim": "High-DoF dexterous hands; included in GR00T N1.6+ embodiment training.",
    },
    "neura-4ne1": {
        "primary_model": "NEURA AURA (Physical AI)",
        "model_family": "vla",
        "stack_layers": ["cognitive layer", "perception", "locomotion", "manipulation"],
        "compute": "On-robot + Neuraverse cloud",
        "third_party": ["NVIDIA", "Bosch"],
        "unique_claim": "Europe's production-ready cognitive humanoid; reservations open with AURA perception stack.",
    },
    "rainbow-hubo": {
        "primary_model": "HUBO2 real-time controller stack",
        "model_family": "hybrid",
        "stack_layers": ["locomotion", "manipulation", "balance"],
        "compute": "On-robot (chest-mounted RT controller)",
        "third_party": [],
        "unique_claim": "World's first commercialized humanoid research platform — 38 DOF, sold to MIT and Google labs.",
    },
    "hexagon-aeon": {
        "primary_model": "Hexagon spatial intelligence + autonomy stack",
        "model_family": "hybrid",
        "stack_layers": ["spatial AI", "manipulation", "reality capture", "inspection"],
        "compute": "Edge + cloud (Microsoft Azure)",
        "third_party": ["NVIDIA", "Microsoft", "Maxon"],
        "unique_claim": "Industrial humanoid with spatial intelligence for manipulation, inspection, and reality capture.",
    },
    "dexmate-vega": {
        "primary_model": "Dexmate embodied AI",
        "model_family": "vla",
        "stack_layers": ["bimanual manipulation"],
        "compute": "On-robot",
        "third_party": [],
        "unique_claim": "Heavy-duty bimanual humanoid (Vega) for industrial manipulation.",
    },
}


def get_ai_stack(slug: str) -> Optional[Dict[str, Any]]:
    """Return curated AI stack for a model_slug, if known."""
    if not slug:
        return None
    stack = AI_STACK_BY_SLUG.get(slug)
    return dict(stack) if stack else None


def resolve_ai_stack(specs: Optional[dict], slug: str) -> Optional[Dict[str, Any]]:
    """Prefer stored specs.ai_stack, else catalog lookup."""
    spec = specs or {}
    stored = spec.get("ai_stack")
    if isinstance(stored, dict) and stored.get("primary_model"):
        return dict(stored)
    return get_ai_stack(slug)


def specs_for_storage(base_specs: dict, slug: str, override: Optional[dict] = None) -> dict:
    """Merge physical specs with ai_stack for JSONB persistence."""
    out = dict(base_specs or {})
    stack = override if override else get_ai_stack(slug)
    if stack:
        out["ai_stack"] = stack
    elif "ai_stack" in out and not out["ai_stack"]:
        del out["ai_stack"]
    return out


def scoring_specs(specs: Optional[dict]) -> dict:
    """Physical specs only — exclude ai_stack from HEIF scoring."""
    spec = dict(specs or {})
    spec.pop("ai_stack", None)
    return spec


def enrich_robot_with_ai_stack(row: dict) -> dict:
    """Attach top-level ai_stack for API / UI consumers."""
    out = dict(row)
    stack = resolve_ai_stack(out.get("specs"), out.get("model_slug") or "")
    if stack:
        out["ai_stack"] = stack
    return out
