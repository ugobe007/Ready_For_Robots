"""
Intelligence Search API
=======================
GET /api/search           — keyword + category full-text search across signals & companies
GET /api/search/categories — list available preset categories

Query params:
  q         str    free-text query (matched against signal text & company name)
  category  str    preset category key (see CATEGORY_KEYWORDS below)
  limit     int    default 30  (max 100)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional, List

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal

router = APIRouter()

# ---------------------------------------------------------------------------
# Category → keyword seeds  (case-insensitive ILIKE on signal_text)
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS: dict = {
    "automation_investment": [
        # funding events & deal types
        "Series A", "Series B", "Series C", "Series D", "seed round",
        "funding round", "raise capital", "venture capital", "VC-backed",
        "private equity", "PE investment", "growth equity", "strategic investment",
        "joint venture", "technology partnership", "R&D investment",
        # government & institutional
        "government grant", "DoD contract", "DARPA", "NSF award", "SBIR",
        "STTR", "federal grant", "IRA incentive", "DOE grant", "stimulus",
        "state grant", "workforce development grant",
        # corporate commitment signals
        "capex automation", "automation budget", "capital allocation",
        "capex approval", "technology roadmap", "digital transformation",
        "innovation hub", "center of excellence", "proof of concept",
        "pilot program", "automation initiative", "robotics program",
        "smart factory", "Industry 4.0", "warehouse of the future",
        # academic & startup ecosystem
        "university spin-out", "research commercialize", "startup partner",
        "accelerator", "incubator", "deep tech", "autonomous systems",
    ],
    "acquisitions": [
        # deal language
        "acqui", "merger", "buyout", "M&A", "acquired by", "acquires",
        "merger agreement", "definitive agreement", "letter of intent",
        "stock purchase", "asset purchase", "all-cash deal", "enterprise value",
        # strategic buyer language
        "strategic buyer", "bolt-on", "tuck-in", "synergies", "integration",
        "post-merger", "due diligence", "deal close", "close the transaction",
        # divestitures & exits
        "divestiture", "spin-off", "carve-out", "divests", "sells off",
        "strategic alternatives", "explore options",
        # industry-specific
        "takes over", "fold into", "absorb", "roll-up", "platform company",
        "consolidation", "vertical integration",
    ],
    "labor_downsizing": [
        # workforce reduction
        "layoff", "lay-off", "downsize", "reduction in force", "RIF",
        "job cuts", "headcount reduction", "workforce reduction", "furlough",
        "restructuring charge", "headcount freeze", "hiring freeze",
        # labor cost & shortage signals — strongest automation buyers
        "labor shortage", "can't find enough workers", "chronically understaffed",
        "high turnover", "vacancy rate", "open positions unfilled",
        "wage inflation", "labor cost rising", "overtime costs",
        "absenteeism", "attrition", "staffing crisis", "temp agency",
        "gig workers", "shift coverage", "scheduling gaps",
        "labor arbitrage", "reduce dependency on labor",
    ],
    "intra_logistics": [
        # core automation technologies
        "AGV", "AMR", "autonomous mobile robot", "autonomous guided vehicle",
        "goods-to-person", "goods to person", "person-to-goods",
        "conveyor system", "sortation", "pick-to-light", "put-to-light",
        "automated storage retrieval", "ASRS", "cube storage", "shuttle system",
        "vertical carousel", "horizontal carousel", "unit load",
        # operations & facility
        "intralogistic", "warehouse automation", "fulfillment center",
        "distribution center", "DC operations", "cross-dock", "cross-docking",
        "pallet", "depalletiz", "palletizing", "truck unload",
        "order picking", "each picking", "case picking", "batch picking",
        "zone routing", "put wall", "pick and place", "dock scheduling",
        "shipping dock", "loading dock", "tote conveyance", "bin management",
        # collaborative & mobile robotics
        "collaborative robot", "cobot", "robot arm", "floor bot",
        "fleet management", "autonomous forklift", "tugger", "cart",
    ],
    "pack_work": [
        # packaging operations
        "pack out", "pack-out", "packout", "packing line", "packaging line",
        "case packing", "end-of-line packaging", "secondary packaging",
        "tray packing", "blister pack", "shrink wrap", "flow wrap",
        "box erection", "case erect", "bundle packaging",
        # co-packing and contract
        "co-pack", "co-packer", "contract packaging", "toll packaging",
        "pick and pack", "pick & pack", "pack station", "pack bench",
        # retail-ready
        "display build", "club pack", "multi-pack", "gift pack",
        "retail ready packaging", "shelf-ready packaging",
        "flexible packaging", "pouch fill seal", "form fill seal",
    ],
    "kitting": [
        # kitting operations
        "kitting", "kit assembly", "kit fulfillment", "kit build",
        "parts kitting", "component kitting", "kit consolidation",
        "kit verification", "kit build to order", "kit room",
        # assembly
        "sub-assembly", "subassembly", "light assembly", "value-added assembly",
        "production kitting", "manufacturing kitting", "work in process",
        # medical & surgical
        "surgical kit", "medical kit", "procedure tray", "instrument tray",
        "case cart", "sterile kit", "OR kit",
        # materials management
        "bill of materials", "BOM", "postponement", "build to order",
        "configure to order", "materials management", "line-side delivery",
    ],
    "restocking": [
        # shelf & store replenishment
        "restock", "shelf replenishment", "shelf management", "facing",
        "store replenishment", "auto-replenishment", "auto-fill",
        "floor replenishment", "dc replenishment",
        # lean & pull systems
        "kanban", "min/max", "safety stock", "reorder point",
        "continuous replenishment", "flow-through", "milk run",
        "pull system", "two-bin system", "bin refill",
        # vendor-managed
        "VMI", "vendor managed inventory", "supplier-managed inventory",
        "consignment", "slotting", "put-away", "slot optimization",
        "cycle count", "inventory refresh",
    ],
    "inventory_management": [
        # systems & platforms
        "WMS", "warehouse management system", "ERP integration",
        "inventory platform", "stock management", "supply chain visibility",
        "inventory visibility", "real-time tracking", "asset tracking",
        "RFID", "barcode scan", "serialization", "lot tracking",
        # accuracy & audit
        "stock accuracy", "inventory accuracy", "cycle counting",
        "physical inventory", "blind count", "warehouse audit",
        "shrinkage", "inventory variance", "stock-out", "out-of-stock",
        "fill rate", "order fulfillment rate", "dead stock", "overstock",
        # data & analytics
        "SKU proliferation", "SKU rationalization", "demand sensing",
        "inventory optimization", "ABC analysis", "velocity slotting",
        "returns processing", "reverse logistics", "disposition",
    ],
    "healthcare_automation": [
        # hospital & health system
        "health system", "health care", "hospital operations",
        "medical center", "integrated delivery network",
        # pharmacy & medication
        "pharmacy automation", "automated dispensing cabinet", "ADC",
        "medication dispensing", "pharmacy robot", "unit-dose packaging",
        "pyxis", "omnicell", "340B",
        # supply chain & logistics
        "hospital supply chain", "OR supply", "procedural supply",
        "central supply", "floor stock", "medical-surgical supply",
        "SPD", "sterile processing", "instrument reprocessing", "CSSD",
        "case cart", "OR scheduling",
        # patient & room services
        "patient transport", "room service model", "dietary deliveries",
        "tray delivery", "room tray", "nurse call",
        # environmental services
        "EVS", "environmental services", "housekeeping robot",
        "floor cleaning", "disinfection robot", "UV disinfection",
        "linen management", "soiled linen",
        # workforce
        "nursing shortage", "clinical staffing", "care delivery",
        "patient-to-nurse ratio", "caregiver burnout",
    ],
    "retail_automation": [
        # grocery & food retail
        "grocery automation", "supermarket", "convenience store",
        "food retail", "grocery chain", "hypermarket",
        # fulfillment models
        "micro-fulfillment", "dark store", "store fulfillment",
        "BOPIS", "buy online pickup in store", "curbside pickup",
        "click and collect", "last-mile fulfillment", "endless aisle",
        "ship from store", "omnichannel fulfillment",
        # in-store automation
        "in-store robot", "store robot", "shelf scanning robot",
        "autonomous checkout", "scan-and-go", "frictionless checkout",
        "store associate reduction", "labor model store",
        # compliance & planogram
        "planogram compliance", "out-of-stock detection",
        "price verification", "inventory drone", "shelf audit",
        "store automation", "front-end automation",
        # supply chain for retail
        "store replenishment", "back-of-store", "backroom",
        "store-level inventory", "retail distribution",
    ],
}

CATEGORY_LABELS: dict = {
    "automation_investment": "Automation Investments",
    "acquisitions":          "Acquisitions & M&A",
    "labor_downsizing":      "Labor Downsizing",
    "intra_logistics":       "Intra-Logistics",
    "pack_work":             "Pack In / Pack Out",
    "kitting":               "Kitting & Assembly",
    "restocking":            "Restocking",
    "inventory_management":  "Inventory Management",
    "healthcare_automation": "Healthcare Automation",
    "retail_automation":     "Retail Automation",
}


def _run_keyword_search(
    db: Session,
    keywords: List[str],
    free_text: Optional[str],
    limit: int,
) -> list:
    """ILIKE match signals (and company names) for given keywords / free-text."""

    # --- signal-text matching ---
    conditions = [Signal.signal_text.ilike(f"%{kw}%") for kw in keywords]
    if free_text and free_text.strip():
        conditions.append(Signal.signal_text.ilike(f"%{free_text.strip()}%"))

    company_signals: dict = {}  # company_id → list of matched signal dicts
    company_match_source: dict = {}  # company_id → "signal" | "name"

    if conditions:
        rows = (
            db.query(
                Signal.company_id,
                Signal.signal_text,
                Signal.signal_type,
                Signal.signal_strength,
            )
            .filter(or_(*conditions))
            .all()
        )
        for row in rows:
            company_signals.setdefault(row.company_id, []).append(
                {
                    "signal_type": row.signal_type,
                    "signal_text": row.signal_text,
                    "strength": round(float(row.signal_strength), 3),
                }
            )
            company_match_source[row.company_id] = "signal"

    # --- company-name matching (always, for any input) ---
    if free_text and free_text.strip():
        name_rows = (
            db.query(Company.id)
            .filter(Company.name.ilike(f"%{free_text.strip()}%"))
            .all()
        )
        for (cid,) in name_rows:
            company_signals.setdefault(cid, [])
            if cid not in company_match_source:
                company_match_source[cid] = "name"

    # also match company names against free keywords (non-trivial terms only)
    long_kw = [kw for kw in keywords if len(kw) > 4]
    if long_kw:
        for kw in long_kw:
            kw_rows = (
                db.query(Company.id)
                .filter(Company.name.ilike(f"%{kw}%"))
                .all()
            )
            for (cid,) in kw_rows:
                company_signals.setdefault(cid, [])
                if cid not in company_match_source:
                    company_match_source[cid] = "name"

    if not company_signals:
        return []

    companies = (
        db.query(Company)
        .options(joinedload(Company.scores))
        .filter(Company.id.in_(list(company_signals.keys())))
        .all()
    )

    results = []
    for c in companies:
        score = round(float(c.scores.overall_intent_score), 1) if c.scores else 0.0
        matched = sorted(
            company_signals.get(c.id, []),
            key=lambda x: x["strength"],
            reverse=True,
        )
        results.append(
            {
                "id": c.id,
                "company_name": c.name,
                "industry": c.industry,
                "location_city": c.location_city,
                "location_state": c.location_state,
                "website": c.website,
                "employee_estimate": c.employee_estimate,
                "overall_score": score,
                "matched_signals": matched[:5],
                "match_source": company_match_source.get(c.id, "signal"),
            }
        )

    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results[:limit]


@router.get("")
@router.get("/")
def search(
    q: Optional[str] = Query(None, description="Free-text query"),
    category: Optional[str] = Query(None, description="Preset category key"),
    limit: int = Query(30, le=100, description="Max results (hard cap 100)"),
    db: Session = Depends(get_db),
):
    """
    Full-text search across signal texts.
    Combine a preset category (keyword seed list) with optional free-text.
    """
    keywords: List[str] = []
    if category and category in CATEGORY_KEYWORDS:
        keywords = CATEGORY_KEYWORDS[category]

    results = _run_keyword_search(db, keywords, q, limit)

    return {
        "results": results,
        "total": len(results),
        "query": q,
        "category": category,
        "category_label": CATEGORY_LABELS.get(category) if category else None,
    }


@router.get("/categories")
def list_categories():
    """Return all available preset search categories."""
    return [{"key": k, "label": v} for k, v in CATEGORY_LABELS.items()]
