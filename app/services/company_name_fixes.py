"""Canonical display-name fixes for truncated / junk buyer names.

Age and scrapers sometimes leave a bare noun (e.g. \"Cheese\") in companies.name.
These exact renames restore the real buyer identity at API emit time so the
pipeline does not wait on a cache rebuild. Persist via cleanup when DB is available.
"""
from __future__ import annotations

from typing import Optional

# Exact match on stripped lowercased name → display name
_EXACT_DISPLAY_FIXES: dict[str, str] = {
    "cheese": "Santori Cheese",
}


def canonical_display_name(name: Optional[str]) -> Optional[str]:
    """Return a corrected display name, or the original string (possibly empty)."""
    if name is None:
        return None
    raw = str(name).strip()
    if not raw:
        return raw
    fixed = _EXACT_DISPLAY_FIXES.get(raw.lower())
    return fixed if fixed else raw
