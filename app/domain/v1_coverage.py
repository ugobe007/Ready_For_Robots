"""V1 robot category / industry coverage (seller matching wedge)."""
from __future__ import annotations

# Categories eligible for URL→profile → Work Envelope → match.
SUPPORTED_V1_CATEGORIES = frozenset(
    {
        "autonomous_forklift",
        "amr",
        "autonomous_tugger",
        "material_movement",
        "humanoid",
    }
)

# Canonical industry labels (align with industry_inference.INDUSTRY_KEYWORDS).
V1_TARGET_INDUSTRIES = (
    "Logistics",
    "Manufacturing",
    "Automotive & Manufacturing",
    "Hospitality",
    "Healthcare",  # hospitals
    "Food Service",  # restaurants
    "Casinos & Gaming",
    "Retail",
    "Defense",
)

# Default industries stored on Robot rows created via V1 analysis.
V1_HUMANOID_INDUSTRIES = list(V1_TARGET_INDUSTRIES) + ["Warehouse"]

V1_LOGISTICS_INDUSTRIES = [
    "Logistics",
    "Manufacturing",
    "Automotive & Manufacturing",
    "Warehouse",
    "Retail",  # DC / back-of-house
    "Defense",  # base / depot logistics
]

V1_HUMANOID_USE_CASES = [
    "Humanoid labor",
    "Material handling",
    "Logistics",
    "Hospitality service",
    "Hospital logistics",
    "Manufacturing line support",
    "Restaurant / F&B support",
    "Casino floor & back-of-house",
    "Retail floor & stockroom",
    "Defense logistics support",
]

V1_LOGISTICS_USE_CASES = [
    "Material movement",
    "Pallet transport",
    "Line replenishment",
    "Warehouse putaway",
]

COMMERCIAL_MATURITY = frozenset(
    {
        "concept",
        "prototype",
        "pilot",
        "commercial",
        "production",
        "discontinued",
        "unknown",
    }
)
