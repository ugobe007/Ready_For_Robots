"""
Robot URL → capability profile (match-url understanding engine).

Extracted from robot_ready so Jobs can reuse understanding without importing
the buyer-lead matching stack.
"""
from __future__ import annotations

import re
from typing import Any, Dict

import requests
from bs4 import BeautifulSoup


def scrape_robot_page(url: str) -> str:
    """Scrape robot product page and extract text content."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ReadyForRobotsCrawler/1.0)"}
        resp = requests.get(url, headers=headers, timeout=(3, 5))
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text[:5000]
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


def analyze_robot_capabilities(robot_name: str, page_text: str) -> Dict[str, Any]:
    """
    Extract robot capabilities from scraped text (keyword matcher used by match-url).
    """
    text_lower = f"{robot_name or ''} {page_text or ''}".lower()

    robot_type = "Unknown"
    if any(kw in text_lower for kw in ["construction", "jobsite", "drywall", "rebar", "concrete", "framing"]):
        robot_type = "Construction Robot"
    elif any(kw in text_lower for kw in ["delivery", "transport", "courier", "cart"]):
        robot_type = "Delivery/Transport"
    elif any(kw in text_lower for kw in ["disinfect", "uv", "sanitize", "clean"]):
        robot_type = "Disinfection/Cleaning"
    elif any(kw in text_lower for kw in ["service", "serve", "hospitality", "restaurant"]):
        robot_type = "Service Robot"
    elif any(kw in text_lower for kw in ["warehouse", "amr", "agv", "logistics", "picking"]):
        robot_type = "Warehouse/Logistics"
    elif any(kw in text_lower for kw in ["surgery", "patient", "medical", "healthcare"]):
        robot_type = "Medical/Healthcare"

    # Detect use case — only assign specific use case if robot serves primarily ONE industry
    # If robot lists multiple industries (3+), keep as "General Automation"
    use_case = "General Automation"
    
    # Count how many industry keywords are present
    industry_matches = []
    if "hotel" in text_lower or "hospitality" in text_lower:
        industry_matches.append("hospitality")
    if re.search(r"\bhospitals?\b|\bhealthcare\b|\bmedical\b|\bclinic\b|\bpatient\b|\bpharma\b", text_lower):
        industry_matches.append("healthcare")
    if "warehouse" in text_lower or "distribution" in text_lower or "fulfillment" in text_lower:
        industry_matches.append("warehouse")
    if "restaurant" in text_lower or "food service" in text_lower:
        industry_matches.append("food_service")
    if "retail" in text_lower or "e-commerce" in text_lower or "grocery" in text_lower:
        industry_matches.append("retail")
    if re.search(r"\b3pl\b", text_lower) or "logistics" in text_lower:
        industry_matches.append("logistics")
    if "industrial" in text_lower or "manufacturing" in text_lower or "factory" in text_lower:
        industry_matches.append("industrial")
    if "construction" in text_lower or "jobsite" in text_lower or "building site" in text_lower:
        industry_matches.append("construction")
    
    # Only assign specific use case if robot primarily serves 1-2 industries
    # If 3+ industries mentioned, it's a multi-industry platform → keep "General Automation"
    if len(industry_matches) <= 2:
        if "construction" in industry_matches:
            use_case = "Construction Operations"
        elif "hospitality" in industry_matches:
            use_case = "Hospitality Services"
        elif "healthcare" in industry_matches:
            use_case = "Healthcare Operations"
        elif "warehouse" in industry_matches:
            use_case = "Warehouse Logistics"
        elif "food_service" in industry_matches:
            use_case = "Food Service"
    # else: 3+ industries → remains "General Automation"

    capabilities = []
    capability_keywords = {
        "autonomous navigation": ["autonomous", "navigation", "lidar", "mapping"],
        "payload delivery": ["payload", "delivery", "transport", "carry"],
        "UV disinfection": ["uv", "disinfect", "sanitize"],
        "temperature control": ["temperature", "refrigerat", "heated"],
        "multi-floor": ["elevator", "multi-floor", "multiple floors"],
        "human interaction": ["touchscreen", "voice", "interface", "interact"],
        "cloud connected": ["cloud", "fleet", "dashboard", "analytics"],
        "HIPAA compliant": ["hipaa", "compliant", "secure"],
    }

    for cap, keywords in capability_keywords.items():
        if any(kw in text_lower for kw in keywords):
            capabilities.append(cap)

    return {
        "type": robot_type,
        "use_case": use_case,
        "capabilities": capabilities,
        "profile_score": min(
            100,
            35
            + (15 if robot_type != "Unknown" else 0)
            + (10 if use_case != "General Automation" else 0)
            + min(40, len(capabilities) * 8),
        ),
    }
