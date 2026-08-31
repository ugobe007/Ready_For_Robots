"""Discover named SKUs from verified OEM product listing hosts.

COMPANY → PRODUCT only. Never invent a SKU. 404/403/429 stay failed.
Resume-friendly: prior discovery JSON is merged and already-seen URLs are skipped.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable, Literal, Optional
from urllib.parse import urljoin, urlparse

from app.services.oem_sku_catalog import (
    DISCOVERY_PATH,
    _FAMILY_BLOB,
    _GENERIC_NAME,
    is_wrong_product_url,
    name_key,
    page_mentions_sku,
    slugify,
)
from app.services.vendor_robot_lookup import (
    JUNK_LOOKUP_HOSTS,
    host_from_url,
    lookup_domain,
    names_are_same_sku,
)

# Official listing paths only — not SKU names.
_LISTING_PATHS = (
    "/",
    "/products",
    "/products/",
    "/product",
    "/robots",
    "/robots/",
    "/en/products",
    "/en-us/products",
    "/en-us/products/robots",
    "/robotics",
    "/our-robots",
)
_LISTING_HINTS = {
    "universal-robots.com": ("/products/",),
    "bostondynamics.com": ("/products/",),
    "unitree.com": ("/",),
    "fanucamerica.com": ("/cnc/robots/", "/products/robots/"),
    "motoman.com": ("/en-us/products/robots",),
    "mobile-industrial-robots.com": ("/products",),
    "ottomotors.com": ("/amrs", "/robots"),
    "pudurobotics.com": ("/products",),
    "locusrobotics.com": ("/products",),
    "kuka.com": ("/en-us/products/robotics-systems",),
    "abb.com": ("/global/en/offerings/robotics",),
    "1x.tech": ("/",),
    "agilityrobotics.com": ("/",),
    "bearrobotics.ai": ("/",),
    "pal-robotics.com": ("/robots/",),
    "anybotics.com": ("/robotics/",),
    "keenon.com": ("/",),
    "ubtrobot.com": ("/",),
    "figure.ai": ("/",),
    "apptronik.com": ("/",),
    "agibot.com": ("/",),
    "magiclab.top": ("/", "/en"),
    "deeprobotics.cn": ("/en", "/en/index"),
    "richtechrobotics.com": ("/products",),
    "seegrid.com": ("/products",),
    "gausium.com": ("/products",),
    "misorobotics.com": ("/",),
    "pringlerobotics.ai": ("/", "/bots"),
    "aotingbot.com": ("/", "/product"),
    "kaercher.com": ("/us/commercial/autonomous-cleaning-equipment.html",),
    "lucidbots.com": ("/", "/sherpa-drone"),
    "ecovacscommercial.com": ("/", "/products"),
    "avidbots.com": ("/",),
    "polarxrobotics.com": ("/", "/products"),
    "cenobots.com": ("/",),
    "tennantco.com": ("/en_us.html", "/en_us/equipment/cleaning-machines/autonomous-floor-cleaning-machines.html"),
    "seer-robotics.ai": ("/", "/amr/others.html"),
}
_NAV_PATH = re.compile(
    r"/(about|careers?|contact|news|blog|press|support|login|privacy|legal|"
    r"investors?|invest(?:ing|ment)?|cart|checkout|search|events?|partners?|"
    r"resources?|download|webinar|whitepaper|case-stud|cookie|terms|team|"
    r"company|media|shop|store|pricing|demo|faq|newsletter|subscribe|"
    r"farmers?|story|stories|our-story|mission|home|"
    r"imprint|impressum|agb|datenschutz|disclaimer|"
    r"terms-and-conditions|privacy-policy|cookie-policy|legal-notice|"
    r"mentions-legales|aviso-legal|note-legali|cgu|cgv)(/|$)",
    re.I,
)
_JUNK_SKU = re.compile(
    r"^(learn more|contact( us)?|see all|view all|read more|get started|"
    r"book a demo|request( a)? (quote|demo)|watch|download|brochure|"
    r"industrial robots?|collaborative robots?|mobile robots?|amrs?|agvs?|"
    r"cobots?|humanoids?|products?|produkts?|produkte|solutions?|robots?|robotics|"
    r"platform|automation|systems?|series|skip to content|"
    r"privacy( & cookies| policy| notice)?|"
    r"terms( of use| & conditions| and conditions)?|"
    r"view privacy( policy)?|imprint|impressum|agb|datenschutz|disclaimer|"
    r"about( us)?|investors?( relations)?|cookie policy|careers?|"
    r"industries|services|locations|patients|healthcare|pharmacy|"
    r"factory|stories|story|farmers?|invest(?:ing|ment|ors?)?|home|mission|"
    r"order|logs|models|our robots)$",
    re.I,
)
_LONG_MARKETING = re.compile(
    r"(tv|tvs|laptop|monitor|refrigerator|buying guide|recap|world record|"
    r"minimum wage|industrie|indications|collections|inch)",
    re.I,
)
_NAV_NAME = re.compile(
    r"\b(privacy|cookie|terms|policy|investor|webinar|onboarding|sitemap|"
    r"skip to|about us|careers?|contact|blog|press|news|ethics|trademark|"
    r"accessibility|culture|master plan|glossary|leadership|sustainability|"
    r"community|entertainment|devices|account|rewards|referral|consultation|"
    r"customer support|request information|find a center|join (us|our team)|"
    r"case studies|site map|see all|explore all|happy hour|beyond the hype|"
    r"in the news|press releases|general inquiry|responsible disclosure|"
    r"veterans|medicare|multiple sclerosis|acquired brain|stroke|"
    r"laser (applications|cutting)|machine tending|material (handling|removal)|"
    r"palletizing|spot welding|all industries|aerospace|packout|kitting|"
    r"goods-to-person|person to goods|3pl|retail|manufacturing|"
    r"automate inspection|data insights|robot capabilities|robot demo|"
    r"let's talk|chemicals|industries|onboarding|patents|hotline|"
    r"idms|veterinary|cybersecurity|locations|patients|services|"
    r"trade-in|refer & earn|my rewards|ecovacs points|free consultation|"
    r"andrea |vivian |join our|terms &|privacy policy|helicopter|"
    r"levels t3|to l5|washtower|nrf|calculator|imts|education k12|euroshop|"
    r"farmers?|stories|our story|\bstory\b|\binvest(?:ing|ment)?\b|mission|"
    r"imprint|impressum|datenschutz|disclaimer|agb)\b",
    re.I,
)
_BAD_PATH = re.compile(
    r"/(applications?|industries|solutions?|content|privacy|terms|about|"
    r"blog|category|shop|webinar|press|news|careers?|legal|cookie|policy|"
    r"accessibility|culture|master-plan|signin|account|veterans|medicare|"
    r"centers|support|contact|demo|onboarding|patents|disclosure|glossary|"
    r"general|latest-press|in-the-news|who-we-are|software|services|"
    r"upgrade|ecovacs-club|vip|callback|ethicspoint|trademarks|"
    r"get-updates|investor|discover|manufacturing|robot-fleet|logs|"
    r"get-started|webinars|responsible|site-map|more-from|stores-|"
    r"amazon-news|entertainment|sustainability|community|leadership|"
    r"join-our|andrea-|vivian-|case-studies|press-releases|"
    r"payload|extras|orbit|inspection|thermal|visual|acoustic|perimeter|"
    r"safety|arm/|videos|impact|collections|indications|cta|"
    r"future-production|4-door|4k-tvs|inch-tvs|monitors|laptops|"
    r"washers-dryers|tradeshow|campaign|education-k12|controllers|"
    r"calculator|nrf|farmers?|story|stories|our-story|invest|mission|"
    r"imprint|impressum|agb|datenschutz|disclaimer|"
    r"terms-and-conditions|privacy-policy|cookie-policy|legal-notice)(/|$)",
    re.I,
)
_INDUSTRY_DIGIT = re.compile(r"^(3pl|2d|3d|4d|5g|\d+)$", re.I)
_COMPACT_SKU = re.compile(r"^[A-Za-z]{1,4}\d+[A-Za-z0-9/]*$")
_SITEMAP_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
_SITEMAP_LINE = re.compile(r"(?im)^sitemap:\s*(\S+)")

# Proper-noun SKUs that may lack digits. Recognition only — still must appear on page.
_KNOWN_SKU_WORDS = frozenset(
    {
        "spot",
        "stretch",
        "atlas",
        "digit",
        "vega",
        "neo",
        "eve",
        "apollo",
        "yumi",
        "gofa",
        "swifti",
        "moxi",
        "sophia",
        "optimus",
        "pepper",
        "anymal",
        "tiago",
        "servi",
        "carti",
        "proteus",
        "sequoia",
        "sparrow",
        "hercules",
        "chuck",
        "origin",
        "relay",
        "tug",
        "walker",
        "phoenix",
        "ameca",
        "cassie",
        "handle",
        "ranger",
        "flippy",
        "par",
        "rosa",
    }
)

# Lone nav / legal / shop labels. Not SKUs. Compact codes with digits stay pickable.
_CHROME_LABELS = frozenset(
    {
        "product",
        "products",
        "produkt",
        "produkte",
        "shop",
        "store",
        "imprint",
        "impressum",
        "terms",
        "terms and conditions",
        "terms of use",
        "terms of service",
        "agb",
        "privacy",
        "privacy policy",
        "view privacy",
        "view privacy policy",
        "datenschutz",
        "cookies",
        "cookie",
        "cookie policy",
        "legal",
        "legal notice",
        "disclaimer",
        "mentions legales",
        "aviso legal",
        "note legali",
        "cgu",
        "cgv",
        "your",
        "our",
        "more",
        "menu",
        "home",
        "about",
        "about us",
        "news",
        "blog",
        "careers",
        "career",
        "contact",
        "contact us",
        "investors",
        "investor",
        "investor relations",
        "vehicles",
        "vehicle",
        "models",
        "model",
        "charging",
        "service",
        "support",
        "esg",
        "events",
        "company",
        "find us",
        "join us",
        "join-us",
        "find-us",
        "sign in",
        "log in",
        "login",
        "subscribe",
        "en",
        "zh",
        "english",
        "chinese",
    }
)
_CHROME_SLUGS = frozenset(
    {
        "product",
        "products",
        "produkt",
        "produkte",
        "shop",
        "store",
        "imprint",
        "impressum",
        "terms",
        "terms-and-conditions",
        "terms-of-use",
        "terms-of-service",
        "agb",
        "privacy",
        "privacy-policy",
        "datenschutz",
        "cookies",
        "cookie",
        "cookie-policy",
        "legal",
        "legal-notice",
        "disclaimer",
        "mentions-legales",
        "aviso-legal",
        "note-legali",
        "cgu",
        "cgv",
        "about",
        "about-us",
        "news",
        "blog",
        "careers",
        "career",
        "contact",
        "contact-us",
        "investors",
        "investor",
        "investor-relations",
        "vehicles",
        "vehicle",
        "models",
        "model",
        "charging",
        "service",
        "support",
        "esg",
        "events",
        "company",
        "find-us",
        "join-us",
        "joinus",
        "signin",
        "login",
        "subscribe",
        "en",
        "zh",
        "ja",
        "ko",
        "de",
        "fr",
        "es",
        "it",
        "pt",
        "ru",
        "ar",
        "zh-cn",
        "zh-tw",
        "en-us",
        "en-gb",
        "zh-hans",
        "zh-hant",
        "about",
        "news",
    }
)
_CHROME_PHRASE = re.compile(
    r"\b(terms\s+and\s+conditions|privacy\s+policy|view\s+privacy|"
    r"imprint|impressum|datenschutz|disclaimer|"
    r"investor\s+relations|allgemein(?:e|en)\s+geschae?ftsbedingungen)\b",
    re.I,
)
# Category / hub paths — fetch for names, never a FIND SKU.
_HUB_SLUGS = frozenset(
    {
        "product",
        "products",
        "produkt",
        "produkte",
        "robots",
        "robot",
        "solutions",
        "solution",
        "platform",
        "technology",
        "hardware",
        "industries",
        "industry",
        "applications",
        "overview",
    }
)
_VEHICLE_PATH = re.compile(
    r"/(?:vehicles?|cars?|evs?|suvs?|mpvs?|charging|"
    r"investor-relations|investors?)(?:/|$)",
    re.I,
)
_VEHICLE_MODEL_PATH = re.compile(r"/model/[a-z0-9][a-z0-9+\-]*", re.I)
_VEHICLE_PAGE = re.compile(
    r"\b(suvs?|mpvs?|sedans?|hatchbacks?|electric vehicles?|"
    r"smart electric|charging network|investor relations)\b",
    re.I,
)
# G6 / P7 / X9 / L03 — car model codes, not robots, unless humanoid evidence.
_VEHICLE_MODEL_CODE = re.compile(r"^[A-Z]{1,3}\d{1,2}\+?$", re.I)
_CTA_HYPHEN_HEAD = frozenset(
    {"join", "find", "sign", "log", "get", "contact", "book", "see", "learn", "try"}
)
# "apple harvester" / "delivery robots" — work category, not a named SKU.
_CATEGORY_BLOB = re.compile(
    r"^(?:the\s+)?(?:apple|strawberry|grape|cotton|berry|warehouse|delivery|"
    r"floor|pallet)?\s*(?:harvest(?:er|ing)?|weeding|tractors?|robots?|"
    r"systems?|platform|automation|equipment)\s*$",
    re.I,
)
# Title-case verbs that collide with SKU words (Handle the Routine).
_SKU_VERB_PHRASE = re.compile(
    r"\b(handles?|rangers?|spots?|stretches?|origins?|walkers?)\s+"
    r"(the|a|an|your|our|their|this|that|routine|work|tasks?|equipment)\b",
    re.I,
)
_MEET_PROSE = re.compile(
    r"\b(?:meet|introducing|i['’]m|i\s+am)\s+"
    r"((?:[A-Z][a-z]{1,14}(?:[A-Z][a-z0-9]+)+)|(?:[A-Z]{2,12})|(?:[A-Z][a-z0-9]{2,16})|(?:[A-Z][A-Za-z0-9#\-]+))\b"
)
_TRADEMARK_NAME = re.compile(
    r"\b([A-Z][A-Za-z0-9]{2,16})[™®]|\b([A-Z][A-Za-z0-9]{2,16})\s*\(TM\)",
    re.I,
)
_SPEC_NEAR = re.compile(
    r"\b(payload|lidar|runtime|battery|dof|actuator|end[- ]effector|"
    r"autonomous|humanoid|cobot|amr|harvest(?:er|ing)|excavator|"
    r"specification|datasheet|kg|hours?)\b",
    re.I,
)
_PROSE_FOLLOW = re.compile(
    r"^\s*(?:the\s+)?(?:AI[- ]powered\s+)?"
    r"(?:robot|humanoid|cobot|serves?|shows?|delivers?|works\b|"
    r"helps?|makes?|mixes?|cleans?|navigates?|skyrockets?|automates?|"
    r"bartender|barista|waiter|server|scrubber|vacuum|"
    r"is\s+an?\s+(?:AI[- ]powered\s+)?(?:humanoid|service|delivery|cleaning))"
    r"\b",
    re.I,
)
_JSONLD_PRODUCT_TYPES = frozenset({"product", "individualproduct"})
_JSONLD_VEHICLE_TYPES = frozenset(
    {
        "vehicle",
        "car",
        "motorizedbicycle",
        "busorcoach",
        "motorcycle",
        "vehiclemake",
        "vehiclemodel",
    }
)


def is_site_chrome_slug(slug: str) -> bool:
    """True for path segments that are site chrome, not a robot SKU."""
    s = (slug or "").strip().lower().strip("/")
    s = re.sub(r"[?#].*$", "", s)
    s = s.rsplit("/", 1)[-1]
    if not s:
        return False
    return s in _CHROME_SLUGS or s in _CHROME_LABELS


def is_site_chrome_name(name: str) -> bool:
    """True for generic nav/legal labels that must never enter the FIND picker."""
    raw = re.sub(r"\s+", " ", (name or "").strip(" .-"))
    if not raw:
        return True
    low = raw.lower()
    if low in _CHROME_LABELS or name_key(raw) in {name_key(x) for x in _CHROME_LABELS}:
        return True
    if is_site_chrome_slug(raw.replace(" ", "-")):
        return True
    if _CHROME_PHRASE.search(raw):
        return True
    return False


def is_junk_sku_name(name: str) -> bool:
    raw = re.sub(r"\s+", " ", (name or "").strip(" .-"))
    if not raw or len(raw) < 2 or len(raw) > 40:
        return True
    if is_site_chrome_name(raw):
        return True
    if _CATEGORY_BLOB.fullmatch(raw):
        return True
    if _JUNK_SKU.fullmatch(raw) or _FAMILY_BLOB.search(raw) or _GENERIC_NAME.search(raw):
        return True
    if _NAV_NAME.search(raw) or _LONG_MARKETING.search(raw):
        return True
    if len(raw.split()) > 5:
        return True
    if raw.lower() in {
        "series",
        "family",
        "line",
        "platform",
        "ai",
        "us",
        "arm",
        "orbit",
        "cta4",
        "farmers",
        "farmer",
        "story",
        "stories",
        "invest",
        "home",
        "mission",
        "vehicles",
        "vehicle",
        "investors",
        "about",
        "news",
        "blog",
        "careers",
        "contact",
    }:
        return True
    if not re.search(r"[A-Za-z]", raw):
        return True
    return False


def looks_like_named_sku(name: str) -> bool:
    """Named model only: digits, known SKU word, or compact code. No nav titles."""
    raw = re.sub(r"\s+", " ", (name or "").strip())
    if is_junk_sku_name(raw):
        return False
    if _INDUSTRY_DIGIT.fullmatch(name_key(raw)):
        return False
    if re.search(r"\d", raw) or "#" in raw:
        return True
    if name_key(raw) in _KNOWN_SKU_WORDS:
        return True
    tokens = [t for t in re.split(r"\s+", raw) if t]
    if len(tokens) == 1 and _COMPACT_SKU.fullmatch(tokens[0]):
        return True
    # LaserWeeder / FieldPrinter — concatenated proper noun, not "apple harvester".
    if re.fullmatch(r"[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+", raw):
        return True
    return False


CandidateKind = Literal["chrome", "hub", "vehicle", "product", "unknown"]


def _path_slug(url: str) -> str:
    path = (urlparse(url or "").path or "").rstrip("/")
    return path.rsplit("/", 1)[-1].split(".", 1)[0].lower() if path else ""


def href_is_vehicle_path(url: str) -> bool:
    path = urlparse(url or "").path or "/"
    return bool(_VEHICLE_PATH.search(path) or _VEHICLE_MODEL_PATH.search(path))


def looks_like_vehicle_model(
    name: str,
    *,
    text: str = "",
    title: str = "",
    links: list | None = None,
) -> bool:
    """G6/P7/X9 on a car OEM homepage — not a FIND robot."""
    compact = re.sub(r"[^A-Za-z0-9+]", "", name or "")
    if not _VEHICLE_MODEL_CODE.fullmatch(compact) and not _VEHICLE_MODEL_CODE.fullmatch(name or ""):
        return False
    blob = f"{title or ''} {text or ''}"
    if _VEHICLE_PAGE.search(blob):
        return True
    for href, _anchor in links or []:
        if href_is_vehicle_path(href):
            return True
    return False


def classify_href_candidate(url: str, name: str = "") -> CandidateKind:
    """chrome | hub | vehicle | product | unknown. Bare /product is never a SKU."""
    label = re.sub(r"\s+", " ", (name or "").strip())
    if label and (is_site_chrome_name(label) or is_site_chrome_slug(label)):
        return "chrome"
    if href_is_vehicle_path(url):
        return "vehicle"
    slug = _path_slug(url)
    if is_site_chrome_slug(slug):
        return "chrome"
    if slug in _HUB_SLUGS:
        return "hub"
    if label.lower() in _HUB_SLUGS:
        return "hub"
    if looks_like_named_sku(label) or looks_like_named_sku(slug) or re.search(r"\d|#", slug):
        return "product"
    if "-" in slug and 3 <= len(slug) <= 24:
        parts = [p for p in slug.split("-") if p]
        if parts and parts[0] in _CTA_HYPHEN_HEAD:
            return "chrome"
        return "product"
    return "unknown"


def trademark_product_names(text: str) -> list[str]:
    """Cruz™ / Name (TM) — named products, not nav labels."""
    out: list[str] = []
    seen: set[str] = set()
    for m in _TRADEMARK_NAME.finditer(text or ""):
        token = (m.group(1) or m.group(2) or "").strip()
        key = name_key(token)
        if not token or not key or key in seen or is_site_chrome_name(token):
            continue
        seen.add(key)
        out.append(token)
    return out


def jsonld_product_names(html: str) -> list[str]:
    """schema.org Product names. Vehicle/Car nodes are not FIND robots."""
    out: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html or "",
        re.I | re.S,
    ):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        stack: list[Any] = data if isinstance(data, list) else [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
                continue
            if not isinstance(node, dict):
                continue
            if isinstance(node.get("@graph"), list):
                stack.extend(node["@graph"])
            types = node.get("@type")
            type_list = [types] if isinstance(types, str) else list(types or [])
            lowered = {str(x).split("/")[-1].lower() for x in type_list}
            if lowered & _JSONLD_VEHICLE_TYPES:
                continue
            if not (lowered & _JSONLD_PRODUCT_TYPES):
                continue
            n = node.get("name")
            if not isinstance(n, str):
                continue
            cleaned = re.sub(r"\s+", " ", n).strip(" .-")
            key = name_key(cleaned)
            if not cleaned or not key or key in seen or is_site_chrome_name(cleaned):
                continue
            seen.add(key)
            out.append(cleaned)
    return out


def product_evidence_kinds(
    name: str,
    *,
    text: str = "",
    html: str = "",
    url: str = "",
) -> list[str]:
    """Evidence that `name` is a robot product on this page. Empty = unproven."""
    raw = re.sub(r"\s+", " ", (name or "").strip())
    if not raw or is_site_chrome_name(raw) or is_junk_sku_name(raw):
        return []
    if url and classify_href_candidate(url, raw) in {"chrome", "hub", "vehicle"}:
        return []
    blob = f"{text or ''} {html or ''}"
    if _VEHICLE_MODEL_CODE.fullmatch(raw) and _VEHICLE_PAGE.search(blob):
        window = _evidence_window(raw, blob)
        if not re.search(r"\b(humanoid|robot|iron)\b", window, re.I):
            return []
    kinds: list[str] = []
    key = name_key(raw)
    for n in jsonld_product_names(html):
        if name_key(n) == key:
            kinds.append("jsonld_product")
            break
    if _MEET_PROSE.search(blob):
        for m in _MEET_PROSE.finditer(blob):
            if name_key(m.group(1) or "") == key:
                kinds.append("meet_prose")
                break
    for m in _TRADEMARK_NAME.finditer(blob):
        token = m.group(1) or m.group(2) or ""
        if name_key(token) == key:
            kinds.append("trademark_name")
            break
    if looks_like_named_sku(raw) and re.search(rf"\b{re.escape(raw)}\b", blob, re.I):
        if re.search(r"\d|#", raw) or _COMPACT_SKU.fullmatch(re.sub(r"[\s_\-]", "", raw)):
            kinds.append("model_code")
        elif re.fullmatch(r"[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+", raw):
            kinds.append("model_code")
        elif "-" in raw and 3 <= len(raw) <= 24:
            kinds.append("hyphen_model")
    window = _evidence_window(raw, blob)
    idx = blob.lower().find(raw.lower())
    if idx >= 0:
        after = blob[idx + len(raw) : idx + len(raw) + 90]
        if _PROSE_FOLLOW.search(after) and not _SKU_VERB_PHRASE.search(
            blob[max(0, idx - 12) : idx + 80]
        ):
            kinds.append("named_robot_prose")
    if window and _SPEC_NEAR.search(window) and not _SKU_VERB_PHRASE.search(window):
        if re.search(
            rf"\b{re.escape(raw)}\b.{{0,80}}\b(robot|humanoid|cobot|amr|harvester|"
            rf"excavator|pods?|autonomous)\b",
            window,
            re.I,
        ) or re.search(
            rf"\b(robot|humanoid|cobot|amr|meet|introducing)\b.{{0,80}}\b{re.escape(raw)}\b",
            window,
            re.I,
        ):
            kinds.append("named_robot_prose")
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for k in kinds:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _evidence_window(name: str, blob: str, radius: int = 140) -> str:
    if not name or not blob:
        return ""
    idx = blob.lower().find(name.lower())
    if idx < 0:
        return ""
    return blob[max(0, idx - radius) : idx + len(name) + radius]


def name_is_proven_product(
    name: str,
    *,
    text: str = "",
    html: str = "",
    url: str = "",
) -> bool:
    """True when at least one on-page evidence kind supports this SKU."""
    if _SKU_VERB_PHRASE.search(_evidence_window(name, text or html or "")):
        # "Handle the Routine" is not the Handle robot.
        kinds = product_evidence_kinds(name, text=text, html=html, url=url)
        return any(k in {"jsonld_product", "meet_prose", "trademark_name", "model_code"} for k in kinds)
    return bool(product_evidence_kinds(name, text=text, html=html, url=url))


def canonical_sku_name(name: str, url: str) -> str:
    """Prefer a compact path SKU (C55, T10) over a marketing headline."""
    last = (urlparse(url).path or "").rstrip("/").rsplit("/", 1)[-1]
    compact = last.replace("_", "-")
    if _COMPACT_SKU.fullmatch(compact) and looks_like_named_sku(compact.upper()):
        return compact.upper()
    return name


def _slug_to_name(slug: str) -> str:
    raw = (slug or "").replace("_", "-").strip("-")
    if not raw:
        return ""
    if re.fullmatch(r"[a-z]{1,3}\d+[a-z0-9]*", raw, re.I):
        return raw.upper()
    parts = [p for p in raw.split("-") if p]
    if not parts:
        return ""
    if parts[0].lower() in {"irb", "crx", "kr", "ur", "gp", "hc", "ar"}:
        head = parts[0].upper()
        rest = " ".join(parts[1:])
        return f"{head} {rest}".strip() if rest else head
    return " ".join(p.upper() if re.search(r"\d", p) else p.title() for p in parts)


def listing_urls_for_company(company: dict[str, Any]) -> list[str]:
    """Official hosts only. Spreadsheet + verified product parents + listing hints."""
    hosts = [h for h in (company.get("domains") or []) if h and h not in JUNK_LOOKUP_HOSTS]
    if not hosts:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def _add(url: str) -> None:
        raw = (url or "").strip()
        if not raw:
            return
        if "://" not in raw:
            raw = "https://" + raw
        host = lookup_domain(raw) or host_from_url(raw)
        if not host or host in JUNK_LOOKUP_HOSTS:
            return
        if hosts and host not in hosts and not any(host.endswith("." + h) or h.endswith("." + host) for h in hosts):
            return
        key = raw.rstrip("/").lower()
        if key in seen:
            return
        seen.add(key)
        out.append(raw)

    for host in hosts:
        _add(f"https://{host}/")
        _add(f"https://www.{host}/")
        for path in _LISTING_PATHS:
            _add(f"https://{host}{path}")
            _add(f"https://www.{host}{path}")
        for path in _LISTING_HINTS.get(host, ()):
            _add(f"https://{host}{path}")
            _add(f"https://www.{host}{path}")
    for url in (company.get("source_urls") or []) + (company.get("verified_urls") or []):
        _add(url)
        parsed = urlparse(url)
        parent = parsed.path.rstrip("/").rsplit("/", 1)[0]
        if parent and parent not in {"", "/"}:
            _add(f"{parsed.scheme}://{parsed.netloc}{parent}/")
    return out


def _path_is_nav(path: str) -> bool:
    p = (path or "").rstrip("/") or "/"
    if p in {"", "/", "/en", "/zh", "/en-us"}:
        return False
    return bool(_NAV_PATH.search(p))


def candidates_from_page(
    page: Any,
    *,
    company: dict[str, Any],
    page_url: str,
) -> list[dict[str, str]]:
    """Named product links on an official host. No invented names."""
    host = lookup_domain(page_url) or host_from_url(page_url)
    siblings = [p.get("name") or "" for p in company.get("products") or []]
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for href, anchor in list(getattr(page, "links", None) or []):
        full = urljoin(page_url, href or "")
        link_host = lookup_domain(full) or host_from_url(full)
        if host and link_host and link_host != host:
            continue
        path = urlparse(full).path or ""
        if _path_is_nav(path) or _BAD_PATH.search(path):
            continue
        last = path.rstrip("/").rsplit("/", 1)[-1] if path else ""
        label = re.sub(r"\s+", " ", (anchor or "").strip())
        name = ""
        if looks_like_named_sku(label):
            name = label
        elif looks_like_named_sku(_slug_to_name(last)):
            name = _slug_to_name(last)
        if name:
            name = canonical_sku_name(name, full)
        if not name or is_junk_sku_name(name) or not looks_like_named_sku(name):
            continue
        if is_wrong_product_url(name, full, sibling_names=siblings + [c["name"] for c in found]):
            continue
        key = name_key(name)
        if not key or key in seen:
            continue
        seen.add(key)
        found.append({"name": name, "url": full.split("#")[0]})
    return found


def _sitemap_urls(fetch_text: Callable[..., Any], domain: str, get_fn) -> list[str]:
    seeds = [
        f"https://{domain}/sitemap.xml",
        f"https://www.{domain}/sitemap.xml",
        f"https://{domain}/robots.txt",
        f"https://www.{domain}/robots.txt",
    ]
    locs: list[str] = []
    for url in seeds:
        page = get_fn(url, kind="text")
        if page is None or isinstance(page, Exception):
            continue
        status, text = page if isinstance(page, tuple) else (getattr(page, "status_code", 0), "")
        if status != 200:
            continue
        blob = text or ""
        if url.endswith("robots.txt"):
            for match in _SITEMAP_LINE.finditer(blob):
                sm = match.group(1).strip()
                if sm:
                    nested = get_fn(sm, kind="text")
                    if isinstance(nested, tuple) and nested[0] == 200:
                        blob += "\n" + (nested[1] or "")
        for loc in _SITEMAP_LOC.findall(blob):
            loc = loc.strip()
            host = lookup_domain(loc) or host_from_url(loc)
            if host and (host == domain or host.endswith("." + domain)):
                if not _path_is_nav(urlparse(loc).path or ""):
                    locs.append(loc)
        if locs:
            break
    # Prefer product-like paths.
    scored: list[tuple[int, str]] = []
    seen: set[str] = set()
    for loc in locs:
        key = loc.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        path = (urlparse(loc).path or "").lower()
        score = 0
        if re.search(r"/(products?|robots?|cobot|amr|humanoid)/", path):
            score += 2
        last = path.rstrip("/").rsplit("/", 1)[-1]
        if looks_like_named_sku(_slug_to_name(last)):
            score += 3
        if score:
            scored.append((score, loc))
    scored.sort(key=lambda x: -x[0])
    return [u for _, u in scored]


def make_discovered_product(company: dict[str, Any], name: str, url: str | None) -> dict[str, Any]:
    host = lookup_domain(url) or host_from_url(url) if url else (company.get("domains") or [None])[0]
    return {
        "name": name,
        "slug": f"{company['slug']}-{slugify(name)}"[:160],
        "company_name": company["name"],
        "company_slug": company["slug"],
        # Identity only. Never copy BellaBot serving onto PUDUA1 (company → category).
        "primary_class": "service_robot",
        "category": None,
        "listed_class": None,
        "task": None,
        "setting": None,
        "status": None,
        "region": company.get("regions"),
        "spreadsheet_sources": [],
        "candidate_sources": [url] if url else [],
        "product_url": None,
        "lookup_host": host,
        "url_status": "unverified",
        "specs": {},
        "capability_confidence": "UNKNOWN",
        "flags": [],
        "source": "oem_listing",
    }


def scrub_discovery(discovery: dict[str, Any]) -> dict[str, Any]:
    """Drop nav/marketing rows that slipped past an earlier loose extractor."""
    kept: list[dict[str, Any]] = []
    dropped = 0
    for row in discovery.get("verified") or []:
        url = row.get("url") or ""
        path = urlparse(url).path or ""
        name = canonical_sku_name(row.get("name") or "", url)
        if (
            is_junk_sku_name(name)
            or not looks_like_named_sku(name)
            or _BAD_PATH.search(path)
            or re.search(r"indication|washer|tradeshow|calculator|nrf|education-k12|controllers", path, re.I)
        ):
            dropped += 1
            continue
        row = dict(row)
        row["name"] = name
        kept.append(row)
    discovery["verified"] = kept
    discovery["counts"] = {
        **(discovery.get("counts") or {}),
        "verified": len(kept),
        "scrubbed": dropped,
    }
    return discovery


def merge_discovered_skus(catalog: dict[str, Any], discovery: dict[str, Any]) -> dict[str, Any]:
    """Append verified named SKUs. Keep workbook rows. Skip junk series blobs."""
    by_slug = {c["slug"]: c for c in catalog.get("companies") or []}
    added = 0
    for row in discovery.get("verified") or []:
        company = by_slug.get(row.get("company_slug") or "")
        if company is None:
            continue
        name = (row.get("name") or "").strip()
        if not name or is_junk_sku_name(name) or _FAMILY_BLOB.search(name):
            continue
        if any(
            names_are_same_sku(name, p.get("name") or "", slug_right=p.get("slug") or "")
            for p in company.get("products") or []
        ):
            continue
        product = make_discovered_product(company, name, row.get("url"))
        product["slug"] = row.get("slug") or product["slug"]
        company["products"].append(product)
        added += 1
    products = [p for c in catalog.get("companies") or [] for p in c.get("products") or []]
    catalog["product_count"] = len(products)
    catalog["company_count"] = len(catalog.get("companies") or [])
    catalog["version"] = "1.1.0"
    notes = list(catalog.get("notes") or [])
    extra = (
        "Discovered named SKUs from official OEM listing pages. "
        "Empty specs stay UNKNOWN. Not Job Card employers."
    )
    if extra not in notes:
        notes.append(extra)
    catalog["notes"] = notes
    catalog["discovered_added"] = added
    return catalog


def discover_skus(
    catalog: dict[str, Any],
    *,
    fetch_page: Callable[..., Any] | None = None,
    fetch_text: Callable[..., Any] | None = None,
    rate_limit_s: float = 0.45,
    max_fetches: int | None = None,
    max_new_per_oem: int = 16,
    max_listings_per_oem: int = 4,
    oem_slug: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
    prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Walk official listing pages. Store only verified named SKUs."""
    if fetch_page is None:
        from app.services.robot_understanding_v1.fetch import fetch_page as _fetch

        fetch_page = _fetch
    if fetch_text is None:
        from app.services.robot_understanding_v1.fetch import fetch_text as _text

        fetch_text = _text

    prior = prior or {}
    oems: dict[str, Any] = dict(prior.get("oems") or {})
    verified: list[dict[str, Any]] = list(prior.get("verified") or [])
    failed: list[dict[str, Any]] = list(prior.get("failed") or [])
    skipped: list[dict[str, Any]] = list(prior.get("skipped") or [])
    queued: list[dict[str, Any]] = []
    seen_verify = {
        (row.get("company_slug"), name_key(row.get("name") or ""))
        for bucket in (verified, failed, skipped)
        for row in bucket
    }
    seen_urls = { (row.get("url") or "").rstrip("/").lower() for row in verified if row.get("url") }
    cache: dict[str, Any] = {}
    fetches = 0

    def _get(url: str, *, kind: str = "page"):
        nonlocal fetches
        key = f"{kind}:{url}"
        if key in cache:
            return cache[key]
        if max_fetches is not None and fetches >= max_fetches:
            return None
        if fetches:
            sleep(rate_limit_s)
        fetches += 1
        try:
            if kind == "text":
                result = fetch_text(url)
            else:
                result = fetch_page(url, allow_archive=False)
        except Exception as exc:
            cache[key] = exc
            return exc
        cache[key] = result
        return result

    companies = list(catalog.get("companies") or [])
    if oem_slug:
        companies = [c for c in companies if c.get("slug") == oem_slug]

    for company in companies:
        slug = company.get("slug") or slugify(company.get("name") or "oem")
        rec = oems.get(slug) or {
            "name": company["name"],
            "slug": slug,
            "status": "pending",
            "existing": len(company.get("products") or []),
            "listing_tried": [],
            "discovered": 0,
        }
        if rec.get("status") == "complete":
            oems[slug] = rec
            continue
        siblings = [p.get("name") or "" for p in company.get("products") or []]
        listing_urls = listing_urls_for_company(company)
        tried = set(rec.get("listing_tried") or [])
        candidates: list[dict[str, str]] = []
        listings_this = 0
        for url in listing_urls:
            if url.rstrip("/").lower() in tried:
                continue
            if listings_this >= max_listings_per_oem:
                break
            if max_fetches is not None and fetches >= max_fetches:
                queued.append({"company": company["name"], "url": url, "reason": "budget"})
                break
            page = _get(url)
            tried.add(url.rstrip("/").lower())
            listings_this += 1
            if page is None:
                queued.append({"company": company["name"], "url": url, "reason": "budget"})
                break
            status = 0 if isinstance(page, Exception) else int(getattr(page, "status_code", 0) or 0)
            if isinstance(page, Exception) or status in {0, 403, 404, 429, 503} or status != 200:
                failed.append(
                    {
                        "company": company["name"],
                        "company_slug": slug,
                        "url": url,
                        "reason": type(page).__name__ if isinstance(page, Exception) else f"http_{status}",
                        "kind": "listing",
                    }
                )
                continue
            candidates.extend(
                candidates_from_page(page, company=company, page_url=getattr(page, "final_url", url) or url)
            )

        domain = (company.get("domains") or [None])[0]
        if domain and rec.get("sitemap") != "done" and (max_fetches is None or fetches < max_fetches):
            for loc in _sitemap_urls(fetch_text, domain, _get)[:24]:
                last = (urlparse(loc).path or "").rstrip("/").rsplit("/", 1)[-1]
                name = _slug_to_name(last)
                if looks_like_named_sku(name):
                    candidates.append({"name": name, "url": loc})
            rec["sitemap"] = "done"

        # Dedup candidates; skip names already in the workbook unless they lack a URL.
        new_this = 0
        for cand in candidates:
            name = cand["name"]
            url = cand["url"]
            if is_junk_sku_name(name) or _FAMILY_BLOB.search(name):
                skipped.append(
                    {
                        "company": company["name"],
                        "company_slug": slug,
                        "name": name,
                        "url": url,
                        "reason": "junk_or_series",
                    }
                )
                continue
            if is_wrong_product_url(name, url, sibling_names=siblings):
                skipped.append(
                    {
                        "company": company["name"],
                        "company_slug": slug,
                        "name": name,
                        "url": url,
                        "reason": "wrong_product_url",
                    }
                )
                continue
            key = (slug, name_key(name))
            url_key = url.rstrip("/").lower()
            if key in seen_verify or url_key in seen_urls:
                continue
            match = next(
                (
                    p
                    for p in company.get("products") or []
                    if names_are_same_sku(name, p.get("name") or "", slug_right=p.get("slug") or "")
                ),
                None,
            )
            if match and match.get("product_url"):
                continue
            if new_this >= max_new_per_oem:
                queued.append({"company": company["name"], "name": name, "url": url, "reason": "oem_cap"})
                continue
            if max_fetches is not None and fetches >= max_fetches:
                queued.append({"company": company["name"], "name": name, "url": url, "reason": "budget"})
                rec["status"] = "partial"
                break
            page = _get(url)
            if page is None:
                queued.append({"company": company["name"], "name": name, "url": url, "reason": "budget"})
                rec["status"] = "partial"
                break
            status = 0 if isinstance(page, Exception) else int(getattr(page, "status_code", 0) or 0)
            if isinstance(page, Exception) or status in {0, 403, 404, 429, 503} or status != 200:
                failed.append(
                    {
                        "slug": f"{slug}-{slugify(name)}"[:160],
                        "name": name,
                        "company": company["name"],
                        "company_slug": slug,
                        "url": url,
                        "reason": type(page).__name__ if isinstance(page, Exception) else f"http_{status}",
                    }
                )
                seen_verify.add(key)
                continue
            text = f"{getattr(page, 'title', '') or ''} {getattr(page, 'text', '') or ''}"
            final = getattr(page, "final_url", None) or url
            if is_wrong_product_url(name, final, sibling_names=siblings):
                skipped.append(
                    {
                        "slug": f"{slug}-{slugify(name)}"[:160],
                        "name": name,
                        "company": company["name"],
                        "company_slug": slug,
                        "url": final,
                        "reason": "wrong_product_url",
                    }
                )
                seen_verify.add(key)
                continue
            if not page_mentions_sku(text, name, company["name"]):
                failed.append(
                    {
                        "slug": f"{slug}-{slugify(name)}"[:160],
                        "name": name,
                        "company": company["name"],
                        "company_slug": slug,
                        "url": final,
                        "reason": "sku_not_on_page",
                    }
                )
                seen_verify.add(key)
                continue
            product_slug = (match or {}).get("slug") or f"{slug}-{slugify(name)}"[:160]
            host = lookup_domain(final) or host_from_url(final)
            verified.append(
                {
                    "slug": product_slug,
                    "name": match["name"] if match else name,
                    "company": company["name"],
                    "company_slug": slug,
                    "url": final,
                    "host": host,
                    "status_code": getattr(page, "status_code", 200),
                    "source": "oem_listing" if not match else "workbook",
                }
            )
            seen_verify.add(key)
            seen_urls.add(final.rstrip("/").lower())
            if not match:
                new_this += 1
                siblings.append(name)

        rec["listing_tried"] = sorted(tried)
        rec["discovered"] = int(rec.get("discovered") or 0) + new_this
        rec["existing"] = len(company.get("products") or [])
        if rec.get("status") != "partial":
            rec["status"] = "complete" if not any(
                q.get("company") == company["name"] for q in queued
            ) else "partial"
        oems[slug] = rec
        print(
            f"discover {company['name']}: status={rec['status']} "
            f"new={rec['discovered']} listings={len(tried)} fetches={fetches}",
            flush=True,
        )

    complete = sum(1 for r in oems.values() if r.get("status") == "complete")
    partial = sum(1 for r in oems.values() if r.get("status") == "partial")
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "fetcher": "app.services.robot_understanding_v1.fetch.fetch_page",
        "resume": f"PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --discover-skus",
        "fetches": fetches,
        "verified": verified,
        "failed": failed,
        "skipped": skipped,
        "queued": queued,
        "oems": oems,
        "counts": {
            "verified": len(verified),
            "failed": len(failed),
            "skipped": len(skipped),
            "queued": len(queued),
            "fetches": fetches,
            "oems_complete": complete,
            "oems_partial": partial,
            "oems_total": len(oems),
        },
    }


def merge_lookup_rows(lookup: dict[str, Any] | None, discovery: dict[str, Any]) -> dict[str, Any]:
    """Copy discovery-verified URLs into the FIND URL lookup file."""
    base = dict(lookup or {})
    verified = list(base.get("verified") or [])
    have = {row.get("slug") for row in verified if row.get("slug")}
    for row in discovery.get("verified") or []:
        if row.get("slug") and row.get("url") and row["slug"] not in have:
            verified.append(
                {
                    "slug": row["slug"],
                    "name": row["name"],
                    "company": row.get("company"),
                    "url": row["url"],
                    "host": row.get("host"),
                    "status_code": row.get("status_code") or 200,
                }
            )
            have.add(row["slug"])
    base["verified"] = verified
    base.setdefault("skipped", list(base.get("skipped") or []))
    base.setdefault("failed", list(base.get("failed") or []))
    base["counts"] = {
        "verified": len(verified),
        "skipped": len(base.get("skipped") or []),
        "failed": len(base.get("failed") or []),
        "queued": len(base.get("queued") or []),
    }
    return base


__all__ = [
    "DISCOVERY_PATH",
    "candidates_from_page",
    "discover_skus",
    "is_junk_sku_name",
    "is_site_chrome_name",
    "is_site_chrome_slug",
    "classify_href_candidate",
    "href_is_vehicle_path",
    "jsonld_product_names",
    "looks_like_vehicle_model",
    "name_is_proven_product",
    "product_evidence_kinds",
    "trademark_product_names",
    "listing_urls_for_company",
    "looks_like_named_sku",
    "merge_discovered_skus",
    "merge_lookup_rows",
    "scrub_discovery",
]
