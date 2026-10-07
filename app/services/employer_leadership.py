"""Find leadership/team pages on an employer site and extract named people.

Used by the decision-maker extract DAG. FIND does not call this.
Names are read from the page. None are invented. Hunter looks up emails later.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import re
import time
from typing import Any, Callable, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.services.robot_job_extract import _is_board_host
from app.services.robot_url_safety import UrlSafetyError, assert_public_http_url

logger = logging.getLogger(__name__)

_ATS_HOSTS = frozenset(
    {
        "greenhouse.io",
        "lever.co",
        "workday.com",
        "myworkdayjobs.com",
        "smartrecruiters.com",
        "icims.com",
        "ultipro.com",
        "paycomonline.net",
        "breezy.hr",
        "bamboohr.com",
        "jobvite.com",
        "taleo.net",
        "successfactors.com",
        "workable.com",
        "fountain.com",
    }
)
_CAREER_HOST_LABELS = frozenset(
    {
        "jobs",
        "careers",
        "career",
        "apply",
        "hiring",
        "recruiting",
        "talent",
    }
)

LEADERSHIP_PATHS = (
    "/leadership",
    "/our-leadership",
    "/leadership-team",
    "/executive-team",
    "/executives",
    "/management",
    "/team",
    "/our-team",
    "/our-people",
    "/about/leadership",
    "/about/team",
    "/company/leadership",
    "/company/team",
    "/about-us/leadership",
)

_SKIP_HREF = re.compile(
    r"career|jobs?(?:/|-)|blog|news|press|privacy|login|signin|investor|"
    r"product|shop|cart|support|cookie|legal|terms|dialysis|waiver|school",
    re.I,
)
_TITLE = re.compile(
    r"(?i)\b("
    r"(?:(?:senior|sr\.?|executive)\s+)?"
    r"(?:(?:pharmacy|warehouse|plant|facilities|operations|manufacturing|"
    r"fulfillment|environmental|evs|support|materials?|culinary|kitchen|"
    r"shipping|receiving|site|nurse|medical|financial|people|strategy|"
    r"operating|executive)\s+){0,3}"
    r"(?:vice\s+)?"
    r"(?:president|director|manager|head|chief|supervisor|vp|officer|coo|ceo|cfo|cmo|cno)"
    r"(?:\s+(?:and\s+)?(?:of\s+(?:the\s+)?)?[A-Za-z][A-Za-z&/ ]{1,50})?"
    r")"
)
_CREDENTIAL = re.compile(
    r"(?:,\s*)?(?:\b(?:MD|DO|PhD|DNP|RN|MBA|MHA|MPH|JD|LLM|CPA|FACHE|FHFMA|"
    r"CCHP-A|IPMA|CP|Jr\.?|Sr\.?|III|IV|Esq\.?)\b\.?\s*)+",
    re.I,
)
_BAD_NAME = frozenset(
    {
        "About",
        "Contact",
        "Company",
        "Leadership",
        "Executive",
        "Operations",
        "Director",
        "Manager",
        "President",
        "Privacy",
        "Terms",
        "Learn",
        "More",
        "Meet",
        "Our",
        "The",
        "This",
        "Team",
        "Staff",
        "Board",
        "View",
        "Read",
        "Your",
        "Ready",
        "Robots",
        "Home",
        "News",
        "Press",
        "Human",
        "Resources",
        "General",
        "Information",
        "Click",
        "Here",
        "Join",
        "Apply",
        "Chief",
        "Vice",
        "Senior",
        "Nurse",
        "Medical",
        "Financial",
        "Legal",
        "People",
        "Strategy",
        "Compliance",
        "Operating",
        "Officer",
        "Pharmacy",
        "Nursing",
        "Health",
        "Policy",
        "Public",
        "Attorney",
        "County",
        "Division",
        "Department",
        "Hospital",
        "System",
        "Affairs",
        "Relations",
        "Communications",
        "Foundation",
        "Locations",
        "History",
        "Media",
        "Office",
        "Program",
        "Programs",
    }
)
_PLACE_OR_ORG = frozenset(
    {
        "North",
        "South",
        "East",
        "West",
        "Northeast",
        "Northwest",
        "Southeast",
        "Southwest",
        "America",
        "American",
        "Europe",
        "European",
        "Asia",
        "Asian",
        "Pacific",
        "Atlantic",
        "Africa",
        "African",
        "Region",
        "Regional",
        "Global",
        "International",
        "Corporate",
        "Group",
        "Chain",
        "Supply",
        "Distribution",
        "Logistics",
        "Manufacturing",
        "Quality",
        "Safety",
        "Clinical",
        "Community",
        "United",
        "States",
        "National",
        "Central",
        "District",
        "Campus",
        "Site",
        "Plant",
        "Warehouse",
        "Fulfillment",
        "Worldwide",
        "Holdings",
        "Limited",
        "Midwest",
        "Midatlantic",
        "New",
        "York",
        "City",
        "Care",
        "Services",
        "Patient",
        "Area",
        "Unit",
        "Floor",
        "Center",
        "Centre",
        "Park",
        "Lake",
        "Bay",
        "Valley",
        "View",
        "River",
    }
)
_MAX_FETCHES = 4
_MAX_PAGES = 1
_MAX_HTML = 220_000
_TIMEOUT = 3.0
_DEADLINE = 12.0


def _blocked_host(host: str) -> bool:
    raw = (host or "").strip().lower().rstrip(".")
    if not raw or raw in {"localhost", "metadata.google.internal"}:
        return True
    if raw.endswith(".internal") or raw.endswith(".localhost"):
        return True
    try:
        ipaddress.ip_address(raw)
        return True
    except ValueError:
        return False


def origin_for_domain(domain: Optional[str]) -> Optional[str]:
    host = (domain or "").strip().lower().removeprefix("www.")
    if not host or "." not in host or _is_board_host(host):
        return None
    if "/" in host or " " in host or _blocked_host(host):
        return None
    if any(host == d or host.endswith("." + d) for d in _ATS_HOSTS):
        return None
    if host.split(".", 1)[0] in _CAREER_HOST_LABELS:
        return None
    return f"https://{host}"


def origins_for_domain(domain: Optional[str]) -> list[str]:
    """www first: some apex hosts drop the path and bounce to /."""
    origin = origin_for_domain(domain)
    if not origin:
        return []
    host = urlparse(origin).hostname or ""
    return [f"https://www.{host}", origin]


def url_score(url: str, label: str = "") -> int:
    path = (urlparse(url).path or "/").lower()
    blob = f"{path} {label}".lower()
    if _SKIP_HREF.search(path) or _SKIP_HREF.search(label):
        return -1
    if "leadership" in blob:
        depth = path.strip("/").count("/") + 1
        return 110 - min(30, depth * 4)
    if "executive-team" in blob or "our-team" in blob:
        return 90
    if re.search(r"/team(?:/|$)", path) or re.search(r"\bteam\b", label.lower()):
        return 80
    if "executives" in blob or "management-team" in blob or "our-people" in blob:
        return 70
    if re.search(r"about[-_/ ]?us", blob) or path.rstrip("/") in {"/about", "/company"}:
        return 12
    return 0


_SKIP_PATH_SEGS = frozenset(
    {
        "pages",
        "default",
        "index.html",
        "sitecollectiondocuments",
        "documents",
        "document",
        "files",
        "images",
        "forms",
        "_layouts",
        "style library",
        "lists",
    }
)


def prefix_leadership_urls(origin: str, url: str) -> list[str]:
    """`/about-us-hh/board/...` also tries `/about-us-hh/leadership`."""
    origin = origin.rstrip("/")
    path = urlparse(url).path or "/"
    segs = [
        s
        for s in path.split("/")
        if s
        and "." not in s
        and s.lower() not in _SKIP_PATH_SEGS
        and not s.lower().endswith(".aspx")
    ]
    if not segs or not re.search(r"about|company|who-we|team|leadership", segs[0], re.I):
        return []
    base = "/" + segs[0]
    return [
        origin + base + tail
        for tail in ("/leadership", "/team", "/our-team", "/executive-team")
    ]


def ranked_leadership_urls(origin: str, homepage_html: str = "") -> list[str]:
    origin = origin.rstrip("/")
    scored: dict[str, int] = {}

    def add(url: str, score: int) -> None:
        if score <= 0:
            return
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path or ''}".rstrip("/")
        scored[clean] = max(scored.get(clean, 0), score)

    # Guessed paths lose to homepage-discovered URLs so a thin /leadership
    # shell does not outrank /about-us-hh/leadership.
    for path in LEADERSHIP_PATHS:
        add(origin + path, url_score(path) - 20)
    soup = BeautifulSoup(homepage_html or "", "html.parser")
    host = (urlparse(origin).hostname or "").lower().removeprefix("www.")
    for anchor in soup.find_all("a", href=True):
        href = urljoin(origin + "/", str(anchor.get("href") or "").strip())
        parsed = urlparse(href)
        link_host = (parsed.hostname or "").lower().removeprefix("www.")
        if not link_host or link_host != host:
            continue
        label = anchor.get_text(" ", strip=True)
        add(href, url_score(href, label) + 20)
        for extra in prefix_leadership_urls(origin, href):
            add(extra, url_score(extra) + 15)
    ranked = sorted(scored.items(), key=lambda item: (-item[1], item[0]))
    return [url for url, score in ranked if score >= 70][:8] or [
        url for url, score in ranked if score >= 12
    ][:2]


def discover_leadership_urls(homepage_html: str, origin: str) -> list[str]:
    return ranked_leadership_urls(origin, homepage_html)


def _plausible_middle(tok: str) -> bool:
    """Ann/Marie yes. York/Care/City no — those are leftover phrases, not people."""
    if not tok or tok in _BAD_NAME | _PLACE_OR_ORG:
        return False
    return 2 <= len(tok) <= 12 and tok.isalpha() and tok[0].isupper() and tok[1:].islower()


def parse_person_name(text: str, *, allow_middle: bool = True) -> Optional[tuple[str, str]]:
    raw = (text or "").replace("\u200b", "").replace("\xa0", " ")
    raw = re.sub(r"\s+", " ", raw).strip(" \t.,;|")
    raw = _CREDENTIAL.sub(" ", raw)
    raw = re.sub(r"\s+", " ", raw).strip(" ,;")
    if not raw or len(raw) > 80:
        return None
    blocked = _BAD_NAME | _PLACE_OR_ORG
    if any(tok[:1].isupper() and tok in blocked for tok in re.findall(r"[A-Za-z]+", raw)):
        return None
    match = re.fullmatch(r"([A-Z])\.\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)", raw)
    if match:
        return match.group(2), match.group(3)
    match = re.fullmatch(r"([A-Z][a-z]+)\s+([A-Z])\.\s+([A-Z][a-z]+)", raw)
    if match:
        return match.group(1), match.group(3)
    match = re.fullmatch(r"([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)", raw)
    if match and allow_middle and _plausible_middle(match.group(2)):
        return match.group(1), match.group(3)
    match = re.fullmatch(r"([A-Z][a-z]+)\s+([A-Z][a-z]+)", raw)
    if match:
        return match.group(1), match.group(2)
    return None


def people_from_html(html: str, source_url: str) -> list[dict[str, Any]]:
    """Pure extract. No HTTP. Empty list when the page names nobody."""
    soup = BeautifulSoup(html or "", "html.parser")
    people: list[dict[str, Any]] = []
    people.extend(_json_ld_people(soup, source_url))
    people.extend(_card_people(soup, source_url))
    people.extend(_text_people(soup.get_text("\n", strip=True), source_url))
    return _dedupe_people(people)


def people_from_pages(pages: Any) -> list[dict[str, Any]]:
    if not isinstance(pages, list):
        return []
    people: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        html = str(page.get("html") or "")
        url = str(page.get("url") or "")
        if html:
            people.extend(people_from_html(html, url))
    return _dedupe_people(people)


def fetch_leadership_pages(
    *,
    domain: Optional[str] = None,
    employer: str = "",
    get_html: Callable[[str], Optional[str]] | None = None,
) -> list[dict[str, Any]]:
    """GET ranked leadership/team URLs. Empty list on miss."""
    origins = origins_for_domain(domain)
    if not origins:
        return []
    getter = get_html or _http_get
    origin = origins[0]
    home: Optional[str] = None
    fetches = 0
    deadline = time.monotonic() + _DEADLINE
    for candidate in origins:
        if fetches >= _MAX_FETCHES or time.monotonic() >= deadline:
            break
        fetches += 1
        html = getter(candidate)
        if html:
            origin = candidate
            home = html
            break
    ranked = ranked_leadership_urls(origin, home or "")
    pages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for url in ranked:
        key = url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        if fetches >= _MAX_FETCHES or len(pages) >= _MAX_PAGES or time.monotonic() >= deadline:
            break
        fetches += 1
        html = getter(url)
        if not html:
            continue
        if re.search(r"<title>[^<]{0,80}404", html, re.I):
            continue
        # Soft-404 / chrome shells have HTML but no named people. Keep going.
        if not people_from_html(html, url):
            continue
        pages.append({"url": url, "html": html})
    if pages:
        logger.info(
            "leadership pages for %s (%s): %s",
            employer or domain,
            domain,
            [p["url"] for p in pages],
        )
    return pages


def _http_get(url: str) -> Optional[str]:
    path = (urlparse(url).path or "").lower()
    if path.endswith((".pdf", ".doc", ".docx", ".zip", ".xls", ".xlsx")):
        return None
    try:
        safe = assert_public_http_url(url)
    except (UrlSafetyError, ValueError):
        return None
    response = None
    try:
        response = requests.get(
            safe,
            headers={"User-Agent": "ReadyForRobots/1.0 (employer leadership)"},
            timeout=_TIMEOUT,
            allow_redirects=True,
            stream=True,
        )
        if response.status_code >= 400:
            return None
        try:
            assert_public_http_url(response.url)
        except (UrlSafetyError, ValueError):
            return None
        content_type = (response.headers.get("content-type") or "").lower()
        if content_type and "html" not in content_type and "xhtml" not in content_type:
            return None
        requested = (urlparse(url).path or "/").rstrip("/") or "/"
        landed = (urlparse(response.url).path or "/").rstrip("/") or "/"
        if requested not in {"/"} and landed in {"/"}:
            return None
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_content(8192):
            if not chunk:
                continue
            size += len(chunk)
            if size > _MAX_HTML:
                break
            chunks.append(chunk)
        return b"".join(chunks).decode("utf-8", errors="replace")[:_MAX_HTML]
    except requests.RequestException as exc:
        logger.info("leadership fetch failed %s: %s", url, exc)
        return None
    finally:
        if response is not None:
            response.close()


def _looks_like_name(first: str, last: str) -> bool:
    if first in _BAD_NAME or last in _BAD_NAME:
        return False
    return bool(
        re.match(r"^[A-Z][a-z]{1,20}$", first) and re.match(r"^[A-Z][a-z]{1,24}$", last)
    )


def _person(first: str, last: str, title: str, source_url: str) -> Optional[dict[str, Any]]:
    parsed = parse_person_name(f"{first} {last}")
    if parsed:
        first, last = parsed
    else:
        first = (first or "").strip().title()
        last = (last or "").strip().title()
    title = re.sub(r"\s+", " ", (title or "").strip()).strip(" ,;|-")
    if not _looks_like_name(first, last):
        return None
    if not title or not _TITLE.search(title):
        return None
    if parse_person_name(title):
        return None
    if len(title) > 90:
        title = title[:90].rstrip()
    return {
        "name": f"{first} {last}",
        "first_name": first,
        "last_name": last,
        "title": title,
        "source": "leadership_page",
        "source_url": source_url,
        "confidence": 90,
    }


def _json_ld_people(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    for script in soup.find_all("script"):
        stype = str(script.get("type") or "").lower()
        if "ld+json" not in stype:
            continue
        try:
            data = json.loads(script.string or "")
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        for node in _walk_json(data):
            if not isinstance(node, dict):
                continue
            types = node.get("@type") or node.get("type") or ""
            if isinstance(types, list):
                types = " ".join(str(t) for t in types)
            if "person" not in str(types).lower():
                continue
            name = str(node.get("name") or "").strip()
            title = str(node.get("jobTitle") or node.get("title") or "").strip()
            bits = parse_person_name(name)
            if not bits:
                continue
            row = _person(bits[0], bits[1], title, source_url)
            if row:
                people.append(row)
    return people


def _walk_json(data: Any) -> list[Any]:
    out: list[Any] = []
    if isinstance(data, list):
        for item in data:
            out.extend(_walk_json(item))
        return out
    if isinstance(data, dict):
        out.append(data)
        for value in data.values():
            out.extend(_walk_json(value))
    return out


def _card_people(soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    for el in soup.find_all(["article", "li", "figure", "div", "section"]):
        classes = " ".join(el.get("class") or []).lower()
        if not any(
            tok in classes for tok in ("team", "leader", "bio", "staff", "executive", "people", "member")
        ):
            continue
        text = el.get_text("\n", strip=True)
        if not text or len(text) > 500:
            continue
        people.extend(_text_people(text, source_url))
    return people


def _split_name_title(line: str) -> Optional[tuple[tuple[str, str], str]]:
    """Same-line `Name Title`, `Name, Title`, or `Title, Name`. No invented people."""
    raw = re.sub(r"\s+", " ", (line or "").strip())
    if not raw or len(raw) > 160:
        return None
    if "," in raw:
        left, right = [p.strip() for p in raw.split(",", 1)]
        # Name first may be first-middle-last. Title-first leftovers stay two-word
        # so "Harris County Attorney" cannot become a person.
        name = parse_person_name(left, allow_middle=True)
        if name and _TITLE.search(right) and not parse_person_name(right):
            return name, right
        name = parse_person_name(right, allow_middle=False)
        if name and _TITLE.search(left) and not parse_person_name(left):
            return name, left
    title_match = _TITLE.search(raw)
    if not title_match:
        return None
    prefix = raw[: title_match.start()].strip(" ,;-")
    suffix = raw[title_match.end() :].strip(" ,;-")
    if prefix and suffix:
        return None
    leftover = prefix or suffix
    name = parse_person_name(leftover, allow_middle=bool(prefix))
    title = title_match.group(0).strip(" ,;-")
    if name and title and not parse_person_name(title):
        return name, title
    return None


def _text_people(text: str, source_url: str) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in (text or "").splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        title = ""
        name_bits = parse_person_name(line)
        if name_bits:
            if i + 1 < len(lines) and _TITLE.search(lines[i + 1]) and not parse_person_name(lines[i + 1]):
                title = lines[i + 1]
                if i + 2 < len(lines) and _TITLE.search(lines[i + 2]) and len(lines[i + 2]) < 60:
                    if lines[i + 1].lower().endswith("and") or len(lines[i + 1]) < 28:
                        title = f"{lines[i + 1]} {lines[i + 2]}"
        else:
            split = _split_name_title(line)
            if not split:
                continue
            name_bits, title = split
        row = _person(name_bits[0], name_bits[1], title, source_url)
        if row:
            people.append(row)
    return people


def _dedupe_people(people: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for person in people:
        if not isinstance(person, dict):
            continue
        key = str(person.get("name") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(person)
    return out
