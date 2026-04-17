"""
External footprint check for company-like strings (optional).

Used when a name passes local heuristics but looks like a long headline or
scraped sentence: we ask Wikidata search whether top hits read as real
organizations vs films, disambiguation pages, etc.

- Network failures and empty search → ``unknown`` (do not reject; many SMBs
  have no Wikidata entry).
- ``likely_not_org`` only when several top results clearly describe non-org
  entity types.

Optional DNS / HTTPS probe: infer ``{brand}.com`` / ``www.{brand}.com`` from the
first non-generic token. ``reachable`` if DNS resolves for any host, or if DNS
resolves and HTTPS responds (HEAD, then GET). Strict mode (separate env) can
reject when the probe is ``unreachable`` (no DNS for inferred hosts).

Enable with ``COMPANY_NAME_WIKIDATA_VERIFY=1`` (default off so CI and local
dev do not depend on wikidata.org).

Enable DNS/HTTPS with ``COMPANY_NAME_DNS_HTTPS_VERIFY=1``; optional strict
reject with ``COMPANY_NAME_DNS_HTTPS_STRICT=1``.
"""
from __future__ import annotations

import logging
import os
import re
import socket
from typing import Literal
from urllib.parse import quote

import requests

Likelihood = Literal["likely_org", "likely_not_org", "unknown"]
ProbeResult = Literal["reachable", "unreachable", "skipped"]

logger = logging.getLogger(__name__)

# Tokens to skip when inferring a brand slug (try the next word).
_SLUG_SKIP: frozenset[str] = frozenset({
    "the", "a", "an", "and", "or", "of", "for", "in", "on", "at", "to", "by", "as",
    "inc", "llc", "ltd", "corp", "co", "plc", "llp", "lp", "gmbh", "bv", "nv", "ag",
    "sa", "srl", "pty", "pte", "holdings", "holding", "group", "international",
    "new", "our", "your", "all", "some", "many", "meet", "here", "there",
    "why", "how", "what", "when", "where", "this", "that", "these", "those",
    "future", "global", "national", "digital", "smart", "advanced", "modern",
    "top", "best", "key", "major", "leading", "public", "private",
})

_ORG_DESC = re.compile(
    r"(?i)\b("
    r"company|companies|corporation|corporations|business|businesses|"
    r"enterprise|enterprises|manufacturer|manufacturers|multinational|"
    r"conglomerate|holding|holdings|subsidiary|retailer|retailers|"
    r"chain|brand|brands|firm|firms|startup|start-up|"
    r"software company|technology company|tech company|e-commerce|ecommerce"
    r")\b"
)
_NOT_ORG_DESC = re.compile(
    r"(?i)\b("
    r"film|television series|tv series|documentary|novel|album|song|single|"
    r"video game|mathematical concept|asteroid|genus|species of|"
    r"disambiguation|given name|family name|surname|human settlement|"
    r"river in|mountain in|album by|song by|film by|wikimedia list"
    r")\b"
)

def wikidata_verify_enabled() -> bool:
    """Read each call so tests can toggle ``COMPANY_NAME_WIKIDATA_VERIFY``."""
    return os.getenv("COMPANY_NAME_WIKIDATA_VERIFY", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def dns_https_verify_enabled() -> bool:
    return os.getenv("COMPANY_NAME_DNS_HTTPS_VERIFY", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def dns_https_strict_enabled() -> bool:
    """When on, ``unreachable`` probe results reject (only with verify on)."""
    return os.getenv("COMPANY_NAME_DNS_HTTPS_STRICT", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _first_brand_slug(name: str) -> str | None:
    """First word suitable for ``slug.com`` inference, or None."""
    words = re.findall(r"[A-Za-z][A-Za-z&'-]*", name)
    for w in words:
        wl = w.lower().strip("'")
        slug = re.sub(r"[^a-z0-9]", "", wl)
        if len(slug) < 3:
            continue
        if slug in _SLUG_SKIP:
            continue
        return slug
    return None


def infer_brand_domain_hosts(name: str) -> list[str]:
    """
    Hostnames probed for ``name`` (``brand.com`` and ``www.brand.com``).
    Exposed for tests; same logic as :func:`dns_https_probe`.
    """
    slug = _first_brand_slug(name)
    if not slug:
        return []
    return [f"{slug}.com", f"www.{slug}.com"]


def _dns_resolves(host: str, *, timeout: float = 2.0) -> bool:
    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        socket.getaddrinfo(host, 443, 0, socket.SOCK_STREAM)
        return True
    except OSError:
        return False
    finally:
        socket.setdefaulttimeout(old)


def _https_ok(url: str, *, timeout: float = 3.0) -> bool:
    headers = {
        "User-Agent": "ReadyForRobots/1.0 (company name verification)",
        "Accept": "*/*",
    }
    try:
        r = requests.head(
            url, allow_redirects=True, timeout=timeout, headers=headers
        )
        if r.status_code < 500:
            return True
    except requests.RequestException:
        pass
    try:
        r = requests.get(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers=headers,
            stream=True,
        )
        if r.status_code < 500:
            r.close()
            return True
        r.close()
    except requests.RequestException:
        pass
    return False


def dns_https_probe(
    name: str,
    *,
    dns_timeout: float = 2.0,
    http_timeout: float = 3.0,
) -> ProbeResult:
    """
    Infer ``{brand}.com`` / ``www.{brand}.com`` and check DNS, then HTTPS.

    - **reachable**: at least one host resolves via DNS, or HTTPS responds on
      ``https://host/`` (HEAD then GET). DNS alone counts as reachable so
      parked or TLS-misconfigured hosts still pass this gate.
    - **unreachable**: we had hosts to try and none resolved (no DNS footprint).
    - **skipped**: could not infer a brand slug (all stop words / too short).
    """
    hosts = infer_brand_domain_hosts(name)
    if not hosts:
        return "skipped"

    any_dns = False
    for host in hosts:
        if _dns_resolves(host, timeout=dns_timeout):
            any_dns = True
            url = f"https://{host}/"
            if _https_ok(url, timeout=http_timeout):
                return "reachable"
    if any_dns:
        return "reachable"
    return "unreachable"


def needs_wikidata_verification(name: str) -> bool:
    """
    Long or very wordy names that often come from headlines, not letterheads.
    Short brands (``Boston Dynamics``) are skipped to avoid API noise.
    """
    s = name.strip()
    if not s:
        return False
    words = re.findall(r"[A-Za-z][A-Za-z&'-]*", s)
    n_words = len(words)
    if n_words >= 7:
        return True
    if len(s) > 52:
        return True
    if n_words >= 5 and len(s) > 38:
        return True
    return False


def wikidata_entity_likelihood(name: str, *, timeout: float = 2.5) -> Likelihood:
    """
    Query Wikidata entity search; classify whether top hits look like orgs.

    Returns ``unknown`` on HTTP errors, timeouts, empty results, or ambiguous
    descriptions (conservative: do not reject).
    """
    q = name.strip()
    if not q:
        return "unknown"

    url = (
        "https://www.wikidata.org/w/api.php"
        "?action=wbsearchentities"
        f"&search={quote(q)}"
        "&language=en"
        "&format=json"
        "&limit=8"
    )
    headers = {
        "User-Agent": "ReadyForRobots/1.0 (company name verification)",
        "Accept": "application/json",
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        logger.debug("Wikidata search failed for %r: %s", q[:80], e)
        return "unknown"

    hits = data.get("search") or []
    if not hits:
        return "unknown"

    org_hits = 0
    not_org_hits = 0
    described = 0
    for h in hits[:5]:
        desc = (h.get("description") or "").strip()
        if not desc:
            continue
        described += 1
        if _ORG_DESC.search(desc):
            org_hits += 1
        elif _NOT_ORG_DESC.search(desc):
            not_org_hits += 1

    if org_hits >= 1:
        return "likely_org"
    # Several described hits and all look explicitly non-org → reject
    if described >= 2 and not_org_hits >= 2 and org_hits == 0:
        return "likely_not_org"
    return "unknown"
