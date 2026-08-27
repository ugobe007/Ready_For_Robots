"""Classify robot morphology from product-page photos.

SOURCE is the manufacturer image (URL + alt/caption, optionally pixels via a
tight vision ask). FACT is product_class. This is not an LLM profile generator:
it only names a morphology class the matcher already understands.
"""
from __future__ import annotations

import os
import re
from typing import Any, Optional

from app.services.robot_understanding_v1.models import RobotFact
from app.services.robot_understanding_v1.sources import CollectedSource

# Filenames / alts that name a morphology. Class words only — never SKU names
# (Avidbots Neo is a scrubber; 1X NEO is a humanoid).
_CLASS_HINTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(humanoid|bipedal|two[- ]legged|android robot)\b", re.I), "humanoid"),
    (re.compile(r"\b(quadruped|four[- ]legged)\b", re.I), "quadruped"),
    (re.compile(r"\b(mobile\s+manipulator|manipulator\s+on\s+(?:a\s+)?base)\b", re.I), "mobile_manipulator"),
    (re.compile(r"\b(cobot|collaborative\s+arm)\b", re.I), "cobot"),
    (re.compile(r"\b(scrubber|floor\s+scrub|autonomous\s+cleaner)\b", re.I), "autonomous_scrubber"),
    (re.compile(r"\b(forklift|pallet\s+jack|reach\s+truck)\b", re.I), "amr"),
    (re.compile(r"\b(amr|agv|autonomous\s+mobile\s+robot|mobile\s+base)\b", re.I), "amr"),
    (re.compile(r"\b(laserweeder|weeding\s+robot|agricultural\s+robot|crop\s+robot)\b", re.I), "agriculture"),
    (re.compile(r"\b(hull\s+inspect|underwater\s+robot|marine\s+robot)\b", re.I), "marine"),
    (re.compile(r"\b(hangar\s+robot|airside|aircraft\s+inspect|avionics)\b", re.I), "avionics"),
    (re.compile(r"\b(construction\s+robot|jobsite\s+robot|layout\s+printer)\b", re.I), "construction"),
]


def _blob_for_images(images: list[tuple[str, str]]) -> str:
    parts: list[str] = []
    for url, alt in images:
        parts.append(alt or "")
        parts.append(url.rsplit("/", 1)[-1].replace("-", " ").replace("_", " "))
    return " ".join(parts)


def classify_image_hints(images: list[tuple[str, str]], page_text: str = "") -> Optional[tuple[str, str]]:
    """Return (product_class, evidence) from photo alts/filenames, else None."""
    blob = f"{_blob_for_images(images)} {page_text[:1500]}"
    if not blob.strip():
        return None
    for rx, cls in _CLASS_HINTS:
        m = rx.search(blob)
        if m:
            return cls, m.group(0)
    return None


def _vision_class(image_url: str) -> Optional[tuple[str, str]]:
    """Optional one-shot morphology ask. Fail-open. Never invents a profile."""
    if (os.getenv("ROBOT_VISUAL_CLASS") or "1").strip().lower() in {"0", "false", "no"}:
        return None
    key = (os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY") or "").strip()
    if not key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, timeout=6.0, max_retries=0)
        model = (os.getenv("ROBOT_VISUAL_CLASS_MODEL") or "gpt-4o-mini").strip()
        prompt = (
            "Look at this manufacturer product photo. Reply with one JSON object "
            '{"class":"humanoid|amr|mobile_manipulator|cobot|quadruped|autonomous_scrubber|unknown",'
            '"evidence":"short visual cue"}. Class is body morphology only: '
            "bipedal humanoid, wheeled AMR, arm on a mobile base, collaborative arm, "
            "four-legged, or floor scrubber. If unsure, class=unknown. No other keys."
        )
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=80,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        m = re.search(
            r'"class"\s*:\s*"(humanoid|amr|mobile_manipulator|cobot|quadruped|autonomous_scrubber|unknown)"',
            raw,
            re.I,
        )
        if not m:
            return None
        cls = m.group(1).lower()
        if cls == "unknown":
            return None
        ev = re.search(r'"evidence"\s*:\s*"([^"]{1,120})"', raw)
        return cls, (ev.group(1) if ev else f"visual class {cls}")
    except Exception:
        return None


def visual_class_facts(
    collected: list[CollectedSource],
    *,
    subject: str,
) -> list[RobotFact]:
    """Emit a product_class fact from manufacturer photos when text missed it."""
    images: list[tuple[str, str]] = []
    text_bits: list[str] = []
    source_id = "visual_class"
    for item in collected:
        page = item.page
        text_bits.append(page.text or "")
        images.extend(list(page.image_alts or []))
        if source_id == "visual_class":
            source_id = item.source.id
    if not images and not text_bits:
        return []
    hit = classify_image_hints(images, " ".join(text_bits)[:2000])
    if hit is None and images:
        hit = _vision_class(images[0][0])
    if hit is None:
        return []
    cls, evidence = hit
    return [
        RobotFact.create(
            subject,
            "product_class",
            cls,
            source_id=source_id,
            epistemic="explicit",
            confidence=0.82,
            evidence_span=f"Product photo: {evidence}"[:240],
        )
    ]


def preview_image_urls(collected: list[CollectedSource], *, limit: int = 6) -> list[str]:
    """First manufacturer product-photo URLs, for the qualify UI."""
    out: list[str] = []
    seen: set[str] = set()
    for item in collected:
        for url, _alt in list(getattr(item.page, "image_alts", None) or []):
            if not url or url in seen:
                continue
            seen.add(url)
            out.append(url)
            if len(out) >= limit:
                return out
    return out
