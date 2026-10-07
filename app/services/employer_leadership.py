"""Find leadership/team pages on an employer site and extract named people.

Used by the decision-maker extract DAG. FIND does not call this.
Names are read from the page. None are invented. Hunter looks up emails later.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.services.robot_job_extract import _is_board_host

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
    "/about",
    "/about-us",
)

_HREF_HINT = re.compile(
    r"leadership|executive[-_/ ]?team|our[-_/ ]?team|(?:^|/)team(?:/|$)|"
    r"our[-_/ ]?people|management[-_/ ]?team|about[-_/ ]?us|about/team",
    re.I,
)
_SKIP_HREF = re.compile(
    r"career|jobs?(?:/|-)|blog|news|press|privacy|login|signin|investor|"
    r"product|shop|cart|support|cookie|legal|terms",
    re.I,
)
_NAME = re.compile(r"\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,24})\b")
_TITLE = re.compile(
    r"(?i)\b("
    r"(?:(?:pharmacy|warehouse|plant|facilities|operations|manufacturing|"
    r"fulfillment|environmental|evs|support|materials?|culinary|kitchen|"
    r"shipping|receiving|site)\s+){0,3}"
    r"(?:executive\s+)?(?:vice\s+)?"
    r"(?:president|director|manager|head|chief|supervisor|vp)"
    r"(?:\s+(?:of\s+(?:the\s+)?)?[A-Za-z][A-Za-z&/ ]{1,40})?"
    r")"
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
    }
)
_MAX_PAGES = 5
_MAX_ATTEMPTS = 10
_MAX_HTML = 220_000
_TIMEOUT = 6.0


def origin_for_domain(domain: Optional[str]) -> Optional[str]:
    host = (domain or "").strip().lower().removeprefix("www.")
    if not host or "." not in host or _is_board_host(host):
        return None
    if "/" in host or " " in host:
        return None
    if any(host == d or host.endswith("." + d) for d in _ATS_HOSTS):
        return None
    if host.split(".", 1)[0] in _CAREER_HOST_LABELS:
        return None
    return f"https://{host}"


def discover_leadership_urls(homepage_html: str, origin: str) -> list[str]:
    """Same-host links whose path or label is leadership/team/about."""
    soup = BeautifulSoup(homepage_html or "", "html.parser")
    origin = origin.rstrip("/")
    host = (urlparse(origin).hostname or "").lower().removeprefix("www.")
    found: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(origin + "/", str(anchor.get("href") or "").strip())
        parsed = urlparse(href)
        link_host = (parsed.hostname or "").lower().removeprefix("www.")
        if not link_host or link_host != host:
            continue
        path = parsed.path or "/"
        label = anchor.get_text(" ", strip=True)
        blob = f"{path} {label}"
        if _SKIP_HREF.search(path) or _SKIP_HREF.search(label):
            continue
        if not _HREF_HINT.search(blob):
            continue
        clean = f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        found.append(clean)
    return found


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
    """GET the employer origin plus leadership/team paths. Empty list on miss."""
    origin = origin_for_domain(domain)
    if not origin:
        return []
    getter = get_html or _http_get
    pages: list[dict[str, Any]] = []
    seen: set[str] = set()
    attempts = 0

    def _add(url: str) -> Optional[str]:
        nonlocal attempts
        key = url.rstrip("/").lower()
        if key in seen or len(pages) >= _MAX_PAGES or attempts >= _MAX_ATTEMPTS:
            return None
        seen.add(key)
        attempts += 1
        html = getter(url)
        if not html:
            return None
        pages.append({"url": url, "html": html})
        return html

    home = _add(origin)
    if home:
        for href in discover_leadership_urls(home, origin):
            if len(pages) >= _MAX_PAGES or attempts >= _MAX_ATTEMPTS:
                break
            _add(href)
    for path in LEADERSHIP_PATHS:
        if len(pages) >= _MAX_PAGES or attempts >= _MAX_ATTEMPTS:
            break
        _add(origin + path)
    if pages:
        logger.info(
            "leadership pages for %s (%s): %s",
            employer or domain,
            domain,
            [p["url"] for p in pages],
        )
    return pages


def _http_get(url: str) -> Optional[str]:
    from app.services.robot_url_safety import UrlSafetyError, assert_public_http_url

    try:
        safe = assert_public_http_url(url)
    except (UrlSafetyError, ValueError) as exc:
        logger.info("leadership URL rejected (SSRF check): %s: %s", url, exc)
        return None
    try:
        response = requests.get(
            safe,
            headers={"User-Agent": "ReadyForRobots/1.0 (employer leadership)"},
            timeout=_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        logger.info("leadership fetch failed %s: %s", url, exc)
        return None
    if response.status_code >= 400:
        return None
    content_type = (response.headers.get("content-type") or "").lower()
    if content_type and "html" not in content_type and "xhtml" not in content_type:
        return None
    return response.text[:_MAX_HTML]


def _looks_like_name(first: str, last: str) -> bool:
    if first in _BAD_NAME or last in _BAD_NAME:
        return False
    return bool(
        re.match(r"^[A-Z][a-z]{1,20}$", first) and re.match(r"^[A-Z][a-z]{1,24}$", last)
    )


def _person(first: str, last: str, title: str, source_url: str) -> Optional[dict[str, Any]]:
    first = (first or "").strip().title()
    last = (last or "").strip().title()
    title = re.sub(r"\s+", " ", (title or "").strip()).strip(" ,;|-")
    if not _looks_like_name(first, last):
        return None
    if not title or not _TITLE.search(title):
        return None
    if len(title) > 80:
        title = title[:80].rstrip()
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
            bits = name.split()
            if len(bits) < 2:
                continue
            row = _person(bits[0], bits[-1], title, source_url)
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


def _text_people(text: str, source_url: str) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    blob = re.sub(r"[ \t]+", " ", text or "")
    for line in blob.splitlines():
        line = line.strip()
        if not line:
            continue
        if "," in line:
            left, right = [p.strip() for p in line.split(",", 1)]
            name_match = _NAME.search(left)
            if name_match and _TITLE.search(right):
                row = _person(name_match.group(1), name_match.group(2), right, source_url)
                if row:
                    people.append(row)
                    continue
            name_match = _NAME.search(right)
            if name_match and _TITLE.search(left):
                row = _person(name_match.group(1), name_match.group(2), left, source_url)
                if row:
                    people.append(row)
                    continue
        name_match = _NAME.search(line)
        title_match = _TITLE.search(line)
        if name_match and title_match:
            row = _person(name_match.group(1), name_match.group(2), title_match.group(1), source_url)
            if row:
                people.append(row)
    lines = [ln.strip() for ln in blob.splitlines() if ln.strip()]
    for i, line in enumerate(lines[:-1]):
        name_match = _NAME.fullmatch(line)
        title_match = _TITLE.search(lines[i + 1])
        if name_match and title_match and len(lines[i + 1]) < 80:
            row = _person(name_match.group(1), name_match.group(2), title_match.group(1), source_url)
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
