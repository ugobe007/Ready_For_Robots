"""Robot URL -> taxonomy product records -> buyer opportunities.

Off unless TAXONOMY_MATCH_ENABLED is 1. The default path stays
compose_robot_job_search, which still matches the old requirement corpus.

What that default path does today, as a user sees it:

1. The user pastes a robot URL on `/`. The client posts it to
   POST /api/robot-job-search.
2. compose_robot_job_search builds an Understanding v1 profile and calls
   match_jobs_from_profile.
3. That matcher derives capabilities and scores a bundled job corpus plus
   live robot_jobs. It never calls extract_robot_taxonomy (prompt v4).
4. Form, offering type, class, functions, and the 29 industries from the
   classifier are not the match keys.
5. companies.industry is free text. Nothing in that request writes or reads
   the 29 taxonomy industries, so a company that is not already inside the
   old corpus cannot show up.
6. Rank is utilization and evidence, not RFP or procurement first.
7. Pausing people-posting ingest stops new job-board rows. It does not stop
   this matcher from returning rows that came from that corpus.

This module is the connection. It reads `company_taxonomy_industries` and
does not update existing tables.
"""
from __future__ import annotations

import os
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.services.taxonomy_buyer_match import match_products_to_buyers
from app.services.taxonomy_industry_map import buyers_from_taxonomy_table


def taxonomy_match_enabled() -> bool:
    return os.getenv("TAXONOMY_MATCH_ENABLED", "0").strip().lower() in ("1", "true", "yes")


def _fact_value(fact: Any) -> str | None:
    if isinstance(fact, dict):
        value = fact.get("value")
    else:
        value = fact
    text = str(value or "").strip()
    return text or None


def slim_product(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_name": product.get("product_name"),
        "company": product.get("company"),
        "offering_type": _fact_value(product.get("offering_type")),
        "form": _fact_value(product.get("form")),
        "primary_class": _fact_value(product.get("primary_class")),
        "primary_function": _fact_value(product.get("primary_function")),
        "secondary_functions": [
            value
            for item in (product.get("secondary_functions") or [])
            if (value := _fact_value(item))
        ],
        "industries": [
            value
            for item in (product.get("industries") or [])
            if (value := _fact_value(item))
        ],
    }


def compose_taxonomy_job_search(
    url: str | None,
    *,
    product: str | None = None,
    page_text: str | None = None,
    buyers: list[dict[str, Any]] | None = None,
    unmapped: list[dict[str, Any]] | None = None,
    db: Session | None = None,
    extract: Callable[..., dict[str, Any]] | None = None,
    fetch: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Classify one robot URL with prompt v4 and join mapped buyers.

    `buyers` lets a preview pass rows it already mapped. When buyers is None
    and a session is passed, buyers are read from company_taxonomy_industries.
    A missing table returns products and an empty buyer list.
    """
    from app.services.robot_url_safety import assert_public_http_url

    safe = assert_public_http_url((url or "").strip())
    text = (page_text or "").strip()
    final_url = safe
    if not text:
        if fetch is None:
            from app.services.robot_understanding_v1.fetch import fetch_page

            fetched = fetch_page(safe)
        else:
            fetched = fetch(safe)
        text = (getattr(fetched, "text", None) or "").strip()
        final_url = getattr(fetched, "final_url", None) or safe
    if not text:
        return {
            "state": "could_not_understand",
            "matcher": "taxonomy_v4",
            "robot_name": product or "your robot",
            "company_name": None,
            "jobs": [],
            "top_jobs": [],
            "job_count": 0,
            "taxonomy_products": [],
            "unmapped_companies": [],
            "unmapped_count": 0,
            "capabilities": [],
            "families": [],
            "products": [],
            "needs_product_choice": False,
            "needs_class_choice": False,
            "class_options": [],
            "source_url": safe,
            "zero_reason": "page_text_empty",
        }

    if extract is None:
        from app.services.robot_understanding_v1.taxonomy_extraction import extract_robot_taxonomy

        extracted = extract_robot_taxonomy(final_url, text, product_name_hint=product or None)
    else:
        extracted = extract(final_url, text, product or None)

    products = [item for item in (extracted.get("products") or []) if isinstance(item, dict)]
    slim = [slim_product(item) for item in products]
    if buyers is None and db is not None:
        try:
            buyers = buyers_from_taxonomy_table(db)
        except Exception:
            buyers = []
    buyers = buyers or []
    matched = match_products_to_buyers(products, buyers)
    jobs = matched["jobs"]
    unmapped_rows = list(unmapped or [])
    names = [item.get("product_name") for item in slim if item.get("product_name")]
    company = next((item.get("company") for item in slim if item.get("company")), None)
    functions = []
    for item in slim:
        if item.get("primary_function"):
            functions.append(item["primary_function"])
        functions.extend(item.get("secondary_functions") or [])
    return {
        "state": "matches" if jobs else ("thin_corpus" if slim else "could_not_understand"),
        "matcher": "taxonomy_v4",
        "robot_name": (product or (names[0] if names else None) or company or "your robot"),
        "company_name": company,
        "jobs": jobs,
        "top_jobs": jobs[:5],
        "job_count": matched["job_count"],
        "taxonomy_products": slim,
        "unmapped_companies": unmapped_rows[:25],
        "unmapped_count": len(unmapped_rows),
        "capabilities": [
            {"key": fn, "label": fn, "confidence": None, "truth_state": "confirmed"}
            for fn in dict.fromkeys(functions)
        ],
        "families": [],
        "products": slim,
        "needs_product_choice": False,
        "needs_class_choice": False,
        "class_options": [],
        "profile": {"taxonomy": extracted.get("extraction_metadata"), "page": extracted.get("page")},
        "source_url": safe,
        "zero_reason": None if jobs or slim else "no_product_records",
    }
