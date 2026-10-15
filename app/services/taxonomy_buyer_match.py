"""Join taxonomy product records to mapped buyers.

A buyer matches when a taxonomy industry overlaps. When the buyer has taxonomy
function tags, one of those functions must overlap too. Buyers with no function
tags stay in the result and are marked function-unmapped, because the company
table does not carry the 29-industry function tags yet.

Rank is readiness first: RFP, procurement, tender, and solicitation before
every other signal. Rows whose source kind is a posting for people are dropped.
"""
from __future__ import annotations

from typing import Any

from app.services.job_posting_ingest_pause import FEED_CLASSIFICATION, PEOPLE_POSTING

_RFP = {"rfp", "procurement", "tender", "solicitation"}
_PEOPLE_KINDS = {
    kind for kind, label in FEED_CLASSIFICATION.items() if label == PEOPLE_POSTING
}


def is_people_posting_source(source_kind: str | None) -> bool:
    kind = (source_kind or "").strip().lower()
    return kind in _PEOPLE_KINDS or kind == PEOPLE_POSTING


def readiness_from_signals(stage: str | None, why: str | None) -> tuple[str | None, str | None]:
    """Classify an existing readiness label. People-posting reasons are excluded.

    Returns (readiness, source_kind). source_kind is `job_board` when the only
    signal is hiring or open postings for people, and None otherwise.
    """
    text = f"{stage or ''} {why or ''}".lower()
    if "open postings" in text or "hiring " in text or text.startswith("hiring"):
        return None, "job_board"
    if any(token in text for token in ("tender", "rfp", "procurement", "solicitation", "vendor selection")):
        return "rfp", "company"
    if "already operates" in text or (stage or "").strip().lower() == "expanding":
        return "expanding", "company"
    stage_name = (stage or "").strip().lower()
    if stage_name:
        return stage_name, "company"
    return None, "company"


def _fact_value(fact: Any) -> str | None:
    if isinstance(fact, dict):
        value = fact.get("value")
    else:
        value = fact
    text = str(value or "").strip()
    return text or None


def product_match_keys(product: dict[str, Any]) -> tuple[list[str], list[str]]:
    industries = []
    for item in product.get("industries") or []:
        value = _fact_value(item)
        if value and value not in industries:
            industries.append(value)
    functions = []
    primary = _fact_value(product.get("primary_function"))
    if primary:
        functions.append(primary)
    for item in product.get("secondary_functions") or []:
        value = _fact_value(item)
        if value and value not in functions:
            functions.append(value)
    return industries, functions


def _readiness_rank(readiness: str | None) -> int:
    name = (readiness or "").strip().lower()
    if name in _RFP:
        return 0
    if name:
        return 1
    return 2


def match_products_to_buyers(
    products: list[dict[str, Any]],
    buyers: list[dict[str, Any]],
    *,
    limit: int = 12,
) -> dict[str, Any]:
    """Return buyer opportunities for these product records.

    `buyers` entries use taxonomy industry keys already mapped. Unmapped
    companies are not in that list; pass them separately if you want them listed.
    """
    jobs: list[dict[str, Any]] = []
    seen: set[tuple[Any, str, str]] = set()
    for product in products:
        industries, functions = product_match_keys(product)
        if not industries:
            continue
        product_name = str(product.get("product_name") or "").strip()
        industry_set = set(industries)
        function_set = set(functions)
        for buyer in buyers:
            if is_people_posting_source(buyer.get("source_kind")):
                continue
            buyer_industries = [
                str(item).strip()
                for item in (buyer.get("taxonomy_industries") or [])
                if str(item).strip()
            ]
            overlap = [item for item in buyer_industries if item in industry_set]
            if not overlap:
                continue
            buyer_functions = [
                str(item).strip()
                for item in (buyer.get("functions") or [])
                if str(item).strip()
            ]
            function_overlap = [item for item in buyer_functions if item in function_set]
            if buyer_functions and not function_overlap:
                continue
            company_name = str(buyer.get("company_name") or "").strip()
            key = (buyer.get("company_id"), company_name)
            if key in seen:
                continue
            seen.add(key)
            readiness = buyer.get("readiness")
            function_matched = bool(function_overlap)
            why = [
                f"readiness: {readiness or 'unspecified'}",
                f"industry: {overlap[0]}",
            ]
            if function_matched:
                why.append(f"function: {function_overlap[0]}")
            else:
                why.append("function: not tagged on this company")
            jobs.append(
                {
                    "job_key": f"taxonomy:{buyer.get('company_id')}:{overlap[0]}:{product_name}",
                    "title": function_overlap[0] if function_overlap else overlap[0],
                    "industry": overlap[0],
                    "company_name": company_name,
                    "locality": None,
                    "verdict": "possible",
                    "why": why,
                    "source": "taxonomy_v4",
                    "source_kind": buyer.get("source_kind"),
                    "readiness": readiness,
                    "function_matched": function_matched,
                    "product_name": product_name,
                    "employer_email": None,
                    "_rank": (
                        _readiness_rank(readiness),
                        0 if function_matched else 1,
                        company_name.lower(),
                    ),
                }
            )
    jobs.sort(key=lambda job: job["_rank"])
    for job in jobs:
        job.pop("_rank", None)
    return {
        "jobs": jobs[:limit],
        "job_count": len(jobs),
        "matcher": "taxonomy_v4",
    }
