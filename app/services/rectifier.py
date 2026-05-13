"""
rectifier.py
============
Post-enrichment re-validation — the final "sniff test" before a lead is
considered production-quality.

After scraping + enrichment + ontological parsing we have a company name
AND a corpus of signals about it.  The rectifier asks: given everything
we now know, does this entity still look like a real buyer company?

Three checks are layered:

  1. Re-classify the company name with text_classifier (same logic as the
     pre-write gate but now runs with more context).

  2. Signal-context subject check — do the signals reference this entity as
     the grammatical SUBJECT of an organizational action?
     ("Acme Corp expands warehouse" ← good)
     ("facility in Acme" ← place reference, not a company)
     ("hired by Acme" ← person-context, suspicious)

  3. Entity coherence check — across all signals, does the name appear
     consistently as a proper noun (title-case) or does it vary wildly
     (suggesting it's a common word, not a brand)?

Outcome
-------
  RectificationResult.passed   True  → lead is valid, proceed to CRM extraction
  RectificationResult.passed   False → quarantine (company.is_internal = False)
                                       reason stored in result.reason

Public API
----------
  validate(company, signals) -> RectificationResult
  quarantine(company, db)    -> None    (sets is_internal=False and commits)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from app.services.text_classifier import classify, EntityType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.company import Company
    from app.models.signal import Signal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RectificationResult:
    passed: bool
    confidence: float           # 0–1 overall confidence this is a valid company
    reason: str = ""            # human-readable explanation if failed
    checks: List[str] = field(default_factory=list)  # log of each check result


# ─────────────────────────────────────────────────────────────────────────────
# Check 1: Re-classify the company name
# ─────────────────────────────────────────────────────────────────────────────

_MIN_NAME_CONFIDENCE = 0.35   # lower bar here — signal context fills in the gap


def _check_name_classification(name: str) -> tuple[bool, float, str]:
    """
    Returns (ok, confidence, evidence_str).
    ok=True  → name passes the entity type gate
    ok=False → name is conclusively not a company name
    """
    tc = classify(name)

    # Conclusive non-company types → fail regardless of confidence
    hard_fail_types = {
        EntityType.PERSON_NAME,
        EntityType.CITY_OR_TOWN,
        EntityType.COUNTRY,
        EntityType.SECTOR_DESCRIPTOR,
        EntityType.FACILITY_DESCRIPTOR,
        EntityType.POPULATION_GROUP,
        EntityType.DESCRIPTOR_ONLY,
        EntityType.MALFORMED_ENTITY,
        EntityType.SAYING,
        EntityType.EQUIPMENT_CAT,
        EntityType.MARKET_FRAGMENT,
    }
    if tc.entity_type in hard_fail_types and tc.confidence >= 0.70:
        return False, tc.confidence, (
            f"name classified as {tc.entity_type.value} "
            f"(conf={tc.confidence:.2f}): {', '.join(tc.evidence[:2])}"
        )

    # ARTICLE_HEADLINE with high confidence → fail
    if tc.entity_type == EntityType.ARTICLE_HEADLINE and tc.confidence >= 0.75:
        return False, tc.confidence, (
            f"name looks like an article headline "
            f"(conf={tc.confidence:.2f}): {', '.join(tc.evidence[:2])}"
        )

    # COMPANY_NAME or UNKNOWN with low-enough confidence to proceed
    return True, tc.confidence, (
        f"name type={tc.entity_type.value} conf={tc.confidence:.2f}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Check 2: Signal-context subject verification
# ─────────────────────────────────────────────────────────────────────────────

# Templates indicating the entity is referenced as a PLACE rather than an org
_PLACE_CONTEXT = re.compile(
    r"\b(?:located\s+in|based\s+in|facility\s+in|office\s+in|"
    r"warehouse\s+in|campus\s+in|site\s+in|plant\s+in|"
    r"headquarters\s+in|hub\s+in)\s+{name_escaped}\b",
    re.IGNORECASE,
)

# Templates indicating the entity is referenced as a PERSON
_PERSON_CONTEXT = re.compile(
    r"\b(?:hired\s+by|according\s+to|said\s+by|comments?\s+from|"
    r"remarks?\s+by|interview\s+with|quote\s+from)\s+{name_escaped}\b",
    re.IGNORECASE,
)

# Templates where the entity IS the subject of an organizational action (good)
_ORG_SUBJECT = re.compile(
    r"\b{name_escaped}\s+(?:is|are|was|were|has|have|will|plans?\s+to|"
    r"announced?|expand\w*|launch\w*|open\w*|invest\w*|deploy\w*|"
    r"hire\w*|acqui\w*|partner\w*|sign\w*|report\w*|post\w*|"
    r"secur\w*|land\w*|win\w*|grow\w*|operat\w*|run\w*|serv\w*)\b",
    re.IGNORECASE,
)


def _escape_for_re(name: str) -> str:
    """Escape name for embedding in regex, preserving word boundaries."""
    return re.escape(name)


def _check_signal_context(name: str, signal_texts: List[str]) -> tuple[bool, float, str]:
    """
    Returns (ok, boost_confidence, note).
    Checks whether signals reference the entity as an organization subject.
    """
    if not signal_texts:
        return True, 0.0, "no signals to check — neutral"

    name_esc = _escape_for_re(name)

    # Compile per-name patterns
    place_re = re.compile(
        _PLACE_CONTEXT.pattern.replace("{name_escaped}", name_esc),
        re.IGNORECASE,
    )
    person_re = re.compile(
        _PERSON_CONTEXT.pattern.replace("{name_escaped}", name_esc),
        re.IGNORECASE,
    )
    org_re = re.compile(
        _ORG_SUBJECT.pattern.replace("{name_escaped}", name_esc),
        re.IGNORECASE,
    )

    place_hits = 0
    person_hits = 0
    org_hits = 0
    name_mention_count = 0

    for text in signal_texts:
        if re.search(re.escape(name), text, re.IGNORECASE):
            name_mention_count += 1
        if place_re.search(text):
            place_hits += 1
        if person_re.search(text):
            person_hits += 1
        if org_re.search(text):
            org_hits += 1

    # No mentions at all → neutral (name may just be implied)
    if name_mention_count == 0:
        return True, 0.0, "entity name not mentioned in signals — neutral"

    # More place or person hits than org hits → suspicious
    bad_hits = place_hits + person_hits
    if bad_hits > org_hits and bad_hits >= 2:
        return False, 0.0, (
            f"entity appears in non-company context "
            f"({place_hits} place refs, {person_hits} person refs) "
            f"vs {org_hits} org-subject refs"
        )

    # Strong org-subject references → confidence boost
    if org_hits >= 2:
        return True, 0.15, f"{org_hits} org-subject signal references found"
    if org_hits == 1:
        return True, 0.08, "1 org-subject signal reference found"

    return True, 0.0, "entity mentioned but no strong context patterns matched"


# ─────────────────────────────────────────────────────────────────────────────
# Check 3: Entity coherence across signals
# ─────────────────────────────────────────────────────────────────────────────

def _check_entity_coherence(name: str, signal_texts: List[str]) -> tuple[bool, float, str]:
    """
    Checks that the name appears with consistent capitalisation across signals.
    A common word (not a brand) will appear in all-lowercase mid-sentence.
    A real brand will mostly appear title-cased or all-caps.
    """
    if not signal_texts or len(name.split()) == 1 and len(name) <= 3:
        return True, 0.0, "single short word — coherence check skipped"

    # Count how often the name appears title-cased vs lower-cased
    title_hits = 0
    lower_hits = 0
    name_title = name.title()
    name_lower = name.lower()

    for text in signal_texts:
        if name_title in text or name.upper() in text:
            title_hits += 1
        # Check if an all-lowercase occurrence exists mid-sentence
        # (not at sentence start, which would always be capitalized)
        if re.search(r"(?<!\.\s)\b" + re.escape(name_lower) + r"\b", text):
            lower_hits += 1

    if lower_hits > title_hits and lower_hits >= 2:
        return False, 0.0, (
            f"name appears lowercase ({lower_hits}x) more than title-case "
            f"({title_hits}x) — likely a common word, not a brand"
        )

    boost = 0.05 if title_hits >= 2 else 0.0
    return True, boost, f"coherence ok (title={title_hits}, lower={lower_hits})"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# Minimum confidence threshold to pass rectification
_PASS_THRESHOLD = 0.45


def validate(company: "Company", signals: List["Signal"]) -> RectificationResult:
    """
    Run all rectification checks.

    Returns RectificationResult with passed=True if the entity passes the
    sniff test, or passed=False with a reason string if it should be quarantined.
    """
    name = getattr(company, "name", None) or ""
    if not name.strip():
        return RectificationResult(
            passed=False, confidence=0.0,
            reason="company has empty name",
            checks=["empty name — auto-fail"],
        )

    signal_texts = [s.signal_text for s in (signals or []) if s.signal_text]
    checks: List[str] = []
    running_confidence = 0.50  # baseline

    # ── Check 1: name classification ─────────────────────────────────────────
    ok1, conf1, note1 = _check_name_classification(name)
    checks.append(f"[name_classify] {note1}")
    if not ok1:
        return RectificationResult(
            passed=False,
            confidence=conf1,
            reason=f"name classification failed: {note1}",
            checks=checks,
        )
    # Adjust running confidence based on name classification result
    running_confidence = max(running_confidence, conf1) if conf1 > 0 else running_confidence

    # ── Check 2: signal context ───────────────────────────────────────────────
    ok2, boost2, note2 = _check_signal_context(name, signal_texts)
    checks.append(f"[signal_context] {note2}")
    if not ok2:
        return RectificationResult(
            passed=False,
            confidence=running_confidence,
            reason=f"signal context check failed: {note2}",
            checks=checks,
        )
    running_confidence = min(0.95, running_confidence + boost2)

    # ── Check 3: entity coherence ─────────────────────────────────────────────
    ok3, boost3, note3 = _check_entity_coherence(name, signal_texts)
    checks.append(f"[coherence] {note3}")
    if not ok3:
        return RectificationResult(
            passed=False,
            confidence=running_confidence,
            reason=f"coherence check failed: {note3}",
            checks=checks,
        )
    running_confidence = min(0.95, running_confidence + boost3)

    # ── Final decision ────────────────────────────────────────────────────────
    if running_confidence < _PASS_THRESHOLD:
        return RectificationResult(
            passed=False,
            confidence=running_confidence,
            reason=(
                f"overall confidence {running_confidence:.2f} below threshold "
                f"{_PASS_THRESHOLD}"
            ),
            checks=checks,
        )

    return RectificationResult(
        passed=True,
        confidence=running_confidence,
        reason="",
        checks=checks,
    )


def quarantine(company: "Company", db: "Session", reason: str = "") -> None:
    """
    Soft-quarantine a company: set is_internal=False so it is excluded from
    the public API and dashboard.  Does NOT delete — admin can review and
    restore if needed.
    """
    try:
        company.is_internal = False
        db.commit()
        logger.info(
            "Rectifier: quarantined company %d (%r) — %s",
            company.id, company.name, reason or "failed rectification",
        )
    except Exception as exc:
        logger.warning("Failed to quarantine company %d: %s", company.id, exc)
        db.rollback()
