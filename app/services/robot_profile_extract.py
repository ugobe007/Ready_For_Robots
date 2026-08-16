"""Conservative product-page fetch + claim extraction (no invented values)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import unescape
from typing import Any
from urllib.parse import urlparse

from app.services.robot_url_safety import UrlSafetyError, assert_public_http_url
from app.domain.v1_coverage import SUPPORTED_V1_CATEGORIES

SUPPORTED_CATEGORIES = set(SUPPORTED_V1_CATEGORIES)

CATEGORY_PATTERNS = (
    ("autonomous_forklift", re.compile(r"\b(autonomous\s+forklift|self[- ]driving\s+forklift|driverless\s+forklift)\b", re.I)),
    ("amr", re.compile(r"\b(amr|autonomous\s+mobile\s+robot)\b", re.I)),
    ("autonomous_tugger", re.compile(r"\b(autonomous\s+tugger|tugger\s+amr|autonomous\s+tow)\b", re.I)),
    ("material_movement", re.compile(r"\b(material\s+handling\s+robot|pallet\s+(?:mover|transport)|goods[- ]to[- ]person)\b", re.I)),
    ("humanoid", re.compile(r"\b(humanoid|bipedal\s+robot|wheeled\s+humanoid)\b", re.I)),
)

SPEC_PATTERNS = {
    "payload_max_kg": [
        re.compile(r"(?:payload|load\s+capacity|max(?:imum)?\s+load)[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)\b", re.I),
        re.compile(r"(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)\s*(?:payload|load\s+capacity)\b", re.I),
        re.compile(r"(?:payload|load\s+capacity)[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds)\b", re.I),
    ],
    "lift_height_max_m": [
        re.compile(r"(?:lift(?:ing)?\s+height|max(?:imum)?\s+lift)[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?)\b", re.I),
        re.compile(r"(?:lift(?:ing)?\s+height|max(?:imum)?\s+lift)[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:mm)\b", re.I),
        re.compile(r"(?:lift(?:ing)?\s+height|max(?:imum)?\s+lift)[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:ft|feet)\b", re.I),
    ],
    "speed_mps": [
        re.compile(r"(?:max(?:imum)?\s+)?speed[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:m/?s|meters?\s+per\s+second)\b", re.I),
        re.compile(r"(?:max(?:imum)?\s+)?speed[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:km/?h|kph)\b", re.I),
    ],
    "runtime_hours": [
        re.compile(r"(?:runtime|run\s+time|operating\s+time|battery\s+life)[^\d]{0,40}(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hours?)\b", re.I),
    ],
}

WORK_ENVELOPE_PATTERNS = (
    ("acquire_pallet", re.compile(r"\b(pick(?:s|ing)?\s+up\s+pallets?|acquire\s+pallets?|pallet\s+pickup)\b", re.I)),
    ("move_pallet", re.compile(r"\b(transport(?:s|ing)?\s+pallets?|move(?:s|ing)?\s+pallets?|pallet\s+transport)\b", re.I)),
    ("floor_placement", re.compile(r"\b(floor\s+placement|place(?:s|ing)?\s+on\s+(?:the\s+)?floor|ground[- ]level\s+drop)\b", re.I)),
    ("rack_placement", re.compile(r"\b(rack\s+placement|putaway|places?\s+(?:into\s+)?racks?)\b", re.I)),
    ("trailer_entry", re.compile(r"\b(trailer\s+entry|enter(?:s|ing)?\s+trailers?|truck\s+loading)\b", re.I)),
    ("tote_case_handling", re.compile(r"\b(tote(?:s)?|carton(?:s)?|case(?:s)?)\b.{0,40}\b(handl|mov|pick|transport|manipulat)", re.I)),
    ("line_side_replenishment", re.compile(r"\b(line[- ]side|milk[- ]run|replenish(?:ment)?|kitting)\b", re.I)),
)


@dataclass
class ExtractedClaim:
    field_path: str
    value: Any
    truth_state: str
    confidence: float
    excerpt: str | None
    unit: str | None = None


@dataclass
class ExtractionResult:
    manufacturer: str | None = None
    model: str | None = None
    category: str | None = None
    category_supported: bool = False
    page_title: str | None = None
    claims: list[ExtractedClaim] = field(default_factory=list)
    work_envelope: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    content_hash: str | None = None
    fetched_at: str | None = None
    source_url: str | None = None
    text_sample: str = ""


def fetch_product_page(url: str, *, timeout: float = 12.0, fetcher=None) -> dict[str, Any]:
    """Fetch HTML for a public product URL. `fetcher` injectable for tests."""
    safe_url = assert_public_http_url(url)
    if fetcher is not None:
        body, final_url = fetcher(safe_url)
        return {
            "url": final_url or safe_url,
            "html": body,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    try:
        import urllib.request

        req = urllib.request.Request(
            safe_url,
            headers={
                "User-Agent": "ReadyForRobotsBot/1.0 (+https://readyforrobots.com)",
                "Accept": "text/html,application/xhtml+xml",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - SSRF gated above
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read(2_000_000)
            html = raw.decode(charset, errors="replace")
            return {
                "url": resp.geturl() or safe_url,
                "html": html,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
    except UrlSafetyError:
        raise
    except Exception as exc:  # network / HTTP errors
        raise RuntimeError(f"Failed to fetch product page: {exc}") from exc


def extract_robot_profile(
    *,
    html: str | None = None,
    description: str | None = None,
    source_url: str | None = None,
    fetched_at: str | None = None,
) -> ExtractionResult:
    """Extract only evidence-backed fields; unknowns stay unknown (not false)."""
    text_parts: list[str] = []
    title = None
    if html:
        title = _extract_title(html)
        text_parts.append(_html_to_text(html))
    if description:
        text_parts.append(description)
    text = "\n".join(p for p in text_parts if p).strip()
    # Understanding research needs deeper pages; keep a generous sample.
    sample_limit = 12000
    result = ExtractionResult(
        page_title=title,
        source_url=source_url,
        fetched_at=fetched_at or datetime.now(timezone.utc).isoformat(),
        text_sample=text[:sample_limit],
        content_hash=hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest() if text else None,
    )
    if not text:
        result.warnings.append("No extractable product text")
        return result

    host = urlparse(source_url or "").hostname or ""
    result.manufacturer = _guess_manufacturer(host, text, title)
    result.model = _guess_model(title, text)
    category, supported = _detect_category(text)
    result.category = category
    result.category_supported = supported

    if result.manufacturer:
        result.claims.append(
            ExtractedClaim(
                field_path="manufacturer",
                value=result.manufacturer,
                truth_state="inferred",
                confidence=0.55 if host else 0.4,
                excerpt=_excerpt_for(text, result.manufacturer),
            )
        )
    else:
        result.claims.append(_unknown("manufacturer"))

    if result.model:
        result.claims.append(
            ExtractedClaim(
                field_path="model",
                value=result.model,
                truth_state="observed" if title and result.model in (title or "") else "inferred",
                confidence=0.7 if title else 0.45,
                excerpt=_excerpt_for(text, result.model),
            )
        )
    else:
        result.claims.append(_unknown("model"))

    if category:
        result.claims.append(
            ExtractedClaim(
                field_path="category",
                value=category,
                truth_state="observed",
                confidence=0.8 if supported else 0.5,
                excerpt=_excerpt_for(text, category.replace("_", " ")),
            )
        )
    else:
        result.claims.append(_unknown("category"))

    for field_path, patterns in SPEC_PATTERNS.items():
        claim = _extract_numeric_spec(field_path, patterns, text)
        result.claims.append(claim)

    for key, pattern in WORK_ENVELOPE_PATTERNS:
        match = pattern.search(text)
        if match:
            result.work_envelope.append(
                {
                    "key": key,
                    "label": key.replace("_", " "),
                    "status": "supported",
                    "truth_state": "observed",
                    "confidence": 0.75,
                    "excerpt": match.group(0)[:240],
                }
            )
        else:
            result.work_envelope.append(
                {
                    "key": key,
                    "label": key.replace("_", " "),
                    "status": "unknown",
                    "truth_state": "unknown",
                    "confidence": 0.0,
                    "excerpt": None,
                }
            )

    # Environment / navigation — only mark when language is present.
    for field_path, pattern in (
        ("environment", re.compile(r"\b(indoor|outdoor|mixed\s+traffic|human[- ]shared)\b", re.I)),
        ("navigation", re.compile(r"\b(lidar|slam|natural\s+feature\s+navigation|contour\s+navigation)\b", re.I)),
        ("human_interaction", re.compile(r"\b(collaborative|human[- ]robot|pedestrian|shared\s+aisle)\b", re.I)),
    ):
        match = pattern.search(text)
        if match:
            result.claims.append(
                ExtractedClaim(
                    field_path=field_path,
                    value=match.group(1).lower(),
                    truth_state="observed",
                    confidence=0.7,
                    excerpt=match.group(0)[:240],
                )
            )
        else:
            result.claims.append(_unknown(field_path))

    return result


def _unknown(field_path: str) -> ExtractedClaim:
    return ExtractedClaim(
        field_path=field_path,
        value=None,
        truth_state="unknown",
        confidence=0.0,
        excerpt=None,
    )


def _extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if not match:
        og = re.search(r'property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
        if not og:
            og = re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:title["\']', html, re.I)
        if og:
            return unescape(og.group(1)).strip() or None
        return None
    return unescape(re.sub(r"\s+", " ", match.group(1))).strip() or None


def _html_to_text(html: str) -> str:
    cleaned = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _guess_manufacturer(host: str, text: str, title: str | None) -> str | None:
    if host:
        base = host.lower().removeprefix("www.").split(".")[0]
        if base and base not in {"product", "products", "www", "shop"}:
            return base.replace("-", " ").title()
    if title and "—" in title:
        return title.split("—")[-1].strip()[:120] or None
    if title and "-" in title:
        return title.split("-")[-1].strip()[:120] or None
    return None


def _guess_model(title: str | None, text: str) -> str | None:
    if title:
        # Prefer left side of separators.
        candidate = re.split(r"\s+[|\-—]\s+", title)[0].strip()
        if candidate and len(candidate) <= 120:
            return candidate
    match = re.search(r"\b([A-Z][A-Z0-9]+(?:[- ][A-Z0-9]+)?)\b", text)
    if match:
        return match.group(1)
    return None


def _detect_category(text: str) -> tuple[str | None, bool]:
    for category, pattern in CATEGORY_PATTERNS:
        if pattern.search(text):
            return category, category in SUPPORTED_CATEGORIES
    # Explicit unsupported robot classes (fixed arms / non-mobile manipulators)
    if re.search(r"\b(cobot|collaborative\s+arm|delta\s+robot|scara)\b", text, re.I):
        return "unsupported", False
    return None, False


def _extract_numeric_spec(field_path: str, patterns: list[re.Pattern[str]], text: str) -> ExtractedClaim:
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        raw = float(match.group(1))
        unit = "kg"
        value = raw
        excerpt = match.group(0)[:240]
        lowered = excerpt.lower()
        if field_path == "payload_max_kg":
            if "lb" in lowered or "pound" in lowered:
                value = round(raw * 0.453592, 3)
                unit = "kg"
            else:
                unit = "kg"
        elif field_path == "lift_height_max_m":
            if "mm" in lowered:
                value = round(raw / 1000.0, 4)
            elif "ft" in lowered or "feet" in lowered:
                value = round(raw * 0.3048, 4)
            else:
                value = raw
            unit = "m"
        elif field_path == "speed_mps":
            if "km" in lowered:
                value = round(raw / 3.6, 4)
            else:
                value = raw
            unit = "m/s"
        elif field_path == "runtime_hours":
            unit = "h"
        return ExtractedClaim(
            field_path=field_path,
            value=value,
            truth_state="observed",
            confidence=0.85,
            excerpt=excerpt,
            unit=unit,
        )
    return _unknown(field_path)


def _excerpt_for(text: str, needle: str | None) -> str | None:
    if not needle:
        return None
    idx = text.lower().find(str(needle).lower())
    if idx < 0:
        return str(needle)[:240]
    start = max(0, idx - 40)
    end = min(len(text), idx + len(str(needle)) + 80)
    return text[start:end].strip()[:240]
