"""
Buyer-intent gate — assess, stamp, and triage end-customer buying evidence.

Used by classify_lead (display junk), secondary pass routing, and harness telemetry.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from app.services.industry_inference import known_industry_for_company_name
from app.services.lead_filter import (
    _buyer_opportunity_gate,
    is_allowlisted_company_name,
)


@dataclass
class BuyerIntentGateResult:
    passed: bool
    reason: str
    disposition: str
    route: str  # pass | secondary | quarantine
    known_brand: bool = False
    has_signals: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_known_buyer_brand(name: str) -> bool:
    name = (name or "").strip()
    if not name:
        return False
    return bool(is_allowlisted_company_name(name) or known_industry_for_company_name(name))


def assess_buyer_intent_gate(
    *,
    company_name: Optional[str],
    signals: Iterable[Any],
) -> BuyerIntentGateResult:
    """
    Structured buyer-opportunity gate for instrumentation and triage.

    disposition:
      - pass — gate satisfied or known brand fast-path
      - no_intent — signals present but no labor/capex/deployment evidence
      - seller_story — vendor/publisher context without buyer intent
      - no_signals — no signal rows (non-promoted COLD; not quarantine target)
    """
    name = (company_name or "").strip()
    sigs = list(signals or [])
    known = _is_known_buyer_brand(name)

    if known:
        return BuyerIntentGateResult(
            passed=True,
            reason="known buyer brand",
            disposition="pass",
            route="pass",
            known_brand=True,
            has_signals=bool(sigs),
        )

    if not sigs:
        return BuyerIntentGateResult(
            passed=True,
            reason="no signals — non-promoted COLD",
            disposition="no_signals",
            route="secondary",
            known_brand=False,
            has_signals=False,
        )

    ok, reason = _buyer_opportunity_gate(sigs, company_name=name)
    if ok:
        return BuyerIntentGateResult(
            passed=True,
            reason="",
            disposition="pass",
            route="pass",
            known_brand=False,
            has_signals=True,
        )

    if "seller/vendor or publisher" in (reason or ""):
        disposition = "seller_story"
        route = "quarantine"
    else:
        disposition = "no_intent"
        route = "quarantine"

    return BuyerIntentGateResult(
        passed=False,
        reason=reason or "buyer intent gate failed",
        disposition=disposition,
        route=route,
        known_brand=False,
        has_signals=True,
    )


def stamp_buyer_intent_gate(company, result: BuyerIntentGateResult) -> None:
    """Persist gate outcome on company.crm_metadata for harness trending."""
    raw = getattr(company, "crm_metadata", None)
    meta = dict(raw) if isinstance(raw, dict) else {}
    meta["buyer_intent_gate"] = {
        **result.to_dict(),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }
    company.crm_metadata = meta


def classify_lead_junk_reason_matches_buyer_gate(junk_reason: str) -> bool:
    low = (junk_reason or "").lower()
    return "buyer opportunity gate" in low
