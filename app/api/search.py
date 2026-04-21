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
from __future__ import annotations

import re
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Dict, FrozenSet, List, Optional, Tuple

from app.database import get_db
from app.models.company import Company
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, pick_primary_score
from app.services.automation_profile import get_automation_profile_for_response
from app.services.industry_inference import effective_industry_for_lead
from app.services.lead_primary_link import enrich_lead_link_fields

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
    "expansion": [
        "expansion", "new facility", "new warehouse", "new distribution center",
        "breaking ground", "square feet", "sf facility", "construction",
        "groundbreaking", "opening", "development", "capacity expansion",
        "facility expansion", "geographic expansion", "new location",
        "new property", "new build", "capital expenditure", "capex",
    ],
    "strategic_hire": [
        "VP ", "SVP ", "COO", "Chief Operating", "Vice President",
        "Director of", "Head of", "appointed", "hired", "joins as",
        "new executive", "Chief ", "executive vice president", "EVP ",
    ],
}

CATEGORY_LABELS: dict = {
    "automation_investment": "Automation Investments",
    "acquisitions":          "Acquisitions & M&A",
    "labor_downsizing":      "Labor Downsizing",
    "expansion":             "Expansion / CapEx",
    "strategic_hire":        "Executive Hire",
    "intra_logistics":       "Intra-Logistics",
    "pack_work":             "Pack In / Pack Out",
    "kitting":               "Kitting & Assembly",
    "restocking":            "Restocking",
    "inventory_management":  "Inventory Management",
    "healthcare_automation": "Healthcare Automation",
    "retail_automation":     "Retail Automation",
}

# Frontend Quick Search keys → API category
CATEGORY_ALIASES: dict = {
    "funding": "automation_investment",
    "expansion": "expansion",
    "labor": "labor_downsizing",
    "exec": "strategic_hire",
    "ma": "acquisitions",
    "warehouse_logistics": "intra_logistics",
    "robot_automation": "automation_investment",
}

# When the user clearly asks for a vertical (e.g. "hotel"), we still ILIKE-match signal text,
# which can hit incidental mentions on high-scoring leads. Bucket sort pulls aligned industries
# ahead of obvious mismatches before applying overall_score.
#
# Order matters: first regex match wins. Put specific phrases (food processing, medtech)
# before broad ones (food service, hospitality).
_QUERY_VERTICAL_PATTERNS: Tuple[Tuple[re.Pattern, str], ...] = (
    (
        re.compile(
            r"\b(surgical\s+robot|lab\s+automation|medical\s+device|diagnostics\s+lab|"
            r"robotic\s+surgery|pharmacy\s+automation|medical\s+technology)\b",
            re.I,
        ),
        "Medical Technology",
    ),
    (
        re.compile(
            r"\b(hospital|hospitals|health\s*system|healthcare|health\s+care|clinic|clinics|"
            r"patient\s+care|senior\s+living|nursing\s+home|assisted\s+living|medical\s+center)\b",
            re.I,
        ),
        "Healthcare",
    ),
    (
        re.compile(
            r"\b(food\s+processing|meat\s+processing|food\s+plant|food\s+manufacturing|"
            r"poultry\s+processing|food\s+factory|slaughter|bottling\s+plant|brewery|brewing)\b",
            re.I,
        ),
        "Food Processing & Manufacturing",
    ),
    (
        re.compile(
            r"\b(restaurant|restaurants|qsr|fast\s+food|dining\s+chain|food\s+service|"
            r"cafe|chain\s+restaurant|franchise\s+restaurant)\b",
            re.I,
        ),
        "Food Service",
    ),
    (
        re.compile(
            r"\b(hotel|hotels|hospitality|resort|resorts|lodging|motel|motels|"
            r"housekeeping\s+staff|guest\s+services)\b",
            re.I,
        ),
        "Hospitality",
    ),
    (
        re.compile(
            r"\b(warehouse|warehouses|logistics|fulfillment\s+center|3pl|distribution\s+center|"
            r"supply\s+chain|cold\s+storage|cross-dock)\b",
            re.I,
        ),
        "Logistics",
    ),
    (
        re.compile(
            r"\b(retail|grocery|supermarket|e-commerce|ecommerce|micro-fulfillment|"
            r"planogram|BOPIS|click-and-collect|omnichannel|in-store\s+robot)\b",
            re.I,
        ),
        "Retail",
    ),
    (
        re.compile(
            r"\b(cpg|fmcg|consumer\s+packaged\s+goods|packaged\s+food\s+brand)\b",
            re.I,
        ),
        "CPG & Consumer Goods",
    ),
    (
        re.compile(
            r"\b(automotive|automaker|vehicle\s+manufacturer|assembly\s+line|"
            r"industrial\s+automation|semiconductor\s+fabrication|oem\s+production)\b",
            re.I,
        ),
        "Automotive & Manufacturing",
    ),
    (
        re.compile(
            r"\b(airport|airports|airline|airlines|aviation|baggage\s+handling|"
            r"boarding\s+gate|terminal\s+operations)\b",
            re.I,
        ),
        "Airports & Aviation",
    ),
    (
        re.compile(
            r"\b(datacenter|data\s+center|hyperscale|colocation|\bcolo\b|server\s+farm|"
            r"cloud\s+infrastructure)\b",
            re.I,
        ),
        "Datacenters",
    ),
    (
        re.compile(
            r"\b(casino|casinos|resort\s+casino|tribal\s+gaming|table\s+games)\b",
            re.I,
        ),
        "Casinos & Gaming",
    ),
    (
        re.compile(
            r"\b(cruise\s+ship|cruise\s+line|cruise\s+lines|onboard\s+operations)\b",
            re.I,
        ),
        "Cruise Lines",
    ),
    (
        re.compile(
            r"\b(theme\s+park|amusement\s+park|water\s+park|roller\s+coaster)\b",
            re.I,
        ),
        "Theme Parks & Entertainment",
    ),
    (
        re.compile(
            r"\b(facilities\s+management|janitorial|commercial\s+real\s+estate|"
            r"building\s+services|facility\s+services)\b",
            re.I,
        ),
        "Real Estate & Facilities",
    ),
    (
        re.compile(
            r"\b(contract\s+manufacturer|contract\s+manufacturing|toll\s+manufacturer|"
            r"toll\s+packaging|\bcmo\b|\bcdmo\b|white\s+label\s+manufacturing)\b",
            re.I,
        ),
        "Contract Manufacturing",
    ),
    (
        re.compile(
            r"\b(apparel|garment\s+factory|textile\s+mill|fashion\s+logistics|"
            r"fabric\s+cutting)\b",
            re.I,
        ),
        "Apparel & Textiles",
    ),
    (
        re.compile(
            r"\b(car\s+dealer|auto\s+dealer|automotive\s+retail|dealership)\b",
            re.I,
        ),
        "Automotive Dealerships",
    ),
    (
        re.compile(
            r"\b(commercial\s+laundry|linen\s+service|industrial\s+laundry|"
            r"uniform\s+cleaning)\b",
            re.I,
        ),
        "Laundry & Linen Services",
    ),
    (
        re.compile(
            r"\b(car\s+wash|carwash|tunnel\s+wash|express\s+wash)\b",
            re.I,
        ),
        "Car Wash",
    ),
)

# Keys = intent string from _QUERY_VERTICAL_PATTERNS (must match INDUSTRY_KEYWORDS / inference labels).
_MEDIA_DEMOTE: FrozenSet[str] = frozenset({"Media & Publishing"})

SEARCH_VERTICAL_RULES: Dict[str, Dict[str, object]] = {
    "Medical Technology": {
        "strong": frozenset({"Medical Technology"}),
        "adjacent": frozenset({"Healthcare"}),
        "demote": frozenset(
            {
                "Retail",
                "Hospitality",
                "Logistics",
                "Food Service",
                "Food Processing & Manufacturing",
                "CPG & Consumer Goods",
                "Casinos & Gaming",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("medical technology", "medtech", "diagnostic"),
    },
    "Healthcare": {
        "strong": frozenset({"Healthcare", "Medical Technology"}),
        "adjacent": frozenset({"Food Service"}),
        "demote": frozenset(
            {
                "Retail",
                "Logistics",
                "CPG & Consumer Goods",
                "Automotive & Manufacturing",
                "Hospitality",
                "Media & Publishing",
                "Airports & Aviation",
            }
        ),
        "raw_strong_substrings": (
            "hospital",
            "healthcare",
            "medical center",
            "clinic",
            "senior living",
            "nursing home",
            "health system",
        ),
    },
    "Food Processing & Manufacturing": {
        "strong": frozenset({"Food Processing & Manufacturing"}),
        "adjacent": frozenset({"CPG & Consumer Goods", "Contract Manufacturing", "Food Service"}),
        "demote": frozenset(
            {
                "Retail",
                "Hospitality",
                "Healthcare",
                "Logistics",
                "Datacenters",
                "Media & Publishing",
                "Airports & Aviation",
            }
        ),
        "raw_strong_substrings": ("food processing", "meat processing", "food plant"),
    },
    "Food Service": {
        "strong": frozenset({"Food Service"}),
        "adjacent": frozenset({"Hospitality", "Retail", "Food Processing & Manufacturing"}),
        "demote": frozenset(
            {
                "Logistics",
                "Medical Technology",
                "Datacenters",
                "Automotive & Manufacturing",
                "Media & Publishing",
                "Airports & Aviation",
            }
        ),
        "raw_strong_substrings": ("restaurant", "food service", "qsr"),
    },
    "Hospitality": {
        "strong": frozenset({"Hospitality"}),
        "adjacent": frozenset(
            {"Casinos & Gaming", "Cruise Lines", "Theme Parks & Entertainment", "Food Service"}
        ),
        "demote": frozenset(
            {
                "Retail",
                "Logistics",
                "CPG & Consumer Goods",
                "Apparel & Textiles",
                "Automotive & Manufacturing",
                "Medical Technology",
                "Healthcare",
                "Food Processing & Manufacturing",
                "Datacenters",
                "Media & Publishing",
                "Airports & Aviation",
            }
        ),
        "raw_strong_substrings": ("hospitality", "hotel", "resort", "lodging"),
    },
    "Logistics": {
        "strong": frozenset({"Logistics"}),
        "adjacent": frozenset({"Retail", "CPG & Consumer Goods", "Airports & Aviation", "Apparel & Textiles"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Healthcare",
                "Food Service",
                "Medical Technology",
                "Casinos & Gaming",
                "Media & Publishing",
                "Real Estate & Facilities",
            }
        ),
        "raw_strong_substrings": ("logistics", "warehouse", "fulfillment", "3pl"),
    },
    "Retail": {
        "strong": frozenset({"Retail", "Automotive Dealerships"}),
        "adjacent": frozenset({"CPG & Consumer Goods", "Logistics", "Food Service"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Healthcare",
                "Medical Technology",
                "Food Processing & Manufacturing",
                "Datacenters",
                "Casinos & Gaming",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("retail", "grocery", "supermarket", "e-commerce"),
    },
    "CPG & Consumer Goods": {
        "strong": frozenset({"CPG & Consumer Goods"}),
        "adjacent": frozenset({"Retail", "Food Processing & Manufacturing", "Logistics", "Contract Manufacturing"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Healthcare",
                "Medical Technology",
                "Airports & Aviation",
                "Casinos & Gaming",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("cpg", "consumer packaged", "fmcg"),
    },
    "Automotive & Manufacturing": {
        "strong": frozenset({"Automotive & Manufacturing"}),
        "adjacent": frozenset({"Contract Manufacturing", "Logistics", "Medical Technology"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Retail",
                "Food Service",
                "Healthcare",
                "Casinos & Gaming",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("automotive", "manufacturing", "assembly"),
    },
    "Airports & Aviation": {
        "strong": frozenset({"Airports & Aviation"}),
        "adjacent": frozenset({"Logistics", "Retail"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Healthcare",
                "Food Processing & Manufacturing",
                "Casinos & Gaming",
                "Media & Publishing",
                "Datacenters",
            }
        ),
        "raw_strong_substrings": ("airport", "aviation", "airline"),
    },
    "Datacenters": {
        "strong": frozenset({"Datacenters"}),
        "adjacent": frozenset({"Automotive & Manufacturing"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Retail",
                "Food Service",
                "Healthcare",
                "Logistics",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("datacenter", "data center", "hyperscale"),
    },
    "Casinos & Gaming": {
        "strong": frozenset({"Casinos & Gaming"}),
        "adjacent": frozenset({"Hospitality", "Retail"}),
        "demote": frozenset(
            {
                "Healthcare",
                "Medical Technology",
                "Logistics",
                "Datacenters",
                "Food Processing & Manufacturing",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("casino", "gaming"),
    },
    "Cruise Lines": {
        "strong": frozenset({"Cruise Lines"}),
        "adjacent": frozenset({"Hospitality", "Logistics"}),
        "demote": frozenset(
            {
                "Retail",
                "Healthcare",
                "Datacenters",
                "Automotive & Manufacturing",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("cruise",),
    },
    "Theme Parks & Entertainment": {
        "strong": frozenset({"Theme Parks & Entertainment"}),
        "adjacent": frozenset({"Hospitality", "Retail"}),
        "demote": frozenset(
            {
                "Healthcare",
                "Logistics",
                "Datacenters",
                "CPG & Consumer Goods",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("theme park", "amusement"),
    },
    "Real Estate & Facilities": {
        "strong": frozenset({"Real Estate & Facilities"}),
        "adjacent": frozenset({"Hospitality", "Logistics"}),
        "demote": frozenset(
            {
                "Retail",
                "Healthcare",
                "Medical Technology",
                "Food Processing & Manufacturing",
                "Casinos & Gaming",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("facilities management", "janitorial", "property management"),
    },
    "Contract Manufacturing": {
        "strong": frozenset({"Contract Manufacturing"}),
        "adjacent": frozenset({"CPG & Consumer Goods", "Food Processing & Manufacturing", "Medical Technology"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Retail",
                "Casinos & Gaming",
                "Media & Publishing",
                "Airports & Aviation",
            }
        ),
        "raw_strong_substrings": ("contract manufacturing", "contract manufacturer", "cmo", "cdmo"),
    },
    "Apparel & Textiles": {
        "strong": frozenset({"Apparel & Textiles"}),
        "adjacent": frozenset({"Retail", "Logistics"}),
        "demote": frozenset(
            {
                "Healthcare",
                "Datacenters",
                "Food Service",
                "Casinos & Gaming",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("apparel", "textile", "garment"),
    },
    "Automotive Dealerships": {
        "strong": frozenset({"Automotive Dealerships", "Retail"}),
        "adjacent": frozenset({"Automotive & Manufacturing"}),
        "demote": frozenset(
            {
                "Hospitality",
                "Healthcare",
                "Food Processing & Manufacturing",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("dealership", "auto dealer"),
    },
    "Laundry & Linen Services": {
        "strong": frozenset({"Laundry & Linen Services"}),
        "adjacent": frozenset({"Healthcare", "Hospitality", "Real Estate & Facilities"}),
        "demote": frozenset(
            {
                "Retail",
                "Datacenters",
                "Automotive & Manufacturing",
                "Media & Publishing",
                "Airports & Aviation",
            }
        ),
        "raw_strong_substrings": ("laundry", "linen"),
    },
    "Car Wash": {
        "strong": frozenset({"Car Wash"}),
        "adjacent": frozenset({"Retail", "Automotive Dealerships"}),
        "demote": frozenset(
            {
                "Healthcare",
                "Hospitality",
                "Datacenters",
                "Food Service",
                "Media & Publishing",
            }
        ),
        "raw_strong_substrings": ("car wash", "carwash"),
    },
}


def _detect_query_vertical(free_text: Optional[str], keywords: List[str]) -> Optional[str]:
    """If search text clearly targets one vertical, return canonical industry name."""
    blob = f" {free_text or ''} {' '.join(keywords)} "
    for rx, vertical in _QUERY_VERTICAL_PATTERNS:
        if rx.search(blob):
            return vertical
    return None


def _vertical_alignment_bucket(
    effective_industry: str,
    stored_industry: Optional[str],
    intent: Optional[str],
) -> int:
    """
    Higher = rank earlier (with reverse sort). Used only when intent is set.
    2 = strong match, 1 = adjacent vertical, 0 = unknown/neutral, -1 = likely off-topic.
    """
    if not intent:
        return 0
    eff = (effective_industry or "").strip()
    raw = (stored_industry or "").strip().lower()
    rules = SEARCH_VERTICAL_RULES.get(intent)
    if not rules:
        return 0

    strong: FrozenSet[str] = rules["strong"]  # type: ignore[assignment]
    adjacent: FrozenSet[str] = rules["adjacent"]  # type: ignore[assignment]
    demote: FrozenSet[str] = rules["demote"]  # type: ignore[assignment]
    raw_subs: Tuple[str, ...] = tuple(rules.get("raw_strong_substrings") or ())  # type: ignore[arg-type]

    if eff in strong:
        return 2
    for sub in raw_subs:
        if sub and sub in raw:
            return 2
    if eff in adjacent:
        return 1
    if eff in demote or eff in _MEDIA_DEMOTE:
        return -1
    return 0


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
        .options(joinedload(Company.scores), joinedload(Company.signals))
        .filter(Company.id.in_(list(company_signals.keys())))
        .all()
    )

    v_intent = _detect_query_vertical(free_text, keywords)
    results = []
    for c in companies:
        ps = pick_primary_score(c.scores)
        score = round(float(ps.overall_intent_score), 1) if ps else 0.0
        matched = sorted(
            company_signals.get(c.id, []),
            key=lambda x: x["strength"],
            reverse=True,
        )
        ind = effective_industry_for_lead(c.name, c.industry, c.signals)
        if not ind or ind.lower() in ("unknown", "other"):
            ind = "New"
        _, _, pri = classify_lead(c, c.scores, c.signals)
        raw_stored = (c.industry or "").strip()
        ov = ind if ind != raw_stored else None
        automation_profile = get_automation_profile_for_response(c, industry_override=ov)
        v_bucket = _vertical_alignment_bucket(ind, c.industry, v_intent)
        link_extras = enrich_lead_link_fields(
            website=c.website,
            signals=c.signals,
            overall_score=score,
            signal_count=len(c.signals or []),
        )
        results.append(
            {
                "id": c.id,
                "company_name": c.name,
                "industry": ind,
                "location_city": c.location_city,
                "location_state": c.location_state,
                "website": c.website,
                "employee_estimate": c.employee_estimate,
                "overall_score": score,
                "matched_signals": matched[:5],
                "match_source": company_match_source.get(c.id, "signal"),
                "priority_tier": pri.tier,
                "automation_profile": automation_profile,
                "_v_bucket": v_bucket,
                **link_extras,
            }
        )

    # Relevance: when the query implies a vertical, rank aligned industries before
    # high-scoring incidental matches (e.g. "hotel" mentioned in retail news).
    if v_intent:
        results.sort(key=lambda x: (x["_v_bucket"], x["overall_score"]), reverse=True)
    else:
        results.sort(key=lambda x: x["overall_score"], reverse=True)
    for r in results:
        r.pop("_v_bucket", None)
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
    resolved = CATEGORY_ALIASES.get(category, category) if category else None
    keywords: List[str] = []
    if resolved and resolved in CATEGORY_KEYWORDS:
        keywords = CATEGORY_KEYWORDS[resolved]

    results = _run_keyword_search(db, keywords, q, limit)

    return {
        "results": results,
        "total": len(results),
        "query": q,
        "category": resolved or category,
        "category_label": CATEGORY_LABELS.get(resolved or category) if (resolved or category) else None,
    }


@router.get("/categories")
def list_categories():
    """Return all available preset search categories."""
    return [{"key": k, "label": v} for k, v in CATEGORY_LABELS.items()]
