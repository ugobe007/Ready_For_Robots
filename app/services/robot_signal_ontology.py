"""Robot automation signal ontology loader and match helpers.

The source of truth is ``Robot Automation Signal Ontology.md`` in the repo root.
This module parses the Markdown into feature vocabularies used by the signal
classifier and scoring ranker.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class OntologyFeatures:
    pain_words: tuple[str, ...]
    buying_phrases: tuple[str, ...]
    trigger_expressions: tuple[str, ...]
    job_title_signals: tuple[str, ...]
    capex_financial_signals: tuple[str, ...]
    expansion_facility_signals: tuple[str, ...]
    regulatory_compliance_signals: tuple[str, ...]


@dataclass(frozen=True)
class OntologyMatches:
    pain_words: tuple[str, ...] = ()
    buying_phrases: tuple[str, ...] = ()
    trigger_expressions: tuple[str, ...] = ()
    job_title_signals: tuple[str, ...] = ()
    capex_financial_signals: tuple[str, ...] = ()
    expansion_facility_signals: tuple[str, ...] = ()
    regulatory_compliance_signals: tuple[str, ...] = ()
    word_shape_hits: tuple[dict, ...] = ()

    @property
    def has_any(self) -> bool:
        return any(
            (
                self.pain_words,
                self.buying_phrases,
                self.trigger_expressions,
                self.job_title_signals,
                self.capex_financial_signals,
                self.expansion_facility_signals,
                self.regulatory_compliance_signals,
                self.word_shape_hits,
            )
        )


def _ontology_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2] / "Robot Automation Signal Ontology.md"
    bundled = Path(__file__).resolve().parent / "data" / "Robot Automation Signal Ontology.md"
    if repo_root.is_file():
        return repo_root
    if bundled.is_file():
        return bundled
    return repo_root


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().strip('"').strip("'")).lower()


def _unique(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        value = _norm(item)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return tuple(out)


def _bullet_value(line: str) -> str:
    value = line.strip()
    if value.startswith("- "):
        value = value[2:]
    return value.strip()


@lru_cache(maxsize=1)
def load_robot_signal_ontology() -> OntologyFeatures:
    text = _ontology_path().read_text(encoding="utf-8")
    current_heading = ""
    buckets: dict[str, list[str]] = {
        "pain_words": [],
        "buying_phrases": [],
        "trigger_expressions": [],
        "job_title_signals": [],
        "capex_financial_signals": [],
        "expansion_facility_signals": [],
        "regulatory_compliance_signals": [],
    }

    heading_to_bucket = {
        "universal pain words": "pain_words",
        "pain signal words": "pain_words",
        "universal buying signal phrases": "buying_phrases",
        "buying signal phrases": "buying_phrases",
        "universal trigger expressions": "trigger_expressions",
        "trigger expressions": "trigger_expressions",
        "universal job title signals": "job_title_signals",
        "job title signals": "job_title_signals",
        "capex and financial signals": "capex_financial_signals",
        "expansion and facility signals": "expansion_facility_signals",
        "regulatory and compliance signals": "regulatory_compliance_signals",
    }

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("### "):
            current_heading = _norm(line[4:])
            continue
        if line.startswith("## ") or line.startswith("---"):
            if not line.startswith("### "):
                current_heading = ""
            continue
        bucket = heading_to_bucket.get(current_heading)
        if not bucket or not line or line.startswith("**"):
            continue
        if line.startswith("- "):
            buckets[bucket].append(_bullet_value(line))
        elif bucket == "pain_words" and "," in line:
            buckets[bucket].extend(part.strip() for part in line.split(","))

    return OntologyFeatures(
        pain_words=_unique(buckets["pain_words"]),
        buying_phrases=_unique(buckets["buying_phrases"]),
        trigger_expressions=_unique(buckets["trigger_expressions"]),
        job_title_signals=_unique(buckets["job_title_signals"]),
        capex_financial_signals=_unique(buckets["capex_financial_signals"]),
        expansion_facility_signals=_unique(buckets["expansion_facility_signals"]),
        regulatory_compliance_signals=_unique(buckets["regulatory_compliance_signals"]),
    )


# Industry commentary / survey decks — not buyer-direct triggers.
_EDITORIAL_TRIGGER_RE = re.compile(
    r"(?:^this article|^companies should|^the industry should|^explores how|"
    r"^according to (?:analysts|experts|survey)|\d+% of .{0,40} (?:have|plan|already)|"
    r"should consider accelerating|article explores|survey found|market report)",
    re.I,
)

# High-fit verticals where pain vocabulary alone is a valid labor signal.
_HIGH_FIT_INDUSTRY_RE = re.compile(
    r"\b(?:hotels?|hospitality|warehouses?|logistics|fulfillment|distribution\s+centers?|"
    r"restaurants?|food\s+service|airports?|airlines?|hospitals?|healthcare|manufacturing|"
    r"cold\s+storage|3pl)\b",
    re.I,
)


def _phrase_matches(text_norm: str, phrases: Iterable[str]) -> tuple[str, ...]:
    matches: list[str] = []
    for phrase in phrases:
        if not phrase:
            continue
        if _EDITORIAL_TRIGGER_RE.search(phrase):
            continue
        left = r"\b" if phrase[0].isalnum() else ""
        right = r"\b" if phrase[-1].isalnum() else ""
        pattern = left + re.escape(phrase).replace(r"\ ", r"\s+") + right
        if re.search(pattern, text_norm, re.I):
            matches.append(phrase)
    return tuple(matches)


def _word_matches(text_norm: str, words: Iterable[str]) -> tuple[str, ...]:
    matches: list[str] = []
    for word in words:
        if not word:
            continue
        if re.search(r"\b" + re.escape(word) + r"\b", text_norm, re.I):
            matches.append(word)
    return tuple(matches)


def match_ontology_features(text: str, db: Optional[Any] = None) -> OntologyMatches:
    from app.services.learned_signal_ontology import (
        get_learned_overlay,
        load_effective_ontology_features,
        match_word_shapes,
    )

    features = load_effective_ontology_features(db)
    text_norm = _norm(text)
    overlay = get_learned_overlay(db)
    shapes = overlay.get("word_shapes") if isinstance(overlay.get("word_shapes"), list) else []
    shape_hits = tuple(match_word_shapes(text, shapes))
    return OntologyMatches(
        pain_words=_word_matches(text_norm, features.pain_words),
        buying_phrases=_phrase_matches(text_norm, features.buying_phrases),
        trigger_expressions=_phrase_matches(text_norm, features.trigger_expressions),
        job_title_signals=_phrase_matches(text_norm, features.job_title_signals),
        capex_financial_signals=_phrase_matches(text_norm, features.capex_financial_signals),
        expansion_facility_signals=_phrase_matches(text_norm, features.expansion_facility_signals),
        regulatory_compliance_signals=_phrase_matches(text_norm, features.regulatory_compliance_signals),
        word_shape_hits=shape_hits,
    )


def signal_types_from_ontology_matches(text: str, db: Optional[Any] = None) -> list[str]:
    matches = match_ontology_features(text, db=db)
    if not matches.has_any:
        return []

    signals: list[str] = []

    def add(signal_type: str) -> None:
        if signal_type not in signals:
            signals.append(signal_type)

    for shape in matches.word_shape_hits:
        maps_to = str(shape.get("maps_to") or "").strip()
        if maps_to:
            add(maps_to.replace("-", "_"))

    # Trigger expressions are exact-match, high-confidence rules (editorial filtered at match time).
    if matches.trigger_expressions:
        add("automation_intent")
    if matches.job_title_signals:
        add("strategic_hire")
    if matches.capex_financial_signals:
        add("capex")
    if matches.expansion_facility_signals:
        add("expansion")
    if matches.regulatory_compliance_signals:
        add("safety_incident")

    buying_text = " ".join(matches.buying_phrases)
    if matches.buying_phrases:
        if re.search(r"\b(?:rfp|proposal|procurement|vendor selection|seeking partners)\b", buying_text, re.I):
            add("vendor_selection")
        elif re.search(r"\b(?:warehouse|material handling|amr|agv|logistics|fulfillment|sortation)\b", buying_text, re.I):
            add("warehouse_throughput")
        elif re.search(r"\b(?:quality|inspection|vision|traceability)\b", buying_text, re.I):
            add("quality_bottleneck")
        else:
            add("automation_interest")

    pain_with_evidence = (
        matches.buying_phrases or matches.trigger_expressions or matches.job_title_signals
    )
    pain_in_high_fit = len(matches.pain_words) >= 2 and _HIGH_FIT_INDUSTRY_RE.search(text)
    if matches.pain_words and (pain_with_evidence or pain_in_high_fit):
        if any(word in {"injuries", "hazardous", "safety", "osha", "fatigue"} for word in matches.pain_words):
            add("safety_incident")
        elif any(word in {"bottleneck", "bottlenecks", "capacity", "throughput"} for word in matches.pain_words):
            add("production_capacity")
        else:
            add("labor_shortage")

    return signals


def ontology_signal_points(text: str, *, signal_type: str = "", source_channel: str = "") -> int:
    """Signal Strength Scoring Guide points from the ontology."""
    matches = match_ontology_features(text)
    source = (source_channel or "").lower()
    lower = (text or "").lower()
    points = 0
    if matches.trigger_expressions:
        points += 35
        if source in {"earnings_call", "press_release"}:
            points += 10
    if matches.job_title_signals:
        points += 25
        if len(matches.job_title_signals) >= 3:
            points += 5
    if matches.capex_financial_signals or signal_type == "capex":
        points += 20
        if re.search(r"\$\s?\d|\b\d+(?:\.\d+)?\s?(?:million|billion|m\b|b\b)", lower, re.I):
            points += 10
    if matches.expansion_facility_signals or signal_type == "expansion":
        points += 20
        if re.search(r"\b(?:permit|construction permit|filed permit)\b", lower, re.I):
            points += 10
    if matches.buying_phrases:
        points += 15
        if re.search(r"^\W*(?:" + "|".join(re.escape(p) for p in matches.buying_phrases[:12]) + r")\b", lower, re.I):
            points += 5
    if matches.pain_words:
        points += 5
        if source in {"osha_filing", "earnings_call"}:
            points += 2
    if matches.regulatory_compliance_signals:
        points += 10
        if re.search(r"\b(?:deadline|mandate|by \d{4}|compliance date|required by)\b", lower, re.I):
            points += 5
    return min(points, 100)
