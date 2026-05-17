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

    # ── Humanoid robots ──────────────────────
    "humanoid_robot": Concept(
        name="humanoid_robot", domain="automation", base_weight=0.95,
        patterns=[
            "humanoid", "humanoids", "bipedal robot", "biped robot", "android robot",
            "boston dynamics atlas", "agility robotics", "figure ai", "figure robot",
            "optimus robot", "tesla bot", "apptronik", "sanctuary ai",
            "1x technologies", "fourier intelligence", "ubtech", "engineered arts",
            "digit robot", "ameca robot", "nao robot", "pepper robot",
        ],
        synonyms=["humanoid bot", "bipedal machine", "android automaton"],
    ),

    # ── Drone / UAV / UAS ─────────────────────
    "drone_uav": Concept(
        name="drone_uav", domain="automation", base_weight=0.90,
        patterns=[
            r"\bdrone\b", r"\bdrones\b", r"\buav\b", r"\buas\b",
            "unmanned aerial", "unmanned aircraft", "quadcopter", "multirotor",
            "fixed wing drone", r"\bevtol\b", "urban air mobility", r"\buam\b",
            "autonomous flight", "aerial robot", "delivery drone",
            "skydio", "dji enterprise", "parrot drone", "zipline", "wing aviation",
            "percepto", "autel robotics", "joby aviation", "archer aviation",
            "wisk aero", "lilium", "vertical aerospace",
        ],
        synonyms=["UAV", "UAS", "unmanned aerial vehicle", "autonomous aircraft"],
    ),

    # ── 3D printing / additive manufacturing ──
    "additive_manufacturing": Concept(
        name="additive_manufacturing", domain="automation", base_weight=0.80,
        patterns=[
            r"3d\s+print", "additive manufactur", "additive mfg",
            "rapid prototyp", "fused deposit", "selective laser sintering",
            "stereolithography", r"\bsla\b", r"\bfdm\b", r"\bsls\b",
            "stratasys", "3d systems", "markforged", "carbon3d",
            "desktop metal", "eos gmbh", "formlabs", "bambu lab",
            "metal printing", "metal additive", "binder jetting",
        ],
        synonyms=["3D printing", "additive mfg", "rapid manufacturing"],
    ),

    # ── Surgical / medical robots ──────────────
    "surgical_robot": Concept(
        name="surgical_robot", domain="automation", base_weight=0.92,
        patterns=[
            "surgical robot", "surgical robotics", "robotic surgery",
            "minimally invasive robot", "laparoscopic robot",
            "orthopedic robot", "da vinci", "intuitive surgical",
            "stryker mako", "medtronic hugo", "cmr surgical",
            "robotic-assisted surgery", "avatera", "moon surgical",
        ],
        synonyms=["surgical system", "robotic OR", "minimally invasive robotics"],
    ),
    "medical_robot": Concept(
        name="medical_robot", domain="automation", base_weight=0.88,
        patterns=[
            "medical robot", "hospital robot", "healthcare robot",
            "pharmacy robot", "uvc disinfection", "uv-c robot",
            "autonomous hospital", "clinical robot", "rehabilitation robot",
            "exoskeleton rehabilitation", "medtech robot", "smart hospital",
        ],
        synonyms=["healthcare automation", "clinical robotics", "medtech bot"],
    ),

    # ── Material handling / warehouse logistics ──
    "material_handling": Concept(
        name="material_handling", domain="automation", base_weight=0.85,
        patterns=[
            "material handling", "goods handling", "pallet handling",
            "autonomous forklift", "automated forklift", "forklift robot",
            "conveyor automat", "sortation system", "automated sortation",
            "goods-to-person", "person-to-goods", "shuttle system",
            "autostore", "vertical carousel", "automated storage",
            r"\basr\b", "automated storage retrieval",
        ],
        synonyms=["material flow", "intralogistics", "goods movement"],
    ),

    # ── Autonomous vehicles / self-driving ───────
    "autonomous_vehicle": Concept(
        name="autonomous_vehicle", domain="automation", base_weight=0.82,
        patterns=[
            "autonomous vehicle", "autonomous car", "self-driving", "self driving",
            r"\bav\b.*vehicle", "driverless", "lidar.*vehicle", "lidar.*autonom",
            r"\bslam\b", "waymo", "cruise automation", "nuro", "serve robotics",
            "starship technologies", "amazon scout", "autonomous delivery",
            "autonomous last mile",
        ],
        synonyms=["AV", "self-driving vehicle", "driverless car"],
    ),

    # ── Exoskeleton / wearable robot ─────────────
    "exoskeleton": Concept(
        name="exoskeleton", domain="automation", base_weight=0.80,
        patterns=[
            "exoskeleton", "exosuit", "powered exoskeleton", "wearable robot",
            "powered suit", "ekso bionics", "sarcos", "suitx",
            "cyberdyne hal", "rewalk", "indego", "hyundai exoskeleton",
        ],
        synonyms=["powered suit", "wearable exo", "augmentation suit"],
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

    # ═══ Robot deployment & automation opportunity signals (March 2026) ═══
    "robot_installation": Concept(
        name="robot_installation", domain="automation", base_weight=0.95,
        patterns=[
            "deploy.*robot", "robot.*deploy", "installed.*robot", "robot.*installed",
            "implements.*robot", "robot.*implement", "fleet.*robot", "robot.*fleet",
            "robot.*operational", "robot.*in production", "robot.*went live",
            "AMR.*deploy", "AGV.*deploy", "cobot.*install", "service robot.*deploy",
            "autonomous.*robot.*deploy", "cleaning robot.*deploy", "disinfection robot",
        ],
        synonyms=["robot deployment", "robot installation", "robot fleet", "AMR fleet"],
    ),
    "pilot_success": Concept(
        name="pilot_success", domain="automation", base_weight=0.88,
        patterns=[
            "successful pilot", "pilot.*exceed", "trial success", "pilot.*expand",
            "pilot.*production", "trial.*permanent", "proof of concept.*success",
            "pilot program.*positive", "pilot.*rollout", "pilot.*full deployment",
        ],
        synonyms=["pilot expansion", "trial to production", "pilot to rollout"],
    ),
    "roi_documented": Concept(
        name="roi_documented", domain="automation", base_weight=0.85,
        patterns=[
            "roi", "return on investment", "payback period", "payback in",
            "saves \\$", "cost savings", "reduced costs by", "labor savings",
            "efficiency gains", "productivity increase", r"\d+% faster", r"\d+% reduction",
        ],
        synonyms=["ROI", "payback", "cost savings", "labor savings"],
    ),
    "disinfection_robot": Concept(
        name="disinfection_robot", domain="automation", base_weight=0.90,
        patterns=[
            "disinfection robot", "UV-C.*robot", "UV robot", "sanitization robot",
            "hospital.*disinfection", "cleaning.*robot.*hospital",
        ],
        synonyms=["UV disinfection", "autonomous disinfection"],
    ),
    "floor_scrubber_automation": Concept(
        name="floor_scrubber_automation", domain="automation", base_weight=0.82,
        patterns=[
            "autonomous floor scrubber", "floor scrubber.*robot",
            "autonomous scrubber", "robotic floor cleaning",
        ],
        synonyms=["autonomous scrubber", "robot floor scrubber"],
    ),
    "vendor_selection": Concept(
        name="vendor_selection", domain="expansion", base_weight=0.78,
        patterns=[
            "selected", "chose", "partnered with", "contracted with",
            "working with.*vendor", "supplier chosen", "signed agreement",
            "multi-year deal", "provider selected",
        ],
        synonyms=["vendor selection", "provider chosen"],
    ),

    # ── Gap-fill: high-value buyer signals (Apr 2026) ─────────────────────
    "rfq_rfp": Concept(
        name="rfq_rfp", domain="expansion", base_weight=0.95,
        patterns=[
            r"\bRFQ\b", r"\bRFP\b", "request for quote", "request for proposal",
            "request for information", r"\bRFI\b", "vendor evaluation",
            "issuing.*bid", "bid.*process", "procurement.*process",
            "sourcing.*robot", "evaluating.*vendor", "evaluating.*solution",
        ],
        synonyms=["RFQ", "RFP", "RFI", "request for quote", "request for proposal"],
    ),
    "regulatory_compliance": Concept(
        name="regulatory_compliance", domain="quality", base_weight=0.72,
        patterns=[
            r"\bOSHA\b", "ergonomic.*regulat", "safety.*compliance",
            r"\bFDA\b", "food.*safety.*regulat", "gmp.*compliance",
            r"\bGMP\b", "fsma", "haccp", r"\bHACCP\b",
            "repetitive.*motion.*violat", "injury.*rate", "workers.*comp",
            "safety.*incident", "recordable.*incident",
        ],
        synonyms=["OSHA compliance", "FDA compliance", "food safety", "GMP", "HACCP"],
    ),
    "supply_chain_disruption": Concept(
        name="supply_chain_disruption", domain="labor_pain", base_weight=0.68,
        patterns=[
            "supply chain.*disrupt", "supply.*shortage", "component.*shortage",
            "nearshoring", "reshoring", "onshoring", "friendshoring",
            "supply.*resilience", "domestic.*manufactur",
            "supply chain.*risk", "single.*source.*risk",
            "inventory.*buffer", "safety.*stock", "just-in-case",
        ],
        synonyms=["supply chain disruption", "reshoring", "nearshoring", "onshoring"],
    ),

    # ═══ End-of-Line (EOL) Automation Concepts (Apr 2026) ═══════════════════

    "eol_palletizing": Concept(
        name="eol_palletizing", domain="automation", base_weight=0.92,
        patterns=[
            r"palletiz", "depalletiz", "palletizer", "pallet robot",
            r"robotic pallet", "automatic.*palletiz", "layer palletiz",
            "case palletiz", "bag palletiz",
        ],
        synonyms=["palletizer", "depalletizer", "robotic palletizing", "pallet stacking robot"],
    ),
    "eol_case_packing": Concept(
        name="eol_case_packing", domain="automation", base_weight=0.88,
        patterns=[
            "case pack", "case packer", "robotic case pack",
            "case erect", "tray pack", "tray former",
            "case.*forming", "wrap-around case", "carton erect",
            "top-load case", "side-load case",
        ],
        synonyms=["case packer", "case erector", "tray packer", "carton packer"],
    ),
    "eol_wrapping_labeling": Concept(
        name="eol_wrapping_labeling", domain="automation", base_weight=0.84,
        patterns=[
            "stretch wrap", "shrink wrap", "stretch hood",
            "automatic.*wrap", "robotic.*wrap",
            "label.*applicat", "print.*apply", "labeling.*automat",
            "checkweigh", "x-ray inspect", "metal detect",
        ],
        synonyms=["stretch wrapper", "shrink wrapper", "label applicator", "checkweigher"],
    ),
    "eol_line_automation": Concept(
        name="eol_line_automation", domain="automation", base_weight=0.90,
        patterns=[
            "end.of.line", "end-of-line", r"\bEOL\b",
            "packaging line automat", "pack-out", "pack-in",
            "intralogistics", "intra-logistics",
            "conveyor.*automat", "automated.*conveyor",
            "line.*integrat", "full.*line.*automat",
        ],
        synonyms=["end-of-line automation", "EOL robotics", "packaging line robotics",
                  "pack-out automation", "intralogistics"],
    ),
    "cpg_food_vertical": Concept(
        name="cpg_food_vertical", domain="industry_fit", base_weight=0.88,
        patterns=[
            "consumer packaged goods", r"\bcpg\b", "food.*manufactur",
            "food.*processing", "food.*production", "food.*plant",
            "beverage.*manufactur", "bottling.*plant", "canning.*plant",
            "snack.*manufactur", "dairy.*plant", "meat.*processing",
            "packaged food", "packaged beverage", "brand manufacturer",
        ],
        synonyms=["CPG", "food processing", "food manufacturing", "beverage plant"],
    ),
    "contract_manufacturing_vertical": Concept(
        name="contract_manufacturing_vertical", domain="industry_fit", base_weight=0.85,
        patterns=[
            "contract.*manufactur", r"\bcmo\b", r"\bcdmo\b",
            "co-packer", "co packer", "contract packer", "contract packager",
            "toll.*manufactur", "toll.*processing",
            "high.*mix.*low.*volume", "rapid.*changeover",
            "flexible.*manufactur", "make.*to.*order",
        ],
        synonyms=["CMO", "CDMO", "co-packer", "contract manufacturer", "toll manufacturer"],
    ),
    "throughput_pressure": Concept(
        name="throughput_pressure", domain="labor_pain", base_weight=0.80,
        patterns=[
            "throughput.*bottleneck", "capacity.*constraint",
            "running.*at.*capacity", "maxed.*out",
            "line.*speed", "uptime.*issue", "changeover.*time",
            "pack-out.*backlog", "production.*bottleneck",
            "output.*target", "rate.*target",
            "scrap.*rate", "defect.*rate", "rework", "reject.*rate",
            "quality.*issue", "inspection.*fail",
        ],
        synonyms=["throughput bottleneck", "capacity constraint", "production pressure"],
    ),
    "ergonomic_risk": Concept(
        name="ergonomic_risk", domain="labor_pain", base_weight=0.75,
        patterns=[
            r"\bOSHA\b", "ergonomic.*risk", "repetitive.*strain",
            "musculoskeletal", r"\bRSI\b", "workplace.*injury",
            "workers.*comp", "ergonomic.*hazard",
            "lifting.*injury", "manual.*handling.*risk",
        ],
        synonyms=["OSHA compliance", "ergonomic hazard", "repetitive strain injury"],
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
    # Robot deployment concepts
    Relationship("robot_installation",       "warehouse_automation",     "implies",         0.95),
    Relationship("robot_installation",       "service_robot",            "implies",         0.85),
    Relationship("pilot_success",            "automation_intent",        "implies",         0.90),
    Relationship("roi_documented",           "automation_intent",        "implies",         0.80),
    Relationship("disinfection_robot",       "healthcare_vertical",      "associated_with", 0.85),
    Relationship("floor_scrubber_automation","service_robot",            "associated_with", 0.80),

    # EOL relationships (Apr 2026)
    Relationship("eol_palletizing",           "eol_line_automation",     "implies",         0.90),
    Relationship("eol_case_packing",          "eol_line_automation",     "implies",         0.85),
    Relationship("eol_wrapping_labeling",     "eol_line_automation",     "associated_with", 0.75),
    Relationship("eol_line_automation",       "cpg_food_vertical",       "associated_with", 0.80),
    Relationship("throughput_pressure",       "reduce_labor_costs",      "implies",         0.70),
    Relationship("ergonomic_risk",            "reduce_labor_costs",      "implies",         0.65),
    Relationship("contract_manufacturing_vertical", "eol_line_automation", "associated_with", 0.80),
    Relationship("cpg_food_vertical",         "labor_shortage",          "associated_with", 0.60),

    # ── Gap-fix: orphaned concept wiring (Apr 2026) ──────────────────────
    # warehouse_automation → downstream outcomes
    Relationship("warehouse_automation",      "reduce_labor_costs",      "implies",         0.75),
    Relationship("warehouse_automation",      "logistics_vertical",      "associated_with", 0.80),
    # cobots
    Relationship("cobots",                    "reduce_labor_costs",      "implies",         0.70),
    Relationship("cobots",                    "amr_agv",                 "associated_with", 0.65),
    Relationship("cobots",                    "automation_intent",       "implies",         0.80),
    # computer_vision / ai_operations
    Relationship("computer_vision",           "ai_operations",           "implies",         0.75),
    Relationship("computer_vision",           "automation_intent",       "associated_with", 0.60),
    Relationship("ai_operations",             "modernization",           "implies",         0.70),
    Relationship("ai_operations",             "warehouse_automation",    "associated_with", 0.55),
    # vertical identifiers → their primary robot type
    Relationship("hospitality_vertical",      "service_robot",           "implies",         0.85),
    Relationship("logistics_vertical",        "amr_agv",                 "implies",         0.85),
    Relationship("logistics_vertical",        "warehouse_automation",    "implies",         0.80),
    Relationship("healthcare_vertical",       "disinfection_robot",      "associated_with", 0.80),
    Relationship("food_beverage_vertical",    "eol_line_automation",     "implies",         0.85),
    Relationship("food_beverage_vertical",    "cpg_food_vertical",       "associated_with", 0.90),
    Relationship("airport_vertical",          "service_robot",           "implies",         0.75),
    Relationship("casino_vertical",           "service_robot",           "associated_with", 0.70),
    # expansion signals → vertical context
    Relationship("hotel_expansion",           "hospitality_vertical",    "implies",         0.80),
    Relationship("hotel_expansion",           "new_construction",        "associated_with", 0.75),
    Relationship("new_construction",          "warehouse_expansion",     "associated_with", 0.60),
    Relationship("new_construction",          "automation_intent",       "associated_with", 0.50),
    Relationship("acquisition",               "ma_activity",             "implies",         0.85),
    Relationship("acquisition",               "operational_scale",       "implies",         0.70),
    # vendor_selection — critical buying signal
    Relationship("vendor_selection",          "automation_intent",       "implies",         0.90),
    Relationship("vendor_selection",          "reduce_labor_costs",      "associated_with", 0.65),
    # regulatory / supply chain new concepts
    Relationship("regulatory_compliance",     "automation_intent",       "implies",         0.70),
    Relationship("regulatory_compliance",     "ergonomic_risk",          "associated_with", 0.60),
    Relationship("supply_chain_disruption",   "warehouse_automation",    "implies",         0.65),
    Relationship("supply_chain_disruption",   "automation_intent",       "associated_with", 0.60),
    Relationship("rfq_rfp",                   "vendor_selection",        "implies",         0.95),
    Relationship("rfq_rfp",                   "automation_intent",       "implies",         0.90),
    # ── New robot categories → industry verticals ────────────────────────────
    Relationship("humanoid_robot",            "automation_intent",       "implies",         0.95),
    Relationship("humanoid_robot",            "robotics_engineer",       "associated_with", 0.85),
    Relationship("drone_uav",                 "automation_intent",       "implies",         0.90),
    Relationship("drone_uav",                 "logistics_vertical",      "associated_with", 0.70),
    Relationship("additive_manufacturing",    "automation_intent",       "implies",         0.80),
    Relationship("additive_manufacturing",    "robotics_engineer",       "associated_with", 0.65),
    Relationship("surgical_robot",            "healthcare_vertical",     "implies",         0.95),
    Relationship("surgical_robot",            "automation_intent",       "implies",         0.90),
    Relationship("medical_robot",             "healthcare_vertical",     "implies",         0.90),
    Relationship("medical_robot",             "automation_intent",       "implies",         0.80),
    Relationship("material_handling",         "warehouse_automation",    "implies",         0.90),
    Relationship("material_handling",         "logistics_vertical",      "associated_with", 0.85),
    Relationship("autonomous_vehicle",        "automation_intent",       "implies",         0.85),
    Relationship("autonomous_vehicle",        "logistics_vertical",      "associated_with", 0.75),
    Relationship("exoskeleton",               "automation_intent",       "implies",         0.80),
    Relationship("exoskeleton",               "ergonomic_risk",          "associated_with", 0.75),
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
    # ═══ Robot deployment & opportunity rules (March 2026) ═══
    InferenceRule(
        name="robot_install_expansion_signal",
        conditions=["robot_installation", "expansion"],
        conclusion_domain="automation",
        boost=0.40,
        description="Robot deployment + expansion → peer pressure for others in industry"
    ),
    InferenceRule(
        name="pilot_success_scale",
        conditions=["pilot_success", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.38,
        description="Successful pilot + labor pain → expansion-ready buyer"
    ),
    InferenceRule(
        name="roi_proven_labor_pain",
        conditions=["roi_documented", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.35,
        description="ROI case study + labor shortage → near-term buyer with proof"
    ),
    InferenceRule(
        name="robot_install_industry",
        conditions=["robot_installation", "hospitality_vertical"],
        conclusion_domain="automation",
        boost=0.32,
        description="Hotel with robot deployment → service robot market validation"
    ),
    InferenceRule(
        name="robot_install_logistics",
        conditions=["robot_installation", "logistics_vertical"],
        conclusion_domain="automation",
        boost=0.35,
        description="Warehouse with robot deployment → AMR market validation"
    ),

    # ═══ EOL / CPG / Food Manufacturing Inference Rules (Apr 2026) ═══
    InferenceRule(
        name="eol_labor_pain_buyer",
        conditions=["eol_line_automation", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.40,
        description="EOL automation context + labor shortage → strong packaging robot buyer"
    ),
    InferenceRule(
        name="food_plant_throughput_pressure",
        conditions=["cpg_food_vertical", "throughput_pressure"],
        conclusion_domain="automation",
        boost=0.38,
        description="Food/CPG plant with throughput constraint → EOL robot prioritization"
    ),
    InferenceRule(
        name="food_plant_labor_shortage",
        conditions=["cpg_food_vertical", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.35,
        description="Food/CPG plant with staffing pain → palletizer/case packer buyer"
    ),
    InferenceRule(
        name="contract_mfg_changeover_pain",
        conditions=["contract_manufacturing_vertical", "throughput_pressure"],
        conclusion_domain="automation",
        boost=0.38,
        description="Co-packer/CMO with changeover pressure → flexible EOL robot buyer"
    ),
    InferenceRule(
        name="eol_capex_buyer",
        conditions=["eol_line_automation", "capex_announcement"],
        conclusion_domain="automation",
        boost=0.42,
        description="Active capex + EOL automation interest → near-term palletizer/case packer buyer"
    ),
    InferenceRule(
        name="ergonomic_eol_driver",
        conditions=["ergonomic_risk", "cpg_food_vertical"],
        conclusion_domain="automation",
        boost=0.32,
        description="OSHA/ergonomic risk at food/CPG plant → palletizing automation driven by safety"
    ),
    InferenceRule(
        name="palletizer_roi_signal",
        conditions=["eol_palletizing", "roi_documented"],
        conclusion_domain="automation",
        boost=0.45,
        description="Palletizer ROI documented → case study / expansion buyer"
    ),
    InferenceRule(
        name="eol_expansion_hire",
        conditions=["eol_line_automation", "strategic_automation_hire"],
        conclusion_domain="automation",
        boost=0.40,
        description="EOL automation context + automation exec hire → capital project in motion"
    ),

    # ── Gap-fill: new inference rules for wired orphans (Apr 2026) ────────
    InferenceRule(
        name="vendor_selection_labor_pain",
        conditions=["vendor_selection", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.42,
        description="Active vendor evaluation + labor shortage → imminent purchase decision"
    ),
    InferenceRule(
        name="rfq_active_buyer",
        conditions=["rfq_rfp", "automation_intent"],
        conclusion_domain="automation",
        boost=0.48,
        description="Live RFQ/RFP + automation intent → highest-priority outreach target"
    ),
    InferenceRule(
        name="rfq_labor_pain",
        conditions=["rfq_rfp", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.45,
        description="Live RFQ + labor shortage → near-term robot buyer with urgency"
    ),
    InferenceRule(
        name="cobot_labor_pain",
        conditions=["cobots", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.38,
        description="Cobot language + labor pain → collaborative robot deployment candidate"
    ),
    InferenceRule(
        name="regulatory_automation_driver",
        conditions=["regulatory_compliance", "ergonomic_risk"],
        conclusion_domain="automation",
        boost=0.35,
        description="OSHA/regulatory pressure + ergonomic risk → compliance-driven automation"
    ),
    InferenceRule(
        name="supply_chain_reshoring",
        conditions=["supply_chain_disruption", "warehouse_automation"],
        conclusion_domain="automation",
        boost=0.33,
        description="Reshoring/nearshoring + warehouse automation → greenfield robot deployment"
    ),
    InferenceRule(
        name="acquisition_integration_pain",
        conditions=["acquisition", "labor_shortage"],
        conclusion_domain="automation",
        boost=0.30,
        description="M&A integration + labor shortage → automation to unify operations"
    ),
    InferenceRule(
        name="new_construction_automation",
        conditions=["new_construction", "automation_intent"],
        conclusion_domain="automation",
        boost=0.35,
        description="Greenfield build + automation intent → robot-ready facility design"
    ),
    InferenceRule(
        name="food_beverage_eol_signal",
        conditions=["food_beverage_vertical", "throughput_pressure"],
        conclusion_domain="automation",
        boost=0.40,
        description="Food/beverage vertical with throughput pain → EOL robot buyer"
    ),
    InferenceRule(
        name="computer_vision_ai_ops",
        conditions=["computer_vision", "ai_operations"],
        conclusion_domain="automation",
        boost=0.28,
        description="CV + AI operations → technology-forward operator ready for robot integration"
    ),
    # ── New robot category rules ─────────────────────────────────────────────
    InferenceRule(
        name="humanoid_oem",
        conditions=["humanoid_robot", "robotics_engineer"],
        conclusion_domain="automation",
        boost=0.45,
        description="Humanoid robot maker with engineering talent → high-priority OEM prospect"
    ),
    InferenceRule(
        name="drone_logistics",
        conditions=["drone_uav", "logistics_vertical"],
        conclusion_domain="automation",
        boost=0.38,
        description="Drone company in logistics → delivery automation convergence signal"
    ),
    InferenceRule(
        name="additive_automation",
        conditions=["additive_manufacturing", "automation_intent"],
        conclusion_domain="automation",
        boost=0.32,
        description="3D printing + automation intent → advanced manufacturing prospect"
    ),
    InferenceRule(
        name="surgical_robot_health",
        conditions=["surgical_robot", "healthcare_vertical"],
        conclusion_domain="automation",
        boost=0.48,
        description="Surgical robot maker in healthcare → premium high-complexity OEM"
    ),
    InferenceRule(
        name="material_handling_warehouse",
        conditions=["material_handling", "warehouse_automation"],
        conclusion_domain="automation",
        boost=0.42,
        description="Material handling + warehouse automation → intralogistics systems buyer"
    ),
    InferenceRule(
        name="autonomous_vehicle_logistics",
        conditions=["autonomous_vehicle", "logistics_vertical"],
        conclusion_domain="automation",
        boost=0.35,
        description="Autonomous vehicle in logistics → last-mile delivery robot prospect"
    ),
    InferenceRule(
        name="exoskeleton_ergonomics",
        conditions=["exoskeleton", "ergonomic_risk"],
        conclusion_domain="automation",
        boost=0.36,
        description="Exoskeleton maker targeting ergonomic risk → industrial wearable robot OEM"
    ),
]


# ──────────────────────────────────────────────
# 7. Industry priors (base robotics-fit score)
# ──────────────────────────────────────────────
INDUSTRY_PRIORS: Dict[str, float] = {
    "logistics":              0.90,
    "hospitality":            0.85,
    "hotel":                  0.85,
    "healthcare":             0.80,
    "medical tech":           0.82,
    # New show verticals
    "humanoid":               0.98,   # Humanoid robot OEM — highest fit
    "surgical robot":         0.97,
    "medical robot":          0.95,
    "drone":                  0.92,
    "uav":                    0.92,
    "additive manufactur":    0.88,
    "3d print":               0.88,
    "material handling":      0.90,
    "autonomous vehicle":     0.87,
    "exoskeleton":            0.85,
    # Existing verticals
    "food service":           0.75,
    "restaurant":             0.72,
    "food process":           0.88,   # EOL buyer — high fit
    "food manufactur":        0.88,
    "cpg":                    0.87,
    "consumer goods":         0.87,
    "contract manufactur":    0.85,
    "beverage":               0.84,
    "bottling":               0.84,
    "packaging":              0.80,
    "airport":                0.78,
    "casino":                 0.70,
    "manufacturing":          0.72,
    "retail":                 0.62,
    "datacenter":             0.70,
    "apparel":                0.65,
    "unknown":                0.40,
}


def get_industry_prior(industry: str) -> float:
    if not industry:
        return INDUSTRY_PRIORS["unknown"]
    low = industry.lower()
    for key, val in INDUSTRY_PRIORS.items():
        if key in low:
            return val
    return INDUSTRY_PRIORS["unknown"]
