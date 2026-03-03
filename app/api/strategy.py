"""
Strategy API
============
GET /api/strategy
  Returns the top 25 scored leads enriched with a full per-opportunity
  sales strategy — robot recommendation, contact target, outreach timing,
  pitch angle, and deal-size estimate.

  Query params:
    limit   int   default 25   — how many opportunities to return (max 50)
    date    str   optional     — ISO date string, used as report label
"""

from datetime import date as dt_date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import Optional

from app.database import get_db
from app.models.company import Company
from app.models.contact import Contact
from app.models.daily_report import DailyReport
from app.services.lead_filter import classify_lead, qualify_hot_lead, strip_html
from app.services.signal_ranker import compute_weighted_score

router = APIRouter()

# ─── Robot recommendations by industry ────────────────────────────────────────

ROBOT_MAP = {
    "Automotive Dealerships": {
        "robots":    ["Titan", "DUST-E", "ADAM"],
        "primary":   "Titan",
        "use_case":  "Parts-to-bay delivery, service drive logistics, lounge hospitality",
    },
    "Automotive Manufacturing": {
        "robots":    ["Titan AMR Fleet"],
        "primary":   "Titan",
        "use_case":  "Kitting, WIP line replenishment, dock-to-line intra-facility transport",
    },
    "Automotive Innovation & Ventures": {
        "robots":    ["Titan", "DUST-E"],
        "primary":   "Titan",
        "use_case":  "Smart factory pilot with partnership or investment discussion",
    },
    "Aerospace & Defense": {
        "robots":    ["Titan AMR Fleet"],
        "primary":   "Titan",
        "use_case":  "Factory floor AMR, MRO parts logistics, tool/kit delivery",
    },
    "Hospitality": {
        "robots":    ["Matradee L5", "ADAM"],
        "primary":   "Matradee L5",
        "use_case":  "In-room delivery, F&B service, lobby concierge support",
    },
    "Logistics": {
        "robots":    ["Titan AMR Fleet"],
        "primary":   "Titan",
        "use_case":  "Warehouse AMR fleet, goods-to-person, sortation assist",
    },
    "Healthcare": {
        "robots":    ["Titan", "ADAM"],
        "primary":   "Titan",
        "use_case":  "Clinical supply delivery, sterile logistics, pharmacy runs",
    },
    "Food Service": {
        "robots":    ["ADAM", "Matradee L5"],
        "primary":   "ADAM",
        "use_case":  "Back-of-house automation, tableside delivery, runner replacement",
    },
    "Casinos & Gaming": {
        "robots":    ["ADAM", "Matradee L5"],
        "primary":   "ADAM",
        "use_case":  "Casino floor F&B delivery, VIP suite service, bar runner",
    },
    "Cruise Lines": {
        "robots":    ["Matradee L5", "ADAM"],
        "primary":   "Matradee L5",
        "use_case":  "Cabin & dining delivery, deck service, events support",
    },
    "Theme Parks & Entertainment": {
        "robots":    ["Matradee L5", "ADAM"],
        "primary":   "Matradee L5",
        "use_case":  "F&B delivery across attraction zones, custodial support",
    },
    "Real Estate & Facilities": {
        "robots":    ["DUST-E SX", "ADAM"],
        "primary":   "DUST-E SX",
        "use_case":  "Commercial floor cleaning, lobby concierge, amenity delivery",
    },
    "Manufacturing": {
        "robots":    ["Titan AMR Fleet"],
        "primary":   "Titan",
        "use_case":  "Intra-facility parts delivery, kitting, WIP replenishment",
    },
    "Distribution": {
        "robots":    ["Titan AMR Fleet"],
        "primary":   "Titan",
        "use_case":  "Warehouse AMR deployment, goods-to-person pick assist",
    },
    "Senior Living": {
        "robots":    ["ADAM", "Matradee L5"],
        "primary":   "ADAM",
        "use_case":  "Meal delivery, medication supply rounds, resident engagement",
    },
    "Retail": {
        "robots":    ["ADAM", "DUST-E SX"],
        "primary":   "ADAM",
        "use_case":  "In-store customer assistance, inventory scan, click-and-collect",
    },
}

_DEFAULT_ROBOT = {
    "robots":   ["Titan"],
    "primary":  "Titan",
    "use_case": "Intra-facility AMR deployment",
}

# ─── Signal urgency & timing ──────────────────────────────────────────────────

SIGNAL_TIMING = {
    "labor_shortage":         "URGENT — Labor pain is live. Contact within 48 hours.",
    "labor_pain":             "URGENT — Active labor pain signal. Reach out today.",
    "capex":                  "TIME-SENSITIVE — CapEx window is open. Engage this week.",
    "strategic_hire":         "IMMEDIATE — New decision-maker just started. First-90-day window.",
    "expansion":              "ALIGNED — New facility incoming. Propose automation as day-one infra.",
    "funding_round":          "STRIKE FAST — 2 weeks post-funding before budget is committed.",
    "ma_activity":            "OPPORTUNISTIC — M&A disruption creates vendor openings.",
    "job_posting":            "ONGOING — Chronic hiring signals sustained automation need.",
    "news":                   "HOOK — Use the news mention as the outreach conversation opener.",
    "automation_intent":      "HIGH PRIORITY — Active automation program in progress.",
    "equipment_integration":  "ALIGNED — WMS/ERP rollout signals robot-ready infrastructure.",
    "service_consistency":    "TIMELY — Brand standard pressure is creating automation urgency.",
}

_DEFAULT_TIMING = "Monitor — Queue for follow-up in 30 days."

# ─── Contact role by industry ─────────────────────────────────────────────────

CONTACT_MAP = {
    "Automotive Dealerships":           "Fixed Ops Director or Parts Manager",
    "Automotive Manufacturing":         "VP of Manufacturing Operations or Plant Manager",
    "Automotive Innovation & Ventures": "Innovation Director or Venture Partner",
    "Aerospace & Defense":              "VP of Manufacturing Operations or Director of MRO",
    "Hospitality":                      "VP of Operations or Director of Guest Services",
    "Logistics":                        "VP of Logistics or Warehouse Operations Manager",
    "Healthcare":                       "VP of Operations or Director of Supply Chain",
    "Food Service":                     "Director of Operations or COO",
    "Casinos & Gaming":                 "VP of F&B or VP of Hotel Operations",
    "Cruise Lines":                     "VP of Hotel Operations or F&B Director",
    "Theme Parks & Entertainment":      "VP of Operations or Director of Guest Experience",
    "Real Estate & Facilities":         "Director of Facilities or VP of Property Operations",
    "Manufacturing":                    "VP of Manufacturing or Plant Manager",
    "Distribution":                     "Director of Distribution Operations",
    "Senior Living":                    "VP of Operations or Director of Resident Services",
    "Retail":                           "VP of Store Operations or Director of In-Store Experience",
}

_DEFAULT_CONTACT = "VP of Operations or COO"

# ─── Pitch generator ─────────────────────────────────────────────────────────

def _pitch(industry: str, top_signal: str, robot: str) -> str:
    """Generate a one-sentence pitch angle tailored to industry + signal."""
    combos = {
        ("Automotive Dealerships",  "labor_shortage"):  f"Your dealership is paying overtime just to move parts — {robot} eliminates that permanently.",
        ("Automotive Dealerships",  "capex"):           f"Your open CapEx budget is a perfect window to deploy {robot} across parts and service.",
        ("Automotive Dealerships",  "expansion"):       f"As you add stores, {robot} lets each new location run parts ops with fewer bodies.",
        ("Automotive Manufacturing","labor_shortage"):  f"Your plant is fighting the labor market — {robot} fills the gap with consistent throughput.",
        ("Automotive Manufacturing","capex"):           f"Your technology spend window is open; {robot} fleet ROI is measurable inside 18 months.",
        ("Automotive Manufacturing","expansion"):       f"New line capacity means new logistics demand — {robot} scales with your footprint.",
        ("Aerospace & Defense",     "capex"):           f"Defense-grade precision meets {robot}'s MRO-ready transport — schedule a facility walkthrough.",
        ("Aerospace & Defense",     "expansion"):       f"New production line = {robot} fleet from day one; we spec to your clearance requirements.",
        ("Hospitality",             "labor_shortage"):  f"When you can't hire enough runners, {robot} delivers to every room 24/7 without turnover.",
        ("Hospitality",             "expansion"):       f"Every new property is an opportunity to launch with {robot} built into the guest experience.",
        ("Logistics",               "capex"):           f"Warehouse CapEx is live — {robot} fleet ROI closes inside 12 months at your throughput.",
        ("Logistics",               "expansion"):       f"New DC means fresh automation budget — {robot} fleet is day-one ready.",
        ("Food Service",            "labor_shortage"):  f"You can't hire runners fast enough — {robot} handles every delivery shift without a sick day.",
        ("Casinos & Gaming",        "capex"):           f"Gaming reinvestment funds fit {robot} perfectly — F&B velocity and guest scores both jump.",
    }
    key = (industry, top_signal)
    if key in combos:
        return combos[key]

    # Generic fallbacks by industry
    generic = {
        "Automotive Dealerships":           f"Reduce parts delivery labor costs by 40% and cut bay wait times with {robot}.",
        "Automotive Manufacturing":         f"Automate kitting and WIP transport with {robot} — your operators focus on value-add work.",
        "Automotive Innovation & Ventures": f"Partner with Richtech to deploy {robot} as a flagship smart facility showcase.",
        "Aerospace & Defense":              f"Precision MRO logistics with {robot} — traceable, consistent, compliant.",
        "Hospitality":                      f"Elevate guest experience and cut labor costs with {robot} handling every delivery.",
        "Logistics":                        f"Scale throughput without headcount with a {robot} AMR fleet customized to your DC.",
        "Healthcare":                       f"Ensure supply reliability and reduce staff walking time with {robot} clinical logistics.",
        "Food Service":                     f"Let {robot} handle every delivery so your team focuses on food quality and service.",
        "Casinos & Gaming":                 f"Boost F&B speed-of-service scores and free your staff for the guest moments that matter.",
        "Cruise Lines":                     f"Delight guests with {robot} cabin delivery — a differentiator no competitor has yet deployed.",
        "Theme Parks & Entertainment":      f"Cut F&B walk time in half and improve queue flow with {robot} across your attraction zones.",
        "Real Estate & Facilities":         f"Consistent, cost-effective floor cleaning and concierge with {robot} — 24/7, no turnover.",
    }
    return generic.get(industry, f"Deploy {robot} to reduce labor dependency and improve operational consistency.")


# ─── Deal tier ────────────────────────────────────────────────────────────────

def _deal_tier(emp: Optional[int]) -> dict:
    if not emp:
        return {"tier": "Unknown", "est_units": 3}
    if emp >= 50000:
        return {"tier": "Enterprise",   "est_units": 50}
    if emp >= 10000:
        return {"tier": "Large",        "est_units": 25}
    if emp >= 2000:
        return {"tier": "Mid-Market",   "est_units": 10}
    if emp >= 500:
        return {"tier": "Regional",     "est_units": 5}
    return {"tier": "SMB", "est_units": 2}


# ─── Talking points ───────────────────────────────────────────────────────────

def _talking_points(industry: str, pri_reasons: list, signals: list, robot: str) -> list:
    points = []

    # Use priority reasons if present
    for r in pri_reasons[:2]:
        points.append(r.capitalize())

    # Add signal-driven talking point
    for sig in signals[:2]:
        st = sig.get("signal_type", "")
        txt = sig.get("raw_text", "")
        if st == "labor_shortage":
            points.append(f"Labor shortage signal detected — automation ROI justification is already built.")
        elif st == "capex" and txt:
            points.append(f"Active CapEx spend confirms budget authority is in place.")
        elif st == "strategic_hire":
            points.append(f"New leadership hire — first-mover advantage on vendor talks.")
        elif st == "expansion":
            points.append(f"Expansion activity = greenfield automation opportunity.")
        elif st == "funding_round":
            points.append(f"Recently funded — budget is available and unallocated.")
        elif st == "ma_activity":
            points.append(f"M&A activity creates operational gaps {robot} can fill immediately.")
        elif st == "job_posting":
            points.append(f"Active job postings confirm persistent labor demand → automation case is easy.")
        if len(points) >= 3:
            break

    # Fallback if still short
    fallbacks = {
        "Automotive Dealerships":  "Fixed Ops productivity is directly measurable — show ROI per bay.",
        "Automotive Manufacturing":"OEM-grade traceability and cycle-time data available on request.",
        "Aerospace & Defense":     "Titan meets AS9100-adjacent handling requirements — compliance-friendly.",
        "Hospitality":             "Guest satisfaction score lift is the fastest way to justify the purchase.",
        "Logistics":               "Payback period under 18 months at standard DC throughput.",
        "Healthcare":              "Reduces walking time per nurse by an average of 1.2 miles per shift.",
        "Food Service":            "Consistent delivery speed improves table turn rate by 12–18%.",
        "Casinos & Gaming":        "F&B delivery speed directly correlates with spend per visit.",
        "Logistics":               "Zero-touch replenishment at picks above 400 units/hour.",
    }
    if len(points) < 3 and industry in fallbacks:
        points.append(fallbacks[industry])

    return points[:3] if points else [f"Demonstrate {robot} ROI with a 30-day pilot proposal."]


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.get("")
@router.get("/")
def get_strategy(
    limit: int = Query(25, description="Number of opportunities (max 50)"),
    date:  Optional[str] = Query(None, description="Report date label (ISO format)"),
    db: Session = Depends(get_db),
):
    """
    Daily strategy brief — top N leads enriched with robot recommendation,
    contact target, outreach timing, pitch angle, and deal-size estimate.
    """
    limit = min(limit, 50)
    report_date = date or str(dt_date.today())

    companies = (
        db.query(Company)
        .options(joinedload(Company.scores), selectinload(Company.signals))
        .limit(2000)
        .all()
    )

    results = []
    for c in companies:
        junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
        if junk:
            continue

        s = c.scores
        sigs = sorted(c.signals or [], key=lambda x: x.signal_strength, reverse=True)

        # Robot recommendation
        industry = (c.industry or "").strip()
        rmap = ROBOT_MAP.get(industry, _DEFAULT_ROBOT)
        primary_robot = rmap["primary"]

        # Top signal for timing + pitch
        top_sig_type = sigs[0].signal_type if sigs else "news"

        fmt_signals = [
            {
                "signal_type":    sig.signal_type,
                "strength":       sig.signal_strength,
                "weighted_score": compute_weighted_score(sig),
                "raw_text":       strip_html(sig.signal_text),
            }
            for sig in sigs
        ]

        deal = _deal_tier(c.employee_estimate)
        contact = CONTACT_MAP.get(industry, _DEFAULT_CONTACT)
        timing  = SIGNAL_TIMING.get(top_sig_type, _DEFAULT_TIMING)
        pitch   = _pitch(industry, top_sig_type, primary_robot)
        talking = _talking_points(industry, pri.reasons, fmt_signals, primary_robot)

        # ── Contacts (from contacts table) ──────────────────────────────
        db_contacts = (
            db.query(Contact)
            .filter(Contact.company_id == c.id)
            .order_by(Contact.confidence_score.desc())
            .all()
        )
        contacts_out = [
            {
                "name":       f"{ct.first_name} {ct.last_name}".strip(),
                "title":      ct.title or contact,
                "linkedin":   ct.linkedin_url,
                "email":      ct.email,
                "confidence": ct.confidence_score,
                "verified":   bool(ct.linkedin_url and (ct.confidence_score or 0) >= 90),
            }
            for ct in db_contacts
        ]

        # ── HOT qualification ─────────────────────────────────────────────
        hot_qual = None
        if pri.tier == "HOT":
            hq = qualify_hot_lead(c.signals or [])
            hot_qual = {
                "buying_window":       hq.buying_window,
                "intent_confidence":   hq.intent_confidence,
                "recommended_action":  hq.recommended_action,
                "window_evidence":     hq.window_evidence,
                "confidence_drivers":  hq.confidence_drivers,
                "freshest_signal_days": hq.freshest_signal_days,
            }

        results.append({
            # Core lead fields
            "id":               c.id,
            "company_name":     c.name,
            "website":          c.website,
            "industry":         industry,
            "location_city":    c.location_city,
            "location_state":   c.location_state,
            "employee_estimate": c.employee_estimate,
            "source":           c.source,
            # Priority
            "priority_tier":    pri.tier,
            "priority_score":   round(pri.score, 1),
            "priority_reasons": pri.reasons,
            # Scores
            "score": {
                "overall_score":    round((s.overall_intent_score if s else 0), 1),
                "automation_score": round((s.automation_score     if s else 0), 1),
                "labor_pain_score": round((s.labor_pain_score     if s else 0), 1),
                "expansion_score":  round((s.expansion_score      if s else 0), 1),
                "market_fit_score": round((s.robotics_fit_score   if s else 0), 1),
            },
            "signal_count":    len(sigs),
            "signals":         fmt_signals,
            "contacts":        contacts_out,
            "hot_qualification": hot_qual,
            # Strategy fields
            "strategy": {
                "robots":          rmap["robots"],
                "primary_robot":   primary_robot,
                "use_case":        rmap["use_case"],
                "contact_role":    contact,
                "outreach_timing": timing,
                "pitch_angle":     pitch,
                "talking_points":  talking,
                "deal_tier":       deal["tier"],
                "deal_est_units":  deal["est_units"],
            },
        })

    # Sort: HOT first, then by priority_score descending
    tier_order = {"HOT": 0, "WARM": 1, "COLD": 2}
    results.sort(key=lambda x: (tier_order.get(x["priority_tier"], 3), -x["priority_score"]))
    results = results[:limit]

    return {
        "report_date":       report_date,
        "opportunity_count": len(results),
        "contacts_found":    sum(len(r.get("contacts", [])) for r in results),
        "opportunities":     results,
    }


@router.get("/today")
def get_today_report(db: Session = Depends(get_db)):
    """
    Returns the most recently *published* daily top-25 brief.
    This is the stored snapshot from `daily_reports` — stable throughout the day.
    Falls back to the most recent published report from a prior day if today's
    hasn't been generated yet (avoids the slow live-scan before the 07:30 UTC job).
    Only generates a live report when there are no published reports at all.
    """
    today = dt_date.today()

    # Look for today's published report first, then any recent report
    report = (
        db.query(DailyReport)
        .order_by(DailyReport.report_date.desc())
        .first()
    )

    if report:
        data = report.get_data()
        data["source"] = "published"
        data["published_at"] = report.generated_at.isoformat() if report.generated_at else None
        # Flag if we're serving a prior day's report (before today's 07:30 UTC job)
        if report.report_date < today:
            data["report_date"] = str(today)   # show today's date in header
            data["prior_date"]  = str(report.report_date)
        return data

    # No published report at all yet — fall back to live strategy (first-run only)
    return get_strategy(limit=25, date=str(today), db=db)


@router.get("/history")
def get_report_history(limit: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """
    Returns metadata for the last N published daily reports (no full payload).
    """
    rows = (
        db.query(DailyReport)
        .order_by(DailyReport.report_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "report_date":      r.report_date.isoformat(),
            "generated_at":     r.generated_at.isoformat() if r.generated_at else None,
            "opportunity_count": r.opportunity_count,
            "contacts_found":   r.contacts_found,
        }
        for r in rows
    ]
