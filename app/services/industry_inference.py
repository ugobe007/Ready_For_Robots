"""
Shared industry inference from text (signal text, company name, article context).
Used by reclassify-unknown and can be used by scrapers.
"""
from typing import Dict

INDUSTRY_KEYWORDS: Dict[str, list] = {
    "Logistics": [
        "warehouse", "logistics", "fulfillment", "distribution", "supply chain",
        "3pl", "third party logistics", "fulfillment center", "fulfillment centre",
        "cold storage", "freight", "shipping", "delivery"
    ],
    "Hospitality": [
        "hotel", "resort", "hospitality", "lodging", "motel", "inn",
        "housekeeping", "guest services", "property management"
    ],
    "Food Service": [
        "restaurant", "food service", "kitchen", "dining", "qsr",
        "fast food", "cafe", "chain restaurant", "franchise"
    ],
    "Healthcare": [
        "hospital", "healthcare", "health system", "clinic", "patient",
        "senior living", "nursing home", "assisted living", "medical center"
    ],
    "Medical Technology": [
        "laboratory", "lab automation", "clinical lab", "diagnostics lab",
        "pharmacy", "hospital pharmacy", "surgical robot", "surgical suite",
        "patient care", "specimen processing", "pathology", "iv compounding",
        "medication dispensing", "robotic surgery", "da vinci", "telepresence",
        "telehealth", "phlebotomy", "surgical", "surgery robot", "korea biomed",
        "vitestro", "roen surgical", "surgerii"
    ],
    "Food Processing & Manufacturing": [
        "food processing", "food manufacturing", "meat processing",
        "bakery", "produce processing", "food packaging", "food safety",
        "food sorting", "food preparation", "cooking automation",
        "robotic chef", "robotic kitchen"
    ],
    "Datacenters": [
        "datacenter", "data center", "server", "hyperscale", "cloud infrastructure",
        "colocation", "server farm", "datacenter operations", "datacenter maintenance"
    ],
    "Airports & Aviation": [
        "airport", "terminal", "aviation", "baggage handling", "boarding gate",
        "airport operations", "airport security", "airport shuttle",
        "airlines", "airline", "metro", "transit", "transportation", "lax station"
    ],
    "Retail": [
        "retail", "store", "shopping", "e-commerce", "grocery", "supermarket",
        "shelf scanning", "inventory robot", "click-and-collect", "micro-fulfillment",
        "retail fulfillment", "retail automation", "cashier", "checkout"
    ],
    "Apparel & Textiles": [
        "garment", "apparel", "clothing", "fashion", "textile",
        "sewing", "fabric cutting", "apparel factory", "apparel warehouse",
        "clothing distribution", "fashion logistics", "garment sorting"
    ],
    "Casinos & Gaming": [
        "casino", "gaming", "resort casino", "slot", "table games",
        "integrated resort", "tribal gaming"
    ],
    "Cruise Lines": [
        "cruise", "cruise line", "cruise ship", "vessel", "onboard"
    ],
    "Theme Parks & Entertainment": [
        "theme park", "amusement park", "roller coaster", "attractions",
        "entertainment venue", "water park", "six flags", "ski resort", "stevens pass"
    ],
    "Real Estate & Facilities": [
        "facilities management", "property management", "commercial real estate",
        "building services", "janitorial", "facility services",
        "corporate office", "corporate offices", "office building", "headquarters",
        "enterprise", "office campus", "office tower", "corporate campus"
    ],
    "Automotive Dealerships": [
        "dealership", "auto dealer", "car dealer", "automotive retail"
    ],
    "Automotive & Manufacturing": [
        "automotive", "manufacturing", "factory", "assembly", "motor group",
        "semiconductor", "cobot", "industrial automation", "hyundai motor",
        "bmw group", "teradyne", "rockwell", "omron", "stmicroelectronics",
        "humanoid robots", "deploy humanoid", "factory from", "assembly line"
    ],
    "Media & Publishing": [
        "manufacturing dive", "motley fool", "new york times", "reuters",
        "business wire", "pr newswire", "financial times", "investing.com",
        "wirecutter", "magazine", "post.", "times.", "dive."
    ],
    "Laundry & Linen Services": [
        "laundry", "linen", "commercial laundry", "industrial laundry",
        "uniform cleaning", "linen service", "laundry service", "laundromat",
        "textile cleaning", "flatwork", "wash dry fold"
    ],
    "Car Wash": [
        "car wash", "carwash", "express wash", "tunnel wash", "conveyor wash",
        "automated car wash", "car wash chain", "quick wash"
    ],
}


def infer_industry_from_text(text: str) -> str:
    """Infer industry from combined text (e.g. company name + all signal texts)."""
    if not (text and text.strip()):
        return "Unknown"
    text_lower = text.lower()
    scores = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[industry] = score
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    return "Unknown"
