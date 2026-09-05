"""
Cal Assembly Agent — curate leads and review copy before autonomous send.

Rule-based gates always run (fail closed). Optional LLM review when ANTHROPIC/OPENAI is set.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.cal_persona import CAL_LLM_SYSTEM, cal_persona_payload

logger = logging.getLogger(__name__)

_FORBIDDEN_PRODUCT_MARKERS = (
    "onstage.bot",
    "stagegate",
    "bonded warehousing",
    "move-in dates",
    "booth number",
)
_MISATTRIBUTED_SIGNAL_RE = re.compile(
    r"\b(skye air|drone delivery|scale up drone|trials humanoid robots as ground handlers)\b",
    re.I,
)


@dataclass
class AssemblyResult:
    approved: bool
    reason: str
    matches: list[dict[str, Any]] = field(default_factory=list)
    subject: str = ""
    body: str = ""
    checks: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    llm_reviewed: bool = False
    llm_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def cal_assembly_required() -> bool:
    return os.getenv("CAL_ASSEMBLY_REQUIRED", "1").strip().lower() not in ("0", "false", "no")


def cal_llm_review_enabled() -> bool:
    if os.getenv("CAL_ASSEMBLY_LLM_REVIEW", "1").strip().lower() in ("0", "false", "no"):
        return False
    from app.services.llm_client import active_provider

    return active_provider() is not None


def _company_name_in_signal(company_name: str, signal_text: str) -> bool:
    name = (company_name or "").strip().lower()
    blob = (signal_text or "").lower()
    if not name or not blob:
        return False
    if name in blob:
        return True
    tokens = [t for t in re.split(r"[\s'&]+", name) if len(t) >= 4]
    return bool(tokens) and any(tok in blob for tok in tokens)


def curate_supply_matches(
    db: Session,
    robot_company: Any,
    matches: list[dict[str, Any]],
    *,
    min_matches: int = 2,
    limit: int = 3,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Re-validate matches at assembly time; drop anything that fails pipeline gates."""
    from app.api.robot_companies import _supply_buyer_lead_eligible
    from app.models.company import Company

    issues: list[str] = []
    curated: list[dict[str, Any]] = []

    for match in matches:
        company_id = int(match.get("id") or 0)
        if not company_id:
            issues.append(f"Match missing company id: {match.get('company_name')}")
            continue
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            issues.append(f"Company id {company_id} not found")
            continue
        ok, skip = _supply_buyer_lead_eligible(company, robot_company)
        if not ok:
            issues.append(f"{company.name}: {skip}")
            continue
        from app.services.cal_pipeline_enrichment import enrichment_supply_eligible

        enrich_ok, enrich_skip = enrichment_supply_eligible(company)
        if not enrich_ok:
            issues.append(f"{company.name}: {enrich_skip}")
            continue
        signal = str(match.get("signal") or "")
        if signal and not _company_name_in_signal(company.name or "", signal):
            issues.append(f"{company.name}: signal does not corroborate company name")
            continue
        if signal and _MISATTRIBUTED_SIGNAL_RE.search(signal):
            issues.append(f"{company.name}: signal looks mis-attributed or off-topic")
            continue
        curated.append(match)
        if len(curated) >= limit:
            break

    if len(curated) < min_matches:
        issues.append(f"Only {len(curated)} vetted match(es); need {min_matches}")

    return curated, issues


def _rule_review_supply(
    *,
    robot_company: Any,
    matches: list[dict[str, Any]],
    subject: str,
    body: str,
    min_matches: int,
) -> AssemblyResult:
    checks: list[str] = []
    issues: list[str] = []

    vendor_name = (getattr(robot_company, "company_name", None) or "").strip()
    if not vendor_name:
        issues.append("Robot company name missing")
    elif vendor_name.lower() not in (body or "").lower():
        issues.append("Email body does not mention vendor company name")

    checks.append("vendor_name_in_body")

    if len(matches) < min_matches:
        issues.append(f"Insufficient matches: {len(matches)} < {min_matches}")
    checks.append("min_matches")

    body_low = (body or "").lower()
    for marker in _FORBIDDEN_PRODUCT_MARKERS:
        if marker in body_low:
            issues.append(f"Wrong product voice in body: {marker}")
    checks.append("rfr_product_voice")

    for match in matches:
        name = str(match.get("company_name") or "")
        signal = str(match.get("signal") or "")
        if name and name not in body:
            issues.append(f"Match {name} not reflected in email body")
        low_name = name.lower()
        if low_name in ("brain corp", "uc davis") or "brain corp" in low_name:
            issues.append(f"Blocked vendor/research name in matches: {name}")

    from app.services.robot_vendor_names import is_known_robotics_vendor_name

    for match in matches:
        name = str(match.get("company_name") or "")
        if is_known_robotics_vendor_name(name):
            issues.append(f"OEM/vendor cited as buyer: {name}")
    checks.append("no_oem_buyers")

    approved = not issues
    return AssemblyResult(
        approved=approved,
        reason="rule_pass" if approved else "rule_fail",
        matches=matches,
        subject=subject,
        body=body,
        checks=checks,
        issues=issues,
    )


def _llm_review_supply(
    *,
    robot_company: Any,
    matches: list[dict[str, Any]],
    subject: str,
    body: str,
) -> Optional[AssemblyResult]:
    from app.services.llm_client import llm_json_completion

    vendor = getattr(robot_company, "company_name", "") or ""
    robot_type = getattr(robot_company, "robot_type", "") or ""
    target = getattr(robot_company, "target_market", "") or ""

    match_block = json.dumps(
        [
            {
                "company": m.get("company_name"),
                "industry": m.get("industry"),
                "why": m.get("why_match"),
                "signal": (m.get("signal") or "")[:400],
            }
            for m in matches
        ],
        indent=2,
    )

    user_prompt = f"""Review this supply-side outreach BEFORE send.

Vendor: {vendor} (robot_type={robot_type}, target_market={target})

Subject: {subject}

Body:
{body[:3500]}

Buyer matches cited:
{match_block}

Approve ONLY if every cited company is an operating buyer (not OEM/vendor/university/research headline),
signals support the claim, tone matches Cal persona, and the email drives signup without hype.
"""

    raw = llm_json_completion(CAL_LLM_SYSTEM, user_prompt, max_tokens=800, temperature=0.2)
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Cal assembly LLM returned non-JSON")
        return None

    approved = bool(data.get("approved"))
    issues = [str(x) for x in (data.get("issues") or []) if x]
    return AssemblyResult(
        approved=approved,
        reason="llm_pass" if approved else "llm_fail",
        matches=matches,
        subject=subject,
        body=body,
        checks=["llm_review"],
        issues=issues,
        llm_reviewed=True,
        llm_summary=str(data.get("summary") or ""),
    )


def assemble_supply_outreach(
    db: Session,
    robot_company: Any,
    matches: list[dict[str, Any]],
    *,
    subject: str,
    body: str,
    min_matches: Optional[int] = None,
) -> AssemblyResult:
    """
    Curate matches + rule review + optional LLM review.
    Caller must not send when approved is False.
    """
    min_n = min_matches if min_matches is not None else int(
        os.getenv("SUPPLY_AUTONOMY_MIN_MATCHES", "2") or "2"
    )
    curated, curate_issues = curate_supply_matches(
        db, robot_company, matches, min_matches=min_n, limit=3
    )
    if curate_issues and len(curated) < min_n:
        return AssemblyResult(
            approved=False,
            reason="curate_fail",
            matches=curated,
            subject=subject,
            body=body,
            checks=["curate_supply_matches"],
            issues=curate_issues,
        )

    # Rebuild match lines in body if curation dropped rows — caller should rebuild email;
    # flag if curated set differs from what body cites.
    rule = _rule_review_supply(
        robot_company=robot_company,
        matches=curated,
        subject=subject,
        body=body,
        min_matches=min_n,
    )
    if not rule.approved:
        rule.matches = curated
        return rule

    if cal_llm_review_enabled():
        llm = _llm_review_supply(
            robot_company=robot_company,
            matches=curated,
            subject=subject,
            body=body,
        )
        if llm is not None:
            llm.matches = curated
            if not llm.approved:
                return llm
            rule.llm_reviewed = True
            rule.llm_summary = llm.llm_summary
            rule.checks.append("llm_review")

    rule.matches = curated
    rule.reason = "approved"
    return rule


def _body_has_buyer_anchor(company_name: str, body: str) -> bool:
    """True if body names the buyer (full legal name or known short label)."""
    name = (company_name or "").strip()
    if not name:
        return False
    low = (body or "").lower()
    if name.lower() in low:
        return True
    from app.services.agent_messaging import _KNOWN_TEAM_SHORT, _short_label

    short = _KNOWN_TEAM_SHORT.get(name.lower()) or _short_label(name)
    return bool(short) and short.lower() in low


def assemble_buyer_outreach(
    *,
    company_name: str,
    subject: str,
    body: str,
) -> AssemblyResult:
    """Lightweight assembly for buyer-side Cal autonomy sends."""
    issues: list[str] = []
    if not (company_name or "").strip():
        issues.append("Missing buyer company name")
    if company_name and not _body_has_buyer_anchor(company_name, body or ""):
        issues.append("Body missing buyer company name")

    body_low = (body or "").lower()
    for marker in _FORBIDDEN_PRODUCT_MARKERS:
        if marker in body_low:
            issues.append(f"Wrong product voice: {marker}")

    from app.services.cal_persona import CAL_BANNED_PHRASES

    for phrase in CAL_BANNED_PHRASES:
        if phrase in body_low:
            issues.append(f"Cal voice violation: {phrase}")

    from app.services.robot_vendor_names import is_known_robotics_vendor_name

    if is_known_robotics_vendor_name(company_name):
        issues.append("Target is a known robotics vendor/OEM")

    approved = not issues
    return AssemblyResult(
        approved=approved,
        reason="approved" if approved else "rule_fail",
        subject=subject,
        body=body,
        checks=["buyer_rule_review"],
        issues=issues,
    )


def get_cal_assembly_status() -> dict[str, Any]:
    return {
        "assembly_required": cal_assembly_required(),
        "llm_review_enabled": cal_llm_review_enabled(),
        "persona": cal_persona_payload(),
    }
