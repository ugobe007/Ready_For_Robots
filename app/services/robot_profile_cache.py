"""Short-lived Robot Profile cache.

Robot specs do not change every minute. Repeat URL submits should reuse a
reasonably fresh grounded profile instead of rebuilding from source pages.

Redis via shared_api_cache when available; in-process LRU fallback otherwise.
Never raises into the request path.
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from typing import Any, Optional
from urllib.parse import urlsplit, urlunsplit

from app.services.shared_api_cache import shared_cache_get, shared_cache_set

logger = logging.getLogger(__name__)

# v6: archive fallback for bot-challenged OEM hosts; named robots from prose.
NAMESPACE = "robot_profile_v6"
DEFAULT_TTL_SEC = 6 * 60 * 60  # 6 hours
_MEM_MAX = 64
_mem: dict[str, tuple[float, dict[str, Any]]] = {}
_mem_lock = threading.Lock()


def profile_cache_ttl_sec() -> int:
    try:
        return max(60, int(os.getenv("ROBOT_PROFILE_CACHE_TTL_SEC", str(DEFAULT_TTL_SEC))))
    except ValueError:
        return DEFAULT_TTL_SEC


def normalize_profile_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if not raw.lower().startswith(("http://", "https://")):
        raw = "https://" + raw
    parts = urlsplit(raw)
    host = (parts.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path.rstrip("/") or "/"
    netloc = host
    if parts.port and parts.port not in {80, 443}:
        netloc = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme.lower() or "https", netloc, path, parts.query, ""))


def profile_cache_key(url: str, product: str | None = None) -> str:
    product_key = (product or "").strip().lower()
    blob = f"{normalize_profile_url(url)}|{product_key}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:40]


def get_cached_profile(url: str, product: str | None = None) -> Optional[dict[str, Any]]:
    key = profile_cache_key(url, product)
    try:
        hit = shared_cache_get(NAMESPACE, key)
        if isinstance(hit, dict) and hit.get("company"):
            return hit
    except Exception:
        logger.exception("robot_profile_cache redis get failed")
    now = time.time()
    with _mem_lock:
        row = _mem.get(key)
        if not row:
            return None
        expires, value = row
        if expires < now:
            _mem.pop(key, None)
            return None
        return value


def _store_cached_profile(url: str, product: str | None, payload: dict[str, Any]) -> None:
    key = profile_cache_key(url, product)
    ttl = profile_cache_ttl_sec()
    try:
        shared_cache_set(NAMESPACE, key, payload, ttl)
    except Exception:
        logger.exception("robot_profile_cache redis set failed")
    expires = time.time() + ttl
    with _mem_lock:
        _mem[key] = (expires, payload)
        if len(_mem) > _MEM_MAX:
            oldest = min(_mem.items(), key=lambda kv: kv[1][0])[0]
            _mem.pop(oldest, None)


def _profile_is_cacheable(payload: dict[str, Any]) -> bool:
    """Do not pin a 6-hour miss when the OEM host challenged and we got nothing."""
    products = payload.get("products") or []
    sources = payload.get("sources") or []
    selected = payload.get("selected_product")
    notes = " ".join(str(n) for n in (payload.get("notes") or []))
    if products or sources or selected:
        return True
    if "bot challenge" in notes.lower() or "degraded" in notes.lower():
        return False
    return False


def set_cached_profile(url: str, product: str | None, payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or not payload.get("company"):
        return
    if not _profile_is_cacheable(payload):
        return
    _store_cached_profile(url, product, payload)
    # First submit caches under product=None; confirming that SKU should hit.
    selected = (payload.get("selected_product") or {}).get("name")
    if isinstance(selected, str) and selected.strip():
        if profile_cache_key(url, selected) != profile_cache_key(url, product):
            _store_cached_profile(url, selected, payload)


def clear_profile_cache_memory() -> None:
    """Tests only."""
    with _mem_lock:
        _mem.clear()
