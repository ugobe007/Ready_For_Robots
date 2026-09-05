"""
OEM Need Probability Scorer
============================
Scores a robot OEM company's likelihood of needing StageGate's services.

StageGate is NOT robot logistics.
StageGate is ROBOT OPERATIONAL INFRASTRUCTURE.

What very few companies can do (and StageGate can):
  • Receive robots off the truck safely
  • Power them up and run diagnostics
  • Diagnose and recover from transit failures
  • Recalibrate sensors and IMUs after shipping
  • Manage battery charge cycles pre-show
  • Staff qualified robot technicians on the show floor
  • Support live demos when things go wrong
  • Recover failed units during active show hours

Las Vegas is becoming a temporary robotics city several times per year.
The companies with the highest need are those with the smallest US teams
and the highest operational risk at their first or most important show.

7 Primary ICPs (Ideal Customer Profiles):
  1. CES Eureka Park startups       — tiny team, first US show, no support
  2. Foreign humanoid robot companies — no US ops, extreme calibration needs
  3. Medical robot companies          — regulatory sensitivity, precision required
  4. Hospitality robots               — customer-facing, failure is public
  5. Security robots                  — autonomous, liability-sensitive
  6. Warehouse AMR companies          — complex fleet, mapping/recalibration
  7. Chinese robot firms entering US  — no English support staff, customs risk

Pipeline position:
  XBOT discovers OEM company
      ↓
  oem_need_scorer.score(company_text, signals)
      ↓
  OEMNeedScore (0–100 + tier + ICP + reasons)
      ↓
  Cal outreach (discovery email)

Scoring dimensions:
  1. International origin        — no US support infrastructure → high need
  2. Battery / hazmat risk       — Li-ion shipping = carnet + bonded storage
  3. Robot type / ICP match      — each ICP has calibrated operational risk weight
  4. Show relevance              — Las Vegas shows score highest
  5. First-time / debut urgency  — operational risk peaks at first US show
  6. Freight / customs signals   — explicit shipping complexity
  7. Operational risk signals    — demo failure, calibration, sensor, small team
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ── Signal patterns ────────────────────────────────────────────────────────────

_INTL_COUNTRY_RE = re.compile(
    r"\b(china|chinese|japan|japanese|korea|korean|germany|german|"
    r"france|french|israel|israeli|taiwan|taiwanese|uk\b|british|"
    r"europe|european|india|indian|singapore|australia|australian|"
    r"canada|canadian|netherlands|dutch|sweden|swedish|denmark|danish|"
    r"finland|finnish|switzerland|swiss|austria|austrian|"
    r"hong kong|beijing|shanghai|tokyo|seoul|berlin|munich|paris|"
    r"pavilion|pavilions)\b",
    re.I,
)

_BATTERY_RE = re.compile(
    r"\b(lithium|li-ion|lipo|battery|batteries|rechargeable|"
    r"ata carnet|carnet|temporary import|bonded|hazmat|"
    r"dangerous goods|hazardous material|electric motor)\b",
    re.I,
)

# ICP 1 – Humanoid / Exoskeleton (highest calibration complexity)
_HUMANOID_RE = re.compile(
    r"\b(humanoid|biped|bipedal|android|full.?body robot|"
    r"atlas|optimus|digit|figure|phoenix|unitree h1|unitree g1|"
    r"ameca|alter3|spot|stretch|mobile manipulator|"
    r"exoskeleton|exosuit|wearable robot|powered suit|"
    r"agility robotics|boston dynamics|1x tech|apptronik|"
    r"sanctuary ai|kepler|fourier|agibot)\b",
    re.I,
)

# ICP 2 – Medical robots (precision-critical, regulatory-sensitive)
_MEDICAL_ROBOT_RE = re.compile(
    r"\b(surgical robot|medical robot|robotic surgery|da vinci|"
    r"orthopedic robot|endoscopic robot|rehabilitation robot|"
    r"medical device robot|clinical robot|hospital robot|"
    r"fda.cleared|ce.marked robot|intuitive surgical|"
    r"stryker robot|globus medical|medtronic robot)\b",
    re.I,
)

# ICP 3 – Hospitality / service robots (customer-facing, public failure risk)
_HOSPITALITY_ROBOT_RE = re.compile(
    r"\b(hospitality robot|hotel robot|service robot|delivery robot|"
    r"food delivery robot|room service robot|concierge robot|"
    r"restaurant robot|waiter robot|bartender robot|"
    r"bear robotics|aethon|savioke|relay robot|keenon|"
    r"pudu robotics|richtech|orion star)\b",
    re.I,
)

# ICP 4 – Security / surveillance robots (autonomous, liability-sensitive)
_SECURITY_ROBOT_RE = re.compile(
    r"\b(security robot|surveillance robot|patrol robot|guard robot|"
    r"autonomous security|perimeter robot|knightscope|aislelabs|"
    r"cobalt robotics|stid|rgb robotics|ascent robotics)\b",
    re.I,
)

# ICP 5 – Warehouse AMR / logistics robots (fleet complexity, mapping)
_WAREHOUSE_AMR_RE = re.compile(
    r"\b(amr\b|agv\b|autonomous mobile robot|warehouse robot|"
    r"fulfillment robot|picking robot|sortation robot|"
    r"geek\+|geekplus|locus robotics|6 river|fetch robotics|"
    r"rapyuta|hikrobot|hai robotics|mushiny|quicktron|"
    r"6rs|vector robotics|seegrid|otto motors|clearpath)\b",
    re.I,
)

# ICP 6 – Industrial arms / cobots
_INDUSTRIAL_ARM_RE = re.compile(
    r"\b(industrial arm|robotic arm|6.?axis|7.?axis|welding robot|"
    r"palletiz|depalletiz|heavy payload|cobot|collaborative robot|"
    r"gantry|crane robot|delta robot|pick and place arm|"
    r"universal robots|ur\d+|kawasaki robot|yaskawa|fanuc|kuka|abb robot|"
    r"techman robot|doosan robot|aubo robot|franka|omron robot)\b",
    re.I,
)

# ICP 7 – Drones / UAV (FAA indoor permits, battery sensitivity)
_DRONE_RE = re.compile(
    r"\b(drone|uav|uas\b|quadcopter|multirotor|fixed.?wing|evtol|"
    r"unmanned aerial|autonomous flight|fpv|lidar drone|"
    r"dji|parrot|skydio|autel|zipline|wing aviation|amazon prime air)\b",
    re.I,
)

# Operational risk signals — the language of companies who NEED what StageGate does
_OPERATIONAL_RISK_RE = re.compile(
    r"\b(calibration|recalibration|sensor calibration|imu calibration|"
    r"lidar calibration|demo failure|unit failed|technical issue|"
    r"transit damage|shipping damage|damaged in transit|"
    r"small team|lean team|no local support|remote support|"
    r"power up|power-up procedure|boot sequence|"
    r"diagnostic|on-site technician|field technician|field engineer|"
    r"battery management|charge cycle|deep discharge|"
    r"demo recovery|show floor support|live demo support)\b",
    re.I,
)

# Eureka Park / startup signals
_EUREKA_PARK_RE = re.compile(
    r"\b(eureka park|ces startup|startup pavilion|ces innovation award|"
    r"ces 2026 startup|ces 2027 startup|seed.stage|series a|"
    r"small robotics startup|first product|prototype)\b",
    re.I,
)

_FIRST_TIMER_RE = re.compile(
    r"\b(first time|first us|debut|inaugural|for the first time|"
    r"first appearance|new to ces|new to automate|"
    r"first north america|first american|first us show)\b",
    re.I,
)

_PRODUCT_LAUNCH_RE = re.compile(
    r"\b(unveil|unveiling|launch|launching|debut|debuting|"
    r"reveal|revealing|showcase|introducing|world premiere|"
    r"exclusive preview|first look|press conference)\b",
    re.I,
)

_FREIGHT_TROUBLE_RE = re.compile(
    r"\b(customs|customs broker|freight forwarder|international shipping|"
    r"cargo|crate|pallet|oversize|overweight|special handling|"
    r"fragile equipment|white glove|inside delivery|liftgate)\b",
    re.I,
)

_LAS_VEGAS_SHOW_RE = re.compile(
    r"\b(ces|ces 202[67]|manifest|himss|nab|nab show|"
    r"ai4|fabtech vegas|sages|pack expo vegas|"
    r"las vegas|lvcc|venetian expo|mandalay bay|"
    r"mgm grand|caesars forum|encore|wynn)\b",
    re.I,
)

_OTHER_US_SHOW_RE = re.compile(
    r"\b(automate|modex|promat|imts|robobusiness|robotics summit|"
    r"auvsi xponential|sea.air.space|ausa|pack expo|fabtech|"
    r"chicago|atlanta|boston|detroit|orlando|nashville)\b",
    re.I,
)


# ── Score output ───────────────────────────────────────────────────────────────

@dataclass
class OEMNeedScore:
    total: float                    # 0–100
    tier: str                       # HOT / WARM / COLD
    icp: str                        # primary ICP label
    reasons: List[str] = field(default_factory=list)

    # Dimension breakdown
    international_score: float = 0.0
    battery_score: float = 0.0
    icp_score: float = 0.0
    show_score: float = 0.0
    urgency_score: float = 0.0
    freight_score: float = 0.0
    operational_risk_score: float = 0.0

    def as_dict(self) -> dict:
        return {
            "total": round(self.total, 1),
            "tier": self.tier,
            "icp": self.icp,
            "reasons": self.reasons,
            "dimensions": {
                "international": round(self.international_score, 1),
                "battery_risk": round(self.battery_score, 1),
                "icp_match": round(self.icp_score, 1),
                "show_relevance": round(self.show_score, 1),
                "urgency": round(self.urgency_score, 1),
                "freight_signals": round(self.freight_score, 1),
                "operational_risk": round(self.operational_risk_score, 1),
            },
        }


# ── Scorer ─────────────────────────────────────────────────────────────────────

def score(text: str, company_name: Optional[str] = None) -> OEMNeedScore:
    """
    Score an OEM prospect's need for StageGate robot operational infrastructure.

    Args:
        text:         Full text blob — headline + description + any enrichment.
                      Combine everything you have about this company/article.
        company_name: Optional company name for name-specific checks.

    Returns:
        OEMNeedScore with total (0–100), tier, ICP label, reasons, dimensions.
    """
    full_text = f"{company_name or ''} {text}"
    reasons: List[str] = []
    intl = battery = icp_pts = show = urgency = freight = ops_risk = 0.0
    icp_label = "General Robotics"

    # ── 1. International origin ─────────────────────────────────────────────────
    intl_matches = _INTL_COUNTRY_RE.findall(full_text)
    if intl_matches:
        intl = min(30.0, 15.0 + len(set(m.lower() for m in intl_matches)) * 5)
        terms = ", ".join(sorted(set(m.lower() for m in intl_matches))[:3])
        reasons.append(f"International company ({terms}) — no US ops team, highest support gap")

    if re.search(r"\bpavilion\b", full_text, re.I):
        intl = min(35.0, intl + 10.0)
        reasons.append("Country pavilion exhibitor — first US appearance, zero local infrastructure")

    # Chinese companies entering US get extra flag (language + customs + no team)
    if re.search(r"\b(china|chinese|beijing|shanghai|shenzhen)\b", full_text, re.I):
        intl = min(38.0, intl + 5.0)
        reasons.append("Chinese company entering US market — language barrier + customs complexity + no US team")

    # ── 2. Battery / hazmat ─────────────────────────────────────────────────────
    battery_matches = _BATTERY_RE.findall(full_text)
    if battery_matches:
        battery = min(20.0, 10.0 + len(set(m.lower() for m in battery_matches)) * 3)
        reasons.append("Battery / hazmat signals — bonded storage, ATA carnet, and charge management needed")

    # ── 3. ICP match — 7 primary target profiles ───────────────────────────────
    # Each ICP has a calibrated weight based on operational risk and support gap.

    if _HUMANOID_RE.search(full_text):
        # Highest operational risk: balance, sensors, IMU, joint calibration
        icp_pts = max(icp_pts, 28.0)
        icp_label = "Foreign Humanoid / Exoskeleton"
        reasons.append(
            "Humanoid / exoskeleton — IMU, joint calibration, balance recalibration after transit. "
            "Most operationally complex robot type."
        )

    if _MEDICAL_ROBOT_RE.search(full_text):
        # Precision-critical: cannot fail during demo, regulatory liability
        icp_pts = max(icp_pts, 26.0)
        icp_label = "Medical Robot"
        reasons.append(
            "Medical robot — precision-critical, regulatory-sensitive. "
            "Demo failure has reputational and liability consequences."
        )

    if _SECURITY_ROBOT_RE.search(full_text):
        # Autonomous navigation, liability-sensitive, often international
        icp_pts = max(icp_pts, 22.0)
        if icp_label == "General Robotics":
            icp_label = "Security / Patrol Robot"
        reasons.append(
            "Security robot — autonomous navigation, liability-sensitive. "
            "Needs map validation and sensor certification after shipping."
        )

    if _HOSPITALITY_ROBOT_RE.search(full_text):
        # Customer-facing: public failure is brand damage
        icp_pts = max(icp_pts, 20.0)
        if icp_label == "General Robotics":
            icp_label = "Hospitality / Service Robot"
        reasons.append(
            "Hospitality / service robot — customer-facing, public demo. "
            "Failure is visible brand damage; highest receptiveness to on-site support."
        )

    if _WAREHOUSE_AMR_RE.search(full_text):
        # Fleet complexity: mapping, fleet management, charging infrastructure
        icp_pts = max(icp_pts, 20.0)
        if icp_label == "General Robotics":
            icp_label = "Warehouse AMR"
        reasons.append(
            "Warehouse AMR — fleet mapping, charging infrastructure, and orchestration "
            "all need reconfiguration at a new venue."
        )

    if _DRONE_RE.search(full_text):
        # FAA indoor permits, battery sensitivity, crash recovery
        icp_pts = max(icp_pts, 18.0)
        if icp_label == "General Robotics":
            icp_label = "Drone / UAV"
        reasons.append(
            "Drone / UAV — FAA indoor flight authorization, battery sensitivity, "
            "propeller inspection, and crash recovery support."
        )

    if _INDUSTRIAL_ARM_RE.search(full_text):
        icp_pts = max(icp_pts, 15.0)
        if icp_label == "General Robotics":
            icp_label = "Industrial Arm / Cobot"
        reasons.append(
            "Industrial arm / cobot — rigging, electrical, end-effector re-mounting "
            "after transit. Teaching-point recalibration needed."
        )

    if _EUREKA_PARK_RE.search(full_text):
        # Startup at Eureka Park: tiny team, first US show, no support
        icp_pts = min(icp_pts + 8.0, 30.0)
        if icp_label == "General Robotics":
            icp_label = "Eureka Park Startup"
        reasons.append(
            "Eureka Park / CES startup — smallest team, first US show. "
            "Highest receptiveness: they literally cannot handle ops alone."
        )

    # ── 4. Show relevance ───────────────────────────────────────────────────────
    if _LAS_VEGAS_SHOW_RE.search(full_text):
        show = 20.0
        reasons.append("Las Vegas show — StageGate home market, fastest response and setup time")
    elif _OTHER_US_SHOW_RE.search(full_text):
        show = 10.0
        reasons.append("Major US show — logistics and ops support opportunity")

    # ── 5. Urgency / debut signals ──────────────────────────────────────────────
    if _FIRST_TIMER_RE.search(full_text):
        urgency += 10.0
        reasons.append(
            "First-time US exhibitor — operational risk peaks here. "
            "Most receptive window for StageGate outreach."
        )
    if _PRODUCT_LAUNCH_RE.search(full_text):
        urgency = min(15.0, urgency + 8.0)
        reasons.append(
            "World premiere / product launch — zero tolerance for logistics failure. "
            "Highest urgency, easiest sell."
        )

    # ── 6. Freight / customs complexity ─────────────────────────────────────────
    if _FREIGHT_TROUBLE_RE.search(full_text):
        freight = 10.0
        reasons.append("Freight / customs language — already aware of shipping complexity")

    # ── 7. Operational risk language ────────────────────────────────────────────
    if _OPERATIONAL_RISK_RE.search(full_text):
        ops_risk = 12.0
        reasons.append(
            "Operational risk signals detected — calibration, diagnostics, or tech support "
            "language present. Company is already thinking about operational support."
        )

    total = min(100.0, intl + battery + icp_pts + show + urgency + freight + ops_risk)

    if total >= 60:
        tier = "HOT"
    elif total >= 35:
        tier = "WARM"
    else:
        tier = "COLD"

    return OEMNeedScore(
        total=total,
        tier=tier,
        icp=icp_label,
        reasons=reasons,
        international_score=intl,
        battery_score=battery,
        icp_score=icp_pts,
        show_score=show,
        urgency_score=urgency,
        freight_score=freight,
        operational_risk_score=ops_risk,
    )


def score_batch(items: List[dict]) -> List[dict]:
    """
    Score a batch of OEM prospects.

    Each item should have:
        company_name (str)
        text         (str)  — full blob of all available text

    Returns items with 'oem_need' field added.
    """
    results = []
    for item in items:
        s = score(
            text=item.get("text", ""),
            company_name=item.get("company_name"),
        )
        results.append({**item, "oem_need": s.as_dict()})
    return results
