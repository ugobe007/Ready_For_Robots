"""URL → FIND workflow critic: product range, named products, capabilities.

Drives the same identity path FIND uses (catalog listing + per-product
classify + capability derive). Never company → category → jobs.
Does not import robot_understanding_v1.fetch / facts (no requests).

Break classes:
  mixed_range_flattened     — mixed OEM collapsed to one company class
  chrome_as_sku             — nav/legal labels treated as products
  invented_sku              — category blob or company+class dump as a SKU
  empty_range_named         — page/catalog names products but picker is empty
  empty_range_on_robot_oem  — known robot OEM hub with 0 named products
  missing_products          — expected named robots absent from the picker
  cleaning_drone_as_scrubber — aerial cleaner classified as floor scrubber
  company_class_not_product_class — sibling SKUs share one OEM dump class
  capability_oem_default    — capabilities from OEM default, not this product
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "app" / "data" / "url_workflow_corpus.json"

BREAK_MIXED_FLAT = "mixed_range_flattened"
BREAK_CHROME = "chrome_as_sku"
BREAK_INVENTED = "invented_sku"
BREAK_EMPTY = "empty_range_named"
BREAK_EMPTY_OEM = "empty_range_on_robot_oem"
BREAK_MISSING = "missing_products"
BREAK_DRONE_SCRUB = "cleaning_drone_as_scrubber"
BREAK_COMPANY_CLASS = "company_class_not_product_class"
BREAK_CAP_DEFAULT = "capability_oem_default"
CLASS_DUMP_NAMES = frozenset({"amr scrubbers", "scrubber", "scrubbers", "seer humanoid"})

CHROME_NAMES = frozenset(
    {
        "about",
        "news",
        "blog",
        "careers",
        "contact",
        "product",
        "products",
        "imprint",
        "impressum",
        "privacy",
        "terms",
        "en",
        "investors",
        "vehicles",
        "home",
        "shop",
        "impact",
        "powered by ai",
        "why dexory",
    }
)
SCRUB_CLASSES = frozenset({"cleaning", "autonomous_scrubber", "scrubber", "cleaning_robot"})
DRONE_CLEAN_CLASSES = frozenset({"cleaning_drone", "drone", "uav"})
GENERIC_COMPANY_CLASSES = frozenset({"service_robot", "service", "robot", "commercial"})


@dataclass
class Break:
    kind: str
    detail: str
    product: str | None = None

    def to_dict(self) -> dict[str, Any]:
        row: dict[str, Any] = {"kind": self.kind, "detail": self.detail}
        if self.product:
            row["product"] = self.product
        return row


@dataclass
class ProductView:
    name: str
    display_class: str | None
    description: str | None = None
    capabilities_present: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_class": self.display_class,
            "description": self.description,
            "capabilities_present": list(self.capabilities_present),
        }


@dataclass
class UrlCritique:
    url: str
    vendor_name: str | None
    matched: bool
    products: list[ProductView]
    product_range: list[str]
    mixed_range: bool
    needs_class_choice: bool
    breaks: list[Break] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.breaks

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "ok": self.ok,
            "vendor_name": self.vendor_name,
            "matched": self.matched,
            "product_range": list(self.product_range),
            "mixed_range": self.mixed_range,
            "needs_class_choice": self.needs_class_choice,
            "products": [p.to_dict() for p in self.products],
            "breaks": [b.to_dict() for b in self.breaks],
            "notes": list(self.notes),
        }


@dataclass
class CriticReport:
    ok: bool
    urls: list[UrlCritique]
    fixtures: list[dict[str, Any]] = field(default_factory=list)
    source: str = "catalog"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source": self.source,
            "url_count": len(self.urls),
            "break_count": sum(len(u.breaks) for u in self.urls),
            "urls": [u.to_dict() for u in self.urls],
            "fixtures": list(self.fixtures),
        }


def load_corpus(path: Path | None = None) -> dict[str, Any]:
    target = path or CORPUS_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def _name_key(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _find_product(products: list[ProductView], want: str) -> ProductView | None:
    key = _name_key(want)
    exact = next((p for p in products if _name_key(p.name) == key), None)
    if exact:
        return exact
    return next((p for p in products if key and key in _name_key(p.name)), None)


def capabilities_for_product(
    name: str,
    display_class: str | None,
    description: str | None = None,
) -> list[str]:
    """Ground capabilities from this product's class + copy. No live fetch."""
    from app.services.robot_capability_derive import derive_capabilities

    cls = (display_class or "").strip().lower() or None
    facts: list[dict[str, Any]] = []
    if cls:
        facts.append(
            {
                "predicate": "product_class",
                "value": cls,
                "epistemic": "explicit",
                "evidence_span": description or name,
            }
        )
    profile = {
        "company": {"name": ""},
        "selected_product": {"name": name},
        "submitted_url": "",
        "facts": facts,
    }
    caps = derive_capabilities(profile)
    return sorted(k for k, cap in caps.items() if getattr(cap, "present", False))


def snapshot_from_listing(
    url: str,
    listing: dict[str, Any] | None = None,
) -> UrlCritique:
    """Catalog/listing path FIND already uses for indexed OEM hubs."""
    from app.services.jobs_oem_listing import listing_payload_for_url
    from app.services.oem_sku_discover import is_site_chrome_name

    payload = listing if isinstance(listing, dict) else listing_payload_for_url(url)
    robots = [
        r
        for r in (payload.get("robots") or [])
        if isinstance(r, dict) and str(r.get("name") or "").strip()
    ]
    products: list[ProductView] = []
    for row in robots:
        name = str(row.get("name") or "").strip()
        cls = (row.get("display_class") or None) or None
        desc = (row.get("description") or None) or None
        products.append(
            ProductView(
                name=name,
                display_class=cls,
                description=desc,
                capabilities_present=capabilities_for_product(name, cls, desc),
            )
        )
    range_classes = list(payload.get("product_range") or [])
    mixed = bool(payload.get("mixed_range"))
    matched = bool(payload.get("matched"))
    needs_picker = (not products) or (
        not any(p.display_class and p.display_class not in GENERIC_COMPANY_CLASSES for p in products)
        and not matched
    )
    critique = UrlCritique(
        url=url,
        vendor_name=(payload.get("vendor_name") or None),
        matched=matched,
        products=products,
        product_range=range_classes,
        mixed_range=mixed,
        needs_class_choice=needs_picker and not products,
    )
    for product in products:
        if is_site_chrome_name(product.name) or _name_key(product.name) in CHROME_NAMES:
            critique.breaks.append(
                Break(BREAK_CHROME, f"chrome name {product.name!r} is not a SKU", product.name)
            )
    return critique


def overlay_live_search(
    critique: UrlCritique,
    search: dict[str, Any],
    status: int,
) -> UrlCritique:
    """Annotate a catalog critique with Fly FIND. Junk SKUs on production are notes, not breaks."""
    from app.services.oem_sku_discover import is_junk_sku_name, is_site_chrome_name

    if status in {0, 502, 503, 504}:
        critique.notes.append(f"live FIND skipped/transient HTTP {status}")
        return critique
    if status != 200:
        critique.notes.append(f"live FIND HTTP {status}")
        return critique
    profile = search.get("profile") if isinstance(search.get("profile"), dict) else {}
    products = search.get("products") or profile.get("products") or []
    names = [
        str(p.get("name") or "").strip()
        for p in products
        if isinstance(p, dict) and str(p.get("name") or "").strip()
    ]
    if names:
        critique.notes.append(f"live FIND products={names[:8]}")
    state = search.get("state")
    if state:
        critique.notes.append(f"live FIND state={state}")
    evidence = [
        n
        for n in names
        if not is_junk_sku_name(n)
        and not is_site_chrome_name(n)
        and _name_key(n) not in CHROME_NAMES
    ]
    junk = [n for n in names if n not in evidence]
    if junk:
        critique.notes.append(f"live FIND junk SKUs ignored={junk[:8]}")
    picker = bool(search.get("needs_class_choice")) or state in {
        "qualify_robot",
        "select_class",
    }
    if picker and evidence:
        critique.breaks.append(
            Break(BREAK_EMPTY, "live FIND showed class picker while products were named")
        )
    return critique


def snapshot_from_rows(

    url: str,
    *,
    vendor_name: str | None,
    rows: list[dict[str, Any]],
) -> UrlCritique:
    """Fixture path: named products with classes/copy, no network."""
    from app.services.jobs_oem_listing import product_range_classes
    from app.services.oem_sku_discover import is_site_chrome_name
    from app.services.robot_class_qualify import classify_product_from_evidence

    products: list[ProductView] = []
    listing_rows: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        evidence = " ".join(
            x for x in (name, row.get("description") or "", row.get("evidence") or "") if x
        )
        catalog_class = (row.get("catalog_class") or row.get("display_class") or None)
        display = classify_product_from_evidence(evidence, catalog_class, name=name)
        if row.get("force_class"):
            display = str(row["force_class"])
        listing_rows.append({"name": name, "display_class": display})
        products.append(
            ProductView(
                name=name,
                display_class=display,
                description=(row.get("description") or None),
                capabilities_present=capabilities_for_product(
                    name, display, row.get("description")
                ),
            )
        )
    range_classes = product_range_classes(listing_rows)
    critique = UrlCritique(
        url=url,
        vendor_name=vendor_name,
        matched=bool(products),
        products=products,
        product_range=range_classes,
        mixed_range=len(range_classes) > 1,
        needs_class_choice=not products,
    )
    for product in products:
        if is_site_chrome_name(product.name) or _name_key(product.name) in CHROME_NAMES:
            critique.breaks.append(
                Break(BREAK_CHROME, f"chrome name {product.name!r} is not a SKU", product.name)
            )
    return critique


def apply_heuristic_breaks(critique: UrlCritique) -> UrlCritique:
    """Breaks that do not need a corpus row — flatten, chrome, drone-as-scrubber."""
    classes = {p.display_class for p in critique.products if p.display_class}
    named = [p for p in critique.products]
    if named and classes and classes <= GENERIC_COMPANY_CLASSES:
        critique.breaks.append(
            Break(
                BREAK_MIXED_FLAT,
                f"every SKU dumped to {sorted(classes)!r} — company class, not product class",
            )
        )
    if len(named) >= 2 and len(classes) == 1 and (classes & GENERIC_COMPANY_CLASSES):
        critique.breaks.append(
            Break(
                BREAK_COMPANY_CLASS,
                f"{len(named)} products share company class {next(iter(classes))!r}",
            )
        )
    for product in named:
        cls = (product.display_class or "").lower()
        blob = f"{product.name} {product.description or ''}".lower()
        aerial = any(
            token in blob
            for token in ("drone", "uav", "facade", "window wash", "exterior")
        )
        if aerial and cls in SCRUB_CLASSES:
            critique.breaks.append(
                Break(
                    BREAK_DRONE_SCRUB,
                    f"{product.name} looks like a cleaning drone but class={cls}",
                    product.name,
                )
            )
        if cls in DRONE_CLEAN_CLASSES and "hard_floor_scrub" in product.capabilities_present:
            critique.breaks.append(
                Break(
                    BREAK_CAP_DEFAULT,
                    f"{product.name} is {cls} but grounded hard_floor_scrub (OEM default)",
                    product.name,
                )
            )
        low = product.name.lower().strip()
        if low in CLASS_DUMP_NAMES:
            critique.breaks.append(
                Break(BREAK_INVENTED, f"{product.name!r} is a category/class dump, not a SKU", product.name)
            )
    return critique


def apply_corpus_breaks(critique: UrlCritique, spec: dict[str, Any]) -> UrlCritique:
    """Operator expectations for one URL."""
    products = critique.products
    by_name = {p.name: p for p in products}
    from app.services.oem_sku_discover import is_junk_sku_name, looks_like_named_sku

    named = [
        p
        for p in products
        if p.name
        and not is_junk_sku_name(p.name)
        and looks_like_named_sku(p.name)
        and p.name.lower().strip() not in CLASS_DUMP_NAMES
    ]

    if spec.get("expects_named_robots") and not spec.get("allow_empty"):
        if not named:
            kind = BREAK_EMPTY_OEM if not products else BREAK_MISSING
            critique.breaks.append(
                Break(
                    kind,
                    "robot OEM hub has 0 named robotic products "
                    "(empty catalog is a break, not an honest pass)",
                )
            )

    for forbidden in spec.get("forbid_products") or []:
        hit = next(
            (p for p in products if _name_key(p.name) == _name_key(forbidden)),
            None,
        )
        if hit:
            critique.breaks.append(
                Break(BREAK_INVENTED, f"forbidden SKU {forbidden!r} present", hit.name)
            )

    expect_products = list(spec.get("expect_products") or [])
    if expect_products and not products and not spec.get("allow_empty"):
        critique.breaks.append(
            Break(
                BREAK_MISSING,
                f"expected named products {expect_products} but listing is empty",
            )
        )
    if expect_products and not products and spec.get("allow_empty"):
        critique.notes.append("empty listing allowed (no invented SKUs)")
    for want in expect_products:
        if not _find_product(products, want):
            if spec.get("allow_empty") and not products:
                continue
            critique.breaks.append(
                Break(BREAK_MISSING, f"expected product {want!r} missing", want)
            )

    expect_classes = set(spec.get("expect_classes") or [])
    if expect_classes and products:
        have = set(critique.product_range)
        missing = expect_classes - have
        if missing:
            if spec.get("expect_mixed") or len(expect_classes) > 1:
                critique.breaks.append(
                    Break(
                        BREAK_MIXED_FLAT,
                        f"hub missing classes {sorted(missing)}; have {sorted(have)}",
                    )
                )
            else:
                critique.breaks.append(
                    Break(
                        BREAK_COMPANY_CLASS,
                        f"hub missing classes {sorted(missing)}; have {sorted(have)}",
                    )
                )

    if spec.get("expect_mixed") and products and not critique.mixed_range:
        critique.breaks.append(
            Break(
                BREAK_MIXED_FLAT,
                f"mixed OEM flattened to range={critique.product_range!r}",
            )
        )

    for left, right in spec.get("distinct_class_pairs") or []:
        a = _find_product(products, left)
        b = _find_product(products, right)
        if a and b and a.display_class and b.display_class and a.display_class == b.display_class:
            critique.breaks.append(
                Break(
                    BREAK_COMPANY_CLASS,
                    f"{a.name} and {b.name} share class {a.display_class!r}",
                    a.name,
                )
            )

    forbid_classes = set(spec.get("forbid_classes") or [])
    if forbid_classes:
        for product in products:
            if (product.display_class or "") in forbid_classes:
                kind = (
                    BREAK_DRONE_SCRUB
                    if product.display_class in SCRUB_CLASSES
                    else BREAK_COMPANY_CLASS
                )
                critique.breaks.append(
                    Break(
                        kind,
                        f"{product.name} class {product.display_class!r} is forbidden on this hub",
                        product.name,
                    )
                )

    for name, forbidden in (spec.get("forbid_classes_on") or {}).items():
        hit = _find_product(products, name)
        if hit and (hit.display_class or "") in set(forbidden):
            critique.breaks.append(
                Break(
                    BREAK_COMPANY_CLASS,
                    f"{hit.name} class {hit.display_class!r} forbidden",
                    hit.name,
                )
            )

    for name, forbidden in (spec.get("forbid_capabilities_on") or {}).items():
        hit = _find_product(products, name)
        if not hit:
            continue
        bad = set(forbidden) & set(hit.capabilities_present)
        if bad:
            critique.breaks.append(
                Break(
                    BREAK_CAP_DEFAULT,
                    f"{hit.name} grounded {sorted(bad)} from OEM default, not this product",
                    hit.name,
                )
            )

    for name, required in (spec.get("require_capabilities_on") or {}).items():
        hit = _find_product(products, name)
        if not hit:
            continue
        missing = [c for c in required if c not in hit.capabilities_present]
        if missing:
            critique.breaks.append(
                Break(
                    BREAK_CAP_DEFAULT,
                    f"{hit.name} missing per-product capabilities {missing}",
                    hit.name,
                )
            )

    needle = (spec.get("product_name_must_match") or "").lower()
    if needle:
        for product in products:
            if needle not in product.name.lower():
                critique.breaks.append(
                    Break(
                        BREAK_INVENTED,
                        f"{product.name!r} is not a robotic {needle} SKU",
                        product.name,
                    )
                )

    for sub in spec.get("forbid_name_substrings") or []:
        low = sub.lower()
        for product in products:
            if low in product.name.lower():
                critique.breaks.append(
                    Break(BREAK_INVENTED, f"{product.name!r} matches forbidden {sub!r}", product.name)
                )

    if spec.get("forbid_chrome"):
        for product in products:
            if _name_key(product.name) in CHROME_NAMES:
                critique.breaks.append(
                    Break(BREAK_CHROME, f"chrome {product.name!r}", product.name)
                )

    _ = by_name
    return critique


def critique_url(url: str, spec: dict[str, Any] | None = None) -> UrlCritique:
    critique = snapshot_from_listing(url)
    apply_heuristic_breaks(critique)
    if spec:
        apply_corpus_breaks(critique, spec)
    return critique


def critique_corpus(
    *,
    corpus: dict[str, Any] | None = None,
    corpus_path: Path | None = None,
) -> CriticReport:
    data = corpus if corpus is not None else load_corpus(corpus_path)
    rows = list(data.get("urls") or [])
    critiques: list[UrlCritique] = []
    for spec in rows:
        url = str(spec.get("url") or "").strip()
        if not url:
            continue
        critiques.append(critique_url(url, spec))
    ok = all(c.ok for c in critiques)
    return CriticReport(ok=ok, urls=critiques, source="catalog")


# ── Fixture suite (CI / pstack; no live OEM HTTP) ───────────────────────────

def _fixture_mixed_range_flattened() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/mixed-flat",
        vendor_name="Mixed OEM",
        rows=[
            {
                "name": "BellaBot",
                "description": "Tray delivery restaurant waiter. Table service.",
                "force_class": "service_robot",
            },
            {
                "name": "CC1",
                "description": "Vacuuming, scrubbing, mopping. Commercial floors.",
                "force_class": "service_robot",
            },
            {
                "name": "D9",
                "description": "Bipedal humanoid robot. Walking on two legs.",
                "force_class": "service_robot",
            },
        ],
    )


def _fixture_chrome_as_sku() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/chrome",
        vendor_name="Unknown OEM",
        rows=[
            {"name": "About", "description": "About the company nav.", "force_class": None},
            {"name": "Products", "description": "Products nav item.", "force_class": None},
            {"name": "News", "description": "News and press.", "force_class": None},
        ],
    )


def _fixture_cleaning_drone_as_scrubber() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/lucid-scrub",
        vendor_name="Lucid Bots",
        rows=[
            {
                "name": "Sherpa Drone",
                "description": (
                    "Cleaning drone for windows, facades and exteriors. "
                    "Window washing drone. Not a floor scrubber."
                ),
                "force_class": "cleaning",
            }
        ],
    )


def _fixture_company_class_not_product() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/company-class",
        vendor_name="Pudu",
        rows=[
            {
                "name": "BellaBot",
                "description": "Tray delivery restaurant waiter. Dining room.",
                "force_class": "serving",
            },
            {
                "name": "CC1",
                "description": "Tray delivery restaurant waiter. Dining room.",
                "force_class": "serving",
            },
        ],
    )


def _fixture_healthy_mixed() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/healthy-mixed",
        vendor_name="Pudu",
        rows=[
            {
                "name": "BellaBot",
                "description": "Tray delivery restaurant waiter. Table service. Restaurants.",
            },
            {
                "name": "CC1",
                "description": "Vacuuming, scrubbing, mopping. Commercial floors. Floor scrubber.",
            },
            {
                "name": "D9",
                "description": "Bipedal humanoid robot. Walking on two legs. Object manipulation.",
            },
        ],
    )


def _fixture_healthy_drone() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/healthy-drone",
        vendor_name="Lucid Bots",
        rows=[
            {
                "name": "Sherpa Drone",
                "description": (
                    "Sherpa Drone commercial cleaning drone for windows and facades. "
                    "Window washing drone. Exterior building washing."
                ),
            }
        ],
    )


def _fixture_empty_robot_oem() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/empty-oem",
        vendor_name="Tennant",
        rows=[],
    )


def _fixture_class_dump_sku() -> UrlCritique:
    return snapshot_from_rows(
        "https://fixture.example/class-dump",
        vendor_name="SEER Robotics",
        rows=[
            {
                "name": "Seer Humanoid",
                "description": "Humanoid robot from the company homepage.",
                "force_class": "humanoid",
            }
        ],
    )


def run_fixture_suite() -> dict[str, Any]:
    """pstack / CI: prove the critic detects each break class, and healthy rows pass."""
    cases: list[tuple[str, UrlCritique, set[str], bool]] = [
        (BREAK_MIXED_FLAT, _fixture_mixed_range_flattened(), {BREAK_MIXED_FLAT, BREAK_COMPANY_CLASS}, False),
        (BREAK_CHROME, _fixture_chrome_as_sku(), {BREAK_CHROME}, False),
        (BREAK_DRONE_SCRUB, _fixture_cleaning_drone_as_scrubber(), {BREAK_DRONE_SCRUB}, False),
        (BREAK_COMPANY_CLASS, _fixture_company_class_not_product(), {BREAK_COMPANY_CLASS}, False),
        (BREAK_EMPTY_OEM, _fixture_empty_robot_oem(), {BREAK_EMPTY_OEM}, False),
        (BREAK_INVENTED, _fixture_class_dump_sku(), {BREAK_INVENTED}, False),
        ("healthy_mixed", _fixture_healthy_mixed(), set(), True),
        ("healthy_drone", _fixture_healthy_drone(), set(), True),
    ]
    results: list[dict[str, Any]] = []
    ok = True
    for case_id, raw, expect_kinds, expect_ok in cases:
        critique = apply_heuristic_breaks(raw)
        if case_id == BREAK_COMPANY_CLASS:
            apply_corpus_breaks(
                critique,
                {"distinct_class_pairs": [["BellaBot", "CC1"]]},
            )
        if case_id == BREAK_EMPTY_OEM:
            apply_corpus_breaks(critique, {"expects_named_robots": True})
        kinds = {b.kind for b in critique.breaks}
        case_ok = critique.ok is expect_ok and (expect_kinds <= kinds if expect_kinds else not kinds)
        if case_id == "healthy_drone":
            sherpa = _find_product(critique.products, "Sherpa Drone")
            cls_ok = bool(sherpa and sherpa.display_class == "cleaning_drone")
            cap_ok = bool(sherpa and "hard_floor_scrub" not in sherpa.capabilities_present)
            case_ok = case_ok and cls_ok and cap_ok
        if not case_ok:
            ok = False
        results.append(
            {
                "id": case_id,
                "ok": case_ok,
                "expect_ok": expect_ok,
                "got_ok": critique.ok,
                "expect_kinds": sorted(expect_kinds),
                "got_kinds": sorted(kinds),
                "breaks": [b.to_dict() for b in critique.breaks],
                "products": [p.to_dict() for p in critique.products],
                "product_range": list(critique.product_range),
            }
        )
    return {"ok": ok, "prove": "url workflow critic fixture suite", "cases": results}


def format_report(report: CriticReport | dict[str, Any], *, width: int = 88) -> str:
    data = report.to_dict() if isinstance(report, CriticReport) else report
    lines = [
        "URL workflow critic",
        f"source={data.get('source')} ok={data.get('ok')} "
        f"urls={data.get('url_count')} breaks={data.get('break_count')}",
        "",
    ]
    for row in data.get("urls") or []:
        flag = "PASS" if row.get("ok") else "BREAK"
        names = ", ".join(
            f"{p.get('name')}={p.get('display_class')}" for p in (row.get("products") or [])[:8]
        )
        lines.append(f"[{flag}] {row.get('url')}")
        lines.append(f"  range={row.get('product_range')} mixed={row.get('mixed_range')} {names}")
        for br in row.get("breaks") or []:
            extra = f" ({br.get('product')})" if br.get("product") else ""
            lines.append(f"  - {br.get('kind')}{extra}: {br.get('detail')}")
        lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    return text if len(text) < 20000 else text[:20000] + "\n…truncated\n"
