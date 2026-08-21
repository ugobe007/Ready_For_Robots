"""Phase 1 — resolve company + product identity from URL evidence."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from app.services.robot_understanding_v1.fetch import FetchedPage
from app.services.robot_understanding_v1.models import RobotCompany, RobotProduct
from app.services.robot_url_safety import registrable_domain
from app.services.vendor_robot_lookup import (
    index_robot_for_name,
    index_robot_names,
    lookup_vendor_by_url,
    select_index_robot,
)

# Product-like proper nouns commonly used as robot SKUs (not OEM allowlists —
# used only to *spot* names already present in page text / anchors).
_PRODUCT_CANDIDATE = re.compile(
    r"\b("
    r"Digit|Vega|Origin|Neo|Spot|Stretch|Atlas|Apollo|Ameca|Optimus|"
    r"Walker|Figure\s*\d+|G1|H1|B2|Go2|Cassie|Handle|Ranger|OTTO\s*\d+|"
    r"GoFa|Phoenix|Pepper|Whiz|TIAGo|ANYmal|Canvas|FieldPrinter|"
    r"Elios\s*\d*|Servi(?:\s*Plus|\+)?|P800|CRX[- ]?\d+\w*|"
    r"Lift\s+RS\d+|T7AMR|A0509"
    r")\b",
    re.I,
)

# Manufacturer product pages (EngineAI /product-pm01.html, /products/t800).
# Path evidence — not an OEM SKU allowlist.
_PRODUCT_HREF = re.compile(
    r"(?:^|/)products?[-_/]([a-z0-9][a-z0-9-]{0,24})(?:\.html?)?$",
    re.I,
)
_PRODUCT_HREF_NOISE = frozenset(
    {
        "purchase",
        "catalog",
        "list",
        "index",
        "home",
        "support",
        "service",
        "center",
        "overview",
        "all",
        "line",
        "lines",
        "family",
        "series",
        "detail",
        "details",
        "info",
        "page",
        "about",
        "news",
        "contact",
        "applications",
        "opensource",
        "policy",
        "parts",
        "app",
        "en",
        "zh",
        "contactinformation",
        "login",
        "privacy",
        "terms",
        "careers",
        "jobs",
        "blog",
        "press",
        "media",
        "investors",
        "company",
        "technology",
        "solutions",
        "resources",
        "rental",
        "rentals",
        "shop",
        "cart",
        "store",
        "pricing",
        "demo",
        "events",
        "partners",
        "team",
        "legal",
        "cookies",
        "search",
        "subscribe",
        "newsletter",
        "faq",
        "industrial",
        "commercial",
        "data",
        "privacy-policy",
        "terms-and-conditions",
        "robot-rentals",
        "get-in-touch",
        "learn-more",
        "more",
        "contact-us",
        "get-started",
        "case-studies",
        "customer-success",
        "company-history",
        "service-plan",
        "eula",
        "ethics",
        "consulting",
        "advertising",
        "industry",
        "models",
        "platform",
        "warehouse",
        "compact",
        "handling",
        "orbit",
        "history",
        "bipedal",
        "humanoid",
        "semi-humanoid",
        "scrubber-dryer",
        "lidar",
    }
)
# Locale product pages (MagicLab /en/x1, /en/human, /en/app/g1).
_LOCALE_PRODUCT_HREF = re.compile(
    r"(?:^|/)(?:en|zh)(?:/app)?/([a-z0-9][a-z0-9-]{0,24})$",
    re.I,
)
_ROBOTS_HREF = re.compile(
    r"(?:^|/)(?:robots?|hardware|models?|platform)/([a-z0-9][a-z0-9-]{0,24})(?:\.html?)?$",
    re.I,
)
_ROOT_PRODUCT_HREF = re.compile(r"^/([a-z0-9][a-z0-9-]{1,40})$", re.I)
_ROBOT_LINE_SLUGS = frozenset({"human", "dog", "panda"})
_MAX_DISCOVERED_PRODUCTS = 10
_COMPACT_SKU = re.compile(r"^[A-Za-z]{1,3}\d{1,3}[A-Za-z]{0,3}$")
_PROSE_NAME = re.compile(
    r"\b((?:[A-Z]{3,10})|(?:[A-Z][a-z]{2,14}(?:-[A-Z0-9][A-Za-z0-9]{0,10}){0,3}))\b"
)
_NAME_FOLLOW = re.compile(
    r"^\s*(?:the\s+)?(?:AI[- ]powered\s+)?(?:dual[- ]arm\s+|single[- ]arm\s+)?"
    r"(?:"
    r"robot|humanoid|cobot|serves?|shows?|delivers?|works\b|helps?|"
    r"makes?|mixes?|cleans?|navigates?|skyrockets?|automates?|"
    r"bartender|barista|waiter|server|scrubber|vacuum|"
    r"is\s+an?\s+(?:AI[- ]powered\s+)?(?:humanoid|service|delivery|cleaning)"
    r")\b",
    re.I,
)
_PROSE_NAME_NOISE = frozenset(
    {
        "the",
        "and",
        "for",
        "our",
        "you",
        "this",
        "with",
        "from",
        "that",
        "ceo",
        "cto",
        "usa",
        "llc",
        "inc",
        "nasdaq",
        "gpu",
        "cpu",
        "api",
        "faq",
        "nvidia",
        "amd",
        "ibm",
        "aws",
        "microsoft",
        "google",
        "amazon",
        "meta",
        "apple",
        "walmart",
        "mercedes",
        "benz",
        "forbes",
        "columbia",
        "solutions",
        "technology",
        "company",
        "investors",
        "resources",
        "contact",
        "privacy",
        "terms",
        "news",
        "learn",
        "watch",
        "video",
        "robotics",
        "robot",
        "robots",
        "recent",
        "bringing",
        "bridging",
        "current",
    }
)

# Nav / CTA / accessory labels that must never appear in the Jobs SKU picker.
_NAV_PRODUCT_LABELS = frozenset(
    {
        "learn more",
        "contact us",
        "get started",
        "get in touch",
        "see all robots",
        "case studies",
        "customer success",
        "company history",
        "service plan",
        "eula",
        "ethics",
        "consulting",
        "advertising",
        "industry",
        "models",
        "platform",
        "warehouse",
        "compact",
        "handling",
        "bipedal",
        "semi-humanoid",
        "semi humanoid",
        "scrubber-dryer",
        "scrubber dryer",
        "orbit",
        "solutions",
        "company",
        "contact",
        "news",
        "about",
        "purchase",
        "product purchase",
    }
)
_ACCESSORY_PRODUCT_NAME = re.compile(
    r"\b(4d\s*lidar|lidar|sdk|datasheet|whitepaper)\b",
    re.I,
)
_CTA_PRODUCT_NAME = re.compile(
    r"^(learn|see|get|contact|read|watch|explore|download)\s+\w+",
    re.I,
)

_PLATFORM_NOISE = re.compile(
    r"\b(cloud\s+platform|fleet\s+management|software\s+platform|WES|WMS)\b",
    re.I,
)

# Infrastructure / document-host labels that must never become company.name
_INFRA_COMPANY = re.compile(
    r"^(library|download|downloads|search|docs?|documentation|cdn|static|"
    r"assets?|media|files?|support|portal|login|sso|api|www)$",
    re.I,
)

# SEO / marketing titles mistaken for brand names
_SEO_TITLE_NOISE = re.compile(
    r"\b(solutions?\s+for|warehouse\s*&\s*logistics|logistics\s+automation|"
    r"industrial\s+automation|robotics\s+solutions|for\s+warehouse|"
    r"download\s+center|document\s+library|technical\s+library|"
    r"product\s+catalog|home\s+page)\b",
    re.I,
)

_ACQUIRER_SIGNAL = re.compile(
    r"\b(acquired\s+by|now\s+part\s+of|"
    r"a\s+(?:brand|division)\s+of|"
    r"brought\s+to\s+you\s+by|distributed\s+by|"
    r"formerly\s+(?:known\s+as|independent)|"
    r"join(?:ed|s)?\s+the\s+\w+\s+family)\b",
    re.I,
)

# Explicit manufacturer / brand attribution (not product SKU promotion).
_BY_BRAND = re.compile(
    r"\bby\s+([A-Z][A-Za-z0-9][A-Za-z0-9 .,&'\-]{0,40}?"
    r"(?:Robotics|Automation|Inc\.?|Ltd\.?|LLC|GmbH|Corp\.?|AI|Motors|"
    r"Corporation|Systems|Industries))\b",
)
_MANUFACTURER_OF = re.compile(
    r"\b(?:manufactured|made|built|developed)\s+by\s+"
    r"([A-Z][A-Za-z0-9][A-Za-z0-9 .,&'\-]{1,48})",
    re.I,
)

# Prose that names a short brand as a company/manufacturer (not merely a product).
_SELF_AS_COMPANY = re.compile(
    r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+)?)"
    r",\s+the\s+(?:world['']?s\s+)?(?:first\s+)?"
    r"[^.]{0,120}?\b(?:company|manufacturer)\b",
)

_COPYRIGHT = re.compile(
    r"(?:©|\(c\)|copyright)\s*(?:20\d{2}\s*[–\-,]?\s*)?(?:20\d{2}\s+)?"
    r"([A-Z][A-Za-z0-9][A-Za-z0-9 .,&'\-]{1,60})",
    re.I,
)

# Sources that independently evidence an organization / brand (not product path).
_ORG_EVIDENCE_SOURCES = frozenset(
    {
        "jsonld",
        "og:site_name",
        "copyright",
        "domain",
        "by_brand",
        "acquirer_brand",
        "self_as_company",
    }
)

_DOC_HOST_PREFIX = re.compile(
    r"^(library|download|downloads|search|docs?|documentation|cdn|static|"
    r"assets?|media|files?|support|portal|help|kb)\.",
    re.I,
)


@dataclass
class ResolveResult:
    company: RobotCompany
    products: list[RobotProduct]
    selected_product: Optional[RobotProduct]
    notes: list[str]


def resolve_identity(
    submitted_url: str,
    home: FetchedPage,
    *,
    product_hint: str | None = None,
) -> ResolveResult:
    """
    Two independent decisions: canonical company, then selected product.

    Never promote a product/model string into company.name merely because it
    appears strongly in title or URL path.
    """
    domain = _root_domain(home.final_url or submitted_url)
    catalog = lookup_vendor_by_url(submitted_url) or lookup_vendor_by_url(home.final_url)
    catalog_names = index_robot_names(catalog) if catalog else []
    # Discover product candidates first so the company step can enforce the
    # negative invariant (product string ≠ company unless org evidence).
    discovered = _discover_product_names(home, product_hint=product_hint)
    product_names = _merge_catalog_names(catalog_names, discovered)
    catalog_only = bool(catalog_names)
    blocked_products = list(product_names)
    if product_hint and product_hint.strip():
        blocked_products.append(product_hint.strip())

    name, company_notes = _company_name(
        home,
        domain,
        product_hint=product_hint,
        blocked_product_names=blocked_products,
    )
    aliases = [domain]
    hosted_notes = [n for n in company_notes if n.startswith("Hosted by:")]
    if hosted_notes:
        # Optional acquirer host note — do not replace company brand.
        host_brand = hosted_notes[0].split(":", 1)[-1].strip()
        if host_brand and host_brand.lower() not in {a.lower() for a in aliases}:
            aliases.append(host_brand)
    company = RobotCompany.create(name=name, primary_domain=domain, aliases=aliases)
    notes_prefix: list[str] = []
    if catalog and catalog.get("vendor_name"):
        catalog_brand = str(catalog["vendor_name"]).strip()
        if catalog_brand:
            name = catalog_brand
            company = RobotCompany.create(name=name, primary_domain=domain, aliases=aliases)
            notes_prefix.append(
                f"Vendor index matched {catalog_brand} "
                f"({len(catalog_names)} robot(s) from vendor robot index)."
            )
            if catalog_only:
                notes_prefix.append(
                    "Picker lists vendor index SKUs only — homepage nav and accessories omitted."
                )

    products: list[RobotProduct] = []
    for pname in product_names:
        display_class = _hint_display_class(pname, home.text)
        indexed = index_robot_for_name(catalog, pname) if catalog else None
        if indexed and indexed.get("primary_class"):
            display_class = str(indexed["primary_class"])
        products.append(
            RobotProduct.create(company.id, pname, display_class=display_class)
        )

    notes: list[str] = list(notes_prefix) + list(company_notes)
    if not product_hint and catalog:
        indexed = select_index_robot(submitted_url, catalog)
        if indexed and indexed.get("name"):
            product_hint = str(indexed["name"])
    selected: Optional[RobotProduct] = None
    if len(products) == 1:
        selected = products[0]
    elif len(products) > 1:
        notes.append(
            f"Multiple products found ({', '.join(p.name for p in products)}); "
            "selected none — caller may choose. Defaulting to first for profile build."
        )
        selected = products[0]
    else:
        notes.append(
            "No named product resolved from homepage evidence; "
            "facts will be attributed to company-level subject."
        )

    # Prefer product_hint as selected when present (identity only — does not
    # rewrite company).
    if product_hint and product_hint.strip():
        hint = product_hint.strip()
        match = next(
            (
                p
                for p in products
                if _name_key(p.name) == _name_key(hint)
                or _name_key(hint) in _name_key(p.name)
                or _name_key(p.name) in _name_key(hint)
            ),
            None,
        )
        selected = match or (
            RobotProduct.create(
                company.id,
                hint,
                display_class=_hint_display_class(hint, home.text),
            )
        )
        if selected.id not in {p.id for p in products}:
            products.insert(0, selected)

    # Final negative invariant: selected product string ineligible as company
    # unless separate org evidence already confirmed it as the brand.
    if selected and _names_collide(company.name, selected.name):
        if not _org_evidence_confirms_name(
            home, domain, company.name, product_hint=product_hint
        ):
            fallback = _registrable_brand(domain) or domain.split(".")[0].replace(
                "-", " "
            ).title()
            if fallback and not _names_collide(fallback, selected.name):
                notes.append(
                    f"Rejected product string `{company.name}` as company.name "
                    f"(no independent organization-brand evidence); using `{fallback}`."
                )
                company = RobotCompany.create(
                    name=fallback[:120],
                    primary_domain=domain,
                    aliases=aliases,
                )
                for p in products:
                    p.company_id = company.id

    return ResolveResult(
        company=company,
        products=products,
        selected_product=selected,
        notes=notes,
    )


def _is_noise_product_name(name: str) -> bool:
    """True for nav CTAs, legal links, class words, and accessories (not a robot SKU)."""
    raw = re.sub(r"\s+", " ", (name or "").strip())
    if not raw:
        return True
    low = raw.lower()
    if low in _NAV_PRODUCT_LABELS or low in _PRODUCT_HREF_NOISE or low in _PROSE_NAME_NOISE:
        return True
    if _name_key(raw) in {_name_key(x) for x in _NAV_PRODUCT_LABELS}:
        return True
    if _ACCESSORY_PRODUCT_NAME.search(raw):
        return True
    if _CTA_PRODUCT_NAME.match(raw):
        return True
    return False


def _merge_catalog_names(catalog_names: list[str], discovered: list[str]) -> list[str]:
    """Indexed SKUs only when the vendor is in the index.

    Homepage crawl may still name robots for unknown OEMs. Nav labels, legal
    links, and accessories never enter the picker.
    """
    out: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        key = _name_key(name)
        if not key or key in seen:
            return
        seen.add(key)
        out.append(name)

    if catalog_names:
        for name in catalog_names:
            _add(name)
        return out
    for name in discovered:
        if _is_noise_product_name(name):
            continue
        _add(name)
    return out


def _root_domain(url: str) -> str:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    if not host:
        return "unknown"
    return registrable_domain(host)


def _registrable_brand(domain: str) -> str:
    """
    Brand stem from host, skipping document-library / CDN prefixes.

    library.e.abb.com → abb; search.abb.com → abb; geekplus.com → geekplus
    """
    host = (domain or "").lower().removeprefix("www.")
    if not host or host == "unknown":
        return ""
    labels = [p for p in host.split(".") if p]
    # Drop leading infra labels
    while labels and _DOC_HOST_PREFIX.match(labels[0] + "."):
        labels = labels[1:]
    # Drop single-letter regional tags (e.g. e.abb.com)
    while len(labels) >= 3 and len(labels[0]) <= 2:
        labels = labels[1:]
    if not labels:
        return ""
    stem = labels[0]
    if _INFRA_COMPANY.match(stem):
        if len(labels) >= 2:
            stem = labels[1] if labels[0] != labels[1] else labels[0]
        else:
            return ""
    if stem.endswith("robotics") and len(stem) > len("robotics"):
        return f"{stem[: -len('robotics')].replace('-', ' ').title()} Robotics"
    # geekplus → Geekplus; softbankrobotics handled above
    return stem.replace("-", " ").title()


def _looks_like_brand(name: str) -> bool:
    n = (name or "").strip()
    if len(n) < 2 or len(n) > 48:
        return False
    if _INFRA_COMPANY.match(n):
        return False
    if _SEO_TITLE_NOISE.search(n):
        return False
    if n.count(" ") >= 5:
        return False
    # Reject sentence-like titles
    if re.search(r"\b(for|with|and|&|the|solutions?|automation)\b", n, re.I) and len(n) > 28:
        return False
    return True


def _clean_org_name(raw: str) -> str | None:
    n = re.sub(r"\s+", " ", (raw or "").strip())
    n = re.sub(r"\s*[\|\-–—:].*$", "", n).strip()  # drop trailing taglines
    if not _looks_like_brand(n):
        return None
    return n[:120]


def _copyright_brand(html: str, text: str) -> str | None:
    blob = f"{html or ''}\n{text or ''}"
    for m in _COPYRIGHT.finditer(blob[:8000]):
        cand = m.group(1).strip().rstrip(".,;")
        # Stop at common legal suffixes noise
        cand = re.split(r"\s+(?:All\s+Rights|Inc\.?|Ltd\.?|LLC|GmbH|Corp\.?)\b", cand, maxsplit=1)[0]
        cleaned = _clean_org_name(cand)
        if cleaned:
            return cleaned
    return None


def _jsonld_org_names(html: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html or "",
        re.I | re.S,
    ):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        nodes = data if isinstance(data, list) else [data]
        stack = list(nodes)
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
                continue
            if not isinstance(node, dict):
                continue
            if "@graph" in node and isinstance(node["@graph"], list):
                stack.extend(node["@graph"])
            t = node.get("@type")
            types = [t] if isinstance(t, str) else list(t or [])
            if any(
                str(x).lower() in {"organization", "corporation", "localbusiness", "brand"}
                for x in types
            ):
                n = node.get("name")
                if isinstance(n, str):
                    cleaned = _clean_org_name(n)
                    if cleaned:
                        out.append(cleaned)
    return out


def _name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _names_collide(a: str, b: str) -> bool:
    ka, kb = _name_key(a), _name_key(b)
    if not ka or not kb:
        return False
    return ka == kb or (len(ka) >= 3 and (ka in kb or kb in ka))


def _looks_like_model_or_sku(name: str) -> bool:
    """
    Product/model strings are ineligible as company.name without separate
    organization-brand evidence. Digits / compact codes → SKU.
    """
    n = (name or "").strip()
    if not n:
        return True
    if re.search(r"\d", n):
        return True
    if re.fullmatch(r"[A-Za-z]{1,4}\d+[A-Za-z0-9\-]*", n):
        return True
    # Multi-token product marketing names ending in Pro/Plus/Max often SKUs
    if re.search(r"\b(pro|plus|max|lite|mini|series)\b", n, re.I) and " " in n:
        return True
    return False


def _manufacturer_attribution_brands(text: str, title: str) -> list[str]:
    out: list[str] = []
    blob = f"{title or ''}\n{(text or '')[:4000]}"
    for rx in (_MANUFACTURER_OF, _BY_BRAND):
        for m in rx.finditer(blob):
            cleaned = _clean_org_name(m.group(1))
            if cleaned and not _looks_like_model_or_sku(cleaned):
                out.append(cleaned)
    return out


def _self_as_company_brands(text: str, product_hint: str | None = None) -> list[str]:
    """Strings the page explicitly calls a company/manufacturer."""
    out: list[str] = []
    blob = (text or "")[:5000]
    hint = (product_hint or "").strip()
    if hint and not _looks_like_model_or_sku(hint):
        # Prefer an exact hint match: "Canvas, the ... company"
        rx = re.compile(
            rf"\b{re.escape(hint)}\s*,\s+the\s+(?:world['']?s\s+)?(?:first\s+)?"
            rf"[^.]{{0,120}}?\b(?:company|manufacturer)\b",
            re.I,
        )
        if rx.search(blob):
            out.append(hint)
            return out
    for m in _SELF_AS_COMPANY.finditer(blob):
        cleaned = _clean_org_name(m.group(1))
        if cleaned and not _looks_like_model_or_sku(cleaned):
            if hint and not _names_collide(cleaned, hint):
                continue
            out.append(cleaned)
    return out


def _org_evidence_confirms_name(
    home: FetchedPage,
    domain: str,
    name: str,
    *,
    product_hint: str | None = None,
) -> bool:
    """True when independent org/brand evidence names `name` (not path alone)."""
    key = _name_key(name)
    if not key:
        return False
    html = home.html or ""
    text = home.text or ""
    brand_from_domain = _registrable_brand(domain)
    evidenced: list[str] = []
    evidenced.extend(_jsonld_org_names(html))
    og = re.search(
        r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.I,
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\']',
        html,
        re.I,
    )
    if og:
        cleaned = _clean_org_name(og.group(1))
        if cleaned:
            evidenced.append(cleaned)
    copy = _copyright_brand(html, text)
    if copy:
        evidenced.append(copy)
    if brand_from_domain:
        evidenced.append(brand_from_domain)
    evidenced.extend(_manufacturer_attribution_brands(text, home.title or ""))
    evidenced.extend(_self_as_company_brands(text, product_hint=product_hint))
    # Acquirer-hosted brand: product hint may be the company brand when
    # page explicitly carries acquirer language and hint is not a model SKU.
    hint = (product_hint or "").strip()
    if (
        hint
        and _names_collide(hint, name)
        and not _looks_like_model_or_sku(hint)
        and _ACQUIRER_SIGNAL.search(text[:3000])
    ):
        evidenced.append(hint)
    return any(_names_collide(e, name) for e in evidenced)


def _company_name(
    home: FetchedPage,
    domain: str,
    *,
    product_hint: str | None = None,
    blocked_product_names: list[str] | None = None,
) -> tuple[str, list[str]]:
    """
    Canonical company binding — independent of product selection.

    Preference order:
      1. Explicit organization/brand from page metadata / schema
      2. Canonical manufacturer brand from domain
      3. Explicit "by <brand>" / manufacturer attribution
      4. Acquirer/brand relationship only when strongly evidenced

    A product path or product title must never override company unless the page
    explicitly evidences that string as the organization brand.
    """
    notes: list[str] = []
    html = home.html or ""
    text = home.text or ""
    brand_from_domain = _registrable_brand(domain)
    blocked = [b for b in (blocked_product_names or []) if b and b.strip()]
    hint = (product_hint or "").strip()

    candidates: list[tuple[float, str, str]] = []  # score, name, source

    for n in _jsonld_org_names(html):
        candidates.append((90.0, n, "jsonld"))

    og = re.search(
        r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.I,
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\']',
        html,
        re.I,
    )
    if og:
        cleaned = _clean_org_name(og.group(1))
        if cleaned:
            candidates.append((85.0, cleaned, "og:site_name"))

    copy = _copyright_brand(html, text)
    if copy:
        candidates.append((80.0, copy, "copyright"))

    if brand_from_domain and _looks_like_brand(brand_from_domain):
        host = domain.lower()
        score = 88.0 if _DOC_HOST_PREFIX.search(host) or ".abb." in f".{host}." else 72.0
        candidates.append((score, brand_from_domain, "domain"))

    for brand in _manufacturer_attribution_brands(text, home.title or ""):
        candidates.append((82.0, brand, "by_brand"))

    for brand in _self_as_company_brands(text, product_hint=hint):
        # Page explicitly calls this string a company — prefer over host org
        # when it is the page subject (matches product hint / path brand).
        score = 91.0 if hint and _names_collide(brand, hint) else 75.0
        candidates.append((score, brand, "self_as_company"))
        if hint and _names_collide(brand, hint) and brand_from_domain:
            if not any(n.startswith("Hosted by:") for n in notes):
                notes.append(f"Hosted by: {brand_from_domain}")

    title = home.title or ""
    # Title tails may be brands — but never promote the product/model string.
    if "|" in title or "—" in title or " - " in title:
        right = re.split(r"[|—]| - ", title)[-1].strip()
        cleaned = _clean_org_name(right)
        if cleaned and not _is_blocked_product_string(cleaned, blocked, hint):
            candidates.append((55.0, cleaned, "title_tail"))
    title_clean = _clean_org_name(title)
    if title_clean and len(title_clean) <= 32:
        if not _is_blocked_product_string(title_clean, blocked, hint):
            candidates.append((40.0, title_clean, "title"))

    # Acquirer-hosted brand pages only: product brand may be the company when
    # (a) acquirer language is explicit, (b) hint is brand-like not a SKU, and
    # (c) host brand differs. Record host as "Hosted by" — do not replace brand.
    if hint and _looks_like_brand(hint) and not _looks_like_model_or_sku(hint):
        host_stem = (brand_from_domain or "").lower()
        hint_key = _name_key(hint)
        host_key = _name_key(host_stem)
        path = (urlparse(home.final_url or "").path or "").lower()
        product_on_path = hint_key and hint_key in re.sub(r"[^a-z0-9]", "", path)
        product_in_title = hint.lower() in title.lower()
        acquirer = bool(_ACQUIRER_SIGNAL.search(text[:3000]))
        if (
            acquirer
            and host_key
            and hint_key
            and hint_key not in host_key
            and host_key not in hint_key
            and (product_on_path or product_in_title)
        ):
            candidates.append((92.0, hint, "acquirer_brand"))
            if brand_from_domain:
                notes.append(f"Hosted by: {brand_from_domain}")
            notes.append(
                "Company bound to product brand (explicit acquirer/distributor evidence)."
            )

    if not candidates:
        fallback = brand_from_domain or domain.split(".")[0].replace("-", " ").title()
        return fallback[:120], notes

    candidates.sort(key=lambda t: (-t[0], t[1]))
    best_name, best_src = candidates[0][1], candidates[0][2]

    def _acceptable(n: str, src: str) -> bool:
        if _INFRA_COMPANY.match(n) or not _looks_like_brand(n):
            return False
        # Negative invariant: product/model string ineligible as company unless
        # this candidate itself is independent org-brand evidence for that string.
        if _is_blocked_product_string(n, blocked, hint):
            if src in _ORG_EVIDENCE_SOURCES and _org_source_names_string(src, n, hint):
                return True
            return False
        return True

    best = None
    best_src_final = best_src
    for _s, n, src in candidates:
        if _acceptable(n, src):
            best = n
            best_src_final = src
            break
    if best is None:
        best = brand_from_domain or candidates[0][1]
        best_src_final = "domain" if brand_from_domain else candidates[0][2]
        # If domain itself collides with product (rare), keep domain — manufacturer
        # domain stem is org evidence by definition.
        if brand_from_domain and _is_blocked_product_string(best, blocked, hint):
            if not _names_collide(brand_from_domain, hint or ""):
                best = brand_from_domain

    if best_src_final == "acquirer_brand" and brand_from_domain:
        if not any(n.startswith("Hosted by:") for n in notes):
            notes.append(f"Hosted by: {brand_from_domain}")

    return best[:120], notes


def _is_blocked_product_string(
    name: str,
    blocked: list[str],
    product_hint: str | None,
) -> bool:
    """True when `name` matches a selected/discovered product or model SKU."""
    if _looks_like_model_or_sku(name):
        # SKU-shaped strings are always blocked as company unless later org evidence
        # confirms the same string — caller checks source.
        if product_hint and _names_collide(name, product_hint):
            return True
        for b in blocked:
            if _names_collide(name, b):
                return True
        # Even without explicit block list, digit-bearing model codes are ineligible
        return True
    for b in blocked:
        if _names_collide(name, b):
            return True
    if product_hint and _names_collide(name, product_hint):
        return True
    return False


def _org_source_names_string(src: str, name: str, product_hint: str | None) -> bool:
    """
    Org-evidence sources may name the company even when that string equals the
    product brand (e.g. Canvas brand on an acquirer host). Model SKUs never qualify
    via path/title alone — only acquirer_brand / schema / domain / attribution.
    """
    if src not in _ORG_EVIDENCE_SOURCES:
        return False
    if _looks_like_model_or_sku(name):
        # Never allow H1 / A0509 / Elios 3 as company via path promotion.
        # Domain/jsonld/copyright matching a SKU string is vanishingly rare; reject.
        return False
    if src == "acquirer_brand":
        return bool(product_hint and _names_collide(name, product_hint))
    if src == "self_as_company":
        return True
    return True


def _canon_path_sku(slug: str) -> str:
    """pm01 / T800 / s2 → compact uppercase SKU."""
    compact = re.sub(r"[^a-zA-Z0-9]", "", slug or "")
    if re.fullmatch(r"[A-Za-z]{1,8}\d{1,4}[A-Za-z]{0,4}", compact):
        return compact.upper()
    return (slug or "").strip()


def _display_from_slug(slug: str) -> str:
    parts = [p for p in re.split(r"[-_]", slug or "") if p]
    out: list[str] = []
    for part in parts:
        if len(part) <= 2:
            out.append(part.upper())
        elif part.isalpha() and part.isupper():
            out.append(part)
        elif part.isalpha() and len(part) <= 4:
            out.append(part.upper())
        else:
            out.append(part[:1].upper() + part[1:])
    return " ".join(out).strip()


def _sku_from_product_href(url: str) -> str | None:
    """SKU from a manufacturer product path, or None if the path is generic."""
    path = (urlparse(url).path or "").rstrip("/")
    match = _PRODUCT_HREF.search(path)
    if match:
        slug = match.group(1)
        if slug.lower() in _PRODUCT_HREF_NOISE:
            return None
        if not _looks_like_model_or_sku(slug) and "-" not in slug:
            # Named product pages still count (/products/adam).
            if not re.fullmatch(r"[a-z]{3,24}", slug, re.I):
                return None
        return _canon_path_sku(slug) or _display_from_slug(slug) or None
    robots = _ROBOTS_HREF.search(path)
    if robots:
        slug = robots.group(1)
        if slug.lower() in _PRODUCT_HREF_NOISE:
            return None
        return _canon_path_sku(slug) or _display_from_slug(slug) or None
    locale = _LOCALE_PRODUCT_HREF.search(path)
    if locale:
        slug = locale.group(1)
        if slug.lower() in _PRODUCT_HREF_NOISE:
            return None
        if _looks_like_model_or_sku(slug):
            return _canon_path_sku(slug) or slug.upper()
        if slug.lower() in _ROBOT_LINE_SLUGS:
            return slug.replace("-", " ").title()
        if re.fullmatch(r"[a-z]{2,10}-[a-z0-9]{1,8}", slug, re.I):
            return slug
        return None
    root = _ROOT_PRODUCT_HREF.search(path or "/")
    if root:
        slug = root.group(1)
        if slug.lower() in _PRODUCT_HREF_NOISE:
            return None
        if _looks_like_model_or_sku(slug) or "-" in slug:
            return _canon_path_sku(slug) or _display_from_slug(slug)
        if re.fullmatch(r"[a-z]{3,20}", slug, re.I):
            return _display_from_slug(slug)
    return None


def _href_product_name(url: str, anchor: str) -> str | None:
    """Prefer 'Family G1' over a label that hides the SKU, or a bare slug."""
    sku = _sku_from_product_href(url)
    if not sku:
        return None
    label = re.sub(r"\s+", " ", (anchor or "").strip())
    sku_canon = sku
    if _COMPACT_SKU.fullmatch(sku):
        sku_canon = sku.upper()
    labeled = (
        2 <= len(label) <= 48
        and re.search(r"[A-Za-z]", label)
        and label.lower() not in _PRODUCT_HREF_NOISE
        and not _is_noise_product_name(label)
    )
    if labeled:
        if sku_canon.lower() not in label.lower() and _looks_like_model_or_sku(sku):
            return f"{label} {sku_canon}".strip()
        return label
    return sku_canon


def _apply_family_prefix(names: list[str]) -> list[str]:
    """Bare SKU next to 'Family G1' → 'Family X1'. Any maker, not one OEM."""
    prefixes: list[str] = []
    for n in names:
        parts = n.split()
        if len(parts) >= 2 and _COMPACT_SKU.fullmatch(parts[-1]):
            prefixes.append(" ".join(parts[:-1]))
    if not prefixes:
        return names
    family = max(set(prefixes), key=prefixes.count)
    out: list[str] = []
    for n in names:
        if _COMPACT_SKU.fullmatch(n):
            out.append(f"{family} {n.upper()}")
        else:
            out.append(n)
    return out


def _dedupe_product_names(names: list[str]) -> list[str]:
    """Drop 'Z1' when 'Family Z1' exists; drop generic Human/Dog/Panda lines."""
    unique: list[str] = []
    seen: set[str] = set()
    for n in names:
        key = _name_key(n)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(n)
    keep: list[str] = []
    for n in unique:
        low = n.lower()
        drop = False
        if low in _ROBOT_LINE_SLUGS:
            if low == "human" and any(re.search(r"bot|g1|humanoid", o, re.I) for o in unique if o != n):
                drop = True
            elif low == "dog" and any(re.search(r"dog", o, re.I) for o in unique if o != n):
                drop = True
            elif low == "panda" and any(re.search(r"panda", o, re.I) for o in unique if o != n):
                drop = True
        if not drop:
            for other in unique:
                if other == n or len(other) <= len(n):
                    continue
                if re.search(rf"\b{re.escape(n)}\b", other, re.I):
                    drop = True
                    break
        if not drop:
            keep.append(n)
    return keep


def _named_robots_from_prose(text: str, *, blocked: set[str] | None = None) -> dict[str, int]:
    """ADAM serves / Scorpion shows — named robots without a SKU regex allowlist."""
    counts: dict[str, int] = {}
    blocked_keys = {_name_key(x) for x in (blocked or set()) if x}
    for m in _PROSE_NAME.finditer(text or ""):
        name = m.group(1)
        low = name.lower()
        if low in _PROSE_NAME_NOISE or low in _PRODUCT_HREF_NOISE:
            continue
        if _name_key(name) in blocked_keys:
            continue
        after = (text or "")[m.end() : m.end() + 90]
        if not _NAME_FOLLOW.search(after):
            continue
        counts[name] = counts.get(name, 0) + 2
    return counts


def _discover_product_names(
    home: FetchedPage,
    *,
    product_hint: str | None = None,
) -> list[str]:
    blob = f"{home.title or ''} {home.text or ''}"
    counts: dict[str, int] = {}
    for m in _PRODUCT_CANDIDATE.finditer(blob):
        name = m.group(1)
        # Normalize Figure N
        if name.lower().startswith("figure"):
            name = re.sub(r"\s+", " ", name, flags=re.I).title()
        else:
            name = name[0].upper() + name[1:] if name.islower() else name
            if name.isupper() and len(name) <= 4:
                pass
            elif not name[0].isupper():
                name = name.title()
        # Prefer exact common casings
        canon = {
            "digit": "Digit",
            "vega": "Vega",
            "origin": "Origin",
            "neo": "Neo",
            "spot": "Spot",
            "stretch": "Stretch",
            "atlas": "Atlas",
            "gofa": "GoFa",
            "tiago": "TIAGo",
            "anymal": "ANYmal",
            "h1": "H1",
            "g1": "G1",
            "b2": "B2",
        }.get(name.lower(), name)
        # Short alphanumeric tokens (H1/G1/B2) need robot-context support
        if re.fullmatch(r"[A-Za-z]?\d+[A-Za-z]?", canon) or canon.upper() in {"H1", "G1", "B2", "GO2"}:
            idx = m.start()
            window = blob[max(0, idx - 60) : idx + 80]
            if not re.search(
                r"\b(robot|humanoid|unitree|quadruped|biped|arm|cobot|payload)\b",
                window,
                re.I,
            ):
                continue
        counts[canon] = counts.get(canon, 0) + 1

    # Also scan anchors for product-only links
    for url, anchor in home.links:
        for m in _PRODUCT_CANDIDATE.finditer(f"{url} {anchor}"):
            canon = m.group(1)
            key = {
                "digit": "Digit",
                "vega": "Vega",
                "origin": "Origin",
                "neo": "Neo",
            }.get(canon.lower(), canon if canon[0].isupper() else canon.title())
            counts[key] = counts.get(key, 0) + 2  # anchor weight

    # Manufacturer product URLs (product-pm01.html /en/x1) — evidence, not an allowlist.
    href_skus: list[str] = []
    for url, anchor in home.links:
        name = _href_product_name(url, anchor)
        if not name:
            continue
        href_skus.append(name)
        counts[name] = counts.get(name, 0) + 3
        label = re.sub(r"\s+", " ", (anchor or "").strip())
        if label and _name_key(label) == _name_key(name):
            counts[name] += 1

    for sku in dict.fromkeys(href_skus):
        counts[sku] = counts.get(sku, 0) + len(
            re.findall(rf"\b{re.escape(sku)}\b", blob, re.I)
        )

    title = home.title or ""
    tail = re.split(r"\s+[|\-–—]\s+", title)[-1] if title else ""
    blocked = {t for t in re.findall(r"[A-Za-z]{3,}", tail)}
    for name, n in _named_robots_from_prose(blob, blocked=blocked).items():
        counts[name] = counts.get(name, 0) + n

    if product_hint:
        hint = product_hint.strip()
        if hint:
            counts[hint] = counts.get(hint, 0) + 5

    # Drop platform-only false positives when never near robot language
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    out: list[str] = []
    for name, n in ranked:
        if n < 1:
            continue
        # Require at least 2 mentions or path/anchor hit
        if n < 2 and name.lower() not in (home.final_url or "").lower():
            if not (product_hint and name.lower() == product_hint.strip().lower()):
                continue
        if _is_noise_product_name(name):
            continue
        out.append(name)
        if len(out) >= _MAX_DISCOVERED_PRODUCTS * 2:
            break
    return _dedupe_product_names(_apply_family_prefix(out))[:_MAX_DISCOVERED_PRODUCTS]


def _hint_display_class(product_name: str, text: str) -> Optional[str]:
    """Descriptive only — not used for matching."""
    window = text
    # Prefer text near product name
    idx = text.lower().find(product_name.lower())
    if idx >= 0:
        window = text[max(0, idx - 200) : idx + 400]
    if re.search(r"\bhumanoid\b|\bbipedal\b", window, re.I):
        return "humanoid"
    if re.search(r"\b(drone|uav|aerial\s+robot|inspection\s+drone)\b", window, re.I):
        return "drone"
    if re.search(r"\b(robot\s+vacuum|autonomous\s+vacuum|vacuum\s+cleaner)\b", window, re.I):
        return "cleaning_robot"
    if re.search(r"\b(floor\s+scrub|scrubber|auto[- ]?scrub)\b", window, re.I):
        return "autonomous_scrubber"
    if re.search(r"\b(quadruped|four[- ]legged|legged\s+robot)\b", window, re.I):
        return "quadruped"
    if re.search(r"\b(cobot|collaborative\s+(?:robot\s+)?arm|6[- ]axis)\b", window, re.I):
        return "cobot_arm"
    if re.search(
        r"\b(construction\s+robot|drywall|layout\s+printer|field\s*printer|"
        r"jobsite\s+robot)\b",
        window,
        re.I,
    ):
        return "construction_robot"
    if re.search(
        r"\b(service\s+robot|hospitality\s+robot|restaurant\s+(?:delivery\s+)?robot|"
        r"social\s+robot)\b",
        window,
        re.I,
    ):
        return "service_robot"
    if re.search(r"\b(dual[- ]arm|mobile\s+manipulat)\b", window, re.I):
        return "mobile_manipulator"
    if re.search(r"\b(amr|autonomous\s+mobile\s+robot|agv)\b", window, re.I):
        return "amr"
    if _PLATFORM_NOISE.search(window):
        return None
    return None
