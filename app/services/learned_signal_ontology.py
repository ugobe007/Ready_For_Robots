"""
Learned signal ontology — vocabulary and word-shape patterns mined from sales leads.

Stored in ``pipeline_cache_store`` under ``learned_signal_ontology_v1`` and merged
with the Markdown base ontology at match time.
"""
from __future__ import annotations

import json
import logging
import re
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from app.services.pipeline_cache_store import cache_read, cache_write
from app.services.robot_signal_ontology import OntologyFeatures, load_robot_signal_ontology

logger = logging.getLogger(__name__)

LEARNED_ONTOLOGY_CACHE_KEY = "learned_signal_ontology_v1"
LEARNED_ONTOLOGY_TTL_MINUTES = 60 * 24 * 30  # 30 days

BUCKET_KEYS = (
    "pain_words",
    "buying_phrases",
    "trigger_expressions",
    "job_title_signals",
    "capex_financial_signals",
    "expansion_facility_signals",
    "regulatory_compliance_signals",
)

MAX_PER_BUCKET = 500
MAX_WORD_SHAPES = 120
MAX_RICH_FACTS_PER_LEAD = 12

_STOP = frozenset(
    {
        "the", "and", "for", "with", "from", "that", "this", "will", "have", "been",
        "their", "about", "into", "over", "after", "before", "company", "announced",
        "said", "says", "news", "report", "according", "more", "also", "year",
    }
)

_OVERLAY_CACHE: tuple[float, Dict[str, Any]] | None = None
_OVERLAY_TTL_SEC = 300.0


def _empty_store() -> Dict[str, Any]:
    return {
        "version": 1,
        "updated_at": None,
        "buckets": {k: [] for k in BUCKET_KEYS},
        "word_shapes": [],
        "stats": {"leads_processed": 0, "terms_added": 0},
    }


def _norm_term(term: str) -> str:
    return re.sub(r"\s+", " ", (term or "").strip().lower())


def validate_ontology_term(term: str, *, bucket: str = "") -> bool:
    t = _norm_term(term)
    if not t or len(t) < 3:
        return False
    if len(t) > 120:
        return False
    if t in _STOP:
        return False
    if bucket == "pain_words" and len(t.split()) > 2:
        return False
    if bucket in ("buying_phrases", "trigger_expressions") and len(t.split()) > 8:
        return False
    if re.search(r"^[\W\d]+$", t):
        return False
    if re.search(r"(?i)\b(best|top \d+|how to|what is)\b", t):
        return False
    return True


def validate_word_shape(pattern: str) -> bool:
    p = (pattern or "").strip()
    if len(p) < 8 or len(p) > 200:
        return False
    try:
        re.compile(p, re.I)
    except re.error:
        return False
    return True


def load_learned_store(db: Session) -> Dict[str, Any]:
    raw = cache_read(db, LEARNED_ONTOLOGY_CACHE_KEY, stale_ok=True)
    if not isinstance(raw, dict):
        return _empty_store()
    out = _empty_store()
    out["version"] = int(raw.get("version") or 1)
    out["updated_at"] = raw.get("updated_at")
    buckets = raw.get("buckets") if isinstance(raw.get("buckets"), dict) else {}
    for key in BUCKET_KEYS:
        vals = buckets.get(key) if isinstance(buckets.get(key), list) else []
        out["buckets"][key] = [str(v) for v in vals if validate_ontology_term(str(v), bucket=key)][:MAX_PER_BUCKET]
    shapes = raw.get("word_shapes") if isinstance(raw.get("word_shapes"), list) else []
    out["word_shapes"] = [
        s for s in shapes
        if isinstance(s, dict) and validate_word_shape(str(s.get("pattern") or ""))
    ][:MAX_WORD_SHAPES]
    out["stats"] = raw.get("stats") if isinstance(raw.get("stats"), dict) else out["stats"]
    return out


def save_learned_store(db: Session, store: Dict[str, Any]) -> None:
    store = deepcopy(store)
    store["updated_at"] = datetime.now(timezone.utc).isoformat()
    cache_write(db, LEARNED_ONTOLOGY_CACHE_KEY, store, ttl_minutes=LEARNED_ONTOLOGY_TTL_MINUTES)
    global _OVERLAY_CACHE
    _OVERLAY_CACHE = (time.monotonic(), store)
    db.commit()


def get_learned_overlay(db: Optional[Session] = None) -> Dict[str, Any]:
    global _OVERLAY_CACHE
    if _OVERLAY_CACHE is not None:
        ts, data = _OVERLAY_CACHE
        if time.monotonic() - ts < _OVERLAY_TTL_SEC:
            return data
    if db is None:
        return _empty_store()
    data = load_learned_store(db)
    _OVERLAY_CACHE = (time.monotonic(), data)
    return data


def load_effective_ontology_features(db: Optional[Session] = None) -> OntologyFeatures:
    """Base Markdown ontology + learned terms from the enrichment agent."""
    base = load_robot_signal_ontology()
    learned = get_learned_overlay(db)
    buckets = learned.get("buckets") if isinstance(learned.get("buckets"), dict) else {}

    def merge(base_tuple: tuple[str, ...], key: str) -> tuple[str, ...]:
        extra = buckets.get(key) if isinstance(buckets.get(key), list) else []
        seen: set[str] = set()
        out: List[str] = []
        for item in (*base_tuple, *extra):
            n = _norm_term(item)
            if not n or n in seen:
                continue
            seen.add(n)
            out.append(n)
        return tuple(out)

    return OntologyFeatures(
        pain_words=merge(base.pain_words, "pain_words"),
        buying_phrases=merge(base.buying_phrases, "buying_phrases"),
        trigger_expressions=merge(base.trigger_expressions, "trigger_expressions"),
        job_title_signals=merge(base.job_title_signals, "job_title_signals"),
        capex_financial_signals=merge(base.capex_financial_signals, "capex_financial_signals"),
        expansion_facility_signals=merge(base.expansion_facility_signals, "expansion_facility_signals"),
        regulatory_compliance_signals=merge(
            base.regulatory_compliance_signals, "regulatory_compliance_signals"
        ),
    )


def match_word_shapes(text: str, shapes: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not text or not shapes:
        return []
    hits: List[Dict[str, Any]] = []
    for shape in shapes:
        if not isinstance(shape, dict):
            continue
        pat = str(shape.get("pattern") or "")
        if not pat:
            continue
        try:
            if re.search(pat, text, re.I):
                hits.append(shape)
        except re.error:
            continue
    return hits


def merge_candidates_into_store(
    store: Dict[str, Any],
    candidates: Dict[str, Any],
    *,
    source_company_id: Optional[int] = None,
) -> int:
    """Append validated candidates; return count of new terms added."""
    added = 0
    buckets = store.setdefault("buckets", {})
    for key in BUCKET_KEYS:
        buckets.setdefault(key, [])
    for key in BUCKET_KEYS:
        incoming = candidates.get(key) if isinstance(candidates.get(key), list) else []
        existing = set(_norm_term(x) for x in buckets.get(key, []))
        for term in incoming:
            t = _norm_term(str(term))
            if not validate_ontology_term(t, bucket=key) or t in existing:
                continue
            buckets[key].append(t)
            existing.add(t)
            added += 1
            if len(buckets[key]) > MAX_PER_BUCKET:
                buckets[key] = buckets[key][-MAX_PER_BUCKET:]
                break

    shapes_in = candidates.get("word_shapes") if isinstance(candidates.get("word_shapes"), list) else []
    shapes = store.setdefault("word_shapes", [])
    existing_pats = {str(s.get("pattern")) for s in shapes if isinstance(s, dict)}
    for shape in shapes_in:
        if not isinstance(shape, dict):
            continue
        pat = str(shape.get("pattern") or "").strip()
        if not validate_word_shape(pat) or pat in existing_pats:
            continue
        entry = {
            "pattern": pat,
            "maps_to": shape.get("maps_to") or "automation_interest",
            "note": (shape.get("note") or "")[:120],
            "source_company_id": source_company_id,
        }
        shapes.append(entry)
        existing_pats.add(pat)
        added += 1
        if len(shapes) > MAX_WORD_SHAPES:
            store["word_shapes"] = shapes[-MAX_WORD_SHAPES:]
            break

    stats = store.setdefault("stats", {})
    stats["leads_processed"] = int(stats.get("leads_processed") or 0) + 1
    stats["terms_added"] = int(stats.get("terms_added") or 0) + added
    return added


def extract_heuristic_candidates(
    text: str,
    *,
    industry: Optional[str] = None,
    fired_rules: Optional[Sequence[Any]] = None,
) -> Dict[str, Any]:
    """
    Deterministic phrase mining when LLM is unavailable.
    Pulls n-grams and known shapes from high-intent sentences.
    """
    from app.services.crm_extractor import _extract_timing
    from app.services.lead_inference_engine import _PROBLEM_PATTERNS, _SCALE_PATTERNS

    blob = (text or "")[:6000]
    low = blob.lower()
    out: Dict[str, Any] = {k: [] for k in BUCKET_KEYS}
    out["word_shapes"] = []
    out["rich_facts"] = []

    for pat, label in _PROBLEM_PATTERNS:
        if pat.search(blob):
            words = re.findall(r"\b[a-z]{4,}\b", label.lower())
            for w in words:
                if validate_ontology_term(w, bucket="pain_words"):
                    out["pain_words"].append(w)

    for pat, _kind in _SCALE_PATTERNS:
        m = pat.search(blob)
        if m:
            out["rich_facts"].append({"claim": m.group(0).strip(), "kind": "scale"})

    for timing in _extract_timing([(blob, "")]):
        phrase = timing.label.strip()
        if validate_ontology_term(phrase, bucket="trigger_expressions"):
            out["trigger_expressions"].append(phrase)

    _phrase_rules = [
        (r"(?i)\b(request for proposal|rfp|procurement|vendor selection|pilot program)\b", "buying_phrases"),
        (r"(?i)\b(capital expenditure|capex|automation budget|series [a-e])\b", "capex_financial_signals"),
        (r"(?i)\b(new (?:warehouse|distribution center|facility|hotel|plant))\b", "expansion_facility_signals"),
        (r"(?i)\b((?:vp|director|chief) of operations|head of automation|robotics engineer)\b", "job_title_signals"),
    ]
    for regex, bucket in _phrase_rules:
        for m in re.finditer(regex, blob):
            phrase = _norm_term(m.group(0))
            if validate_ontology_term(phrase, bucket=bucket):
                out[bucket].append(phrase)

    if fired_rules:
        for rule in fired_rules:
            desc = getattr(rule, "description", None) or (rule.get("description") if isinstance(rule, dict) else "")
            if desc and validate_ontology_term(str(desc)[:80], bucket="trigger_expressions"):
                out["trigger_expressions"].append(_norm_term(str(desc)[:80]))

    if industry and validate_ontology_term(f"{industry.lower()} automation", bucket="buying_phrases"):
        out["buying_phrases"].append(f"{industry.lower()} automation")

    shape_templates = [
        (r"(?i)\bdeploy(?:ed|ing|s)?\s+\d+\s+(?:amrs?|agvs?|robots?)\b", "robot_installation"),
        (r"(?i)\bwithin\s+\d{1,2}\s+months?\b", "near_term_horizon"),
        (r"(?i)\b\$[\d,.]+[mb]?\s+(?:investment|automation|capex)\b", "capex"),
    ]
    for pat, maps_to in shape_templates:
        if re.search(pat, blob):
            out["word_shapes"].append({"pattern": pat, "maps_to": maps_to, "note": "heuristic"})

    return out
