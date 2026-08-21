"""Phase 2 — typed source pack (deliberate, ranked — not a generic crawl)."""
from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from app.services.robot_understanding_v1.fetch import (
    DEFAULT_PAGE_TIMEOUT,
    DEFAULT_TEXT_TIMEOUT,
    FetchedPage,
    fetch_page,
    fetch_text,
    timeout_for_deadline,
)
from app.services.robot_understanding_v1.models import RobotSource, SourceType

# Sitemap discovery is a bounded fallback for thin/JS homepages whose product
# pages are still server-rendered and listed in sitemap.xml. All caps are hard.
_SITEMAP_MAX_CHILD_MAPS = 3
_SITEMAP_MAX_LOCS = 400
_SITEMAP_MAX_CANDIDATES = 20
_THIN_HOMEPAGE_LINKS = 6  # homepages with fewer same-domain links look like SPA shells
_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
# Product-ish sitemap paths worth adding as candidates
_SITEMAP_PRODUCT_PATH = re.compile(
    r"/(product|products|robot|robots|platform|hardware|solution|solutions|"
    r"use[-_]?case|application|spec|specs|specification|datasheet)",
    re.I,
)

# (path substring or keyword, source_type, base confidence)
_TYPE_RULES: list[tuple[re.Pattern[str], SourceType, float]] = [
    (
        re.compile(
            r"(\.pdf(?:$|\?|\s|/|#))|/(spec|specs|specification|datasheet|data-sheet|tech[-_]?sheet|"
            r"technical[-_]?data|product[-_]?sheet|spec[-_]?sheet)",
            re.I,
        ),
        "specifications",
        0.95,
    ),
    (
        re.compile(
            r"\b(datasheet|data\s*sheet|tech\s*sheet|spec\s*sheet|specifications?|"
            r"technical\s+(?:data|specs?|sheet)|download\s+(?:pdf|datasheet|specs?))\b",
            re.I,
        ),
        "specifications",
        0.94,
    ),
    (re.compile(r"/(manual|support|docs?|documentation|download|technical)", re.I), "documentation", 0.88),
    (re.compile(r"/(case[-_]?stud|customer[-_]?stor|deployment|success[-_]?stor)", re.I), "case_study", 0.88),
    (re.compile(r"/(press|newsroom|news/|latest-press)", re.I), "press_release", 0.45),
    (re.compile(r"/(solution|solutions|use[-_]?case|application|industr)", re.I), "solutions", 0.85),
    (re.compile(r"/(product|products|robot|robots|platform|hardware)", re.I), "product", 0.9),
    (re.compile(r"/(faq|glossary|resource)", re.I), "documentation", 0.75),
]

_SPEC_ANCHOR = re.compile(
    r"\b(datasheet|data\s*sheet|spec(?:ification)?s?|tech(?:nical)?\s*(?:sheet|data|specs?)|"
    r"download\s*(?:pdf|specs?)|product\s*sheet|\.pdf)\b",
    re.I,
)

# Paths that must not enter the primary research pack
_REJECT_PATH = re.compile(
    r"/(careers?|jobs?|privacy|terms|cookie|cookies|login|signin|sign-up|signup|"
    r"investors?|sales|cart|checkout|legal|trust-center|dsar|terms-of-service|"
    r"contact(?:-us)?|leadership|team|board|about(?:-us)?|company/?$|"
    r"newsletter|subscribe|"
    # Indexes (not articles): bare blog/news hubs
    r"blog/?$|blogs/?$|news/?$|press/?$|resources/?$)"
    r"(/|$|\?)",
    re.I,
)

# Accessory / sibling / marketplace paths — demote unless subject is explicitly supported
_ACCESSORY_PATH = re.compile(
    r"/(arm|arms|extras?|accessories|add-?ons?|payloads?|top-modules?|"
    r"marketplace|enabled-robotics|mir-go|go/enabled|"
    r"fleet/?$|software/?$)(/|$)",
    re.I,
)

_REJECT_TITLE = re.compile(
    r"\b(404|page\s+not\s+found|not\s+found|error\s+\d{3}|access\s+denied|"
    r"privacy\s+policy|cookie\s+(policy|settings)|terms\s+of\s+(use|service))\b",
    re.I,
)

_REJECT_BODY = re.compile(
    r"(no\s+robot\s+can\s+help\s+you\s+here|this\s+page\s+may\s+have\s+moved|"
    r"page\s+not\s+found|404\s+not\s+found)",
    re.I,
)

# Prefer these hubs when discovering from homepage links
_HUB_BONUS = {
    "specifications": 35,
    "product": 30,
    "solutions": 24,
    "case_study": 22,
    "documentation": 18,
    "support": 12,
    "press_release": 2,
    "homepage": 8,
    "other": 0,
}

# Allowed into pack only when pack would otherwise be empty (identity fallback)
_IDENTITY_ONLY_TYPES = frozenset({"homepage"})

_MAX_FETCH_WORKERS = 6
_PREFETCH_CAP = 12


def _fetch_workers() -> int:
    raw = (os.getenv("ROBOT_PROFILE_FETCH_WORKERS") or str(_MAX_FETCH_WORKERS)).strip()
    try:
        n = int(raw)
    except ValueError:
        n = _MAX_FETCH_WORKERS
    return max(1, min(8, n))


@dataclass
class CollectedSource:
    source: RobotSource
    page: FetchedPage


def collected_from_page(
    page: FetchedPage,
    *,
    product_id: str | None = None,
) -> Optional[CollectedSource]:
    """Wrap an already-fetched page as a typed source — no extra HTTP."""
    if page is None or not (page.text or "").strip():
        return None
    if getattr(page, "fetch_degraded", False) and len((page.text or "").strip()) < 40:
        return None
    stype, conf = classify_source_type(page.final_url, title=page.title or "")
    if stype == "other":
        stype, conf = "homepage", 0.55
    src = RobotSource.create(
        page.final_url,
        stype,
        publisher_role="manufacturer",
        title=page.title,
        confidence=conf,
        product_id=product_id,
        text_excerpt=(page.text or "")[:400],
    )
    return CollectedSource(source=src, page=page)


def classify_source_type(url: str, anchor: str = "", title: str = "") -> tuple[SourceType, float]:
    blob = f"{url} {anchor} {title}"
    for pattern, stype, conf in _TYPE_RULES:
        if pattern.search(blob):
            return stype, conf
    path = urlparse(url).path or "/"
    if path in {"", "/"}:
        return "homepage", 0.55
    return "other", 0.35


def should_reject_url(url: str) -> bool:
    path = urlparse(url).path or "/"
    return bool(_REJECT_PATH.search(path))


def is_unusable_page(page: FetchedPage) -> bool:
    """404s, error shells, legal/cookie pages, empty chrome."""
    if page.status_code >= 400:
        return True
    title = page.title or ""
    if _REJECT_TITLE.search(title):
        return True
    text = page.text or ""
    if len(text) < 160:
        return True
    head = text[:500]
    if _REJECT_BODY.search(head):
        return True
    cookie_hits = len(re.findall(r"\bcookie\b", text[:1200], re.I))
    if cookie_hits >= 6 and len(text) < 900:
        return True
    return False


def subject_tokens(product_name: str) -> set[str]:
    """Normalized tokens used to detect subject support on a page."""
    raw = (product_name or "").strip().lower()
    if not raw:
        return set()
    alnum = re.sub(r"[^a-z0-9]+", "", raw)
    dashed = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    spaced = re.sub(r"[^a-z0-9]+", " ", raw).strip()
    out = {raw, alnum, dashed, spaced}
    # Split trailing model digits: "mir250" / "ur10e" already in alnum
    m = re.match(r"^([a-z]+?)(\d.*)$", alnum)
    if m and len(m.group(1)) >= 2:
        out.add(f"{m.group(1)} {m.group(2)}")
        out.add(f"{m.group(1)}-{m.group(2)}")
    return {t for t in out if len(t) >= 2}


def page_supports_subject(
    *,
    url: str,
    title: str = "",
    text: str = "",
    product_name: str | None,
) -> bool:
    """True if URL/title/body explicitly mention the selected product."""
    if not product_name:
        return True
    blob = f"{url} {title} {text[:2500]}".lower()
    return any(tok and tok in blob for tok in subject_tokens(product_name))


def is_accessory_or_marketplace(url: str) -> bool:
    path = urlparse(url).path or "/"
    return bool(_ACCESSORY_PATH.search(path))


def discover_from_sitemap(
    origin: str, *, product_name: str | None = None, deadline_monotonic: float | None = None
) -> list[tuple[str, str]]:
    """Best-effort product URLs from sitemap.xml — bounded and fail-open.

    Reads /sitemap.xml (and up to a few child sitemaps if it is an index), keeps
    same-origin product-ish URLs, and prefers ones that name the subject. Returns
    (url, anchor) pairs (anchor always ""). Any error → []. Never raises.
    """
    try:
        host = (urlparse(origin).hostname or "").lower()
        if not host:
            return []
        locs: list[str] = []
        for sm in ("/sitemap.xml", "/sitemap_index.xml"):
            if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
                break
            text_timeout = timeout_for_deadline(
                deadline_monotonic, default=DEFAULT_TEXT_TIMEOUT
            )
            if text_timeout is None:
                break
            status, body = fetch_text(origin + sm, timeout=text_timeout)
            if status and body:
                locs.extend(_LOC_RE.findall(body))
            if locs:
                break
        if not locs:
            return []

        # Expand a sitemap index (entries are themselves .xml sitemaps).
        child_maps = [u for u in locs if u.lower().rstrip("/").endswith(".xml")][:_SITEMAP_MAX_CHILD_MAPS]
        page_locs = [u for u in locs if not u.lower().rstrip("/").endswith(".xml")]
        for cm in child_maps:
            if len(page_locs) >= _SITEMAP_MAX_LOCS:
                break
            if deadline_monotonic is not None and time.monotonic() >= deadline_monotonic:
                break
            text_timeout = timeout_for_deadline(
                deadline_monotonic, default=DEFAULT_TEXT_TIMEOUT
            )
            if text_timeout is None:
                break
            status, body = fetch_text(cm, timeout=text_timeout)
            if status and body:
                page_locs.extend(u for u in _LOC_RE.findall(body) if not u.lower().rstrip("/").endswith(".xml"))

        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        subject_first: list[tuple[str, str]] = []
        for u in page_locs[:_SITEMAP_MAX_LOCS]:
            if (urlparse(u).hostname or "").lower() != host:
                continue
            if should_reject_url(u):
                continue
            if not _SITEMAP_PRODUCT_PATH.search(urlparse(u).path or ""):
                continue
            key = u.split("#")[0].rstrip("/").lower()
            if key in seen:
                continue
            seen.add(key)
            if product_name and page_supports_subject(url=u, product_name=product_name):
                subject_first.append((u, ""))
            else:
                out.append((u, ""))
        # Subject-supporting URLs first, then the rest, capped hard.
        return (subject_first + out)[:_SITEMAP_MAX_CANDIDATES]
    except Exception:
        return []


def collect_source_pack(
    home: FetchedPage,
    *,
    product_name: str | None = None,
    max_sources: int = 6,
    deadline_monotonic: float | None = None,
    allow_archive: bool = False,
) -> list[CollectedSource]:
    """
    Build a small typed pack: best same-domain evidence pages.

    When product_name is set, prefer pages that support that subject and demote
    sibling SKUs, accessories, and marketplaces.

    deadline_monotonic: stop fetching additional pages after this clock so the
    submit path can match on a grounded-enough pack instead of waiting for
    every candidate. Extractors are unchanged.

    allow_archive defaults False — guessed hubs (/adam, /products, sitemap)
    must not fan out to Wayback when the live OEM is challenged. That is how
    unknown and catalog-miss URLs used to take ~90s.
    """
    if getattr(home, "fetch_degraded", False) and not (home.text or "").strip():
        # Challenge / empty interstitial — do not fan out to /adam, sitemap, or
        # Wayback copies of every hub (that is how Richtech took ~90s).
        return []

    origin = f"{urlparse(home.final_url).scheme}://{urlparse(home.final_url).netloc}"
    candidates: list[tuple[float, str, SourceType, float, str]] = []
    slug = _product_slug(product_name) if product_name else None

    def _add(url: str, score: float, stype: SourceType, conf: float, hint: str) -> None:
        if should_reject_url(url):
            return
        # Subject-aware demotion of accessories / marketplaces
        if product_name and is_accessory_or_marketplace(url):
            # Keep only if the accessory URL still names the subject (rare)
            if not page_supports_subject(url=url, title=hint, product_name=product_name):
                return
            score -= 45
        if product_name:
            if page_supports_subject(url=url, title=hint, product_name=product_name):
                score += 55
            elif stype in {"product", "specifications"}:
                # Generic product hubs without subject — demote hard
                score -= 25
        candidates.append((score, url, stype, conf, hint))

    if not is_unusable_page(home) and not should_reject_url(home.final_url):
        home_type, home_conf = classify_source_type(home.final_url, title=home.title or "")
        if home_type == "other":
            home_type, home_conf = "homepage", 0.55
        _add(
            home.final_url,
            55.0 if home_type == "homepage" else 90.0,
            home_type,
            home_conf,
            home.title or "",
        )

    for url, anchor in home.links:
        if should_reject_url(url):
            continue
        stype, conf = classify_source_type(url, anchor)
        # Elevate PDF / datasheet anchors even when path is /download/...
        if _SPEC_ANCHOR.search(f"{url} {anchor}") or url.lower().endswith(".pdf"):
            stype, conf = "specifications", max(conf, 0.95)
        if stype in {"press_release", "other"} and not (
            product_name and page_supports_subject(url=url, title=anchor, product_name=product_name)
        ):
            if stype == "other" and not url.lower().endswith(".pdf"):
                continue
        score = float(_HUB_BONUS.get(stype, 0))
        if stype == "specifications":
            score += 40  # Prefer evidence pages where numeric facts live
        if product_name and page_supports_subject(url=url, title=anchor, product_name=product_name):
            score += 50
            if stype in {"other", "homepage", "press_release"}:
                stype, conf = "product", 0.9
        path = urlparse(url).path or ""
        score += min(8, path.count("/"))
        _add(url, score, stype, conf, anchor)

    # Thin/JS homepage fallback: if the homepage exposed few same-domain links
    # (a likely SPA shell), try sitemap.xml to discover server-rendered product
    # pages. Bounded + fail-open; adds candidates that flow through the same
    # subject/type gates below. Skipped when the homepage already links plenty.
    same_domain_links = len(home.links)
    _deadline_ok = deadline_monotonic is None or time.monotonic() < deadline_monotonic
    if same_domain_links < _THIN_HOMEPAGE_LINKS and _deadline_ok:
        for sm_url, sm_anchor in discover_from_sitemap(origin, product_name=product_name, deadline_monotonic=deadline_monotonic):
            if should_reject_url(sm_url):
                continue
            stype, conf = classify_source_type(sm_url, sm_anchor)
            if stype == "other" and not sm_url.lower().endswith(".pdf"):
                continue
            score = float(_HUB_BONUS.get(stype, 0))
            if stype == "specifications":
                score += 40
            if product_name and page_supports_subject(url=sm_url, product_name=product_name):
                score += 50
            _add(sm_url, score, stype, conf, sm_anchor)

    if slug:
        for path, stype, conf in (
            (f"/product/{slug}", "product", 0.92),
            (f"/products/{slug}", "product", 0.92),
            (f"/products/robots/{slug}", "product", 0.94),
            (f"/robots/{slug}", "product", 0.92),
            (f"/robots/meet-{slug}", "product", 0.92),
            (f"/robot/{slug}", "product", 0.92),
            (f"/platform/{slug}", "product", 0.9),
            (f"/{slug}", "product", 0.72),
            (f"/specs/{slug}", "specifications", 0.95),
            (f"/specifications/{slug}", "specifications", 0.95),
        ):
            _add(origin + path, _HUB_BONUS.get(stype, 0) + 55, stype, conf, path)

    for hub, stype, conf in (
        ("/solutions", "solutions", 0.85),
        ("/products", "product", 0.88),
        ("/product", "product", 0.85),
        ("/robots", "product", 0.88),
        ("/specs", "specifications", 0.95),
        ("/specifications", "specifications", 0.95),
        ("/datasheets", "specifications", 0.95),
        ("/datasheet", "specifications", 0.95),
        ("/downloads", "documentation", 0.82),
        ("/resources/datasheets", "specifications", 0.94),
        ("/industries", "solutions", 0.8),
        ("/use-cases", "solutions", 0.85),
        ("/case-studies", "case_study", 0.88),
        ("/documentation", "documentation", 0.88),
        ("/docs", "documentation", 0.85),
        ("/faq", "documentation", 0.7),
    ):
        # Generic hubs are weak when a subject is selected (except specs)
        if stype == "specifications":
            bonus = 18 if not product_name else 12
        else:
            bonus = 6 if not product_name else -5
        _add(origin + hub, _HUB_BONUS.get(stype, 0) + bonus, stype, conf, hub)

    candidates.sort(key=lambda t: (-t[0], t[1]))
    out: list[CollectedSource] = []
    seen: set[str] = set()

    def _norm(u: str) -> str:
        return u.rstrip("/").lower().split("?")[0]

    def _past_deadline() -> bool:
        return deadline_monotonic is not None and time.monotonic() >= deadline_monotonic

    def _try_fetch(url: str, stype: SourceType, conf: float, hint: str) -> Optional[CollectedSource]:
        if _past_deadline() and _norm(url) != _norm(home.final_url):
            return None
        timeout = timeout_for_deadline(deadline_monotonic, default=DEFAULT_PAGE_TIMEOUT)
        if timeout is None and _norm(url) != _norm(home.final_url):
            return None
        try:
            if _norm(url) == _norm(home.final_url):
                page = home
            else:
                page = fetch_page(
                    url,
                    timeout=timeout or DEFAULT_PAGE_TIMEOUT,
                    allow_archive=allow_archive,
                )
        except Exception:
            return None
        if getattr(page, "fetch_degraded", False) and not (page.text or "").strip():
            return None
        # PDFs / download endpoints may not look like HTML product pages
        is_pdf = (getattr(page, "content_type", "") or "").startswith("application/pdf") or (
            page.final_url or ""
        ).lower().endswith(".pdf")
        if not is_pdf and (is_unusable_page(page) or should_reject_url(page.final_url)):
            return None
        if is_pdf and len((page.text or "").strip()) < 40:
            return None
        # Subject gate after fetch: drop accessory/sibling pages that don't name the product
        if product_name:
            supports = page_supports_subject(
                url=page.final_url,
                title=page.title or "",
                text=page.text or "",
                product_name=product_name,
            )
            if is_accessory_or_marketplace(page.final_url) and not supports:
                return None
            if not supports and stype in {"product", "specifications", "solutions"}:
                # Allow thin homepage only as filler later
                if stype != "homepage":
                    return None
            if supports:
                conf = min(0.98, conf + 0.05)
            else:
                conf = min(conf, 0.45)
        stype2, conf2 = classify_source_type(page.final_url, hint, page.title or "")
        if stype2 != "other":
            stype, conf = stype2, max(conf, conf2)
        if stype == "press_release":
            conf = min(conf, 0.5)
        if stype == "homepage":
            conf = min(conf, 0.55)
        src = RobotSource.create(
            page.final_url,
            stype,
            publisher_role="manufacturer",
            title=page.title,
            confidence=conf,
            text_excerpt=page.text[:400],
        )
        return CollectedSource(source=src, page=page)

    def _run_wave(
        batch: list[tuple[str, SourceType, float, str]],
    ) -> dict[str, Optional[CollectedSource]]:
        found: dict[str, Optional[CollectedSource]] = {}
        if not batch:
            return found
        workers = min(_fetch_workers(), len(batch))
        if workers <= 1:
            for url, stype, conf, hint in batch:
                found[_norm(url)] = _try_fetch(url, stype, conf, hint)
            return found
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {
                pool.submit(_try_fetch, url, stype, conf, hint): url
                for url, stype, conf, hint in batch
            }
            wait_s = None
            if deadline_monotonic is not None:
                wait_s = max(0.05, deadline_monotonic - time.monotonic() + 0.15)
            try:
                for fut in as_completed(futs, timeout=wait_s):
                    url = futs[fut]
                    try:
                        found[_norm(url)] = fut.result()
                    except Exception:
                        found[_norm(url)] = None
            except TimeoutError:
                for fut, url in futs.items():
                    if _norm(url) not in found:
                        found[_norm(url)] = None
        return found

    def _take_batch(
        ranked: list[tuple[float, str, SourceType, float, str]],
        *,
        skip_identity: bool,
        limit: int,
    ) -> list[tuple[str, SourceType, float, str]]:
        batch: list[tuple[str, SourceType, float, str]] = []
        local = set(seen)
        for _score, url, stype, conf, hint in ranked:
            if skip_identity and stype in _IDENTITY_ONLY_TYPES:
                continue
            key = _norm(url)
            if key in local:
                continue
            local.add(key)
            batch.append((url, stype, conf, hint))
            if len(batch) >= limit:
                break
        return batch

    def _keep(url: str, item: Optional[CollectedSource]) -> None:
        if not item or len(out) >= max_sources:
            return
        key = _norm(url)
        final_key = _norm(item.page.final_url)
        if key in seen or final_key in seen:
            return
        seen.add(key)
        seen.add(final_key)
        out.append(item)

    prefetch_limit = min(_PREFETCH_CAP, max(max_sources * 2, 8))
    wave = _take_batch(candidates, skip_identity=True, limit=prefetch_limit)
    fetched = _run_wave(wave)
    for _score, url, stype, conf, hint in candidates:
        if _past_deadline() and out:
            break
        if len(out) >= max_sources:
            break
        key = _norm(url)
        if key in seen or stype in _IDENTITY_ONLY_TYPES:
            continue
        if key in fetched:
            item = fetched[key]
        elif not _past_deadline():
            item = _try_fetch(url, stype, conf, hint)
        else:
            item = None
        _keep(url, item)

    if len(out) < max_sources:
        product_pages = [c for c in out if c.source.source_type == "product"]
        if product_pages:
            # Prefer the subject-supporting product page as hop seed
            seed = product_pages[0]
            for c in product_pages:
                if page_supports_subject(
                    url=c.page.final_url,
                    title=c.page.title or "",
                    text=c.page.text or "",
                    product_name=product_name,
                ):
                    seed = c
                    break
            hop_cands: list[tuple[float, str, SourceType, float, str]] = []
            for url, anchor in seed.page.links:
                if should_reject_url(url) or _norm(url) in seen:
                    continue
                if product_name and is_accessory_or_marketplace(url):
                    if not page_supports_subject(url=url, title=anchor, product_name=product_name):
                        continue
                stype, conf = classify_source_type(url, anchor)
                if _SPEC_ANCHOR.search(f"{url} {anchor}") or url.lower().endswith(".pdf"):
                    stype, conf = "specifications", max(conf, 0.95)
                if stype not in {
                    "specifications",
                    "documentation",
                    "solutions",
                    "case_study",
                    "product",
                    "support",
                }:
                    continue
                score = float(_HUB_BONUS.get(stype, 0))
                if stype == "specifications":
                    score += 35
                if product_name and page_supports_subject(
                    url=url, title=anchor, product_name=product_name
                ):
                    score += 40
                hop_cands.append((score, url, stype, conf, anchor))
            hop_cands.sort(key=lambda t: (-t[0], t[1]))
            hop_wave = _take_batch(hop_cands, skip_identity=True, limit=prefetch_limit)
            hop_fetched = _run_wave(hop_wave)
            for _score, url, stype, conf, hint in hop_cands:
                if len(out) >= max_sources or _past_deadline():
                    break
                key = _norm(url)
                if key in seen:
                    continue
                _keep(url, hop_fetched.get(key))

    if len(out) < 2:
        for _score, url, stype, conf, hint in candidates:
            if stype not in _IDENTITY_ONLY_TYPES and stype != "homepage":
                continue
            key = _norm(url)
            if key in seen:
                continue
            item = _try_fetch(url, stype, conf, hint)
            if not item:
                continue
            final_key = _norm(item.page.final_url)
            if final_key in seen:
                continue
            seen.add(key)
            seen.add(final_key)
            out.append(item)
            if len(out) >= max(2, min(3, max_sources)):
                break

    type_rank = {
        "specifications": 0,
        "product": 1,
        "documentation": 2,
        "solutions": 3,
        "case_study": 4,
        "support": 5,
        "press_release": 6,
        "homepage": 7,
        "other": 8,
    }
    out.sort(key=lambda c: (type_rank.get(c.source.source_type, 9), -c.source.confidence))
    strong = [
        c
        for c in out
        if c.source.source_type
        in {"specifications", "product", "documentation", "solutions", "case_study", "support"}
    ]
    if len(strong) >= 2:
        out = [
            c
            for c in out
            if c.source.source_type not in {"press_release", "homepage"}
        ] or strong

    # Final subject preference: keep supporting pages first when product set
    if product_name and out:
        supporting = [
            c
            for c in out
            if page_supports_subject(
                url=c.page.final_url,
                title=c.page.title or "",
                text=c.page.text or "",
                product_name=product_name,
            )
        ]
        if supporting:
            rest = [c for c in out if c not in supporting]
            out = supporting + rest

    return out[:max_sources]


def _product_slug(name: str) -> str:
    raw = name.strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-") or raw
