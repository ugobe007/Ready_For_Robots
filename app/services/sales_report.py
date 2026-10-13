"""Sales-ready robot job opportunity report.

Generates clean, structured reports matching the PDF format:
- RFP Open section (budget confirmed)
- Exploring section (active pipeline)
- Per-company cards with:
  * Primary job (1-2 workflows)
  * Robot types (sales-friendly names)
  * Timeline + Budget + incumbent
  * Evidence quotes with dates
  * Likely Next (cross-sell workflows)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from app.services.opportunity_map import CATEGORIES, build_map


# ─── Robot Type Mapping (sales-friendly names) ───────────────────────────────

ROBOT_TYPES: dict[str, str] = {
    "cleaning": "Floor cleaning robots",
    "restroom_sanitizing": "Sanitizing robots",
    "delivery_service": "Delivery and serving robots",
    "food_prep": "Kitchen and food-prep robots",
    "entertainment": "Entertainment robots",
    "concierge": "Concierge robots",
    "security": "Security robots",
    "warehouse_amr": "Warehouse AMRs",
    "palletizing": "Palletizing robots",
    "forklift": "Autonomous forklifts",
    "inventory": "Inventory robots",
    "laundry": "Laundry robots",
    "manufacturing": "Cobots and industrial robots",
    "healthcare_logistics": "Hospital logistics robots",
    "outdoor": "Outdoor robots",
    "last_mile": "Delivery robots",
    "humanoid": "Humanoid robots",
}


# ─── Budget Extraction ────────────────────────────────────────────────────────

_BUDGET_RE = re.compile(
    r"(?:invest(?:ing|s|ed|ment)?|commit(?:ting|s|ted)?|spend(?:ing|s)?|approv(?:es|ed|ing)?|"
    r"budget(?:ing|ed)?|allocat(?:es|ed|ing)?|capital|deploy(?:ing|ment)?)\s+"
    r"(?:of\s+)?(?:over\s+|up\s+to\s+|more\s+than\s+|approximately\s+|about\s+|~\s*)?"
    r"((?:USD|EUR|GBP|CHF|CAD)?\s*[\$€£¥]\s*\d+(?:[.,]\d+)*(?:\s*[BMK])?|"
    r"(?:USD|EUR|GBP|CHF|CAD)\s+\d+(?:[.,]\d+)*(?:\s*[BMK])?|"
    r"\d+(?:[.,]\d+)*\s*(?:million|billion|thousand|[BMK]))\b",
    re.I,
)

_VENDOR_RE = re.compile(
    r"\b(?:incumbent|vendor|supplier|partner|provider|using|deploying|with|from)[:\s]+([A-Z][A-Za-z0-9\s&-]+(?:\s+(?:Robotics|Technologies|Inc|LLC|Corp|Corporation|Systems))?)\b"
)


def extract_budget(text: str) -> Optional[str]:
    """Extract budget amount from evidence text. Returns normalized string like '$60.0M' or None."""
    match = _BUDGET_RE.search(text)
    if not match:
        return None
    
    amount_str = match.group(1).replace(",", "").replace(" ", "")
    
    # Normalize to $X.XM or $X.XB format
    currency = "$"
    if "€" in amount_str or "EUR" in amount_str.upper():
        currency = "€"
        amount_str = amount_str.replace("€", "").replace("EUR", "").replace("eur", "")
    elif "£" in amount_str or "GBP" in amount_str.upper():
        currency = "£"
        amount_str = amount_str.replace("£", "").replace("GBP", "").replace("gbp", "")
    elif "CHF" in amount_str.upper():
        currency = "CHF"
        amount_str = amount_str.replace("CHF", "").replace("chf", "")
    elif "CAD" in amount_str.upper():
        currency = "CAD"
        amount_str = amount_str.replace("CAD", "").replace("cad", "")
    elif "¥" in amount_str:
        currency = "¥"
        amount_str = amount_str.replace("¥", "")
    else:
        amount_str = amount_str.replace("$", "").replace("USD", "").replace("usd", "")
    
    # Extract number and unit
    num_match = re.match(r"([\d.]+)([BMK]?)", amount_str, re.I)
    if not num_match:
        return None
    
    try:
        value = float(num_match.group(1))
    except ValueError:
        return None
    unit = num_match.group(2).upper() or ""
    
    # Check for "million" or "billion" words if no unit suffix
    if not unit:
        if "million" in text.lower()[match.start():match.end()+20]:
            unit = "M"
        elif "billion" in text.lower()[match.start():match.end()+20]:
            unit = "B"
        elif "thousand" in text.lower()[match.start():match.end()+20]:
            unit = "K"
        else:
            # No unit and no keyword: assume raw dollars, not millions
            if value >= 1000000:
                value = value / 1000000
                unit = "M"
            elif value >= 1000:
                value = value / 1000
                unit = "K"
            else:
                return None  # Too small to be meaningful
    
    # Normalize
    if unit == "K":
        if value >= 1000:
            value = value / 1000
            unit = "M"
    elif unit == "M":
        if value >= 1000:
            value = value / 1000
            unit = "B"
    
    return f"{currency}{value:.1f}{unit}"


def extract_vendor(text: str) -> Optional[str]:
    """Extract incumbent vendor name from evidence text."""
    match = _VENDOR_RE.search(text)
    if match:
        vendor = match.group(1).strip()
        # Clean up common trailing noise words
        vendor = re.sub(r"\s+(robots?|systems?|solutions?|products?|platforms?|automation)$", "", vendor, flags=re.I)
        # Clean up common false positives
        if len(vendor) < 3 or vendor.lower() in ("the", "its", "our", "their", "this"):
            return None
        return vendor
    return None


# ─── Timeline Estimation ──────────────────────────────────────────────────────

def estimate_timeline(stage: str, signals: list[dict[str, Any]]) -> str:
    """Estimate timeline based on stage and signal dates.
    
    Returns strings like:
    - "Capital program phase (est. 90–210 days)"
    - "Q3 2025"
    - "in 2026"
    - "High-intent window (est. 45–120 days)"
    """
    # Check for explicit timeline mentions in evidence
    for sig in signals:
        text = sig.get("signal_text", "")
        
        # Quarter mentions
        quarter_match = re.search(r"\b(Q[1-4])\s+(20\d{2})\b", text, re.I)
        if quarter_match:
            return f"{quarter_match.group(1)} {quarter_match.group(2)}"
        
        # Year mentions
        year_match = re.search(r"\bin\s+(20\d{2})\b", text, re.I)
        if year_match:
            return f"in {year_match.group(1)}"
        
        # Month-Year mentions
        month_match = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})\b", text, re.I)
        if month_match:
            return f"{month_match.group(1)} {month_match.group(2)}"
    
    # Default timeline by stage
    if stage == "rfp":
        return "High-intent window (est. 45–120 days)"
    elif stage in ("exploring", "piloting"):
        return "Capital program phase (est. 90–210 days)"
    elif stage == "expanding":
        return "Expansion window (est. 60–180 days)"
    else:
        return "Capital program phase (est. 90–210 days)"


# ─── Job Opportunity Card ─────────────────────────────────────────────────────

@dataclass
class JobOpportunity:
    """One sales-ready robot job opportunity card."""
    
    rank: int
    company_name: str
    industry: str
    city: str
    state_country: str
    
    # Primary opportunity
    job_workflows: list[str]                    # 1-2 main workflows
    robot_types: list[str]                      # Sales-friendly robot type names
    
    # Sales intelligence
    timeline: str                               # "Q3 2025", "Capital program phase (est. 90–210 days)"
    has_robots: str                             # "Yes — Floor & surface cleaning" or "No"
    budget: Optional[str] = None                # "$60.0M", "$1.9B"
    status: Optional[str] = None                # "RFP (incumbent: Locus)"
    
    # Evidence
    evidence_quotes: list[tuple[str, str]] = field(default_factory=list)  # [(text, date), ...]
    
    # Cross-sell
    likely_next: list[str] = field(default_factory=list)
    
    # Contact
    website: Optional[str] = None


def build_job_opportunity(
    rank: int,
    company: Any,
    readiness: Any,
    signals: list[dict[str, Any]],
) -> JobOpportunity:
    """Build a sales-ready job opportunity card from buyer readiness data."""
    
    # Get opportunity map (per-workflow status)
    opp_map = build_map(
        signals,
        industry=company.industry or "",
        company_name=company.name,
    )
    
    # Find primary open workflows (rfp > expanding > exploring > piloting)
    open_workflows = [
        (cat, opp)
        for cat, opp in opp_map.items()
        if opp.status in ("rfp", "expanding", "exploring", "piloting")
    ]
    
    # Sort by status priority
    status_priority = {"rfp": 1, "expanding": 2, "exploring": 3, "piloting": 4}
    open_workflows.sort(key=lambda x: (status_priority.get(x[1].status, 9), -x[1].score))
    
    # Take top 1-2 workflows
    primary_workflows = open_workflows[:2]
    job_workflows = [CATEGORIES[cat][0] for cat, _ in primary_workflows]
    robot_types = [ROBOT_TYPES.get(cat, CATEGORIES[cat][0]) for cat, _ in primary_workflows]
    
    # Check what robots they already have
    deployed_workflows = [
        CATEGORIES[cat][0]
        for cat, opp in opp_map.items()
        if opp.status == "deployed"
    ]
    
    if deployed_workflows:
        has_robots = f"Yes — {'; '.join(deployed_workflows[:2])}"
        if len(deployed_workflows) > 2:
            has_robots += f" (+{len(deployed_workflows) - 2} more)"
    else:
        has_robots = "No"
    
    # Extract budget and vendor from evidence and opportunity map
    budget = None
    vendors = []
    
    # Get vendors from opportunity map first (already curated)
    for cat, opp in primary_workflows:
        vendors.extend(v for v in opp.vendors if v not in vendors)
    
    # Then extract from evidence text
    for ev in readiness.evidence[:5]:
        if not budget:
            budget = extract_budget(ev.text)
        vendor = extract_vendor(ev.text)
        if vendor and vendor not in vendors:
            vendors.append(vendor)
    
    # Build status line
    status = None
    if primary_workflows:
        top_status = primary_workflows[0][1].status
        if top_status == "rfp":
            status = "RFP"
        elif top_status in ("exploring", "piloting"):
            status = "Exploring"
        elif top_status == "expanding":
            status = "Expanding"
        
        if status and vendors:
            status += f" (incumbent: {vendors[0]})"
    
    # Extract evidence quotes with dates
    evidence_quotes = []
    for ev in readiness.evidence[:3]:
        # Use seen_at if available, otherwise try to extract from URL or text
        date = ev.seen_at if hasattr(ev, 'seen_at') and ev.seen_at else ""
        if not date:
            date = extract_date_from_evidence(ev.source_url or "", ev.text)
        evidence_quotes.append((ev.text, date))
    
    # Timeline
    timeline = estimate_timeline(
        primary_workflows[0][1].status if primary_workflows else "exploring",
        signals,
    )
    
    # Likely next (predicted high-confidence workflows not yet open)
    predicted_workflows = [
        (cat, opp)
        for cat, opp in opp_map.items()
        if opp.status == "predicted" and opp.score >= 60.0
    ]
    predicted_workflows.sort(key=lambda x: -x[1].score)
    likely_next = [CATEGORIES[cat][0] for cat, _ in predicted_workflows[:4]]
    
    return JobOpportunity(
        rank=rank,
        company_name=company.name,
        industry=company.industry or "Unknown",
        city=company.location_city or "",
        state_country=company.location_state or "",
        job_workflows=job_workflows,
        robot_types=robot_types,
        timeline=timeline,
        has_robots=has_robots,
        budget=budget,
        status=status,
        evidence_quotes=evidence_quotes,
        likely_next=likely_next,
        website=company.website,
    )


def extract_date_from_evidence(url: str, text: str) -> str:
    """Extract date from evidence URL or text. Returns YYYY-MM-DD or empty string."""
    # Try URL first (common pattern: /2026/08/15/ or /2026-08-15/)
    date_match = re.search(r"/(\d{4})[/-](\d{1,2})[/-](\d{1,2})", url)
    if date_match:
        year, month, day = date_match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Try text (patterns like "August 15, 2026" or "2026-08-15")
    date_match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if date_match:
        year, month, day = date_match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Try "Month DD, YYYY"
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    month_match = re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})\b",
        text.lower(),
    )
    if month_match:
        month_name, day, year = month_match.groups()
        month = month_map[month_name]
        return f"{year}-{month}-{day.zfill(2)}"
    
    return ""


# ─── Report Formatting ────────────────────────────────────────────────────────

def format_job_opportunity_text(opp: JobOpportunity) -> str:
    """Format a job opportunity card as plain text matching the PDF format."""
    
    lines = []
    
    # Header: rank, company, industry, location
    lines.append(f"{opp.rank:03d}  {opp.company_name}")
    location = f"{opp.city}, {opp.state_country}" if opp.city and opp.state_country else (opp.city or opp.state_country or "")
    if location:
        lines.append(f"{opp.industry} · {location}")
    else:
        lines.append(f"{opp.industry}")
    
    # Job workflows
    if opp.job_workflows:
        lines.append(f"Job: {'; '.join(opp.job_workflows)}")
    
    # Robot types
    if opp.robot_types:
        lines.append(f"Robot Types: {'; '.join(opp.robot_types)}")
    
    # Sales intelligence line
    intel_parts = []
    if opp.timeline:
        intel_parts.append(f"Schedule: {opp.timeline}")
    intel_parts.append(f"Has Robots: {opp.has_robots}")
    if opp.budget:
        intel_parts.append(f"Budget: {opp.budget}")
    
    if intel_parts:
        lines.append(" | ".join(intel_parts))
    
    # Status line
    if opp.status:
        lines.append(f"Status: {opp.status}")
    
    # Evidence quotes
    for quote, date in opp.evidence_quotes:
        date_str = f" ({date})" if date else ""
        lines.append(f'"{quote}"{date_str}')
    
    # Likely next
    if opp.likely_next:
        lines.append(f"Likely Next: {', '.join(opp.likely_next)}")
    
    return "\n".join(lines)


def format_sales_report_text(opportunities: list[JobOpportunity]) -> str:
    """Format full sales report as plain text matching the PDF format."""
    
    lines = []
    lines.append("Robot Buyer Intelligence Report")
    lines.append("")
    
    # Group by stage
    rfp_open = [o for o in opportunities if o.status and o.status.startswith("RFP")]
    exploring = [o for o in opportunities if o.status and o.status.startswith("Exploring")]
    expanding = [o for o in opportunities if o.status and o.status.startswith("Expanding")]
    other = [o for o in opportunities if not o.status or o.status not in (
        "RFP", "Exploring", "Expanding",
    ) and not o.status.startswith(("RFP", "Exploring", "Expanding"))]
    
    # RFP Open section
    if rfp_open:
        lines.append("RFP Open — Published RFP / Vendor Search, Budget Confirmed")
        lines.append("")
        for opp in rfp_open:
            lines.append(format_job_opportunity_text(opp))
            lines.append("")
    
    # Exploring section
    if exploring or expanding or other:
        lines.append("Exploring — Planning, Budgeting or Piloting, No Vendor Locked In")
        lines.append("")
        for opp in exploring + expanding + other:
            lines.append(format_job_opportunity_text(opp))
            lines.append("")
    
    return "\n".join(lines)
