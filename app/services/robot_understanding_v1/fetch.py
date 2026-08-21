"""Safe page fetch for Understanding v1."""
from __future__ import annotations

import io
import json
import re
import ssl
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional
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
ARCHIVE_PAGE_TIMEOUT: tuple[float, float] = (2.0, 8.0)

_CHALLENGE_TITLE = re.compile(
    r"(vercel security checkpoint|just a moment(\.\.\.)?|attention required|"
    r"enable javascript to continue|checking your browser|"
    r"please wait( while we verify)?|cf-browser-verification|"
    r"un instant|un momento)",
    re.I,
)
_ARCHIVE_WRAP = re.compile(
    r"/web/\d{8,14}(?:id_|if_)?/(https?://.+)$",
    re.I,
)

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
    # Product photos harvested from img / og:image / Next.js JSON (url, alt).
    image_alts: list[tuple[str, str]] = field(default_factory=list)


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


def unwrap_archive_url(url: str) -> str:
    """Strip Wayback/archive.org wrappers so identity uses the manufacturer host."""
    raw = (url or "").strip()
    match = _ARCHIVE_WRAP.search(raw.replace("&amp;", "&"))
    if match:
        return match.group(1)
    return raw


def is_bot_challenge(
    *,
    status_code: int,
    title: str | None,
    html: str,
    headers: dict[str, str] | None = None,
) -> bool:
    """True when the response is a CDN/WAF interstitial, not the OEM page."""
    if status_code in {401, 403, 429, 503}:
        return True
    hdrs = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    mitigated = hdrs.get("x-vercel-mitigated") or hdrs.get("cf-mitigated") or ""
    if mitigated.lower() in {"challenge", "error"}:
        return True
    blob = f"{title or ''} {(html or '')[:4000]}"
    return bool(_CHALLENGE_TITLE.search(blob))


def _hosts_match(a: str | None, b: str | None) -> bool:
    def norm(host: str | None) -> str:
        h = (host or "").lower()
        return h[4:] if h.startswith("www.") else h

    na, nb = norm(a), norm(b)
    return bool(na) and na == nb


def _archive_fetch_url(url: str) -> str:
    return "https://web.archive.org/web/" + url


def _empty_page(url: str, *, notes: list[str], status_code: int = 0) -> FetchedPage:
    return FetchedPage(
        url=url,
        final_url=url,
        status_code=status_code,
        title=None,
        text="",
        html="",
        links=[],
        fetch_degraded=True,
        fetch_notes=notes,
        content_type="application/octet-stream",
    )


def fetch_page(
    url: str,
    *,
    timeout: tuple[float, float] = DEFAULT_PAGE_TIMEOUT,
    allow_archive: bool = True,
) -> FetchedPage:
    safe = assert_public_http_url(url)
    notes: list[str] = []
    try:
        resp = _get(safe, timeout=timeout)
    except requests.exceptions.SSLError as exc:
        notes.append(f"TLS/fetch degraded: {type(exc).__name__}")
        return _empty_page(safe, notes=notes)
    except requests.RequestException as exc:
        notes.append(f"Fetch degraded: {type(exc).__name__}")
        return _empty_page(safe, notes=notes)

    page = _page_from_response(safe, resp, notes=notes)
    if page.fetch_degraded and not (page.text or "").strip() and allow_archive:
        archived = _fetch_archive_copy(safe, notes, timeout=timeout)
        if archived:
            return archived
    return page


def _fetch_archive_copy(
    live_url: str,
    notes: list[str],
    timeout: tuple[float, float] = ARCHIVE_PAGE_TIMEOUT,
) -> FetchedPage | None:
    """Best-effort Internet Archive copy when the live OEM host challenges bots."""
    if "web.archive.org" in (urlparse(live_url).hostname or "").lower():
        return None
    archive = _archive_fetch_url(live_url)
    try:
        assert_public_http_url(archive)
        resp = _get(archive, timeout=timeout)
    except Exception as exc:
        notes.append(f"Archive fallback failed: {type(exc).__name__}")
        return None
    page = _page_from_response(
        live_url,
        resp,
        notes=notes,
        canonical_url=live_url,
        unwrap_archive=True,
    )
    if is_bot_challenge(
        status_code=page.status_code,
        title=page.title,
        html=page.html,
    ) or not (page.text or page.html):
        notes.append("Archive fallback was also a challenge or empty")
        return None
    page.fetch_notes.append("Live manufacturer page blocked; used Internet Archive copy")
    page.fetch_degraded = False
    return page


def _page_from_response(
    requested: str,
    resp: requests.Response,
    *,
    notes: list[str],
    canonical_url: str | None = None,
    unwrap_archive: bool = False,
) -> FetchedPage:
    ctype = (resp.headers.get("Content-Type") or "").lower()
    final = canonical_url or unwrap_archive_url(resp.url or requested) or requested
    raw = resp.content or b""
    headers = {str(k): str(v) for k, v in resp.headers.items()}

    if "pdf" in ctype or final.lower().endswith(".pdf") or raw[:4] == b"%PDF":
        title, text = _pdf_text(raw, final)
        return FetchedPage(
            url=requested,
            final_url=final,
            status_code=resp.status_code,
            title=title,
            text=text,
            html="",
            links=[],
            fetch_degraded=False,
            fetch_notes=notes,
            content_type="application/pdf",
        )

    html = resp.text or ""
    if unwrap_archive:
        html = _ARCHIVE_WRAP.sub(lambda m: m.group(1), html)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    if is_bot_challenge(
        status_code=resp.status_code,
        title=title,
        html=html,
        headers=headers,
    ):
        notes.append(
            f"Bot challenge from manufacturer host (HTTP {resp.status_code})"
        )
        return FetchedPage(
            url=requested,
            final_url=canonical_url or requested,
            status_code=resp.status_code,
            title=title,
            text="",
            html="",
            links=[],
            fetch_degraded=True,
            fetch_notes=notes,
            content_type="text/html",
        )

    page_url = canonical_url or unwrap_archive_url(resp.url or requested) or requested
    images = _harvest_page_images(soup, page_url)
    text = _html_to_text(soup, page_url=page_url)
    host = (urlparse(page_url).hostname or "").lower()
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        raw_href = unwrap_archive_url(a["href"])
        if raw_href.startswith(("http://", "https://")):
            full = raw_href
        else:
            full = urljoin(page_url, raw_href)
        parsed = urlparse(full)
        if not _hosts_match(parsed.hostname, host):
            continue
        key = full.split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        anchor = re.sub(r"\s+", " ", (a.get_text() or "").strip())[:120]
        links.append((key, anchor))

    return FetchedPage(
        url=requested,
        final_url=page_url,
        status_code=resp.status_code,
        title=title,
        text=text,
        html=html,
        links=links,
        fetch_degraded=False,
        fetch_notes=list(notes),
        content_type="text/html",
        image_alts=images,
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


_JSON_SCRIPT_TYPES = frozenset(
    {
        "application/json",
        "application/ld+json",
        "application/ld+json; charset=utf-8",
    }
)
_JSON_KEEP_TERMS = re.compile(
    r"\b(humanoid|quadruped|bipedal|payload|autonomous|lidar|slam|"
    r"manipulator|cobot|amr|dexterous|bimanual|gripper|android)\b",
    re.I,
)
_EMBEDDED_JSON_CAP = 20_000
_IMAGE_FILE = re.compile(r"\.(png|jpe?g|webp|gif|avif)(\?|$)", re.I)
_SKIP_IMAGE = re.compile(
    r"(favicon|sprite|pixel|1x1|tracking|logo[-_]?mark|social[-_]?icon)",
    re.I,
)


def _keep_json_string(value: str) -> bool:
    """Keep prose / capability language; drop URLs, hashes, asset paths."""
    s = (value or "").strip()
    if not (8 <= len(s) <= 800):
        return False
    if s.startswith(("http://", "https://", "/", "data:")):
        return False
    if re.fullmatch(r"[0-9a-fA-F-]{20,}", s):
        return False
    if re.search(r"\.(png|jpe?g|gif|webp|svg|mp4|webm)(\?|$)", s, re.I):
        return False
    if " " in s or _JSON_KEEP_TERMS.search(s):
        return True
    return False


def _walk_json_strings(obj: Any, out: list[str], *, budget: int) -> None:
    if len(out) >= budget:
        return
    if isinstance(obj, str):
        if _keep_json_string(obj):
            out.append(re.sub(r"\s+", " ", obj.strip()))
        return
    if isinstance(obj, dict):
        # Keep sibling strings together so "NEO" stays near "humanoid robot".
        local: list[str] = []
        nested: list[Any] = []
        for v in obj.values():
            if isinstance(v, str):
                if _keep_json_string(v):
                    local.append(re.sub(r"\s+", " ", v.strip()))
            else:
                nested.append(v)
        if local:
            out.append(" ".join(local))
        for v in nested:
            _walk_json_strings(v, out, budget=budget)
        return
    if isinstance(obj, list):
        for v in obj:
            _walk_json_strings(v, out, budget=budget)


def _embedded_json_text(soup: BeautifulSoup) -> str:
    """Manufacturer claims often live in Next.js / JSON-LD, not visible HTML.

    Stripping every <script> before reading them is why JS product pages
    (1X NEO) produced payload/IP facts and UNKNOWN class/mobility/autonomy.
    This is source collection, not a v1 extractor retune.
    """
    chunks: list[str] = []
    for script in soup.find_all("script"):
        stype = (script.get("type") or "").strip().lower()
        sid = (script.get("id") or "").strip()
        if sid != "__NEXT_DATA__" and stype not in _JSON_SCRIPT_TYPES:
            continue
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw or raw[0] not in "{[":
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        _walk_json_strings(data, chunks, budget=80)
        if sum(len(c) for c in chunks) >= _EMBEDDED_JSON_CAP:
            break
    if not chunks:
        return ""
    # Preserve order, drop exact duplicates.
    seen: set[str] = set()
    uniq: list[str] = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    blob = " ".join(uniq)
    return blob[:_EMBEDDED_JSON_CAP]


def _looks_like_image_url(value: str) -> bool:
    s = (value or "").strip()
    if len(s) < 12 or len(s) > 2000:
        return False
    if _SKIP_IMAGE.search(s):
        return False
    if s.startswith("data:"):
        return False
    if s.startswith(("http://", "https://", "/", "//")) and _IMAGE_FILE.search(s.split("?")[0]):
        return True
    return False


def _walk_json_images(obj: Any, out: list[str], *, budget: int) -> None:
    if len(out) >= budget:
        return
    if isinstance(obj, str):
        if _looks_like_image_url(obj):
            out.append(obj.strip())
        return
    if isinstance(obj, dict):
        for v in obj.values():
            _walk_json_images(v, out, budget=budget)
        return
    if isinstance(obj, list):
        for v in obj:
            _walk_json_images(v, out, budget=budget)


def _harvest_page_images(soup: BeautifulSoup, page_url: str) -> list[tuple[str, str]]:
    """Collect product photos as visual sources (url, alt/caption)."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(raw: str, alt: str) -> None:
        href = (raw or "").strip()
        if not href or href.startswith("data:"):
            return
        full = urljoin(page_url or "", href)
        key = full.split("#")[0]
        if not key or key in seen:
            return
        if _SKIP_IMAGE.search(key):
            return
        seen.add(key)
        found.append((key, re.sub(r"\s+", " ", (alt or "").strip())[:160]))

    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").strip().lower()
        if prop in {"og:image", "og:image:url", "twitter:image", "twitter:image:src"}:
            add(meta.get("content") or "", "Open Graph product photo")
    for img in soup.find_all("img"):
        alt = img.get("alt") or img.get("title") or ""
        src = img.get("src") or img.get("data-src") or ""
        add(src, alt)
        srcset = img.get("srcset") or ""
        if srcset:
            first = srcset.split(",")[0].strip().split(" ")[0]
            add(first, alt)
    for script in soup.find_all("script"):
        stype = (script.get("type") or "").strip().lower()
        sid = (script.get("id") or "").strip()
        if sid != "__NEXT_DATA__" and stype not in _JSON_SCRIPT_TYPES:
            continue
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw or raw[0] not in "{[":
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        urls: list[str] = []
        _walk_json_images(data, urls, budget=24)
        for u in urls:
            add(u, "")
    return found[:24]


def _with_photo_alts(text: str, images: list[tuple[str, str]]) -> str:
    alts = [alt for _, alt in images if alt and alt.lower() not in {"open graph product photo"}]
    if not alts:
        return text
    blob = " ".join(f"Product photo: {alt}." for alt in alts[:12])
    return f"{text} {blob}".strip() if text else blob


def _html_to_text(soup: BeautifulSoup, page_url: str = "") -> str:
    """Preserve table/spec density better than flat get_text collapse."""
    images = _harvest_page_images(soup, page_url)
    embedded = _embedded_json_text(soup)
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
    text = re.sub(r"\s+", " ", text).strip()
    if embedded:
        text = f"{text} {embedded}".strip() if text else embedded
    return _with_photo_alts(text, images)


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
