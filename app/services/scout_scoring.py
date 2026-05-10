from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.models.company import Company

FACTOR_WEIGHTS = {
    "readiness": 25,
    "useCase": 20,
    "roi": 15,
    "deploymentSize": 15,
    "recognizableProblem": 15,
    "customerValue": 10,
}


def normalize_domain(raw: str | None) -> str | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        parsed = urlparse(value if "://" in value else f"https://{value}")
        host = parsed.hostname or value
    except Exception:
        host = value
    host = host.lower().strip().removeprefix("www.")
    return host or None


def score_band(total: float | int | None) -> str:
    value = float(total or 0)
    if value >= 80:
        return "Hot"
    if value >= 60:
        return "Warm"
    if value >= 40:
        return "Developing"
    return "Monitoring"


def _latest_score(company: Company) -> Any | None:
    scores = list(getattr(company, "scores", None) or [])
    if not scores:
        return None
    return max(scores, key=lambda s: getattr(s, "last_calculated_at", None) or 0)


def _signal_strength(company: Company) -> float:
    signals = list(getattr(company, "signals", None) or [])
    if not signals:
        return 0.0
    total = 0.0
    for signal in signals[:12]:
        strength = float(getattr(signal, "signal_strength", 0.5) or 0.5)
        total += strength * (100 if strength <= 1 else 1)
    return min(100.0, total / max(1, min(len(signals), 12)))


def _clamp(value: float | int | None, maximum: int) -> int:
    if value is None:
        return 0
    return int(round(max(0, min(maximum, float(value)))))


def scout_score_for_company(company: Company | None, url: str | None = None, name: str | None = None) -> dict[str, Any]:
    if not company:
        fallback_name = (name or normalize_domain(url) or "Unknown company").strip()
        return {
            "total": 42,
            "band": score_band(42),
            "factors": {
                "readiness": 9,
                "useCase": 9,
                "roi": 6,
                "deploymentSize": 6,
                "recognizableProblem": 7,
                "customerValue": 5,
            },
            "weights": FACTOR_WEIGHTS,
            "summary": f"SCOUT has enough public signal to monitor {fallback_name}, but needs more evidence before calling it sales-ready.",
        }

    score = _latest_score(company)
    signal_strength = _signal_strength(company)
    overall = float(getattr(score, "overall_intent_score", 0.0) or signal_strength or 0.0)
    automation = float(getattr(score, "automation_score", 0.0) or 0.0)
    labor = float(getattr(score, "labor_pain_score", 0.0) or 0.0)
    expansion = float(getattr(score, "expansion_score", 0.0) or 0.0)
    robotics = float(getattr(score, "robotics_fit_score", 0.0) or automation or 0.0)
    employee_estimate = int(getattr(company, "employee_estimate", 0) or 0)

    factors = {
        "readiness": _clamp(overall / 100 * FACTOR_WEIGHTS["readiness"], FACTOR_WEIGHTS["readiness"]),
        "useCase": _clamp(robotics / 100 * FACTOR_WEIGHTS["useCase"], FACTOR_WEIGHTS["useCase"]),
        "roi": _clamp(max(labor, automation) / 100 * FACTOR_WEIGHTS["roi"], FACTOR_WEIGHTS["roi"]),
        "deploymentSize": _clamp((min(employee_estimate, 5000) / 5000 * 100 if employee_estimate else expansion) / 100 * FACTOR_WEIGHTS["deploymentSize"], FACTOR_WEIGHTS["deploymentSize"]),
        "recognizableProblem": _clamp(signal_strength / 100 * FACTOR_WEIGHTS["recognizableProblem"], FACTOR_WEIGHTS["recognizableProblem"]),
        "customerValue": _clamp(max(overall, automation, robotics) / 100 * FACTOR_WEIGHTS["customerValue"], FACTOR_WEIGHTS["customerValue"]),
    }
    total = int(sum(factors.values()))
    band = score_band(total)
    return {
        "total": total,
        "band": band,
        "factors": factors,
        "weights": FACTOR_WEIGHTS,
        "summary": f"{company.name} is a {band.lower()} SCOUT opportunity with {len(getattr(company, 'signals', None) or [])} tracked signal(s).",
    }


def serialize_company_result(company: Company | None, url: str | None = None, name: str | None = None) -> dict[str, Any]:
    score = scout_score_for_company(company, url=url, name=name)
    signals = []
    if company:
        for signal in list(getattr(company, "signals", None) or [])[:6]:
            signals.append(
                {
                    "type": getattr(signal, "signal_type", None),
                    "text": getattr(signal, "signal_text", None) or getattr(signal, "ingestion_raw_text", None),
                    "strength": getattr(signal, "signal_strength", None),
                    "sourceUrl": getattr(signal, "source_url", None),
                    "createdAt": getattr(signal, "created_at", None).isoformat() if getattr(signal, "created_at", None) else None,
                }
            )
    return {
        "company": {
            "id": getattr(company, "id", None) if company else None,
            "name": getattr(company, "name", None) if company else (name or normalize_domain(url) or "Unknown company"),
            "website": getattr(company, "website", None) if company else url,
            "industry": getattr(company, "industry", None) if company else None,
            "employeeEstimate": getattr(company, "employee_estimate", None) if company else None,
            "location": ", ".join(
                [p for p in [getattr(company, "location_city", None), getattr(company, "location_state", None)] if p]
            ) if company else None,
        },
        "score": score,
        "signals": signals,
        "nextBestActions": [
            "Validate the highest-strength signal with a human source.",
            "Map the buyer problem to one robotics use case.",
            "Draft a concise outreach note tied to current trigger events.",
        ],
    }
