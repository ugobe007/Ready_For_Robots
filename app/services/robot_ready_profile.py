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
    if any(kw in text_lower for kw in ["delivery", "transport", "courier", "cart"]):
        robot_type = "Delivery/Transport"
    elif any(kw in text_lower for kw in ["disinfect", "uv", "sanitize", "clean"]):
        robot_type = "Disinfection/Cleaning"
    elif any(kw in text_lower for kw in ["service", "serve", "hospitality", "restaurant"]):
        robot_type = "Service Robot"
    elif any(kw in text_lower for kw in ["warehouse", "amr", "agv", "logistics", "picking"]):
        robot_type = "Warehouse/Logistics"
    elif any(kw in text_lower for kw in ["surgery", "patient", "medical", "healthcare"]):
        robot_type = "Medical/Healthcare"

    use_case = "General Automation"
    if "hotel" in text_lower or "hospitality" in text_lower:
        use_case = "Hospitality Services"
    elif re.search(r"\bhospitals?\b|\bhealthcare\b|\bmedical\b|\bclinic\b|\bpatient\b", text_lower):
        use_case = "Healthcare Operations"
    elif "warehouse" in text_lower or "distribution" in text_lower:
        use_case = "Warehouse Logistics"
    elif "restaurant" in text_lower or "food service" in text_lower:
        use_case = "Food Service"

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
