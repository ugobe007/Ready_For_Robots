"""Safe page fetch for Understanding v1."""
from __future__ import annotations

import io
import re
import ssl
import threading
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

from app.services.robot_url_safety import assert_public_http_url

# Per-page defaults. The source pack also caps these to remaining deadline so a
# hung OEM page cannot add another 12s after the budget is already spent.
DEFAULT_PAGE_TIMEOUT: tuple[float, float] = (2.5, 6.0)
DEFAULT_TEXT_TIMEOUT: tuple[float, float] = (2.0, 4.0)

_tls = threading.local()

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ReadyForRobots-Understanding/1.0; "
        "+https://readyforrobots.com)"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/pdf;"
        "q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.8",
}


@dataclass
class FetchedPage:
    url: str
    final_url: str
    status_code: int
    title: Optional[str]
    text: str
    html: str
    links: list[tuple[str, str]]  # (url, anchor_text)
    fetch_degraded: bool = False
    fetch_notes: list[str] = field(default_factory=list)
    content_type: str = "text/html"


class _TLSFlexAdapter(HTTPAdapter):
    """Retry-friendly adapter for hosts with brittle TLS stacks."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        # Prefer modern TLS but allow renegotiation quirks without weakening
        # identity rules — used only after a first standard request fails.
        try:
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        except Exception:
            pass
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def timeout_for_deadline(
    deadline_monotonic: float | None,
    *,
    default: tuple[float, float] = DEFAULT_PAGE_TIMEOUT,
    min_total: float = 0.4,
) -> tuple[float, float] | None:
    """Connect/read timeouts that fit remaining deadline, or None if too late."""
    connect, read = default
    if deadline_monotonic is None:
        return (connect, read)
    left = deadline_monotonic - time.monotonic()
    if left < min_total:
        return None
    connect = min(connect, max(0.3, left * 0.3))
    read = min(read, max(0.3, left - connect))
    if connect + read < min_total:
        return None
    return (connect, read)


def fetch_page(url: str, *, timeout: tuple[float, float] = DEFAULT_PAGE_TIMEOUT) -> FetchedPage:
    safe = assert_public_http_url(url)
    notes: list[str] = []
    degraded = False
    try:
        resp = _get(safe, timeout=timeout)
    except requests.exceptions.SSLError as exc:
        # Soft-fail TLS: do not redefine company via a different host.
        # Caller keeps the submitted URL identity; mark acquisition degraded.
        degraded = True
        notes.append(f"TLS/fetch degraded: {type(exc).__name__}")
        return FetchedPage(
            url=safe,
            final_url=safe,
            status_code=0,
            title=None,
            text="",
            html="",
            links=[],
            fetch_degraded=True,
            fetch_notes=notes,
            content_type="application/octet-stream",
        )
    except requests.RequestException as exc:
        degraded = True
        notes.append(f"Fetch degraded: {type(exc).__name__}")
        return FetchedPage(
            url=safe,
            final_url=safe,
            status_code=0,
            title=None,
            text="",
            html="",
            links=[],
            fetch_degraded=True,
            fetch_notes=notes,
            content_type="application/octet-stream",
        )

    ctype = (resp.headers.get("Content-Type") or "").lower()
    final = resp.url or safe
    raw = resp.content or b""

    if "pdf" in ctype or final.lower().endswith(".pdf") or raw[:4] == b"%PDF":
        title, text = _pdf_text(raw, final)
        return FetchedPage(
            url=safe,
            final_url=final,
            status_code=resp.status_code,
            title=title,
            text=text,
            html="",
            links=[],
            fetch_degraded=degraded,
            fetch_notes=notes,
            content_type="application/pdf",
        )

    html = resp.text or ""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    text = _html_to_text(soup)

    host = (urlparse(resp.url).hostname or "").lower()
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        full = urljoin(resp.url, a["href"])
        parsed = urlparse(full)
        if (parsed.hostname or "").lower() != host:
            continue
        key = full.split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        anchor = re.sub(r"\s+", " ", (a.get_text() or "").strip())[:120]
        links.append((key, anchor))

    return FetchedPage(
        url=safe,
        final_url=resp.url,
        status_code=resp.status_code,
        title=title,
        text=text,
        html=html,
        links=links,
        fetch_degraded=degraded,
        fetch_notes=notes,
        content_type="text/html",
    )


def fetch_text(url: str, *, timeout: tuple[float, float] = DEFAULT_TEXT_TIMEOUT) -> tuple[int, str]:
    """Fetch raw response text (e.g. an XML sitemap) — fail-open.

    Returns (status_code, text). On any error returns (0, ""). Goes through the
    same SSRF guard as fetch_page; does not parse HTML. Used only for lightweight
    sitemap discovery, so it never raises into the pipeline.
    """
    try:
        safe = assert_public_http_url(url)
        resp = _get(safe, timeout=timeout)
        ctype = (resp.headers.get("Content-Type") or "").lower()
        # Guard against huge/binary payloads sneaking in as "sitemaps".
        if "html" in ctype and "xml" not in ctype:
            # Some hosts serve a soft-404 HTML page for missing sitemaps.
            return resp.status_code, ""
        text = resp.text or ""
        return resp.status_code, text[:2_000_000]
    except Exception:
        return 0, ""


def _session() -> requests.Session:
    """Thread-local pooled session so parallel source fetches reuse TLS."""
    sess = getattr(_tls, "session", None)
    if sess is None:
        sess = requests.Session()
        adapter = HTTPAdapter(pool_connections=8, pool_maxsize=8, max_retries=0)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)
        sess.headers.update(_HEADERS)
        sess.max_redirects = 5
        _tls.session = sess
    return sess


def _get(url: str, *, timeout: tuple[float, float]) -> requests.Response:
    session = _session()
    try:
        return session.get(url, timeout=timeout, allow_redirects=True)
    except requests.exceptions.SSLError:
        # One flexible TLS retry on same URL — never rewrite to acquirer host.
        # Cap retry so a brittle handshake cannot double the page wait.
        retry = (min(2.0, timeout[0]), min(4.0, timeout[1]))
        if retry[0] + retry[1] < 1.5:
            raise
        flex = requests.Session()
        flex.mount("https://", _TLSFlexAdapter())
        flex.headers.update(_HEADERS)
        flex.max_redirects = 5
        return flex.get(url, timeout=retry, allow_redirects=True)


def _html_to_text(soup: BeautifulSoup) -> str:
    """Preserve table/spec density better than flat get_text collapse."""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Normalize tables: join cells with separators so "Payload 1900 kg" survives
    for table in soup.find_all("table"):
        rows_out: list[str] = []
        for tr in table.find_all("tr"):
            cells = [
                re.sub(r"\s+", " ", c.get_text(" ", strip=True))
                for c in tr.find_all(["th", "td"])
            ]
            cells = [c for c in cells if c]
            if cells:
                rows_out.append(" | ".join(cells))
        if rows_out:
            table.replace_with(soup.new_string(" " + " ; ".join(rows_out) + " "))

    # Definition lists often hold specs
    for dl in soup.find_all("dl"):
        parts: list[str] = []
        for dt in dl.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            dt_t = re.sub(r"\s+", " ", dt.get_text(" ", strip=True))
            dd_t = re.sub(r"\s+", " ", dd.get_text(" ", strip=True)) if dd else ""
            if dt_t and dd_t:
                parts.append(f"{dt_t}: {dd_t}")
        if parts:
            dl.replace_with(soup.new_string(" " + " ; ".join(parts) + " "))

    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _pdf_text(raw: bytes, url: str) -> tuple[Optional[str], str]:
    try:
        from pypdf import PdfReader
    except Exception:
        return None, ""
    try:
        reader = PdfReader(io.BytesIO(raw))
        chunks: list[str] = []
        for page in reader.pages[:12]:
            try:
                chunks.append(page.extract_text() or "")
            except Exception:
                continue
        text = re.sub(r"\s+", " ", " ".join(chunks)).strip()
        title = None
        meta = getattr(reader, "metadata", None)
        if meta and getattr(meta, "title", None):
            title = str(meta.title).strip() or None
        if not title:
            title = urlparse(url).path.rsplit("/", 1)[-1] or None
        return title, text[:50000]
    except Exception:
        return None, ""
