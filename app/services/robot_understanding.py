"""
Robot understanding: URL is a starting identity signal, not the whole corpus.

Stages (v0):
  1. Exact page extract
  2. Same-domain research (nav / solutions / product / specs / robot pages)
  3. (Reserved) web research
  4. Multi-product select
  5. Capability chips — only after research fails

No OEM hostname allowlists. Evidence must come from fetched text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Tuple
from urllib.parse import urljoin, urlparse

from app.services.robot_capability_profile import (
    CapabilityProfile,
    build_capability_profile,
)
from app.services.robot_profile_extract import extract_robot_profile, fetch_product_page
from app.services.robot_url_safety import UrlSafetyError, assert_public_http_url

Fetcher = Callable[[str], Tuple[str, Optional[str]]]

# Paths that often hold capability evidence (generic; not OEM-specific)
_RESEARCH_PATH_TOKENS = (
    "/product",
    "/products",
    "/robot",
    "/robots",
    "/solution",
    "/solutions",
    "/hardware",
    "/platform",
    "/specs",
    "/spec",
    "/datasheet",
    "/use-case",
    "/usecase",
    "/applications",
    "/application",
    "/industries",
    "/industry",
    "/capabilities",
    "/technology",
    "/warehouse",
    "/manufactur",
    "/logistics",
    "/deploy",
    "/digit",  # common product slug pattern — also covered by /solution*
    "/vega",
)

# Soft-exclude pure news/PR unless product tokens also appear
_SKIP_PATH_TOKENS = (
    "/careers",
    "/privacy",
    "/terms",
    "/cookie",
    "/login",
    "/cart",
    "/checkout",
)

_PRODUCT_NAME_HINTS = re.compile(
    r"\b("
    r"Digit|Spot|Stretch|Atlas|Origin|Neo|Vega|G1|H1|B2|Go2|Walker|Figure\s*\d+"
    r"|Apollo|Optimus|Ameca|Phoenix|Cassie"
    r")\b",
    re.I,
)

_HUMANOID_HINT = re.compile(r"\b(humanoid|bipedal|biped)\b", re.I)
_PLATFORM_NOT_ROBOT = re.compile(
    r"\b(cloud\s+platform|software\s+platform|fleet\s+management|WES|WMS)\b",
    re.I,
)


@dataclass
class ResearchStage:
    id: str
    label: str
    status: str  # pending | active | done | skipped
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass
class ProductCandidate:
    name: str
    robot_class: str | None = None
    evidence_url: str | None = None
    confidence: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "robot_class": self.robot_class,
            "evidence_url": self.evidence_url,
            "confidence": self.confidence,
        }


@dataclass
class UnderstandingResult:
    company_name: str | None
    products: list[ProductCandidate] = field(default_factory=list)
    selected_product: ProductCandidate | None = None
    profile: CapabilityProfile | None = None
    stages: list[ResearchStage] = field(default_factory=list)
    evidence_urls: list[str] = field(default_factory=list)
    evidence_text: str = ""
    needs_product_choice: bool = False
    source_url: str | None = None
    content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "products": [p.to_dict() for p in self.products],
            "selected_product": self.selected_product.to_dict() if self.selected_product else None,
            "profile": self.profile.to_dict() if self.profile else None,
            "research_stages": [s.to_dict() for s in self.stages],
            "evidence_urls": self.evidence_urls,
            "needs_product_choice": self.needs_product_choice,
            "source_url": self.source_url,
            "content_hash": self.content_hash,
        }


def discover_research_urls(html: str, base_url: str, *, limit: int = 8) -> list[str]:
    """Same-host links likely to hold robot / solutions / specs evidence."""
    host = (urlparse(base_url).hostname or "").lower()
    if not host or not html:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for href in re.findall(r"""href=["']([^"']+)["']""", html, flags=re.I):
        if href.startswith("#") or href.lower().startswith(("mailto:", "tel:", "javascript:")):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if (parsed.hostname or "").lower() != host:
            continue
        path = (parsed.path or "").lower()
        if any(tok in path for tok in _SKIP_PATH_TOKENS):
            continue
        # Skip long press/PR URLs unless they clearly name a robot workflow
        if "/content/" in path and len(path) > 50:
            if not any(tok in path for tok in ("digit", "tote", "deploy", "humanoid", "vega", "spot")):
                continue
        path_ok = any(tok in path for tok in _RESEARCH_PATH_TOKENS)
        name_ok = bool(_PRODUCT_NAME_HINTS.search(path)) or bool(
            _PRODUCT_NAME_HINTS.search(href)
        )
        content_robot = "/content/" in path and (
            "digit" in path
            or "tote" in path
            or "humanoid" in path
            or "vega" in path
        )
        if not (path_ok or name_ok or content_robot):
            continue
        key = full.split("#")[0].rstrip("/")
        if not key or key in seen:
            continue
        if key.rstrip("/") == base_url.rstrip("/"):
            continue
        seen.add(key)
        out.append(key)
        if len(out) >= limit * 2:
            break

    def rank(u: str) -> tuple[int, int, int, int]:
        path = (urlparse(u).path or "").lower()
        # Prefer specific product/solution pages over bare hubs and long press releases
        specific = 0 if re.search(r"/(product|solutions?|robots?)/[^/]+", path) else 1
        hub = 0 if path.rstrip("/").endswith(("/solutions", "/products", "/robots", "/industries")) else 1
        press = 2 if "/content/" in path else 0
        return (press, specific, hub, -min(len(path), 80))

    out.sort(key=rank)
    return out[:limit]


def _company_from_host(url: str | None, page_title: str | None, text: str) -> str | None:
    host = (urlparse(url or "").hostname or "").lower().removeprefix("www.")
    if not host:
        if page_title:
            parts = re.split(r"\s+[|\-—]\s+", page_title)
            if len(parts) > 1:
                return parts[-1].strip()[:80] or None
        return None

    slug = host.split(".")[0]
    if not slug or slug in {"www", "shop", "store", "product", "products"}:
        return None

    blob = f"{page_title or ''}\n{text or ''}"

    # Title right-hand brand: "… | Agility" (prefer over noisy body matches)
    if page_title and "|" in page_title:
        right = page_title.split("|")[-1].strip()
        if right and len(right) <= 40 and " " not in right:
            if re.search(rf"\b{re.escape(right)}\s+Robotics\b", blob, re.I):
                return f"{right} Robotics"
            if right.lower() in slug.replace("-", ""):
                if slug.endswith("robotics"):
                    return f"{right} Robotics"
                return right

    # Host slug → Agility Robotics
    if slug.endswith("robotics") and len(slug) > len("robotics"):
        stem = slug[: -len("robotics")]
        return f"{stem.replace('-', ' ').title()} Robotics"
    return slug.replace("-", " ").title()


def _detect_products(text: str, urls: list[str], html: str | None = None) -> list[ProductCandidate]:
    found: dict[str, ProductCandidate] = {}

    def add(name: str, *, url: str | None, robot_class: str | None, conf: float) -> None:
        key = name.strip()
        if not key or len(key) < 2:
            return
        # Skip platform-only names when context screams software
        window = ""
        if text:
            idx = text.lower().find(key.lower())
            if idx >= 0:
                window = text[max(0, idx - 80) : idx + len(key) + 120]
        if _PLATFORM_NOT_ROBOT.search(window) and not _HUMANOID_HINT.search(window):
            if key.lower() in {"arc", "fleet", "cloud"}:
                return
        existing = found.get(key.lower())
        if existing and existing.confidence >= conf:
            return
        found[key.lower()] = ProductCandidate(
            name=key if not key.isupper() or len(key) <= 4 else key.title(),
            robot_class=robot_class,
            evidence_url=url,
            confidence=conf,
        )

    # From URL paths
    for u in urls:
        path = urlparse(u).path or ""
        for m in _PRODUCT_NAME_HINTS.finditer(path):
            add(m.group(1), url=u, robot_class=_class_near(text, m.group(1)), conf=0.75)
        # /solutions/digit or /product/vega
        m2 = re.search(r"/(?:products?|solutions?|robots?)/([a-z0-9][\w-]{1,40})", path, re.I)
        if m2:
            slug = m2.group(1).replace("-", " ").strip()
            if slug.lower() not in {"digit", "spec", "sheet", "overview", "index"}:
                # still accept digit as product
                pass
            pretty = slug.title() if slug.lower() != "digit" else "Digit"
            if slug.lower() in {"digit", "vega", "origin", "neo", "spot", "stretch"} or len(slug) <= 12:
                if slug.lower() not in {"spec", "sheet", "overview", "index", "all"}:
                    add(
                        "Digit" if slug.lower() == "digit" else pretty,
                        url=u,
                        robot_class=_class_near(text, pretty),
                        conf=0.8,
                    )

    # From body text product mentions near robot language
    blob = text or ""
    for m in _PRODUCT_NAME_HINTS.finditer(blob):
        name = m.group(1)
        window = blob[max(0, m.start() - 60) : m.end() + 100]
        if re.search(r"\b(robot|humanoid|amr|quadruped|cobot|manipulator|deploy)\b", window, re.I):
            add(name, url=None, robot_class=_class_near(blob, name), conf=0.7)

    # Explicit "Digit is a … humanoid"
    for m in re.finditer(
        r"\b([A-Z][A-Za-z0-9]{1,20})\s+is\s+a\s+(?:commercially\s+deployed\s+)?(humanoid|amr|quadruped|mobile\s+manipulator|robot)",
        blob,
    ):
        add(m.group(1), url=None, robot_class=m.group(2).lower().replace(" ", "_"), conf=0.9)

    # HTML alt/title cues
    if html:
        for m in re.finditer(
            r"(?:alt|title|aria-label)=[\"']([^\"']{2,60})[\"']",
            html,
            flags=re.I,
        ):
            label = m.group(1).strip()
            pm = _PRODUCT_NAME_HINTS.search(label)
            if pm and re.search(r"robot|humanoid|profile", label, re.I):
                add(pm.group(1), url=None, robot_class=_class_near(label, pm.group(1)), conf=0.65)

    ranked = sorted(found.values(), key=lambda p: (-p.confidence, p.name))
    return ranked[:8]


def _class_near(text: str, name: str) -> str | None:
    if not text or not name:
        return None
    idx = text.lower().find(name.lower())
    window = text[max(0, idx - 80) : idx + len(name) + 120] if idx >= 0 else text[:200]
    if _HUMANOID_HINT.search(window):
        return "humanoid"
    if re.search(r"\bquadruped|spot\b", window, re.I):
        return "quadruped"
    if re.search(r"\bamr\b|autonomous\s+mobile", window, re.I):
        return "amr"
    if re.search(r"\bcobot|collaborative\s+arm", window, re.I):
        return "cobot"
    if re.search(r"\bmobile\s+manip", window, re.I):
        return "mobile_manipulator"
    return None


def _merge_profile_texts(*parts: str) -> str:
    seen: set[str] = set()
    chunks: list[str] = []
    for part in parts:
        p = (part or "").strip()
        if not p:
            continue
        # Dedupe exact chunks
        key = p[:200]
        if key in seen:
            continue
        seen.add(key)
        chunks.append(p)
    # Cap aggregate so regex stays fast
    return "\n\n".join(chunks)[:24000]


def understand_robot_url(
    url: str,
    *,
    fetcher: Fetcher | None = None,
    html: str | None = None,
    description: str | None = None,
    product_name: str | None = None,
    chip: str | None = None,
    max_follow: int = 5,
) -> UnderstandingResult:
    """
    Identify company/product and build a capability profile via same-domain research.
    """
    stages = [
        ResearchStage("identify_company", "Identifying company", "pending"),
        ResearchStage("find_robots", "Finding robots", "pending"),
        ResearchStage("research_capabilities", "Understanding capabilities", "pending"),
        ResearchStage("match_jobs", "Searching jobs", "pending"),
    ]

    result = UnderstandingResult(company_name=None, stages=stages)

    if chip and not url and not html and not description:
        result.profile = build_capability_profile(text="", chip=chip, robot_name="your robot")
        stages[0].status = "skipped"
        stages[1].status = "skipped"
        stages[2].status = "done"
        stages[2].detail = "Visitor capability prior"
        return result

    source_url: str | None = None
    page_html = html
    fetched_at = None
    seed_text = description or ""

    if page_html is None and description is None and url:
        safe = assert_public_http_url(url)
        source_url = safe
        page = fetch_product_page(safe, timeout=12.0, fetcher=fetcher)
        page_html = page["html"]
        source_url = page.get("url") or safe
        fetched_at = page.get("fetched_at")
    elif url:
        try:
            source_url = assert_public_http_url(url)
        except UrlSafetyError:
            source_url = url

    result.source_url = source_url

    extraction = extract_robot_profile(
        html=page_html,
        description=description,
        source_url=source_url,
        fetched_at=fetched_at,
    )
    seed_text = _merge_profile_texts(extraction.text_sample, description or "", source_url or "")
    evidence_urls = [source_url] if source_url else []
    evidence_html_bits = [page_html or ""]

    company = _company_from_host(source_url, extraction.page_title, seed_text)
    stages[0].status = "done"
    stages[0].detail = company or extraction.page_title or "Unknown"
    result.company_name = company

    # Level 1 profile from seed page
    profile = build_capability_profile(
        text=seed_text,
        page_title=extraction.page_title,
        manufacturer=extraction.manufacturer,
        model=extraction.model,
        chip=chip,
        robot_class=extraction.category,
    )
    products = _detect_products(seed_text, evidence_urls, page_html)
    stages[1].status = "active"

    # Level 2 — same-domain research when Level 1 is thin OR landing is a site root
    path_only = (urlparse(source_url or "").path or "/").rstrip("/") or "/"
    is_site_root = path_only in {"/", ""}
    thin_evidence = profile.evidence_count < 3
    need_research = (
        (not profile.understood)
        or thin_evidence
        or is_site_root
        or (page_html and not products)
    )
    follow_urls: list[str] = []
    if page_html and source_url and description is None and html is None:
        discovered = discover_research_urls(page_html, source_url, limit=max_follow + 3)
        hubs: list[str] = []
        if need_research and source_url:
            parsed = urlparse(source_url)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            for hub in ("/solutions", "/products", "/robots", "/product", "/industries"):
                hubs.append(origin + hub)
        # Product/detail links first; hubs fill gaps (never starve discovered URLs)
        follow_urls = list(discovered) + hubs
        deduped: list[str] = []
        seen_u: set[str] = set()
        for u in follow_urls:
            key = u.rstrip("/")
            if key in seen_u:
                continue
            seen_u.add(key)
            deduped.append(u)
        follow_urls = deduped

    researched_texts = [seed_text]
    if need_research:
        for follow in follow_urls[:max_follow]:
            try:
                page2 = fetch_product_page(follow, timeout=10.0, fetcher=fetcher)
            except Exception:
                continue
            html2 = page2.get("html") or ""
            if not html2:
                continue
            ext2 = extract_robot_profile(
                html=html2,
                source_url=page2.get("url") or follow,
                fetched_at=page2.get("fetched_at"),
            )
            t2 = ext2.text_sample or ""
            if len(t2) < 80:
                continue
            researched_texts.append(t2)
            evidence_urls.append(page2.get("url") or follow)
            evidence_html_bits.append(html2)
            agg = _merge_profile_texts(*researched_texts)
            trial = build_capability_profile(
                text=agg,
                page_title=ext2.page_title or extraction.page_title,
                manufacturer=company or extraction.manufacturer,
                model=extraction.model,
                chip=chip,
                robot_class=ext2.category or extraction.category,
            )
            # Keep going until we have rich confirmed evidence (not just class priors)
            if trial.understood and trial.evidence_count >= 4:
                profile = trial
                extraction = ext2
                break
            elif trial.evidence_count > profile.evidence_count:
                profile = trial
                extraction = ext2

    agg_text = _merge_profile_texts(*researched_texts)
    result.evidence_text = agg_text
    result.evidence_urls = evidence_urls
    result.content_hash = extraction.content_hash

    # Re-detect products on full evidence
    products = _detect_products(agg_text, evidence_urls, "\n".join(x for x in evidence_html_bits if x)[:200000])
    # Filter obvious non-robots (Arc cloud) when Digit/humanoid present
    if any(p.name.lower() == "digit" for p in products):
        products = [p for p in products if p.name.lower() not in {"arc"}]

    result.products = products

    # Product selection
    selected: ProductCandidate | None = None
    if product_name:
        for p in products:
            if p.name.lower() == product_name.lower():
                selected = p
                break
        if not selected:
            selected = ProductCandidate(name=product_name, confidence=0.5)
    elif len(products) == 1:
        selected = products[0]
    elif len(products) > 1:
        # Prefer humanoid / highest confidence; if clearly one primary, auto-pick
        humanoids = [p for p in products if (p.robot_class or "") == "humanoid"]
        if len(humanoids) == 1 and humanoids[0].confidence >= 0.7:
            selected = humanoids[0]
        elif products[0].confidence >= 0.85 and (
            len(products) == 1 or products[0].confidence - products[1].confidence >= 0.15
        ):
            selected = products[0]
        else:
            result.needs_product_choice = True
            stages[1].status = "done"
            stages[1].detail = ", ".join(p.name for p in products[:4])
            stages[2].status = "pending"
            stages[2].detail = "Select a robot"
            result.selected_product = None
            result.profile = profile
            return result
    else:
        # Infer name from model / title / company robot language
        if extraction.model and extraction.model.lower() not in (company or "").lower():
            selected = ProductCandidate(
                name=extraction.model.split("|")[0].strip()[:80],
                robot_class=extraction.category,
                confidence=0.45,
            )

    stages[1].status = "done"
    stages[1].detail = (
        selected.name
        if selected
        else (", ".join(p.name for p in products[:3]) if products else "No product named yet")
    )
    result.selected_product = selected

    robot_name = (
        (selected.name if selected else None)
        or extraction.model
        or (f"{company}" if company else None)
        or extraction.page_title
        or "your robot"
    )
    if company and selected and selected.name.lower() not in company.lower():
        # Prefer short product name for board: "Digit" not "Agility Digit"
        robot_name = selected.name

    robot_class = (selected.robot_class if selected else None) or extraction.category

    profile = build_capability_profile(
        text=agg_text,
        robot_name=str(robot_name)[:120],
        page_title=extraction.page_title,
        manufacturer=company or extraction.manufacturer,
        model=selected.name if selected else extraction.model,
        chip=chip,
        robot_class=robot_class,
    )
    result.profile = profile
    stages[2].status = "done" if profile.understood else "done"
    stages[2].detail = (
        f"{len(profile.capabilities)} signals"
        if profile.capabilities
        else "Insufficient evidence"
    )
    stages[3].status = "pending"
    return result
