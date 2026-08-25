"""Jobs CRM presentation of Hermes overlay — no SIGNAL internals."""

from __future__ import annotations

import re
from typing import Any

_SIGNAL_RATIONALE_NOISE = (
    re.compile(r"hot-type signals", re.I),
    re.compile(r"\d+\s+signals\b", re.I),
    re.compile(r"work family:\s*unknown", re.I),
    re.compile(r"high-fit industry", re.I),
    re.compile(r"^\[rfr_inference_v1\]", re.I),
)
_ROBOT_TYPE_SLUG = re.compile(
    r"^(amr|agv|cobot|arm|humanoid|uav|drone|mobile.?manipulator)$",
    re.I,
)


def is_real_vendor_name(value: str) -> bool:
    t = (value or "").strip()
    if len(t) < 3 or len(t) > 48:
        return False
    if "_" in t:
        return False
    if re.fullmatch(r"[a-z0-9]+", t):
        return False
    if _ROBOT_TYPE_SLUG.fullmatch(t):
        return False
    return bool(re.search(r"[A-Z]", t) or " " in t)


def humanize_overlay_rationale(raw: str | None) -> str:
    if not raw:
        return ""
    stripped = re.sub(r"^\[rfr_inference_v1\]\s*", "", raw.strip(), flags=re.I)
    parts: list[str] = []
    seen: set[str] = set()
    for part in re.split(r";\s*", stripped):
        p = part.strip()
        if not p:
            continue
        if any(rx.search(p) for rx in _SIGNAL_RATIONALE_NOISE):
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(p)
    return parts[0] if parts else ""


def _vendor_label(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        return str(item.get("vendor") or item.get("manufacturer_name") or "").strip()
    return ""


def sanitize_hermes_pipeline_overlay(overlay: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop SIGNAL dump fields before they reach Jobs CRM / pipeline JSON."""
    if not overlay:
        return None
    vendors: list[Any] = []
    for item in overlay.get("vendor_shortlist") or []:
        label = _vendor_label(item)
        if not is_real_vendor_name(label):
            continue
        if isinstance(item, dict):
            vendors.append(
                {
                    "vendor": label,
                    "model": item.get("model") or item.get("robot_model"),
                    "why": item.get("why"),
                }
            )
        else:
            vendors.append({"vendor": label, "model": None, "why": None})
        if len(vendors) >= 4:
            break
    rationale = humanize_overlay_rationale(str(overlay.get("rationale") or ""))
    if not vendors:
        return None
    return {
        "rationale": rationale or None,
        "vendor_shortlist": vendors,
        "updated_at": overlay.get("updated_at"),
    }
