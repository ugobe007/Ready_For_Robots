"""Cross-process JSON cache helpers for public API and agent payloads."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

KEY_PREFIX = "rfr:api:v1:"

_client: Any = None
_last_connect_fail_at: float = 0.0


def _redis_url() -> str:
    return (os.getenv("API_CACHE_REDIS_URL") or os.getenv("REDIS_URL") or "").strip()


def _retry_sec() -> float:
    try:
        return max(5.0, float(os.getenv("API_CACHE_REDIS_RETRY_SEC", "30")))
    except ValueError:
        return 30.0


def shared_cache_redis_wanted() -> bool:
    if os.getenv("API_CACHE_USE_REDIS", "").strip().lower() in {"0", "false", "no", "off"}:
        return False
    return bool(_redis_url())


def _get_client():
    global _client, _last_connect_fail_at
    if not shared_cache_redis_wanted():
        return None
    if _client is not None:
        return _client
    now = time.monotonic()
    if now - _last_connect_fail_at < _retry_sec():
        return None
    try:
        import redis

        redis_client = redis.from_url(
            _redis_url(),
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
        )
        redis_client.ping()
        _client = redis_client
        return _client
    except Exception as exc:
        _last_connect_fail_at = time.monotonic()
        logger.warning("Shared API cache unavailable (%s); retry in %.0fs", exc, _retry_sec())
        return None


def shared_cache_get(namespace: str, key: str) -> Optional[Any]:
    redis_client = _get_client()
    if not redis_client:
        return None
    try:
        raw = redis_client.get(f"{KEY_PREFIX}{namespace}:{key}")
        return json.loads(raw) if raw is not None else None
    except Exception as exc:
        logger.warning("Shared API cache GET failed for %s: %s", namespace, exc)
        return None


def shared_cache_set(namespace: str, key: str, value: Any, ttl_sec: int) -> None:
    redis_client = _get_client()
    if not redis_client:
        return
    try:
        redis_client.setex(
            f"{KEY_PREFIX}{namespace}:{key}",
            max(1, int(ttl_sec)),
            json.dumps(value, default=str, ensure_ascii=False),
        )
    except Exception as exc:
        logger.warning("Shared API cache SET failed for %s: %s", namespace, exc)
