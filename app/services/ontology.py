"""
Robotics Domain Ontology
========================
Defines concepts, relationships, and weights for the robotics
buying-intent inference engine.

Structure:
  - CONCEPTS       : named nodes with synonyms, patterns, and base weight
  - RELATIONSHIPS  : edges between concepts (implication / association)
  - INDUSTRY_PRIORS: base robotics-fit score per industry vertical
  - INFERENCE_RULES: forward-chaining rules that fire when concept sets match
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple

# ──────────────────────────────────────────────
# 1. Concept Node
# ──────────────────────────────────────────────
@dataclass
class Concept:
    name: str                          # canonical name
    domain: str                        # e.g. "automation", "labor_pain", "expansion"
    base_weight: float                 # 0.0 – 1.0
    patterns: List[str] = field(default_factory=list)   # regex / substring patterns
    synonyms: List[str] = field(default_factory=list)   # surface-form aliases


# ──────────────────────────────────────────────
# 2. Relationship
# ──────────────────────────────────────────────
@dataclass
class Relationship:
    source: str     # concept name
    target: str     # concept name
    relation: str   # "implies" | "associated_with" | "contradicts"
    weight: float   # multiplier applied when source is active


# ──────────────────────────────────────────────
# 3. Inference Rule
# ──────────────────────────────────────────────
@dataclass
class InferenceRule:
    name: str
    conditions: List[str]          # concept names that must ALL be active
    conclusion_domain: str         # which score domain to boost
    boost: float                   # additive boost (0.0 – 1.0)
    description: str = ""


# ──────────────────────────────────────────────
# 4. Concept Definitions
# ──────────────────────────────────────────────
CONCEPTS: Dict[str, Concept] = {

    # ── Automation intents ──────────────────
    "warehouse_automation": Concept(
        name="warehouse_automation", domain="automation", base_weight=0.85,
        patterns=["warehouse automat", "automat.*warehouse", "fulfillment automat"],
        synonyms=["automated warehouse", "warehouse robotics", "dc automation"],
    ),
    "amr_agv": Concept(
        name="amr_agv", domain="automation", base_weight=0.90,
        patterns=[r"\bAMR\b", r"\bAGV\b", "autonomous mobile robot", "automated guided"],
        synonyms=["mobile robot", "guided vehicle", "autonomous cart"],
    ),
    "robotics_engineer": Concept(
        name="robotics_engineer", domain="automation", base_weight=0.80,
        patterns=["robotics engineer", "robot.*engineer", "automation engineer",
                  "robotic.*technician", "mechatronics"],
        synonyms=["robotics developer", "automation specialist"],
    ),
    "pick_place": Concept(
        name="pick_place", domain="automation", base_weight=0.75,
        patterns=["pick.and.place", "pick & place", "order pick", "goods.to.person"],
        synonyms=["picking robot", "palletizer", "depalletizer"],
    ),
    "wms_integration": Concept(
        name="wms_integration", domain="automation", base_weight=0.70,
        patterns=[r"\bWMS\b", "warehouse management system", "inventory management system",
                  r"\bERP\b.*integrat", "system integrat"],
        synonyms=["WMS", "inventory platform", "ERP integration"],
    ),
    "computer_vision": Concept(
        name="computer_vision", domain="automation", base_weight=0.72,
        patterns=["computer vision", "machine vision", "visual inspect",
                  "image recogni", "AI.*camera", "camera.*AI"],
        synonyms=["visual AI", "inspection AI"],
    ),
    "ai_operations": Concept(
        name="ai_operations", domain="automation", base_weight=0.68,
        patterns=["AI.*(operat|integrat|transfor)", "artificial intelligence.*operat",
                  "machine learning.*operat", "intelligent automat"],
        synonyms=["AI ops", "intelligent operations"],
    ),
    "service_robot": Concept(
        name="service_robot", domain="automation", base_weight=0.88,
        patterns=["service robot", "delivery robot", "cleaning robot",
                  "front.of.house robot", "robot.*hospitality", "robot.*server",
                  "robot.*bellhop", "autonomous.*delivery"],
        synonyms=["robot waiter", "robot butler", "hospitality robot"],
    ),
    "cobots": Concept(
        name="cobots", domain="automation", base_weight=0.75,
        patterns=[r"\bcobot\b", "collaborative robot", "human.robot.*collaborat"],
        synonyms=["cobot", "collaborative automation"],
    ),

    # ── Labor pain signals ──────────────────
    "labor_shortage": Concept(
        name="labor_shortage", domain="labor_pain", base_weight=0.85,
        patterns=[
            "labor shortage", "labour shortage",
            "staff.*short", "short.*staff",
            "worker.*short", "short.*worker",
            r"can.t find.*(worker|staff|people|employee)",
            r"find.*(enough|enough).*(worker|staff|people)",
            r"(worker|staff|employee|people).*(scarc|hard to find|difficult to find)",
            "hiring.*difficult", "difficult.*hiring", "trouble.*hiring",
            "can.t.*hire", "hard to hire", "unable to hire",
            "turnover.*high", "high.*turnover",
            "understaffed", "under.staffed",
            "staff.retention", "retention.*issue", "retention.*problem",
            "workforce.*challeng", "staffing.*challeng",
            "no.*staff", "not enough.*staff", "not enough.*worker",
            "vacancy", "unfilled.*position", "open.*position.*difficult",
        ],
        synonyms=["staffing crisis", "workforce shortage", "staff shortage",
                  "can't find workers", "can't find staff"],
    ),
    "high_turnover": Concept(
        name="high_turnover", domain="labor_pain", base_weight=0.78,
        patterns=[
            "high turnover", "employee.*turnover", "turnover.*rate",
            "retention.*problem", "retention.*challenge",
            "workforce.*instab", "attrition",
            "constant.*hiring", "always.*hiring", "revolving.*door",
        ],
        synonyms=["employee churn", "staff attrition", "high attrition"],
    ),
    "reduce_labor_costs": Concept(
        name="reduce_labor_costs", domain="labor_pain", base_weight=0.82,
        patterns=[
            "reduce.*labor cost", "lower.*labor cost", "cut.*labor",
            "labor.*efficien", "headcount.*reduc", "operational.*cost.*reduc",
            "save.*labor", "labor.*saving", "replace.*worker",
            "automat.*labor", "reduce.*headcount",
        ],
        synonyms=["cost reduction", "labor efficiency", "labor savings"],
    ),
    "operational_efficiency": Concept(
        name="operational_efficiency", domain="labor_pain", base_weight=0.65,
        patterns=[
            "operational efficien", "process efficien", "workflow optim",
            "productivity.*improv", "throughput.*increas",
            "streamlin", "faster.*operat", "improve.*efficiency",
        ],
        synonyms=["ops efficiency", "workflow improvement", "process optimization"],
    ),
    "modernization": Concept(
        name="modernization", domain="labor_pain", base_weight=0.60,
        patterns=["moderniz", "digital.transfor", "technology.*upgrad",
                  "innovat.*operat", "future.*proof"],
        synonyms=["digitization", "tech transformation"],
    ),

    # ── Expansion signals ──────────────────
    "warehouse_expansion": Concept(
        name="warehouse_expansion", domain="expansion", base_weight=0.80,
        patterns=[
            "warehouse.*expan", "expan.*warehouse",
            "expand.*warehouse", "warehouse.*expand",
            "new.*warehouse", "warehouse.*new",
            "distribution.*center.*new", "new.*distribution.*center",
            "fulfillment.*center.*open", "open.*fulfillment.*center",
            "expand.*facility", "facility.*expan",
            "sq.?ft.*warehouse", "warehouse.*sq.?ft",
            "new.*dc", r"\bdc\b.*open", "new.*fulfillment",
            "additional.*warehouse", "warehouse.*addition",
            "bigger.*warehouse", "larger.*facility",
        ],
        synonyms=["new DC", "new fulfillment center", "warehouse expansion",
                  "new warehouse", "expanding warehouse"],
    ),
    "hotel_expansion": Concept(
        name="hotel_expansion", domain="expansion", base_weight=0.78,
        patterns=["new.*hotel", "hotel.*open", "property.*expan",
                  "resort.*open", "opening.*location"],
        synonyms=["new property", "hotel opening"],
    ),
    "funding_announcement": Concept(
        name="funding_announcement", domain="expansion", base_weight=0.72,
        patterns=["series [a-z]", "funding round", "raised.*million",
                  "venture.*capital", "private equity", r"\$\d+[MB].*fund"],
        synonyms=["VC funding", "investment round"],
    ),
    "new_construction": Concept(
        name="new_construction", domain="expansion", base_weight=0.70,
        patterns=["breaking ground", "construction.*begin", "new.*facilit.*open",
                  "grand opening", "ribbon cutting"],
        synonyms=["facility opening", "groundbreaking"],
    ),
    "acquisition": Concept(
        name="acquisition", domain="expansion", base_weight=0.65,
        patterns=["acqui[rs]", "merger", "acqui.*company", "strategic.*acqui"],
        synonyms=["M&A", "buyout"],
    ),

    # ── Industry fit signals ────────────────
    "hospitality_vertical": Concept(
        name="hospitality_vertical", domain="industry_fit", base_weight=0.90,
        patterns=["hotel", "resort", "motel", "hospitality", "lodging",
                  "inn ", "bed and breakfast", r"\bBnB\b"],
        synonyms=["lodging", "accommodation"],
    ),
    "logistics_vertical": Concept(
        name="logistics_vertical", domain="industry_fit", base_weight=0.92,
        patterns=["logistic", "warehouse", "distribution", "fulfillment",
                  "supply chain", "freight", "3pl", "last.mile"],
        synonyms=["supply chain", "3PL", "distribution"],
    ),
    "healthcare_vertical": Concept(
        name="healthcare_vertical", domain="industry_fit", base_weight=0.85,
        patterns=["hospital", "clinic", "senior.*living", "nursing.*home",
                  "healthcare", "assisted.*living", "long.term.*care"],
        synonyms=["senior living", "medical facility"],
    ),
    "food_beverage_vertical": Concept(
        name="food_beverage_vertical", domain="industry_fit", base_weight=0.75,
        patterns=["restaurant", "food.*service", "dining", "cafeteria",
                  "catering", "quick.*service", r"\bQSR\b", "food.*beverage"],
        synonyms=["QSR", "food service"],
    ),
    "airport_vertical": Concept(
        name="airport_vertical", domain="industry_fit", base_weight=0.80,
        patterns=["airport", "terminal", "airline.*hub", "aviation.*facilit"],
        synonyms=["aviation", "air terminal"],
    ),
    "casino_vertical": Concept(
        name="casino_vertical", domain="industry_fit", base_weight=0.78,
        patterns=["casino", "gaming.*facilit", "resort.*casino"],
        synonyms=["gaming", "resort gaming"],
    ),

    # ── Strategic hiring signals ────────────────────────────────────────────
    "strategic_automation_hire": Concept(
        name="strategic_automation_hire", domain="automation", base_weight=0.88,
        patterns=[
            r"(VP|SVP|Director|Head|Chief).*(automat|robot|technolog|operat|transform)",
            r"(Chief Automation|Chief Robotics|Chief Digital|Chief Technolog)",
            r"hire.*head of (automat|robot|supply chain|logistics technol)",
            r"appoint.*(automat|robot|AI|technolog).*(lead|head|director|officer)",
            "automation lead", "robotics lead", "head of automation",
            "vp of robotics", "director of automation", "svp operations technology",
            "chief automation officer", "chief robotics",
        ],
        synonyms=["automation executive", "robotics director", "head of robotics"],
    ),
    "operations_technology_hire": Concept(
        name="operations_technology_hire", domain="automation", base_weight=0.80,
        patterns=[
            r"(VP|Director|Head|Chief).*(supply chain|operations|fulfillment|distribution).*(technol|digital|transfor)",
            "chief supply chain officer", "vp supply chain technology",
            "director of intelligent operations", "head of digital supply chain",
            "hired.*operations.*innovati", "new.*coo.*automat",
        ],
        synonyms=["supply chain technology hire", "ops tech executive"],
    ),

    # ── Capital & growth signals ────────────────────────────────────────────
    "capex_announcement": Concept(
        name="capex_announcement", domain="expansion", base_weight=0.82,
        patterns=[
            r"capital.*expenditure", r"capex.*\$", r"\$.*capex",
            r"invest.*\$(\d+[MB]|\.\d+\s*billion)",
            "capital investment plan", "multi.year.*investment",
            r"committing.*\$.*to (automat|technolog|facilit|infrastruct)",
            r"allocated.*\$.*for (automat|robot|expansion|technolog)",
            "infrastructure investment", "technology investment program",
        ],
        synonyms=["capital expenditure", "capex plan", "major investment"],
    ),
    "growth_plan": Concept(
        name="growth_plan", domain="expansion", base_weight=0.75,
        patterns=[
            "growth strategy", "strategic growth", "expansion strategy",
            "five.year plan", "3.year plan", "strategic plan.*expand",
            "scaling.*operation", "scale.*business", "aggressive.*expand",
            r"grow.*from \d+ to \d+", "double.*capacity", "triple.*capacity",
            "nationwide.*expansion", "national.*rollout", "market.*expansion",
        ],
        synonyms=["expansion plan", "strategic expansion", "scaling strategy"],
    ),
    "ma_activity": Concept(
        name="ma_activity", domain="expansion", base_weight=0.78,
        patterns=[
            r"acqui[rs]", "merger", "acqui.*company", "strategic.*acqui",
            "merges with", "acquired by", "buyout", "takeover",
            "joint venture", "strategic partnership.*automat",
            r"integrat.*acqui", "post.merger.*integrat",
            "integration.*newly acquired",
        ],
        synonyms=["M&A", "merger acquisition", "buyout", "joint venture"],
    ),
    "series_funding": Concept(
        name="series_funding", domain="expansion", base_weight=0.85,
        patterns=[
            r"series [a-e]\b", r"series [a-e] round",
            r"raised? \$\d+[mb]", r"raises? \$\d+[mb]",
            r"\$\d+[mb] (funding|investment|round|raise)",
            "funding round", "venture capital", "private equity.*invest",
            r"ipo\.?\s", "initial public offering", "spac",
            "growth equity", "growth round", "debt financing",
            r"backed by .{0,30}(capital|ventures|partners)",
        ],
        synonyms=["Series A", "Series B", "VC funding", "investment round", "raised funding"],
    ),
    "operational_scale": Concept(
        name="operational_scale", domain="expansion", base_weight=0.70,
        patterns=[
            r"(\d+[,.]?\d*) (new )?(warehouse|facilit|distribution center|fulfillment center|hotel|propert|location)",
            "rapid.*growth", "hyper.*growth", "fast.*growing",
            r"expan.*from \d+ to \d+",
            "adding.*locations", "opening.*locations",
            r"fleet.*expan", r"network.*expan",
            "scale.*rapidly", "significant.*growth",
        ],
        synonyms=["rapid scaling", "network expansion", "fleet growth"],
    ),

    # ── Buyer automation-readiness signals ───────────────────────────────────────
    "automation_intent": Concept(
        name="automation_intent", domain="automation", base_weight=0.78,
        patterns=[
            "process improvement", "operational excellence",
            "lean.*operat", "six sigma.*operat",
            "continuous improvement.*program",
            "automation.*initiative", "automation.*program", "automation.*pilot",
            "robot.*pilot", "robot.*trial", "proof of concept.*robot",
            "digital.*transform.*operat",
            "smart.*hotel", "smart.*restaurant", "smart.*warehouse", "smart.*facilit",
            "automation.*strateg", "automate.*operat",
        ],
        synonyms=["automation program", "lean initiative", "process excellence", "robot pilot"],
    ),
    "service_consistency": Concept(
        name="service_consistency", domain="quality", base_weight=0.72,
        patterns=[
            "brand standard", "service.*consistenc",
            "guest experience.*improv", "service.*quality.*program",
            "uniform.*service", "consistent.*deliver",
            "franchise.*standard", "brand.*compliance",
            "service.*level.*agreement", "quality.*audit",
            "standardiz.*service", "service.*benchmark",
        ],
        synonyms=["brand compliance", "service standardization", "guest experience program"],
    ),
    "equipment_integration": Concept(
        name="equipment_integration", domain="automation", base_weight=0.68,
        patterns=[
            r"WMS.*implement", r"ERP.*go.live", r"ERP.*integrat",
            "system.*integrat.*operat", "technology.*platform.*rollout",
            "automation.*integrat.*existing", "connect.*existing.*equipment",
            r"WMS.*rollout", r"PLC.*SCADA.*integrat",
            "fleet.*management.*system", "building.*management.*system",
            "integrat.*new.*equipment", "equipment.*api",
        ],
        synonyms=["WMS integration", "ERP rollout", "system integration", "technology integration"],
    ),
    "franchise_operations": Concept(
        name="franchise_operations", domain="industry_fit", base_weight=0.73,
        patterns=[
            "franchise.*operat", "multi.unit.*operat",
            "brand.*franchis", "franchisee.*operat",
            r"\d{2,}.*(location|unit|store|propert|restaurant|hotel)",
            "chain operat", "portfolio.*propert",
            "operating.*portfolio", "portfolio.*hotel", "portfolio.*restaurant",
            "multi.propert", "brand.*portfolio",
        ],
        synonyms=["franchise chain", "multi-unit operator", "portfolio operator"],
    ),
}


# ──────────────────────────────────────────────
# 5. Relationships
# ──────────────────────────────────────────────
RELATIONSHIPS: List[Relationship] = [
    Relationship("amr_agv",                  "warehouse_automation",     "implies",         0.9),
    Relationship("pick_place",               "warehouse_automation",     "associated_with", 0.7),
    Relationship("wms_integration",          "warehouse_automation",     "associated_with", 0.6),
    Relationship("labor_shortage",           "reduce_labor_costs",       "implies",         0.8),
    Relationship("high_turnover",            "labor_shortage",           "associated_with", 0.7),
    Relationship("service_robot",            "hospitality_vertical",     "associated_with", 0.85),
    Relationship("warehouse_expansion",      "warehouse_automation",     "implies",         0.75),
    Relationship("funding_announcement",     "warehouse_expansion",      "associated_with", 0.5),
    Relationship("modernization",            "ai_operations",            "associated_with", 0.6),
    Relationship("robotics_engineer",        "amr_agv",                  "associated_with", 0.7),
    # New relationships
    Relationship("series_funding",           "capex_announcement",       "implies",         0.7),
    Relationship("series_funding",           "growth_plan",              "associated_with", 0.65),
    Relationship("ma_activity",              "operational_scale",        "associated_with", 0.6),
    Relationship("strategic_automation_hire","warehouse_automation",     "implies",         0.80),
    Relationship("strategic_automation_hire","amr_agv",                  "associated_with", 0.65),
    Relationship("operations_technology_hire","modernization",           "implies",         0.70),
    Relationship("capex_announcement",       "warehouse_expansion",      "associated_with", 0.70),
    Relationship("growth_plan",              "warehouse_expansion",      "associated_with", 0.55),
    Relationship("operational_scale",        "labor_shortage",           "associated_with", 0.50),
    # Automation readiness
    Relationship("automation_intent",        "warehouse_automation",     "implies",         0.70),
    Relationship("automation_intent",        "reduce_labor_costs",       "associated_with", 0.65),
    Relationship("service_consistency",      "service_robot",            "implies",         0.75),
    Relationship("franchise_operations",     "service_consistency",      "associated_with", 0.70),
    Relationship("franchise_operations",     "labor_shortage",           "associated_with", 0.55),
    Relationship("equipment_integration",    "warehouse_automation",     "associated_with", 0.60),
    Relationship("equipment_integration",    "automation_intent",        "associated_with", 0.65),
]


# ──────────────────────────────────────────────
# 6. Inference Rules  (forward-chaining)
# ──────────────────────────────────────────────
INFERENCE_RULES: List[InferenceRule] = [
    InferenceRule(
        name="warehouse_ready",
        conditions=["warehouse_automation", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.25,
        description="Company shows warehouse automation need AND labor pain → strong buy signal"
    ),
    InferenceRule(
        name="hotel_robotics_ready",
        conditions=["hospitality_vertical", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.30,
        description="Hotel with labor shortage → high service-robot fit"
    ),
    InferenceRule(
        name="logistics_expansion_signal",
        conditions=["logistics_vertical", "warehouse_expansion"],
        conclusion_domain="expansion",
        boost=0.30,
        description="Logistics player opening new facility → strong expansion signal"
    ),
    InferenceRule(
        name="funded_expansion",
        conditions=["funding_announcement", "warehouse_expansion"],
        conclusion_domain="expansion",
        boost=0.35,
        description="Funded AND expanding → very likely capex spend on automation"
    ),
    InferenceRule(
        name="tech_forward_operator",
        conditions=["ai_operations", "modernization"],
        conclusion_domain="automation",
        boost=0.20,
        description="AI + modernization language → technology-forward operator"
    ),
    InferenceRule(
        name="healthcare_automation",
        conditions=["healthcare_vertical", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.28,
        description="Healthcare + labor shortage → strong automation candidate"
    ),
    InferenceRule(
        name="full_stack_signal",
        conditions=["amr_agv", "wms_integration", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.40,
        description="AMR + WMS + labor pain → near-term buyer"
    ),
    InferenceRule(
        name="service_industry_pain",
        conditions=["reduce_labor_costs", "operational_efficiency"],
        conclusion_domain="labor_pain",
        boost=0.22,
        description="Cost reduction + efficiency → operational pressure to automate"
    ),
    # ── New rules: funding, M&A, hiring, capex ──────────────────────────────
    InferenceRule(
        name="funded_automation_buyer",
        conditions=["series_funding", "strategic_automation_hire"],
        conclusion_domain="automation",
        boost=0.38,
        description="Funding round + automation executive hire → near-term technology buyer"
    ),
    InferenceRule(
        name="funded_expansion_capex",
        conditions=["series_funding", "capex_announcement"],
        conclusion_domain="expansion",
        boost=0.40,
        description="Raised capital + capex plan → active capex deployment cycle"
    ),
    InferenceRule(
        name="ma_integration_need",
        conditions=["ma_activity", "operational_scale"],
        conclusion_domain="automation",
        boost=0.30,
        description="M&A + rapid scale → integration automation urgency"
    ),
    InferenceRule(
        name="strategic_hire_labor_pain",
        conditions=["strategic_automation_hire", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.35,
        description="Automation exec hire + labor shortage → mandate to automate now"
    ),
    InferenceRule(
        name="growth_scale_pressure",
        conditions=["growth_plan", "labor_shortage"],
        conclusion_domain="labor_pain",
        boost=0.28,
        description="Aggressive growth plan + labor shortage → scaling pain driving automation"
    ),
    InferenceRule(
        name="capex_logistics_buyer",
        conditions=["capex_announcement", "logistics_vertical"],
        conclusion_domain="automation",
        boost=0.32,
        description="Logistics company with active capex → strong automation buyer signal"
    ),
    InferenceRule(
        name="capex_hospitality_buyer",
        conditions=["capex_announcement", "hospitality_vertical"],
        conclusion_domain="automation",
        boost=0.28,
        description="Hospitality company with active capex → service robot readiness"
    ),
    InferenceRule(
        name="funded_expansion_hire_triple",
        conditions=["series_funding", "growth_plan", "strategic_automation_hire"],
        conclusion_domain="automation",
        boost=0.45,
        description="Funding + growth plan + automation executive = highest-priority buyer"
    ),
    # ── Buyer automation-readiness rules ───────────────────────────────────────
    InferenceRule(
        name="automation_intent_labor_pain",
        conditions=["automation_intent", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.38,
        description="Active efficiency/automation program + labor shortage → near-term buyer"
    ),
    InferenceRule(
        name="service_consistency_labor_pain",
        conditions=["service_consistency", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.30,
        description="Service quality pressure + staffing pain → robots for consistent delivery"
    ),
    InferenceRule(
        name="franchise_scale_consistency",
        conditions=["franchise_operations", "service_consistency"],
        conclusion_domain="automation",
        boost=0.28,
        description="Multi-unit franchise + service consistency mandate → robot deployment fit"
    ),
    InferenceRule(
        name="equipment_integration_ready",
        conditions=["equipment_integration", "operational_efficiency"],
        conclusion_domain="automation",
        boost=0.25,
        description="Active tech integration + efficiency focus → robot-ready infrastructure"
    ),
    InferenceRule(
        name="franchise_labor_scale",
        conditions=["franchise_operations", "labor_shortage"],
        conclusion_domain="labor_pain",
        boost=0.32,
        description="Multi-unit operator with staffing pain → high-ROI automation candidate"
    ),
]


# ──────────────────────────────────────────────
# 7. Industry priors (base robotics-fit score)
# ──────────────────────────────────────────────
INDUSTRY_PRIORS: Dict[str, float] = {
    "logistics":     0.90,
    "hospitality":   0.85,
    "hotel":         0.85,
    "healthcare":    0.80,
    "food service":  0.75,
    "restaurant":    0.72,
    "airport":       0.78,
    "casino":        0.70,
    "manufacturing": 0.68,
    "retail":        0.62,
    "unknown":       0.40,
}


def get_industry_prior(industry: str) -> float:
    if not industry:
        return INDUSTRY_PRIORS["unknown"]
    low = industry.lower()
    for key, val in INDUSTRY_PRIORS.items():
        if key in low:
            return val
    return INDUSTRY_PRIORS["unknown"]
