"""Assemble Phases 1–3 into an auditable Robot Profile."""
from __future__ import annotations

import os
import time
from typing import Any

from app.services.robot_understanding_v1.coverage import (
    apply_research_gaps,
    derive_profile_tier,
    material_facts,
    score_source_quality,
)
from app.services.robot_understanding_v1.facts import (
    extract_facts_from_sources,
    filter_facts_to_subject,
    mark_contradictions,
)
from app.services.robot_understanding_v1.fetch import (
    DEFAULT_PAGE_TIMEOUT,
    FetchedPage,
    fetch_page,
    timeout_for_deadline,
)
from app.services.robot_understanding_v1.models import (
    ProfileTier,
    RobotFact,
    RobotProduct,
    RobotProfile,
    RobotSource,
)
from app.services.robot_understanding_v1.resolve import resolve_identity
from app.services.robot_understanding_v1.sources import (
    CollectedSource,
    collect_source_pack,
    collected_from_page,
    homepage_is_chrome_only,
)
from app.services.robot_url_safety import assert_public_http_url, normalize_product_url
from app.services.vendor_robot_lookup import (
    catalog_claim_facts,
    index_robot_for_name,
    lookup_vendor_by_url,
    select_index_robot,
)


def _catalog_identity_page(url: str) -> FetchedPage:
    """Placeholder page so indexed vendors never wait on a live OEM host.

    FIND's client budget is 22s. A hung manufacturer homepage used to abort
    with "paste a product URL" even when the vendor index already had SKUs.
    Identity and specs come from that index; this stub is not evidence.
    """
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=0,
        title=None,
        text="",
        html="",
        links=[],
        fetch_degraded=False,
        fetch_notes=[
            "Skipped live manufacturer fetch — vendor is in the robot index."
        ],
        content_type="text/html",
    )


def _source_budget_sec() -> float | None:
    """Wall-clock budget for unknown-OEM live fetch + source pack.

    FIND's client abort is 22s. Indexed vendors skip live I/O entirely.
    For unknown hosts this budget covers homepage fetch AND pack fan-out
    together so a slow Cloudflare/WAF page cannot spend 8s then start a
    fresh 12s crawl. 0/empty = no cap.
    """
    raw = (os.getenv("ROBOT_PROFILE_SOURCE_BUDGET_MS") or "12000").strip()
    try:
        ms = int(raw)
    except ValueError:
        ms = 12000
    if ms <= 0:
        return None
    return max(1.0, ms / 1000.0)


def build_robot_profile(
    url: str,
    *,
    product_name: str | None = None,
    max_sources: int = 6,
    auto_select_single: bool = True,
    timings: dict[str, Any] | None = None,
) -> RobotProfile:
    """
    URL → company/product → typed sources → facts → Robot Profile.

    Stops before capabilities/workflows/jobs.
    If multiple products and no product_name, returns needs_product_choice=True
    without fetching the full source pack (identity only).

    When product_name is supplied (CLI/API), it ALWAYS becomes selected_product
    even if homepage resolve missed the string — company-level research is fallback only.

    timings, if provided, is filled with resolve_ms and profile_ms.
    """
    t0 = time.perf_counter()
    # Catalog match is host-string only. Do it before SSRF DNS so a hung
    # Cloudflare OEM resolver cannot burn FIND's 22s budget on vendors we
    # already list (Reflex, Richtech, …).
    normalized = normalize_product_url(url) or (url or "").strip()
    catalog = lookup_vendor_by_url(normalized) or lookup_vendor_by_url(url)
    catalog_skus = False
    if catalog and (catalog.get("robots") or []):
        from app.services.jobs_oem_listing import listing_from_catalog

        catalog_skus = bool(listing_from_catalog(catalog))
    if catalog_skus:
        safe = normalized
    else:
        safe = assert_public_http_url(url)
    live_budget = _source_budget_sec()
    live_deadline = (time.monotonic() + live_budget) if live_budget is not None else None
    # Indexed OEM homepages (and SKU URLs) skip live fetch — Reflex-class
    # sites where every SKU URL is the homepage are normal, not an error.
    # Unknown hosts still load the submitted page under live_deadline; never
    # Wayback it (archive copies of challenged hosts sat FIND on a ~90s spinner).
    if catalog_skus:
        home = _catalog_identity_page(safe)
        if timings is not None:
            timings["home_fetch"] = "skipped"
    else:
        home_timeout = timeout_for_deadline(
            live_deadline, default=DEFAULT_PAGE_TIMEOUT
        )
        if home_timeout is None:
            home = FetchedPage(
                url=safe,
                final_url=safe,
                status_code=0,
                title=None,
                text="",
                html="",
                links=[],
                fetch_degraded=True,
                fetch_notes=["Live manufacturer fetch skipped — FIND deadline exhausted."],
                content_type="text/html",
            )
        else:
            home = fetch_page(
                safe, timeout=home_timeout, allow_archive=False
            )
        if timings is not None:
            timings["home_fetch"] = "live"
    resolved = resolve_identity(safe, home, product_hint=product_name)
    resolve_ms = int((time.perf_counter() - t0) * 1000)
    if timings is not None:
        timings["resolve_ms"] = resolve_ms

    selected = None
    notes_extra: list[str] = []
    if getattr(home, "fetch_degraded", False):
        notes_extra.extend(getattr(home, "fetch_notes", None) or [])
        notes_extra.append(
            "Source acquisition degraded — canonical company/product identity preserved; "
            "do not redefine company from acquirer fallback hosts."
        )
    if product_name:
        selected = _bind_requested_product(resolved.company.id, resolved.products, product_name)
        if selected.id not in {p.id for p in resolved.products}:
            resolved.products.append(selected)
            notes_extra.append(
                f"Bound requested product `{selected.name}` (not found on homepage resolve)."
            )
        elif selected.name.lower() != product_name.strip().lower():
            notes_extra.append(f"Bound requested product via alias match → `{selected.name}`.")
    elif len(resolved.products) == 1 and auto_select_single:
        selected = resolved.products[0]
    elif len(resolved.products) > 1 and not product_name:
        stages = _stages(
            company=resolved.company.name,
            products=[p.name for p in resolved.products],
            sources_n=0,
            profile_ready=False,
            needs_choice=True,
        )
        if timings is not None:
            timings["profile_ms"] = 0
            if catalog_skus:
                timings["source_strategy"] = "catalog"
        return RobotProfile(
            submitted_url=safe,
            company=resolved.company,
            products=resolved.products,
            selected_product=None,
            sources=[],
            facts=[],
            profile_confidence="C",
            source_grounding_rate=1.0,
            coverage_rate=0.0,
            coverage_level="low",
            source_quality_rate=0.0,
            source_quality_level="low",
            notes=list(resolved.notes)
            + ["Multiple products found — select one to research."],
            needs_product_choice=True,
            research_stages=stages,
        )
    elif resolved.selected_product and auto_select_single:
        selected = resolved.selected_product

    subject = selected.name if selected else resolved.company.name
    t_profile = time.perf_counter()
    t_sources = time.perf_counter()
    home_blocked = bool(
        getattr(home, "fetch_degraded", False) and not (home.text or "").strip()
    )
    if catalog_skus:
        # Indexed vendor: identity and specs come from the vendor index.
        # The submitted URL was not fetched; do not guess hubs.
        collected = []
        home_src = collected_from_page(home)
        if home_src:
            collected.append(home_src)
        if timings is not None:
            timings["sources_ms"] = int((time.perf_counter() - t_sources) * 1000)
            timings["source_strategy"] = "catalog"
        notes_extra.append(
            "Catalog vendor — skipped live manufacturer fetch and source fan-out; "
            "facts come from the vendor index."
        )
    elif home_blocked:
        collected = []
        if timings is not None:
            timings["sources_ms"] = 0
            timings["source_strategy"] = "blocked"
    elif homepage_is_chrome_only(
        home, product_name=selected.name if selected else product_name
    ):
        # Chrome/JS homepage, no product URL — skip sitemap and guessed hubs.
        collected = []
        home_src = collected_from_page(home)
        if home_src:
            collected.append(home_src)
        if timings is not None:
            timings["sources_ms"] = int((time.perf_counter() - t_sources) * 1000)
            timings["source_strategy"] = "chrome"
        notes_extra.append(
            "Homepage is site chrome (JS shell / nav only) — skipped hub crawl; "
            "class picker is next. Do not invent a SKU."
        )
    else:
        collected = collect_source_pack(
            home,
            product_name=selected.name if selected else product_name,
            max_sources=max_sources,
            deadline_monotonic=live_deadline,
            allow_archive=False,
        )
        if timings is not None:
            timings["sources_ms"] = int((time.perf_counter() - t_sources) * 1000)
            timings["source_strategy"] = "live_pack"
    if selected:
        for c in collected:
            c.source.product_id = selected.id

    facts = extract_facts_from_sources(collected, subject=subject)
    if selected and not any(
        f.predicate == "product_class" and f.epistemic not in ("unknown", "contradicted")
        for f in facts
    ):
        from app.services.robot_visual_class import visual_class_facts

        extra_vis = visual_class_facts(collected, subject=subject)
        if extra_vis:
            facts.extend(extra_vis)
            notes_extra.append(
                "Visual class grounded from manufacturer product photos."
            )
    from app.services.robot_visual_class import preview_image_urls

    preview_images = preview_image_urls(collected)
    # Sibling contamination gate: drop material facts whose evidence is about another SKU.
    # On multi-product companies, capability/class claims must be subject-proximate so a
    # shared nav cannot leak a sibling product's capability onto the selected product.
    if selected:
        multi_product = len(resolved.products) > 1
        facts, dropped_sib = filter_facts_to_subject(
            facts, collected, subject=selected.name, multi_product=multi_product
        )
        if dropped_sib:
            notes_extra.append(
                f"Dropped {dropped_sib} sibling/off-subject fact(s) to prevent SKU contamination."
            )

    catalog_robot = None
    if catalog and selected:
        catalog_robot = index_robot_for_name(catalog, selected.name) or select_index_robot(
            safe, catalog
        )
    if catalog_robot:
        src, extra = _facts_from_catalog_robot(
            catalog_robot, subject=subject, product_id=selected.id if selected else None
        )
        collected.append(CollectedSource(source=src, page=home))
        known = {
            f.predicate
            for f in facts
            if f.epistemic not in ("unknown", "contradicted")
        }
        added = 0
        for fact in extra:
            if fact.predicate in known:
                continue
            facts.append(fact)
            known.add(fact.predicate)
            added += 1
        if added:
            notes_extra.append(
                f"Used vendor index for {catalog_robot.get('name')} "
                f"({added} catalog fact(s)"
                + (
                    "; live OEM pages were blocked)."
                    if home_blocked
                    else ")."
                )
            )

    # Robot Inference Engine (M1 narrow reopen): deterministic phased inference
    # over the SAME evidence pack. Seeds explicit facts from evidence signals, then
    # forward-chains structural/capability inference — each conclusion carries its
    # evidence + basis + confidence. Emits facts v1's narrow regex missed. Fails
    # open to v1. Source of truth: evidence → inference → capability (not an LLM).
    inference: dict[str, Any] | None = None
    try:
        from app.services.robot_inference_engine import infer_facts as _infer_facts
        from app.services.robot_understanding_v1.sources import page_supports_subject

        # Pass filtered evidence to avoid sibling-SKU contamination
        inference_pack = collected
        if selected:
            # When a product is selected, filter evidence to subject-relevant pages
            inference_pack = [
                c for c in collected
                if page_supports_subject(
                    url=c.page.final_url,
                    title=c.page.title or "",
                    text=c.page.text or "",
                    product_name=selected.name,
                )
            ]
        extra_facts, inference = _infer_facts(inference_pack, subject=subject, existing_facts=facts)
        if extra_facts:
            facts.extend(extra_facts)
            notes_extra.append(
                f"Inference engine grounded {len(extra_facts)} additional capability fact(s) "
                "from manufacturer evidence (evidence → inference → capability)."
            )
    except Exception:
        inference = None

    facts = mark_contradictions(facts)

    # Set display_class from strongest product_class claim (descriptive only).
    # Domain work (healthcare, agriculture, …) beats torso morphology: Moxi
    # is a hospital assistant, not a humanoid tile because it has a torso.
    if selected:
        class_facts = [
            f
            for f in facts
            if f.predicate == "product_class" and f.epistemic not in ("unknown", "contradicted")
        ]
        if class_facts:
            from app.services.robot_ontology import domain_priority_classes

            domain_priority = domain_priority_classes() | {
                "healthcare",
                "healthcare_robot",
                "medical_robot",
                "clinical_robot",
                "hospital_robot",
                "hospitality",
                "hospitality_robot",
                "hotel_robot",
                "food_prep",
                "agriculture",
                "agricultural_robot",
                "construction",
                "construction_robot",
                "marine",
                "marine_robot",
                "avionics",
                "aviation_robot",
                "aerospace",
                "aerospace_robot",
                "mining",
                "mining_robot",
            }
            domain = [f for f in class_facts if str(f.value).lower() in domain_priority]
            if domain:
                best = max(domain, key=lambda f: f.confidence)
            else:
                morph_vals = {"humanoid", "semi-humanoid", "biped", "bipedal"}
                morph = [
                    f
                    for f in class_facts
                    if str(f.value).lower() in morph_vals
                ]
                best = max(morph or class_facts, key=lambda f: f.confidence)
            selected.display_class = str(best.value)

    facts, morphology, coverage_rate, coverage_level = apply_research_gaps(
        facts,
        subject=subject,
        display_class=selected.display_class if selected else None,
    )

    source_ids = {c.source.id for c in collected}
    claim_facts = material_facts(facts)
    ungrounded = [
        f.id
        for f in claim_facts
        if f.source_id not in source_ids and f.source_id != "research_checklist"
    ]
    grounded = len(claim_facts) - len(ungrounded)
    grounding = 1.0 if not claim_facts else grounded / len(claim_facts)

    auth_sources = [
        c.source
        for c in collected
        if c.source.source_type
        in {"product", "specifications", "documentation", "solutions", "case_study", "support"}
    ]
    avg_auth = (
        sum(s.confidence for s in auth_sources) / len(auth_sources) if auth_sources else 0.0
    )
    sq_rate, sq_level = score_source_quality(
        {c.source.source_type for c in collected},
        avg_auth,
    )

    tier: ProfileTier = derive_profile_tier(  # type: ignore[assignment]
        has_product=bool(selected),
        grounding=grounding,
        coverage=coverage_rate,
        source_quality=sq_rate,
    )

    notes = list(resolved.notes) + notes_extra
    if grounding < 1.0:
        notes.append(
            f"Source grounding rate {grounding:.0%} — ungrounded facts must not be presented as factual."
        )
    if not claim_facts:
        notes.append("No concrete claims extracted; profile is identity + sources only.")
    notes.extend(_contradiction_notes(facts))
    unknown_n = sum(1 for f in facts if f.epistemic == "unknown")
    if unknown_n:
        notes.append(
            f"{unknown_n} research checklist slot(s) remain UNKNOWN — profile is incomplete until filled."
        )

    stages = _stages(
        company=resolved.company.name,
        products=[p.name for p in resolved.products],
        sources_n=len(collected),
        profile_ready=True,
        needs_choice=False,
        tier=tier,
    )

    profile = RobotProfile(
        submitted_url=safe,
        company=resolved.company,
        products=resolved.products,
        selected_product=selected,
        sources=[c.source for c in collected],
        facts=facts,
        profile_confidence=tier,
        source_grounding_rate=grounding,
        coverage_rate=coverage_rate,
        coverage_level=coverage_level,
        source_quality_rate=sq_rate,
        source_quality_level=sq_level,
        research_morphology=morphology,
        ungrounded_fact_ids=ungrounded,
        notes=notes,
        needs_product_choice=False,
        research_stages=stages,
        inference=inference,
        preview_images=preview_images,
    )
    if timings is not None:
        timings["profile_ms"] = int((time.perf_counter() - t_profile) * 1000)
    return profile


def _stages(
    *,
    company: str,
    products: list[str],
    sources_n: int,
    profile_ready: bool,
    needs_choice: bool,
    tier: str | None = None,
) -> list[dict[str, Any]]:
    prod_detail = ", ".join(products) if products else "none found"
    return [
        {
            "id": "identify_company",
            "label": "Identifying company",
            "status": "done",
            "detail": company,
        },
        {
            "id": "find_products",
            "label": "Finding robot products",
            "status": "done",
            "detail": prod_detail,
        },
        {
            "id": "review_sources",
            "label": "Reviewing product sources",
            "status": "done" if sources_n or needs_choice else "pending",
            "detail": None if needs_choice else f"{sources_n:02d} sources",
        },
        {
            "id": "build_profile",
            "label": "Building robot profile",
            "status": "done" if profile_ready else ("skipped" if needs_choice else "pending"),
            "detail": f"Profile {tier}" if profile_ready and tier else None,
        },
    ]


def _facts_from_catalog_robot(
    robot: dict,
    *,
    subject: str,
    product_id: str | None,
) -> tuple[RobotSource, list[RobotFact]]:
    url = (robot.get("product_url") or robot.get("vendor_url") or "").strip()
    src = RobotSource.create(
        url or "vendor-robots-index",
        "product",
        title=str(robot.get("name") or subject),
        confidence=0.72,
        product_id=product_id,
        text_excerpt="Vendor robot index (not a live OEM crawl).",
    )
    facts = [
        RobotFact.create(
            subject,
            str(claim["predicate"]),
            claim["value"],
            source_id=src.id,
            epistemic=claim.get("epistemic") or "explicit",
            units=claim.get("units"),
            confidence=0.72,
            evidence_span=claim.get("evidence_span"),
        )
        for claim in catalog_claim_facts(robot)
    ]
    return src, facts


def _contradiction_notes(facts) -> list[str]:
    contradicted = [f for f in facts if f.epistemic == "contradicted"]
    if not contradicted:
        return []
    preds = sorted({f.predicate for f in contradicted})
    return [
        f"CONFLICTED across manufacturer sources: {', '.join(preds)}. "
        "Both values retained — do not collapse."
    ]


def _norm_product_key(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def _bind_requested_product(
    company_id: str,
    products: list[RobotProduct],
    product_name: str,
) -> RobotProduct:
    """
    Always materialize the caller-requested product as selected_product.

    Exact / fuzzy match against resolved list; otherwise create a new RobotProduct.
    No OEM-specific branches — name matching only.
    """
    wanted = product_name.strip()
    if not wanted:
        return RobotProduct.create(company_id, "Unknown")
    key = _norm_product_key(wanted)
    for p in products:
        if _norm_product_key(p.name) == key:
            return p
    for p in products:
        pk = _norm_product_key(p.name)
        if key in pk or pk in key:
            return p
    return RobotProduct.create(company_id, wanted)
