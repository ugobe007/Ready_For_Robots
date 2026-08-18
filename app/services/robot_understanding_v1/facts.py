"""
Phase 3 — extract atomic facts from typed sources.

Extraction contract (docs/robot_understanding_v1.md):
  Ask: What concrete claims about this robot are supported by this source?
  Do not ask: What can this robot do?
  Do not resolve contradictions — emit multiple facts.
  Do not invent capabilities, workflows, or jobs.
"""
from __future__ import annotations

import re
from typing import Callable

from app.services.robot_understanding_v1.models import RobotFact, RobotSource
from app.services.robot_understanding_v1.sources import CollectedSource

# predicate extractors: (predicate, pattern, value_fn, units_or_none, confidence)
# value_fn(match) -> value


def extract_facts_from_sources(
    collected: list[CollectedSource],
    *,
    subject: str,
) -> list[RobotFact]:
    facts: list[RobotFact] = []
    for item in collected:
        facts.extend(
            _extract_from_page(
                item.source,
                item.page.text or "",
                subject=subject,
                page_url=item.page.final_url,
                page_title=item.page.title or "",
            )
        )
    return facts


# Capability/class claims that define what the *selected* product does. On a
# multi-product company these must be attributed by evidence proximity, not by a
# page-level subject match — a shared nav/footer that lists "Servi" makes every
# sibling page (e.g. a floor-scrubber page) "support" Servi, which is how a
# serving robot wrongly inherited scrubbing. Numeric constraints are always gated.
_CONSTRAINT_PREDS = {
    "carrying_capacity",
    "battery_runtime",
    "reach_or_workspace",
    "max_speed",
    "arm_count",
    "degrees_of_freedom",
    "ingress_protection",
    "product_class",
}
_SCOPED_CAPABILITY_PREDS = {
    "product_class",
    "claims_surface_cleaning",
    "supports_hard_floor_scrubbing",
    "claims_food_prep",
    "claims_beverage_prep",
    "supports_tote_handling",
    "claims_warehouse_transport",
    "claims_item_delivery",
    "claims_load_unload",
    "has_dexterous_hands",
    "end_effector",
}
# Proximity window: the subject name must appear within this many characters of
# the capability evidence for the claim to attach to the selected product.
_SUBJECT_PROXIMITY_CHARS = 240


_GENERIC_PAGE_SLUGS = {
    "", "faq", "about", "contact", "products", "product", "platform", "home",
    "index", "restaurants", "restaurant", "pricing", "blog", "news", "support",
    "solutions", "company", "technology", "hospitality", "healthcare", "warehouse",
    "logistics", "industries", "resources", "en", "eldercare", "airport", "retail",
    "manufacturing", "commercial", "utilities", "specs", "specifications", "features",
    "overview", "details", "datasheet", "documentation", "docs", "applications", "indoor",
}


# Path segments that are NOT product identities: locale/country codes (en, en-us),
# versions (v1, v2), and category/listing words. If a nested path is made up only
# of these plus generic leaves, it is a listing page (no specific product), so the
# slug is "" and the subject-proximity gate applies.
_LOCALE_SEGMENT_RE = re.compile(r"^[a-z]{2}([-_][a-z]{2,3})?$")  # en, en-us, en_gb, fr
_VERSION_SEGMENT_RE = re.compile(r"^v\d+(?:[._]\d+)*$")           # v1, v2, v2.1
_NON_PRODUCT_SLUGS = {
    "robots", "robot", "models", "model", "catalog", "catalogue", "category",
    "categories", "lineup", "portfolio", "series", "range", "fleet",
    "us", "usa", "uk", "eu", "global", "intl", "international",
}


def _page_product_slug(url: str) -> str:
    """Deepest path segment that names a specific product — or "" for a listing.

    For nested paths (e.g. /servi-clean/specs) returns the product slug
    ("serviclean"). Locale/country/version/category prefixes (en-us, v2, robots,
    us) are NOT product identities and are skipped; a path with only such segments
    plus generic leaves returns "" so it is treated as a generic listing page and
    the subject-proximity gate still runs (prevents sibling capability leakage)."""
    from urllib.parse import urlparse

    try:
        path = (urlparse(url).path or "").rstrip("/")
        segments = [s for s in path.split("/") if s]
        for seg in reversed(segments):
            low = seg.lower()
            normalized = re.sub(r"[^a-z0-9]", "", low)
            if not normalized:
                continue
            if normalized in _GENERIC_PAGE_SLUGS or normalized in _NON_PRODUCT_SLUGS:
                continue
            if _LOCALE_SEGMENT_RE.match(low) or _VERSION_SEGMENT_RE.match(low):
                continue
            return normalized
        # No product-specific segment — a listing/locale/version path.
        return ""
    except Exception:
        return ""


def _page_is_prefix_sibling(page_slug: str, subj_key: str) -> bool:
    """True if the page is a dedicated page for a DIFFERENT product in the same
    prefix family (e.g. subject 'servi' vs page 'serviclean'/'serviplus'/'serviq').
    This is the case a bare word/proximity match cannot separate."""
    if not page_slug or not subj_key or page_slug == subj_key:
        return False
    if page_slug in _GENERIC_PAGE_SLUGS:
        return False
    # Same family, more/less specific → a sibling variant page.
    return page_slug.startswith(subj_key) or subj_key.startswith(page_slug)


def _subject_in_window(window: str, subj_key: str, tokens: set[str]) -> bool:
    """True if the selected product is named (as a whole word) in the window.
    Word-bounded so "Servi" does not spuriously match "service"/"serving"."""
    low = (window or "").lower()
    for t in tokens:
        t = (t or "").strip()
        if len(t) < 3:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", low):
            return True
    return False


def filter_facts_to_subject(
    facts: list[RobotFact],
    collected: list[CollectedSource],
    *,
    subject: str,
    multi_product: bool = False,
) -> tuple[list[RobotFact], int]:
    """
    Drop material facts whose evidence is about a sibling SKU / off-subject page.

    Gate: selected-product profiles must not present another model's payload etc.
    When ``multi_product`` is set (the company sells several robots), capability
    and product-class claims must be *subject-proximate* — a claim whose evidence
    does not mention the selected product nearby belongs to a sibling product and
    is dropped. Single-product companies keep the permissive page-level behaviour.
    """
    from app.services.robot_understanding_v1.sources import page_supports_subject, subject_tokens

    by_id = {c.source.id: c for c in collected}
    subj_key = re.sub(r"[^a-z0-9]", "", subject.lower())
    tokens = subject_tokens(subject)
    kept: list[RobotFact] = []
    dropped = 0

    for f in facts:
        if f.epistemic == "unknown":
            kept.append(f)
            continue
        item = by_id.get(f.source_id)
        if item is None:
            kept.append(f)
            continue
        page = item.page
        supports = page_supports_subject(
            url=page.final_url,
            title=page.title or "",
            text=page.text or "",
            product_name=subject,
        )
        span = f.evidence_span or ""
        window = span
        prox_window = span
        if span and page.text:
            idx = page.text.find(span[: min(40, len(span))])
            if idx >= 0:
                window = page.text[max(0, idx - 100) : idx + len(span) + 100]
                prox_window = page.text[
                    max(0, idx - _SUBJECT_PROXIMITY_CHARS)
                    : idx + len(span) + _SUBJECT_PROXIMITY_CHARS
                ]

        if f.predicate in _CONSTRAINT_PREDS and not supports:
            # Off-subject product/spec page — do not inherit constraints
            dropped += 1
            continue

        if f.predicate in _CONSTRAINT_PREDS and _evidence_names_sibling_sku(
            window, subj_key=subj_key, tokens=tokens
        ):
            dropped += 1
            continue

        # Multi-product subject scoping for capability/class claims.
        if multi_product and subj_key and f.predicate in _SCOPED_CAPABILITY_PREDS:
            page_slug = _page_product_slug(page.final_url or item.source.url or "")
            # (a) Dedicated page for a prefix-sibling product (e.g. /servi-clean
            #     while researching Servi) — its capabilities are that product's,
            #     not the subject's. A bare word/proximity match can't separate
            #     these because the sibling name contains the subject name.
            if _page_is_prefix_sibling(page_slug, subj_key):
                dropped += 1
                continue
            # (b) Any page that is NOT the subject's own product page (listings,
            #     company/overview pages, or a different product) must name the
            #     subject near the evidence — otherwise the claim belongs to some
            #     other product. Only the subject's dedicated page (slug == subject)
            #     is trusted unconditionally.
            elif page_slug != subj_key and not _subject_in_window(
                prox_window, subj_key, tokens
            ):
                dropped += 1
                continue

        kept.append(f)
    return kept, dropped


def _evidence_names_sibling_sku(window: str, *, subj_key: str, tokens: set[str]) -> bool:
    """True if evidence window cites a different model SKU than the subject."""
    if not window:
        return False
    # Compact model tokens only (MiR250, UR10e, MC-600) — not "Runtime 90" / "Weight 14"
    for m in re.finditer(r"\b([A-Za-z]{2,}[-]?\d{2,4}[A-Za-z]?)\b", window):
        raw = m.group(1)
        key = re.sub(r"[^a-z0-9]", "", raw.lower())
        if key.startswith("ip") and key[2:].isdigit():
            continue
        if key.startswith("iso"):
            continue
        if key == subj_key or any(key == re.sub(r"[^a-z0-9]", "", t) for t in tokens):
            continue
        if subj_key and (key in subj_key or subj_key in key):
            continue
        if re.search(r"\d", key) and key != subj_key:
            return True
    return False


def _extract_from_page(
    source: RobotSource,
    text: str,
    *,
    subject: str,
    page_url: str = "",
    page_title: str = "",
) -> list[RobotFact]:
    if not text or len(text) < 40:
        return []
    out: list[RobotFact] = []
    page_about_subject = True
    if subject and len(subject) >= 2:
        from app.services.robot_understanding_v1.sources import page_supports_subject

        page_about_subject = page_supports_subject(
            url=page_url or source.url,
            title=page_title or (source.title or ""),
            text=text,
            product_name=subject,
        )

    def add(
        predicate: str,
        value,
        *,
        units: str | None = None,
        span: str,
        confidence: float = 0.9,
        require_subject_near: bool = False,
        start: int | None = None,
        end: int | None = None,
        value_scope: str = "whole_robot",
    ) -> None:
        if require_subject_near and start is not None and end is not None:
            if not page_about_subject and not _subject_near(subject, text, start, end):
                return
        if predicate in {
            "carrying_capacity",
            "battery_runtime",
            "reach_or_workspace",
            "max_speed",
        }:
            if not _numeric_value_plausible(
                predicate, value, units, span, value_scope=value_scope
            ):
                return
            if (
                predicate == "carrying_capacity"
                and value_scope in {"per_tray", "per_shelf", "per_deck", "accessory"}
            ):
                return
        out.append(
            RobotFact.create(
                subject=subject,
                predicate=predicate,
                value=value,
                source_id=source.id,
                epistemic="explicit",
                units=units,
                confidence=min(0.98, confidence * source.confidence / 0.85),
                evidence_span=span.strip(),
            )
        )

    # Dense label/value tables first (where datasheet facts live)
    _extract_spec_table_facts(text, add)

    # --- carrying / payload (manufacturer phrasing varies) ---
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*\+?\s*"
        r"(lb|lbs|pound|pounds|kg|kilogram|kilograms)\s+"
        r"(?:carrying\s+capacity|payload(?:\s+capacity)?|high\s+payload|of\s+payload|"
        r"load\s+capacity|rated\s+load)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.95,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(?:carrying\s+capacity|payload(?:\s+capacity)?|high\s+payload|max\s+(?:payload|weight)|"
        r"payload\s+capacity|load\s+capacity|rated\s+(?:load|payload)|max\.?\s*payload)\s*"
        r"(?:\([^)]*\)\s*)?(?:of\s+|[:：\|]\s*)?"
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*\+?\s*"
        r"(lb|lbs|pound|pounds|kg|kilogram|kilograms)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.95,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*\+?\s*"
        r"(lb|lbs|pound|pounds)\s+(?:carrying\s+capacity|per\s+arm)",
        text,
        re.I,
    ):
        scope = (
            "per_arm"
            if re.search(r"per\s+arm", m.group(0), re.I)
            else _infer_payload_scope(text, m.start(), m.end())
        )
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.93,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=scope,
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*\+\s*(lbs?|pounds?|kg)\s+High\s+payload",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    # Compact: "14kg of payload" / "250kg payload" / "1,900 kg payload"
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(kg|lb|lbs)\s+(?:of\s+)?payload(?:\s+capacity)?",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.94,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(?:handle|handles|handling)\s+up\s+to\s+"
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(kg|lb|lbs)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope=_infer_payload_scope(text, m.start(), m.end()),
        )
    for m in re.finditer(
        r"(?:total(?:\s+capacity)?|capacity\s+total)\s*"
        r"(?:of\s+|[:：]\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
        r"(kg|lb|lbs|pound|pounds)",
        text,
        re.I,
    ):
        add(
            "carrying_capacity",
            _num(m.group(1)),
            units=_unit(m.group(2)),
            span=m.group(0),
            confidence=0.94,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
            value_scope="whole_robot",
        )
    for m in re.finditer(
        r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(kg|lb|lbs)\s+total\b",
        text,
        re.I,
    ):
        ctx = text[max(0, m.start() - 40) : m.end() + 40]
        if re.search(r"payload|capacit|load|carry", ctx, re.I):
            add(
                "carrying_capacity",
                _num(m.group(1)),
                units=_unit(m.group(2)),
                span=m.group(0),
                confidence=0.9,
                require_subject_near=True,
                start=m.start(),
                end=m.end(),
                value_scope="whole_robot",
            )

    # --- battery / runtime (hours and minutes) ---
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(hour|hours|hr|hrs|h)\s+"
        r"(?:battery(?:\s+life)?|long\s+operation\s+time|operation\s+time)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:battery(?:\s+life)?|operation\s+time|runtime|average\s+runtime|"
        r"run\s*time|operating\s+time)\s*\*?\s*"
        r"(?:of\s+|[:：\|]\s*)?(\d+(?:\.\d+)?)\s*\+?\s*"
        r"(hour|hours|hr|hrs|h|min|mins|minutes)\b",
        text,
        re.I,
    ):
        units = "min" if re.search(r"min", m.group(2), re.I) else "hr"
        add(
            "battery_runtime",
            _num(m.group(1)),
            units=units,
            span=m.group(0),
            confidence=0.93,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*\+\s*h\b[^.]{0,40}(?:operation|battery|charge)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0)[:80],
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:run|operate|operates)\s+up\s+to\s+(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs)\s+a\s+day",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0),
            confidence=0.88,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*(min|mins|minutes)\s+(?:average\s+)?(?:runtime|battery)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="min",
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*[-–/]\s*(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs)\s+"
        r"(?:runtime|battery|operation)",
        text,
        re.I,
    ):
        add(
            "battery_runtime",
            _num(m.group(1)),
            units="hr",
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- product class / form (explicit claims only) ---
    for m in re.finditer(
        r"\b((?:commercially\s+deployed\s+)?humanoid(?:\s+robot)?|bipedal(?:\s+robot)?)\b",
        text,
        re.I,
    ):
        if not _subject_near(subject, text, m.start(), m.end()):
            continue
        # Skip third-party news blurbs
        ctx = text[max(0, m.start() - 80) : m.end() + 40]
        if re.search(r"\b(honda|asimo|avatar|in\s+the\s+news|ieee)\b", ctx, re.I):
            continue
        add("product_class", "humanoid", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(autonomous\s+mobile\s+robots?|\bAMR\b|autonomous\s+guided\s+vehicles?|\bAGV\b)\b",
        text,
        re.I,
    ):
        ctx = text[max(0, m.start() - 60) : m.end() + 40]
        if re.search(
            r"\b(unlike|versus|vs\.?|compared\s+to|different\s+from|not\s+an|"
            r"AGV\s*\(|AMR\s*\(|shift\s+from|platform\s+for\s+enterprise)\b",
            ctx,
            re.I,
        ):
            continue
        if subject and len(subject) >= 2 and not page_about_subject:
            near = text[max(0, m.start() - 100) : m.end() + 100]
            if subject.lower() not in near.lower() and not re.search(
                r"\b(our\s+robot|this\s+robot|collaborative\s+robot)\b", near, re.I
            ):
                continue
        label = "amr" if re.search(r"amr|autonomous\s+mobile", m.group(0), re.I) else "agv"
        add("product_class", label, span=m.group(0), confidence=0.88)

    # Title/H1 style: "Locus Origin: Collaborative Robots Warehouse"
    if subject and re.search(rf"\b{re.escape(subject)}\b", text[:300], re.I):
        head = text[:400]
        if re.search(r"\bcollaborative\s+robots?\b", head, re.I) and re.search(
            r"\bwarehouse\b", head, re.I
        ):
            add(
                "product_class",
                "amr",
                span="collaborative robots warehouse",
                confidence=0.75,
            )

    for m in re.finditer(
        r"\b(floor\s+scrubber|autonomous\s+(?:hard[- ]floor\s+)?scrubber|auto[- ]?scrubber|"
        r"robotic\s+floor\s+scrubber)\b",
        text,
        re.I,
    ):
        add("product_class", "autonomous_scrubber", span=m.group(0), confidence=0.92)

    for m in re.finditer(
        r"\b((?:autonomous|commercial|robotic)\s+vacuum(?:\s+cleaner)?|"
        r"robot\s+vacuum|vacuum\s+cleaning\s+robots?|cleaning\s+robots?)\b",
        text,
        re.I,
    ):
        if re.search(r"scrub", m.group(0), re.I):
            continue
        add("product_class", "cleaning_robot", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(mobile\s+manipulation(?:\s+robot)?|mobile\s+manipulator|"
        r"general[- ]purpose\s+mobile\s+robot)\b",
        text,
        re.I,
    ):
        # Avoid accessory-arm bleed: require subject near or page about subject
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "mobile_manipulator", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(quadruped|four[- ]legged(?:\s+robot)?|legged\s+mobile\s+robot|"
        r"agile\s+mobile\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        label = (
            "quadruped"
            if re.search(r"quadruped|four[- ]legged|legged", m.group(0), re.I)
            else "mobile_robot"
        )
        add("product_class", label, span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(collaborative\s+(?:robot\s+)?arm|cobot(?:\s+arm)?|"
        r"collaborative\s+industrial\s+robot|6[- ]axis\s+(?:robot\s+)?arm|"
        r"collaborative\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "cobot_arm", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b((?:indoor\s+)?(?:inspection\s+)?drone|UAV|aerial\s+(?:robot|platform)|"
        r"flying\s+robot|confined[- ]space\s+(?:drone|UAV))\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "drone", span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"\b(construction\s+robot|drywall\s+(?:finishing|robot)|layout\s+printer|"
        r"field\s*printer|jobsite\s+robot|construction\s+(?:layout|finishing)\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "construction_robot", span=m.group(0), confidence=0.88)

    for m in re.finditer(
        r"\b(service\s+robot|hospitality\s+robot|restaurant\s+(?:delivery\s+)?robot|"
        r"social\s+robot|delivery\s+robot)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("product_class", "service_robot", span=m.group(0), confidence=0.88)

    for m in re.finditer(r"\b(dual[- ]arm|two\s+arms|bimanual)\b", text, re.I):
        add("arm_count", 2, span=m.group(0), confidence=0.9)

    for m in re.finditer(
        r"(\d+)\s*(?:DoF|DOF|degrees?\s+of\s+freedom)",
        text,
        re.I,
    ):
        add(
            "degrees_of_freedom",
            _num(m.group(1)),
            span=m.group(0),
            confidence=0.88,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:DoF|DOF|degrees?\s+of\s+freedom)\s*[:：\|]?\s*(\d+)",
        text,
        re.I,
    ):
        add(
            "degrees_of_freedom",
            _num(m.group(1)),
            span=m.group(0),
            confidence=0.88,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- reach / work envelope (m / mm / ft) ---
    for m in re.finditer(
        r"(?:stretch(?:es)?\s+up\s+to|reach(?:es)?\s+up\s+to|large\s+workspace|"
        r"workspace|reach|wrist\s+reach|max(?:imum)?\s+reach)\s*[:(|]?\s*"
        r"(\d+(?:\.\d+)?)\s*(mm|cm|m|meters?|ft|feet|'|′)\b",
        text,
        re.I,
    ):
        unit_raw = m.group(2).lower()
        if unit_raw in {"mm"}:
            unit = "mm"
        elif unit_raw in {"cm"}:
            unit = "cm"
        elif unit_raw in {"m", "meter", "meters"}:
            unit = "m"
        else:
            unit = "ft"
        add(
            "reach_or_workspace",
            _num(m.group(1)),
            units=unit,
            span=m.group(0)[:100],
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*(mm|m)\s+reach\b",
        text,
        re.I,
    ):
        add(
            "reach_or_workspace",
            _num(m.group(1)),
            units=m.group(2).lower(),
            span=m.group(0),
            confidence=0.92,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )
    for m in re.finditer(
        r"(?:stretch|reach|workspace|high[- ]reaching)[^.]{0,80}\((\d+(?:\.\d+)?)\s*m\)",
        text,
        re.I,
    ):
        add(
            "reach_or_workspace",
            _num(m.group(1)),
            units="m",
            span=m.group(0)[:100],
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- speed ---
    for m in re.finditer(
        r"(?:max(?:imum)?\s+speed|top\s+speed|moves?\s+along\s+at)\s*"
        r"(?:of\s+|[:：]\s*)?(\d+(?:\.\d+)?)\s*(m/s|meters?\s+per\s+second)",
        text,
        re.I,
    ):
        add(
            "max_speed",
            _num(m.group(1)),
            units="m/s",
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- ingress / environment rating ---
    for m in re.finditer(r"\b(IP\d{2}[A-Z]?)\b", text, re.I):
        add(
            "ingress_protection",
            m.group(1).upper(),
            span=m.group(0),
            confidence=0.9,
            require_subject_near=True,
            start=m.start(),
            end=m.end(),
        )

    # --- end effector / hands ---
    for m in re.finditer(
        r"\b(dexterous\s+hands?|end[- ]effectors?|grippers?|bimanual\s+dexterity)\b",
        text,
        re.I,
    ):
        add("has_dexterous_hands", True, span=m.group(0), confidence=0.88)
        add("end_effector", "dexterous_hand", span=m.group(0), confidence=0.85)

    # --- tote handling (explicit demonstration / claim) ---
    for m in re.finditer(
        r"(moves?\s+over\s+[\d,]+\s+totes?|tote[- ]based\s+workflows?|"
        r"managing\s+tote[- ]based|handling\s+(?:different\s+types\s+of\s+)?totes?|"
        r"loading\s+and\s+unloading[^.]*totes?|"
        r"tote[- ]?arrays?|containers?,?\s+including\s+tote|"
        r"from\s+tote[- ]?arrays?)",
        text,
        re.I,
    ):
        add(
            "supports_tote_handling",
            True,
            span=m.group(0),
            confidence=0.9,
        )

    # --- goods movement claims (concrete, not job inference) ---
    for m in re.finditer(
        r"\b(person[- ]to[- ]goods|goods[- ]to[- ]person|P2G|G2P|"
        r"point[- ]to[- ]point\s+transport|warehouse\s+transport)\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_warehouse_transport", True, span=m.group(0), confidence=0.85)

    # --- autonomous item delivery / transport (service & delivery robots) ---
    # A robot that itself carries and delivers items point-to-point (meals,
    # medications, lab samples, guest amenities, room service, packages). This is
    # a transport capability that is NOT warehouse tote handling — hospitality and
    # healthcare delivery robots (Relay, Keenon, Pudu) are transport robots too.
    for m in re.finditer(
        r"\b(?:"
        r"delivery\s+robots?|autonomous\s+delivery|"
        r"(?:deliver|transport|carr(?:y|ies|ying)|bring)\w*\s+(?:[\w-]+\s+){0,4}?"
        r"(?:items?|goods|medications?|medicines?|supplies|samples?|specimens?|"
        r"amenities|meals?|food|drinks?|beverages?|packages?|parcels?|documents?|"
        r"linens?|laundry|room[- ]service)|"
        r"room[- ]service\s+(?:delivery|deliveries|items?)|guest\s+amenities"
        r")\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_item_delivery", True, span=m.group(0)[:120], confidence=0.85)

    # Serving (restaurant food/drink running to tables) and luggage/bellhop are
    # delivery variants — the robot carries and delivers to a destination.
    for m in re.finditer(
        r"\b(?:"
        r"food[- ]runn\w+|food\s+runner|bus(?:s|es|sing|ses)\s+tables?|table\s+service|"
        r"robot\s+server|server\s+robot|serv(?:e|es|ing)\s+(?:[\w-]+\s+){0,3}?"
        r"(?:food|drinks?|meals?|entr[e\u00e9]es?|dishes|beverages?|guests?|tables?|customers?|diners?)|"
        r"bell[- ]?hop|luggage|baggage"
        r")\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_item_delivery", True, span=m.group(0)[:120], confidence=0.82)

    # --- food preparation / cooking (kitchen & food-prep robots) ---
    # Dexterous food manipulation: frying, grilling, cooking, chopping, and
    # assembling meals. Kept a distinct capability (food_prep) — it must NOT leak
    # into generic industrial manipulation (a fry robot is not a CNC-tender).
    for m in re.finditer(
        r"\b(?:"
        r"fry(?:ing)?\s+station|fry\s+cook|fried\s+menu|cooking\s+robot|"
        r"ai[- ]controlled\s+cooking|automated\s+cooking|robotic\s+kitchen|kitchen\s+automation|"
        r"food\s+prep(?:aration)?|"
        r"prepar(?:e|es|ing)\s+(?:[\w-]+\s+){0,2}?(?:food|meals?|salads?|bowls?|dishes|entr[e\u00e9]es?|ingredients?)|"
        r"assembl(?:e|es|ing)\s+(?:[\w-]+\s+){0,2}?(?:meals?|bowls?|salads?|dishes|entr[e\u00e9]es?|tacos?|burritos?|sandwich\w*|pizzas?)|"
        r"grill\w+\s+(?:food|burgers?|patties|meat)|cook\w*\s+(?:food|meals?|fries|burgers?|the\s+\w+\s+menu)|"
        r"(?:chop|slice|dice|peel)\w*\s+(?:vegetables?|produce|ingredients?|food)"
        r")\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_food_prep", True, span=m.group(0)[:120], confidence=0.85)

    # --- beverage / drink preparation (barista & bartender robots) ---
    for m in re.finditer(
        r"\b(?:"
        r"barista(?:\s+robot)?|robot\s+barista|bartend\w*|robot\s+bartender|"
        r"(?:make|makes|making|prepar\w+|craft\w+|brew\w+|mix\w+)\s+(?:[\w-]+\s+){0,3}?"
        r"(?:coffee|espresso|latte\w*|cappuccino\w*|cocktails?|drinks?|beverages?|smoothies?|boba|bubble\s+tea)|"
        r"(?:coffee|espresso|cocktail|drink|beverage)\s+(?:making|preparation|robot|station)"
        r")\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_beverage_prep", True, span=m.group(0)[:120], confidence=0.82)

    # --- surface / restroom cleaning (broader than hard-floor scrubbing) ---
    # Restroom/bathroom cleaning, fixtures (toilets, urinals, sinks), carpet and
    # vacuum cleaning. Distinct from hard_floor_scrub so it maps to the right work.
    for m in re.finditer(
        r"\b(?:"
        r"bathroom\s+cleaning|restroom\s+cleaning|clean\w*\s+(?:bathrooms?|restrooms?)|"
        r"clean\w*\s+(?:toilets?|urinals?|sinks?|fixtures?|mirrors?)|"
        r"(?:toilets?|urinals?)\s*,?\s+(?:and\s+)?(?:floors?|sinks?|fixtures?)|"
        r"carpet\s+(?:clean\w*|extract\w*|shampoo\w*)|"
        r"vacuum\w*\s+(?:carpets?|floors?|robot)|robotic\s+vacuum|"
        r"commercial\s+cleaning\s+robot"
        r")\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_surface_cleaning", True, span=m.group(0)[:120], confidence=0.85)

    # --- retail shelf / inventory scanning (autonomous inventory robots) ---
    # Simbe Tally-class: computer-vision robots that scan aisles/shelves for
    # out-of-stocks, pricing, and planogram compliance. A perception capability,
    # distinct from manipulation/transport/cleaning.
    for m in re.finditer(
        r"\b(?:"
        r"shelf[-\s]scann\w+|inventory\s+robots?|autonomous\s+inventory|"
        r"scan(?:s|ning)?\s+(?:the\s+)?(?:aisles?|shelves|shelf|store\s+shelves)|"
        r"out[-\s]of[-\s]stock\s+(?:detection|alerts?|monitoring)|planogram\w*|"
        r"on[-\s]shelf\s+availability|shelf\s+(?:intelligence|conditions)"
        r")\b",
        text,
        re.I,
    ):
        if not page_about_subject and not _subject_near(subject, text, m.start(), m.end()):
            continue
        add("claims_shelf_scan", True, span=m.group(0)[:120], confidence=0.85)

    # --- warehouse / factory deployment claims ---
    for m in re.finditer(
        r"\b(commercially\s+deployed|commercial\s+deployment|deployed\s+in\s+"
        r"(?:a\s+)?(?:warehouse|factory|fulfillment)|warehouse(?:s)?\s+and\s+factory(?:ies)?|"
        r"manufacturing\s+and\s+warehous(?:e|ing)|warehousing\s+workflows?)\b",
        text,
        re.I,
    ):
        add("warehouse_or_factory_deployment", True, span=m.group(0), confidence=0.85)

    # --- scrubbing (explicit) ---
    for m in re.finditer(
        r"\b(hard[- ]floor\s+(?:scrub|clean)|floor\s+scrubbing|auto[- ]?scrub(?:bing)?\s+routes?)\b",
        text,
        re.I,
    ):
        add("supports_hard_floor_scrubbing", True, span=m.group(0), confidence=0.93)

    # --- mobile base / mobility architecture ---
    for m in re.finditer(
        r"\b(omni[- ]?directional\s+(?:mobile\s+)?base(?:\s+movement)?|"
        r"omnidirectional\s+mobile\s+base|mobile\s+base|"
        r"wheeled\s+(?:base|platform)|bipedal\s+(?:walk|locomotion|mobility)|"
        r"walk(?:s|ing)?\s+and\s+run(?:s|ning)?|"
        r"autonomous\s+navigation)\b",
        text,
        re.I,
    ):
        if re.search(r"omni|mobile\s+base|wheeled|bipedal|walk", m.group(0), re.I):
            add("has_mobile_base", True, span=m.group(0), confidence=0.9)
            if re.search(r"omni", m.group(0), re.I):
                add(
                    "mobility_architecture",
                    "omnidirectional_base",
                    span=m.group(0),
                    confidence=0.9,
                )
            elif re.search(r"bipedal|walk", m.group(0), re.I):
                add(
                    "mobility_architecture",
                    "bipedal",
                    span=m.group(0),
                    confidence=0.88,
                )
        if re.search(r"autonomous\s+navigation", m.group(0), re.I):
            add("autonomous_navigation", True, span=m.group(0), confidence=0.88)

    for m in re.finditer(
        r"\b(LiDAR\s+navigation|SLAM|programmed\s+routes?|autonomous\s+(?:driving|routing|mapping)|"
        r"AI[- ]?(?:powered\s+)?navigation|indoor\s+(?:GPS|navigation)|FlyAware|"
        r"obstacle\s+avoidance|autonomous(?:ly)?\s+(?:navigat\w+|map\w+|patrol\w+)|"
        r"navigat\w+\s+(?:your|the|its)\s+(?:building|facility|facilities|floors?|space|environment|way)|"
        r"navigat\w+\s+(?:[\w.,-]+\s+){0,3}?(?:stores?|aisles?|warehouses?|facilit\w+)|"
        r"mov(?:e|es)\s+(?:autonomously|on\s+its\s+own)|drives?\s+itself|self[- ]driving|self[- ]navigat\w+)\b",
        text,
        re.I,
    ):
        add("autonomous_navigation", True, span=m.group(0), confidence=0.86)

    # --- operating environment / vertical (using ontology keys only) ---
    for m in re.finditer(
        r"\b((?:indoor|outdoor)\s+(?:industrial\s+)?(?:spaces?|environments?|facilities?)|"
        r"confined\s+(?:spaces?|industrial)|"
        r"nursing\s+homes?|senior\s+living|assisted\s+living|memory\s+care|"
        r"skilled\s+nursing|long[-\s]term\s+care|rehabilitation|physical\s+therapy|"
        r"surgery\s+cent(?:er|re)s?|surgical\s+cent(?:er|re)s?|clinics?|"
        r"pharmac(?:y|ies)|laborator(?:y|ies)|medical\s+cent(?:er|re)s?|"
        r"(?:hotels?|airports?|hospitals?|healthcare|retail|restaurants?|hospitality|"
        r"reception|warehouses?|factories?|jobsites?|construction\s+sites?))\b",
        text,
        re.I,
    ):
        raw = m.group(0).lower()
        # Vertical/environment ontology — see ontology/vertical_ontology.v1.json
        # Every emitted value must be a known vertical key.
        val = None
        if re.search(
            r"nursing\s+home|senior\s+living|assisted\s+living|memory\s+care|"
            r"skilled\s+nursing|long[-\s]term\s+care|rehabilitation|physical\s+therapy",
            raw,
        ):
            val = "eldercare"
        elif re.search(
            r"\bhospitals?\b|\bhealthcare\b|\bclinics?\b|surgery\s+cent|surgical\s+cent|"
            r"\bpharmac(?:y|ies)\b|\blaborator(?:y|ies)\b|medical\s+cent",
            raw,
        ):
            # Word-bounded: "hospital" must not match "hospitality" (a substring),
            # which belongs to the hospitality vertical below.
            val = "healthcare"
        elif re.search(r"hotel|hospitality", raw):
            val = "hospitality"
        elif re.search(r"restaurant", raw):
            val = "restaurant"
        elif re.search(r"airport", raw):
            val = "airport"
        elif re.search(r"retail", raw):
            val = "retail"
        elif re.search(r"workplace|facility|reception", raw):
            val = "commercial"
        elif re.search(r"construction|jobsite", raw):
            val = "construction"
        elif re.search(r"warehouse|factory", raw):
            val = "warehouse"
        elif re.search(r"confined", raw):
            val = "indoor"
        elif re.search(r"^indoor\s+", raw):
            val = "indoor"
        # Outdoor spaces/environments not yet mapped to a vertical — skip
        # rather than emit an unknown key.
        if val is not None:
            add("operating_environment", val, span=m.group(0)[:120], confidence=0.84)

    # --- load/unload as explicit claim (fact about claim, not capability inference) ---
    for m in re.finditer(
        r"\b(load(?:ing)?\s+and\s+unload(?:ing)?(?:\s+(?:of\s+)?(?:containers?|totes?|parts?))?)\b",
        text,
        re.I,
    ):
        add("claims_load_unload", True, span=m.group(0), confidence=0.85)

    return _dedupe_same_source_same_value(out)


def _extract_spec_table_facts(text: str, add) -> None:
    """Generic dense-table / label:value parser for manufacturer specs."""
    specs: list[tuple[str, re.Pattern[str]]] = [
        (
            "carrying_capacity",
            re.compile(
                r"(?:payload(?:\s+capacity)?|carrying\s+capacity|load\s+capacity|"
                r"max(?:imum)?\s+payload|rated\s+(?:load|payload)|max\.?\s*weight)\s*"
                r"[:：\|\-–—]\s*"
                r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
                r"(kg|lb|lbs|pounds?|kilograms?)",
                re.I,
            ),
        ),
        (
            "battery_runtime",
            re.compile(
                r"(?:(?:average\s+)?runtime|battery(?:\s+life)?|operation\s+time|"
                r"operating\s+time|run\s*time)\s*"
                r"\*?\s*[:：\|\-–—]\s*"
                r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hours?|min|mins|minutes)",
                re.I,
            ),
        ),
        (
            "reach_or_workspace",
            re.compile(
                r"(?:reach|workspace|wrist\s+reach|max(?:imum)?\s+reach)\s*"
                r"[:：\|\-–—]\s*"
                r"(\d+(?:\.\d+)?)\s*(mm|cm|m|meters?|ft)",
                re.I,
            ),
        ),
        (
            "degrees_of_freedom",
            re.compile(
                r"(?:degrees?\s+of\s+freedom|DoF|DOF)\s*[:：\|\-–—]?\s*(\d{1,2})\b",
                re.I,
            ),
        ),
        (
            "max_speed",
            re.compile(
                r"(?:max(?:imum)?\s+speed|top\s+speed)\s*[:：\|\-–—]\s*"
                r"(\d+(?:\.\d+)?)\s*(m/s|km/h)",
                re.I,
            ),
        ),
        (
            "ingress_protection",
            re.compile(
                r"(?:ingress\s+protection|IP\s*rating)\s*[:：\|\-–—]\s*(IP\d{2}[A-Z]?)",
                re.I,
            ),
        ),
    ]
    for predicate, pat in specs:
        for m in pat.finditer(text):
            if predicate == "ingress_protection":
                add(predicate, m.group(1).upper(), span=m.group(0), confidence=0.93)
                continue
            if predicate == "degrees_of_freedom":
                add(
                    predicate,
                    _num(m.group(1)),
                    span=m.group(0),
                    confidence=0.9,
                    require_subject_near=True,
                    start=m.start(),
                    end=m.end(),
                )
                continue
            raw_u = m.group(2)
            if predicate == "battery_runtime":
                units = "min" if re.search(r"min", str(raw_u), re.I) else "hr"
            elif predicate == "carrying_capacity":
                units = _unit(str(raw_u))
            elif predicate == "reach_or_workspace":
                u = str(raw_u).lower()
                units = (
                    "mm"
                    if u == "mm"
                    else ("cm" if u == "cm" else ("ft" if "ft" in u else "m"))
                )
            else:
                units = "m/s" if "m/s" in str(raw_u).lower() else str(raw_u)
            scope = (
                _infer_payload_scope(text, m.start(), m.end())
                if predicate == "carrying_capacity"
                else "whole_robot"
            )
            add(
                predicate,
                _num(m.group(1)),
                units=units,
                span=m.group(0),
                confidence=0.94,
                require_subject_near=True,
                start=m.start(),
                end=m.end(),
                value_scope=scope,
            )


def _infer_payload_scope(text: str, start: int, end: int) -> str:
    window = text[max(0, start - 50) : end + 50].lower()
    if re.search(r"\bper\s+tray\b|\b/tray\b|\beach\s+tray\b|\btray\s+capacity\b", window):
        return "per_tray"
    if re.search(r"\bper\s+shelf\b|\b/shelf\b", window):
        return "per_shelf"
    if re.search(r"\bper\s+deck\b|\b/deck\b", window):
        return "per_deck"
    if re.search(r"\bper\s+arm\b|\b/arm\b|\beach\s+arm\b", window):
        return "per_arm"
    if re.search(r"\baccessory\b|\badd[- ]?on\b|\boptional\s+module\b", window):
        return "accessory"
    if re.search(r"\btotal\b|\bwhole\b|\boverall\b|\bmax(?:imum)?\s+payload\b", window):
        return "whole_robot"
    return "whole_robot"


def _numeric_value_plausible(
    predicate: str,
    value,
    units: str | None,
    span: str,
    *,
    value_scope: str = "whole_robot",
) -> bool:
    """Reject JS placeholders and wrong-scope numerics (prefer unknown)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return True
    if v == 0:
        return False
    if value_scope in {"per_tray", "per_shelf", "per_deck", "accessory"}:
        return False
    return True


def _subject_near(subject: str, text: str, start: int, end: int, window: int = 140) -> bool:
    if not subject or len(subject) < 2:
        return True
    near = text[max(0, start - window) : end + window].lower()
    from app.services.robot_understanding_v1.sources import subject_tokens

    for tok in subject_tokens(subject):
        if tok and tok in near:
            return True
    if subject.lower() in near:
        return True
    return bool(re.search(r"\b(our\s+robot|this\s+robot)\b", near, re.I))


def _num(s: str) -> float:
    v = float(str(s).replace(",", ""))
    return int(v) if v.is_integer() else v


def _unit(raw: str) -> str:
    r = raw.lower()
    if r.startswith("kg") or "kilogram" in r:
        return "kg"
    return "lb"


def _dedupe_same_source_same_value(facts: list[RobotFact]) -> list[RobotFact]:
    """Drop exact duplicates from one source; keep cross-source contradictions."""
    seen: set[tuple] = set()
    out: list[RobotFact] = []
    for f in facts:
        key = (f.source_id, f.predicate, str(f.value), f.units)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


# Predicates where differing values are true contradictions (not multi-label).
_SCALAR_CONTRADICTION_PREDICATES = frozenset(
    {
        "carrying_capacity",
        "battery_runtime",
        "arm_count",
    }
)


def mark_contradictions(facts: list[RobotFact]) -> list[RobotFact]:
    """
    If same subject+scalar-predicate has differing values, mark epistemic
    as contradicted on conflicting rows (do not drop any).

    Multi-label predicates (e.g. product_class=humanoid and mobile_manipulator)
    are not treated as contradictions.
    """
    from collections import defaultdict

    groups: dict[tuple[str, str], list[RobotFact]] = defaultdict(list)
    for f in facts:
        if f.predicate not in _SCALAR_CONTRADICTION_PREDICATES:
            continue
        groups[(f.subject.lower(), f.predicate)].append(f)

    for rows in groups.values():
        values = {(str(r.value), r.units) for r in rows}
        if len(values) <= 1:
            continue
        for r in rows:
            r.epistemic = "contradicted"
    return facts
