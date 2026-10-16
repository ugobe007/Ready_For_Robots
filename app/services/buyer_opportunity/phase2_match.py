"""Phase 2: classify the submitted page and join jobs on industry.

Behind ``RFR_BUYER_OPPORTUNITIES_V1`` (default off). The old FIND flow is
unchanged while the flag is off. This does not add a second matcher: jobs
still come from the bundled corpus, kept when the robot's taxonomy function
and industries overlap the job, then passed through the form-fit rule.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Iterable
from urllib.parse import urljoin, urlparse

from app.services.form_fit import jobs_fit_form
from app.services.job_card_provenance import (
    buyer_rows,
    is_example_job,
    job_source_url,
    public_employer_email,
    public_employer_name,
)
from app.services.robot_understanding_v1.industries import with_parents

_GENERIC_SEGMENTS = frozenset(
    {
        "robots",
        "robot",
        "products",
        "product",
        "solutions",
        "solution",
        "hardware",
        "platform",
        "models",
        "series",
        "family",
        "overview",
        "index",
        "home",
        "en",
        "zh",
        "ja",
        "ko",
        "de",
        "fr",
        "es",
    }
)

# Fixed-base forms. Mobile work is dropped for these by jobs_fit_form.
STATIONARY_FORMS = frozenset(
    {
        "robotic_arm_cobot",
        "fixed_gantry_system",
        "portable_stationary_unit",
    }
)

_FUNCTION_FAMILIES: dict[str, frozenset[str]] = {
    "food_beverage_prep": frozenset({"beverage"}),
    "cleaning": frozenset({"scrub", "restroom"}),
    "disinfection": frozenset({"disinfection"}),
    "serving_hospitality": frozenset({"serve"}),
    "picking_packing_palletizing": frozenset({"pick_pack", "sortation", "transport", "cart"}),
    "delivery_transport": frozenset({"transport", "cart", "pallet_move", "pallet"}),
    "inspection": frozenset({"inspect", "shelf_scan"}),
    "security_patrol": frozenset({"inspect"}),
    "construction_task": frozenset({"construction"}),
    "agricultural_task": frozenset({"agriculture"}),
    "machine_tending_assembly": frozenset({"machine_tending"}),
}

_HEALTHCARE_DELIVERY = frozenset({"clinical_delivery", "resident_services"})
_WAREHOUSE_INDUSTRIES = frozenset(
    {
        "warehouse_distribution",
        "3pl",
        "logistics_parcel",
        "manufacturing",
        "food_manufacturing",
        "automotive_dealership",
    }
)
_CARE_INDUSTRIES = frozenset({"hospital", "surgery_center", "senior_living"})
_HOSPITALITY_DELIVERY = frozenset({"hotel", "casino"})
# Theme pages that share a prefix with product catalogs but are not robots.
_THEME_TOKENS = frozenset(
    {
        "labor",
        "constraints",
        "scaling",
        "peak",
        "throughput",
        "brownfield",
        "omnichannel",
        "collaborative",
        "fulfillment",
        "autonomous",
        "customer",
        "success",
        "support",
        "security",
        "compliance",
        "intelligence",
        "how",
        "works",
        "why",
        "resources",
        "blog",
        "faq",
        "glossary",
        "events",
        "company",
        "about",
        "legal",
        "privacy",
        "careers",
        "contact",
        "demo",
        "customers",
        "industries",
        "industry",
    }
)

# First match wins. Phrases are the bundled corpus's free-text industry field.
_CORPUS_INDUSTRY_RULES: tuple[tuple[re.Pattern[str], frozenset[str]], ...] = (
    (re.compile(r"surgery\s+center", re.I), frozenset({"surgery_center"})),
    (re.compile(r"senior|assisted living|skilled nursing|memory care", re.I), frozenset({"senior_living"})),
    (re.compile(r"hospital|clinic", re.I), frozenset({"hospital"})),
    (re.compile(r"healthcare", re.I), frozenset({"hospital"})),
    (re.compile(r"airport", re.I), frozenset({"airport"})),
    (re.compile(r"hotel", re.I), frozenset({"hotel"})),
    (re.compile(r"casino", re.I), frozenset({"casino"})),
    (re.compile(r"quick-service|fast-casual|fast food|\bqsr\b", re.I), frozenset({"qsr_fast_food"})),
    (re.compile(r"restaurant|\bcafe\b|coffee", re.I), frozenset({"restaurant"})),
    (re.compile(r"\bbar\b|nightclub", re.I), frozenset({"bar_nightclub"})),
    (re.compile(r"grocery", re.I), frozenset({"grocery"})),
    (re.compile(r"\bmall\b", re.I), frozenset({"shopping_mall"})),
    (re.compile(r"retail", re.I), frozenset({"retail_store"})),
    (re.compile(r"warehouse|\bdc\b|fulfillment|distribution", re.I), frozenset({"warehouse_distribution"})),
    (re.compile(r"\b3pl\b", re.I), frozenset({"3pl"})),
    (re.compile(r"\bfactory\b", re.I), frozenset({"manufacturing"})),
    (re.compile(r"manufactur|machine shop|\bplant\b|\bcpg\b|industrial", re.I), frozenset({"manufacturing"})),
    (re.compile(r"\bconstruction\b", re.I), frozenset({"construction"})),
    (re.compile(r"\bagriculture\b", re.I), frozenset({"agriculture"})),
    (re.compile(r"dealership", re.I), frozenset({"automotive_dealership"})),
    (re.compile(r"auto parts", re.I), frozenset({"warehouse_distribution"})),
    (re.compile(r"office", re.I), frozenset({"office_building"})),
    (re.compile(r"facilities|facility", re.I), frozenset({"facility_services", "office_building"})),
    (re.compile(r"university|college|\bschool\b", re.I), frozenset({"college_university"})),
    (re.compile(r"pharma", re.I), frozenset({"warehouse_distribution"})),
    (re.compile(r"apparel", re.I), frozenset({"warehouse_distribution"})),
)


def buyer_opportunities_enabled() -> bool:
    return os.getenv("RFR_BUYER_OPPORTUNITIES_V1", "").strip().lower() in ("1", "true", "yes")


def fact_value(fact: Any) -> str | None:
    if isinstance(fact, dict):
        value = fact.get("value")
        text = str(value).strip() if value not in (None, "") else ""
        return text or None
    if isinstance(fact, str) and fact.strip():
        return fact.strip()
    return None


def fact_values(facts: Iterable[Any] | None) -> list[str]:
    out: list[str] = []
    for fact in facts or []:
        value = fact_value(fact)
        if value:
            out.append(value)
    return out


_ROBOT_OFFERINGS = frozenset({"robot_product", "robotics_as_a_service"})


def classification_is_clean(product: dict[str, Any] | None) -> bool:
    """A page classifies cleanly when the match fields are present and supported.

    offering_type may be missing. A value that is present and is not a robot
    offering still fails.
    """
    if not isinstance(product, dict):
        return False
    offering = fact_value(product.get("offering_type"))
    if offering is not None and offering not in _ROBOT_OFFERINGS:
        return False
    if not fact_value(product.get("form")):
        return False
    if not fact_value(product.get("primary_class")):
        return False
    if not fact_value(product.get("primary_function")):
        return False
    return bool(fact_values(product.get("industries")))


def _tokens(value: str) -> list[str]:
    return [part for part in re.split(r"[^a-z0-9]+", (value or "").lower()) if part]


def product_slug(url: str | None) -> str:
    path = urlparse(url or "").path
    parts = [
        part
        for part in path.split("/")
        if part and part.lower() not in _GENERIC_SEGMENTS
    ]
    return parts[-1] if parts else ""


def product_name_from_slug(slug: str) -> str:
    tokens = _tokens(slug)
    if len(tokens) >= 2 and len(tokens[1]) == 1:
        head = f"{tokens[0]}-{tokens[1]}".upper()
        tail = " ".join(token.upper() for token in tokens[2:])
        return f"{head} {tail}".strip()
    return " ".join(token.upper() for token in tokens)


def _contiguous(needle: list[str], hay: list[str]) -> bool:
    if not needle or len(needle) > len(hay):
        return False
    width = len(needle)
    for i in range(len(hay) - width + 1):
        if hay[i : i + width] == needle:
            return True
    return False


def url_names_product(url: str | None, product_name: str | None) -> bool:
    """True when the URL names this product, not merely the same maker."""
    slug = _tokens(product_slug(url or ""))
    product = _tokens(product_name or "")
    if not slug or not product:
        return False
    if slug == product:
        return True
    if _contiguous(product, slug):
        return True
    distinctive = len(slug) >= 2 or (len(slug) == 1 and len(slug[0]) >= 4)
    return bool(distinctive and _contiguous(slug, product))


def corpus_industry_to_taxonomy(industry: str | None) -> frozenset[str]:
    text = (industry or "").strip()
    if not text:
        return frozenset()
    for pattern, values in _CORPUS_INDUSTRY_RULES:
        if pattern.search(text):
            return values
    return frozenset()


def industries_join(robot_industries: Iterable[str], job_industry: str | None) -> bool:
    job_ids = corpus_industry_to_taxonomy(job_industry)
    if not job_ids:
        return False
    return bool(with_parents(robot_industries) & with_parents(job_ids))


def industries_for_match(product: dict[str, Any]) -> list[str]:
    """Industries used for the join.

    A pharma-warehouse case study is not a hospital. Taxonomy rule 1: a
    warehouse robot doing pharma logistics is warehouse_distribution or 3pl.
    """
    kept: list[str] = []
    for fact in product.get("industries") or []:
        value = fact_value(fact)
        if not value:
            continue
        evidence = str(fact.get("evidence") or "") if isinstance(fact, dict) else ""
        if (
            value == "hospital"
            and re.search(r"pharma|healthcare\s*/\s*pharma", evidence, re.I)
            and not re.search(r"\bhospital\b|\bclinic\b|\bpatient\b", evidence, re.I)
        ):
            continue
        kept.append(value)
    return kept


def families_for_product(product: dict[str, Any]) -> frozenset[str]:
    function = fact_value(product.get("primary_function")) or ""
    families = set(_FUNCTION_FAMILIES.get(function, ()))
    industries = with_parents(industries_for_match(product))
    if function == "delivery_transport" and industries & _CARE_INDUSTRIES:
        families |= set(_HEALTHCARE_DELIVERY)
        if not industries & _WAREHOUSE_INDUSTRIES:
            families -= {"transport", "cart", "pallet_move", "pallet"}
    if function == "delivery_transport" and industries & _HOSPITALITY_DELIVERY:
        if not industries & _WAREHOUSE_INDUSTRIES:
            families |= {"cart", "transport"}
    if "senior_living" not in industries:
        families.discard("resident_services")
    return frozenset(families)


def form_is_stationary(product: dict[str, Any]) -> bool:
    return (fact_value(product.get("form")) or "") in STATIONARY_FORMS


def _link_href(link: Any) -> str:
    if isinstance(link, str):
        return link
    if isinstance(link, (tuple, list)) and link:
        return str(link[0] or "")
    if isinstance(link, dict):
        return str(link.get("href") or link.get("url") or "")
    return ""


def _is_product_path(path: str, slug_tokens: list[str]) -> bool:
    lowered = (path or "").lower()
    if not any(bit in lowered for bit in ("/solutions/", "/products/", "/product/", "/robots/", "/platform/")):
        return False
    if not slug_tokens:
        return False
    if "/platform/" in lowered or "/solutions/" in lowered:
        if any(token in _THEME_TOKENS for token in slug_tokens):
            return False
    return True


def discover_product_pages(page_url: str, links: Iterable[Any]) -> list[dict[str, str]]:
    """Product URLs linked from a maker homepage or catalog. One row per product."""
    host = (urlparse(page_url).hostname or "").lower().removeprefix("www.")
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for link in links or []:
        href = _link_href(link)
        if not href:
            continue
        absolute = urljoin(page_url, href).split("#")[0]
        parsed = urlparse(absolute)
        link_host = (parsed.hostname or "").lower().removeprefix("www.")
        if host and link_host and link_host != host:
            continue
        slug = product_slug(absolute)
        tokens = _tokens(slug)
        if not _is_product_path(parsed.path or "", tokens):
            continue
        marker = " ".join(tokens)
        if not marker or marker in seen:
            continue
        seen.add(marker)
        found.append(
            {
                "name": _catalog_name(page_url, slug),
                "url": absolute.split("?")[0],
            }
        )
    return found


def _catalog_name(page_url: str, slug: str) -> str:
    from app.services.vendor_robot_lookup import lookup_vendor_by_url

    vendor = lookup_vendor_by_url(page_url)
    label = product_name_from_slug(slug)
    if not vendor:
        return label
    for robot in vendor.get("robots") or []:
        name = str(robot.get("name") or "")
        if name and url_names_product(f"https://example.test/{slug}", name):
            return name
    return label


def _shared_product_name(products: list[dict[str, Any]], url: str) -> str:
    host = (urlparse(url).hostname or "").split(".")[0].lower()
    token_sets = []
    for product in products:
        name = fact_value(product.get("product_name")) or str(product.get("product_name") or "")
        token_sets.append(set(_tokens(name)))
    if not token_sets:
        return ""
    common = set.intersection(*token_sets)
    def cased(token: str) -> str:
        for product in products:
            raw = fact_value(product.get("product_name")) or str(product.get("product_name") or "")
            for part in re.split(r"[^A-Za-z0-9]+", raw):
                if part.lower() == token:
                    return part
        return token.upper() if len(token) <= 5 else token.title()

    for token in sorted(common, key=len, reverse=True):
        if len(token) >= 4 and host.startswith(token):
            return cased(token)
    if common:
        return cased(max(common, key=len))
    first = fact_value(products[0].get("product_name")) or str(products[0].get("product_name") or "")
    return first


def merge_market_variants(products: list[dict[str, Any]], url: str) -> dict[str, Any] | None:
    """One robot sold into several industries is one product, not several robots."""
    clean = [product for product in products if classification_is_clean(product)]
    if len(clean) <= 1:
        return clean[0] if clean else None
    forms = {fact_value(product.get("form")) for product in clean}
    functions = {fact_value(product.get("primary_function")) for product in clean}
    if len(forms) != 1 or len(functions) != 1 or None in forms or None in functions:
        return None
    industries = []
    seen: set[str] = set()
    for product in clean:
        for fact in product.get("industries") or []:
            value = fact_value(fact)
            if value and value not in seen:
                seen.add(value)
                industries.append(fact)
    merged = dict(clean[0])
    merged["industries"] = industries
    merged["product_name"] = _shared_product_name(clean, url)
    return merged


def pick_product_record(
    extraction: dict[str, Any] | None,
    url: str,
    product_name: str | None = None,
) -> dict[str, Any] | None:
    """The record for the submitted product. Never a sibling from the same page."""
    products = (extraction or {}).get("products") or []
    hint = (product_name or "").strip()
    slug = product_slug(url)
    matches = []
    for product in products:
        if not isinstance(product, dict):
            continue
        name = fact_value(product.get("product_name")) or str(product.get("product_name") or "")
        if hint and url_names_product(f"https://example.test/{hint}", name):
            matches.append(product)
            continue
        if slug and url_names_product(url, name):
            matches.append(product)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return merge_market_variants(matches, url)
    rows = [product for product in products if isinstance(product, dict)]
    if not slug:
        return merge_market_variants(rows, url)
    return None


def _corpus_rows() -> list[dict[str, Any]]:
    from app.services.robot_job_capability_match import load_match_corpus
    from app.services.robot_job_live_corpus import merge_live_jobs

    return list(buyer_rows(merge_live_jobs(load_match_corpus())))


def jobs_for_classification(product: dict[str, Any], *, limit: int = 12) -> list[dict[str, Any]]:
    """Corpus rows that share an industry with the robot and fit its form."""
    families = families_for_product(product)
    industries = industries_for_match(product)
    stationary = form_is_stationary(product)
    rows = [
        job
        for job in jobs_fit_form(_corpus_rows(), stationary=stationary)
        if (job.get("tape_family") or "") in families
        and industries_join(industries, job.get("industry"))
    ]
    robot_name = fact_value(product.get("product_name")) or str(product.get("product_name") or "")
    jobs_out = []
    for job in rows[:limit]:
        jobs_out.append(
            {
                "job_key": job.get("job_key"),
                "title": job.get("title"),
                "industry": job.get("industry"),
                "path": job.get("path"),
                "company_name": public_employer_name(job),
                "locality": job.get("locality"),
                "tape_family": job.get("tape_family"),
                "score": None,
                "unknowns": list(job.get("unknowns") or []),
                "source": job.get("source"),
                "employer_email": public_employer_email(
                    job.get("employer_email"), job.get("company_name")
                ),
                "contact_url": job.get("contact_url"),
                "apply_url": job.get("apply_url"),
                "source_url": job_source_url(job),
                "is_example": is_example_job(job),
                "for_robot": robot_name,
            }
        )
    return jobs_out


def _public_product(product: dict[str, Any]) -> dict[str, Any]:
    name = fact_value(product.get("product_name")) or str(product.get("product_name") or "")
    return {
        "name": name,
        "display_class": fact_value(product.get("primary_class")),
        "robot_class": fact_value(product.get("primary_class")),
        "description": fact_value(product.get("primary_function")),
    }


def classified_match_payload(
    product: dict[str, Any],
    *,
    url: str,
    company_name: str | None = None,
) -> dict[str, Any]:
    jobs = jobs_for_classification(product)
    name = fact_value(product.get("product_name")) or product_name_from_slug(product_slug(url))
    company = company_name or fact_value(product.get("company")) or ""
    function = fact_value(product.get("primary_function"))
    return {
        "state": "matches" if jobs else "thin_corpus",
        "robot_name": name,
        "company_name": company,
        "capabilities": [{"key": function, "label": (function or "").replace("_", " ")}] if function else [],
        "families": sorted(families_for_product(product)),
        "jobs": jobs,
        "top_jobs": jobs[:3],
        "job_count": len(jobs),
        "profile": {
            "selected_product": {"name": name, "display_class": fact_value(product.get("primary_class"))},
            "company": {"name": company} if company else None,
        },
        "products": [_public_product(product)],
        "needs_product_choice": False,
        "needs_class_choice": False,
        "class_options": [],
        "matcher": "buyer_opportunities_v1",
        "zero_reason": None if jobs else "corpus_gap",
        "robot_class": fact_value(product.get("primary_class")),
        "source_url": url,
        "classified_product": product,
    }


def unrecognized_payload(
    url: str,
    *,
    company_name: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    # The catalog row's name, when the caller has one. The URL slug is all caps
    # ("LOCUS ORIGIN") and was showing beside the catalog name.
    label = (display_name or "").strip() or product_name_from_slug(product_slug(url)) or "This robot"
    return {
        "state": "thin_corpus",
        "robot_name": label,
        "company_name": company_name or "",
        "capabilities": [],
        "families": [],
        "jobs": [],
        "top_jobs": [],
        "job_count": 0,
        "profile": None,
        "products": [],
        "needs_product_choice": False,
        "needs_class_choice": False,
        "class_options": [],
        "matcher": "buyer_opportunities_v1",
        "zero_reason": "unrecognized_product",
        "robot_class": None,
        "source_url": url,
    }


def _indexed_robot_count(url: str) -> int:
    """How many robots the vendor index lists for this domain.

    A missing row is zero. That is the whole decision for a homepage that
    linked no product page: two or more robots fall through to the catalog
    picker; zero or one keeps classifying the page (Relay).
    """
    from app.services.vendor_robot_lookup import index_robot_names, lookup_vendor_by_url

    vendor = lookup_vendor_by_url(url)
    if not isinstance(vendor, dict):
        return 0
    return len(index_robot_names(vendor))


def catalog_payload(url: str, products: list[dict[str, str]], *, company_name: str | None = None) -> dict[str, Any]:
    return {
        "state": "select_product",
        "robot_name": company_name or "",
        "company_name": company_name or "",
        "capabilities": [],
        "families": [],
        "jobs": [],
        "top_jobs": [],
        "job_count": 0,
        "profile": None,
        "products": [{"name": row["name"], "display_class": None, "product_url": row.get("url")} for row in products],
        "needs_product_choice": True,
        "needs_class_choice": False,
        "class_options": [],
        "matcher": None,
        "zero_reason": None,
        "robot_class": None,
        "source_url": url,
    }


def _fact_or_plain(raw: Any, plain: Any) -> Any:
    if fact_value(raw):
        return raw
    text = str(plain).strip() if plain not in (None, "") else ""
    if text:
        return {"value": text}
    return raw


def product_from_saved_row(row: Any) -> dict[str, Any]:
    """Rebuild the classifier product dict from one rfr_robot_products row."""
    evidence = row["evidence"] if "evidence" in row.keys() else None
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except json.JSONDecodeError:
            evidence = {}
    if not isinstance(evidence, dict):
        evidence = {}
    product: dict[str, Any] = {"product_name": {"value": row["product_name"]}}
    company = row["company_name"]
    if company:
        product["company"] = {"value": company}
    for field in ("offering_type", "form", "primary_class", "primary_function"):
        product[field] = _fact_or_plain(evidence.get(field), row[field])
    industries = evidence.get("industries")
    if not fact_values(industries if isinstance(industries, list) else None):
        plain = row["industries"] or []
        if isinstance(plain, str):
            try:
                plain = json.loads(plain)
            except json.JSONDecodeError:
                plain = []
        industries = [{"value": value} for value in plain if value]
    product["industries"] = industries
    return product


def saved_clean_product(db: Any, url: str) -> dict[str, Any] | None:
    """Newest clean row for this URL at the current prompt and taxonomy versions.

    A row for another version, or a row that does not classify cleanly, is not a hit.
    """
    from sqlalchemy import desc, select

    from app.services.buyer_opportunity.tables import rfr_robot_products
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    rows = db.execute(
        select(rfr_robot_products)
        .where(rfr_robot_products.c.source_url == (url or "")[:2048])
        .where(rfr_robot_products.c.prompt_version == str(PROMPT_VERSION)[:16])
        .where(rfr_robot_products.c.taxonomy_version == str(get_taxonomy_version())[:16])
        .order_by(desc(rfr_robot_products.c.id))
    ).mappings()
    for row in rows:
        product = product_from_saved_row(row)
        if classification_is_clean(product):
            return product
    return None


def saved_product_for_request(db: Any, url: str, product_name: str | None) -> dict[str, Any] | None:
    """Reuse a saved row only when this URL is that product.

    A homepage has no product slug, so it always goes through discovery.
    When the caller passed a product hint, the saved name has to match it.
    """
    if not product_slug(url):
        return None
    saved = saved_clean_product(db, url)
    if saved is None:
        return None
    saved_name = fact_value(saved.get("product_name")) or str(saved.get("product_name") or "")
    if not url_names_product(url, saved_name):
        return None
    hint = (product_name or "").strip()
    if hint and not url_names_product(f"https://example.test/{hint}", saved_name):
        return None
    return saved


def try_phase2_search(
    url: str,
    product_name: str | None = None,
    *,
    fetch: Callable[..., Any] | None = None,
    extract: Callable[..., Any] | None = None,
    db: Any | None = None,
) -> dict[str, Any] | None:
    """Classify one submitted page. None lets the old flow run (flag off or fetch miss)."""
    if not buyer_opportunities_enabled():
        return None
    if fetch is None:
        from app.services.robot_understanding_v1.fetch import fetch_page

        fetch = fetch_page
    if extract is None:
        from app.services.robot_understanding_v1.taxonomy_extraction import extract_robot_taxonomy

        extract = extract_robot_taxonomy

    if db is not None:
        try:
            saved = saved_product_for_request(db, url, product_name)
        except Exception:
            saved = None
            try:
                db.rollback()
            except Exception:
                pass
        else:
            if saved is not None:
                # Reuse the saved classification. The API inserts a row whenever
                # classified_product is present, so drop the key the matcher sets.
                payload = classified_match_payload(
                    saved, url=url, company_name=fact_value(saved.get("company"))
                )
                payload.pop("classified_product", None)
                return payload

    try:
        page = fetch(url)
    except Exception:
        return None
    links = getattr(page, "links", None) or []
    text = (getattr(page, "text", None) or "").strip()
    slug = product_slug(url)
    discovered = discover_product_pages(url, links) if not slug else []
    hint = (product_name or "").strip()
    if discovered and hint:
        chosen = next((row for row in discovered if row["name"].casefold() == hint.casefold()), None) or next(
            (row for row in discovered if url_names_product(row["url"], hint)), None
        )
        if chosen:
            return try_phase2_search(chosen["url"], hint, fetch=fetch, extract=extract, db=db)
    if not slug and discovered:
        # Homepage or catalog: one row per linked product, not the first robot's jobs.
        from app.services.vendor_robot_lookup import lookup_vendor_by_url

        vendor = lookup_vendor_by_url(url)
        company = (vendor or {}).get("vendor_name")
        return catalog_payload(url, discovered, company_name=company)
    if not slug and _indexed_robot_count(url) >= 2:
        # The page linked no product URL. A maker with several robots in the
        # vendor index must not collapse to one classified product. None lets
        # the old flow open the catalog picker. Zero or one indexed robot
        # (Relay, or a domain we have not indexed) keeps today's classification.
        return None

    if not text:
        return unrecognized_payload(url, display_name=hint) if slug else None
    try:
        extraction = extract(url, text, product_name)
    except Exception:
        return unrecognized_payload(url, display_name=hint)
    page_record = (extraction or {}).get("page") or {}
    if page_record and page_record.get("produces_records") is False:
        linked = discover_product_pages(url, links)
        if linked:
            return catalog_payload(url, linked)
        return unrecognized_payload(url, display_name=hint) if slug else None
    product = pick_product_record(extraction, url, product_name)
    if product is None or not classification_is_clean(product):
        # A named product page stays empty. A homepage that did not classify
        # falls through to the old flow. A clean sibling on the same page is
        # not a substitute.
        return unrecognized_payload(url, display_name=hint) if slug else None
    company = fact_value(product.get("company"))
    payload = classified_match_payload(product, url=url, company_name=company)
    payload["classified_product"] = {
        "product": product,
        "metadata": (extraction or {}).get("extraction_metadata") or {},
        "source_url": url,
    }
    return payload


def persist_classified_product(db: Any, record: dict[str, Any]) -> None:
    """Insert one rfr_robot_products row. Failures are the caller's to log."""
    from sqlalchemy import insert

    from app.services.buyer_opportunity.tables import rfr_robot_products
    from app.services.robot_understanding_v1.taxonomy_extraction import PROMPT_VERSION, get_taxonomy_version

    product = record.get("product") or {}
    meta = record.get("metadata") or {}
    evidence = {
        field: product.get(field)
        for field in ("offering_type", "form", "primary_class", "primary_function", "industries")
    }
    db.execute(
        insert(rfr_robot_products).values(
            source_url=(record.get("source_url") or "")[:2048],
            company_name=(fact_value(product.get("company")) or "")[:255] or None,
            product_name=(fact_value(product.get("product_name")) or product_name_from_slug(product_slug(record.get("source_url"))))[:255],
            page_type=((record.get("page_type") or "")[:64] or None),
            offering_type=(fact_value(product.get("offering_type")) or "")[:64] or None,
            form=(fact_value(product.get("form")) or "")[:64] or None,
            primary_class=(fact_value(product.get("primary_class")) or "")[:64] or None,
            primary_function=(fact_value(product.get("primary_function")) or "")[:64] or None,
            secondary_functions=fact_values(product.get("secondary_functions")),
            industries=fact_values(product.get("industries")),
            evidence=evidence,
            unsupported_facts=list(product.get("unsupported_facts") or []),
            prompt_version=str(meta.get("prompt_version") or PROMPT_VERSION)[:16],
            taxonomy_version=str(meta.get("taxonomy_version") or get_taxonomy_version())[:16],
        )
    )
    db.commit()
