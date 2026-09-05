"""
Lead relevance evaluation — name extraction + topic fit, not RSS-source guilt.

Google News RSS often wraps real headlines in HTML. This module:
  1. Strips HTML and dedupes signal phrases
  2. Extracts company names from clean text (multiple strategies)
  3. Scores relevancy to the scraper-assigned industry / vertical
  4. Returns a disposition (keep | enrich | rename | review | junk)

RSS HTML ratio is a *quality signal*, never an automatic delete gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Sequence, Tuple

from app.services.industry_inference import (
    effective_industry_for_lead,
    infer_industry_from_text,
    infer_industry_scores,
    known_industry_for_company_name,
)
from app.services.industry_sector_ontology import (
    normalize_term,
    text_matches_subject_inference,
)
from app.services.known_brands import is_allowlisted_company_name
from app.services.lead_filter import is_junk
from app.services.signal_text_normalize import strip_signal_html
from app.services.rss_noise_lead import _GOOGLE_RSS_HTML_RE

# Minimum confidence to auto-rename on --apply
RENAME_CONFIDENCE_MIN = 0.72

_DISPOSITIONS = frozenset({"keep", "enrich", "rename", "review", "junk"})


@dataclass
class ExtractedName:
    name: str
    source: str
    confidence: float


@dataclass
class LeadRelevanceReport:
    company_id: int
    stored_name: str
    stored_industry: str
    suggested_name: Optional[str] = None
    extracted_names: List[ExtractedName] = field(default_factory=list)
    clean_text_blob: str = ""
    deduped_phrases: List[str] = field(default_factory=list)
    deduped_word_count: int = 0
    industry_from_name: Optional[str] = None
    industry_from_text: str = "Unknown"
    effective_industry: str = "Unknown"
    industry_alignment_score: float = 0.0
    topic_relevance_score: float = 0.0
    buyer_intent_score: float = 0.0
    rss_html_ratio: float = 0.0
    disposition: str = "review"
    disposition_reason: str = ""
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["extracted_names"] = [asdict(n) for n in self.extracted_names]
        return d


def dedupe_word_strings(texts: Sequence[str]) -> Tuple[str, List[str], int]:
    """
    Dedupe signal phrases (case-insensitive) and return:
      - joined clean blob
      - unique phrase list (longest first)
      - count of unique normalized word tokens across phrases
    """
    seen_phrase_keys: set[str] = set()
    phrases: List[str] = []

    for raw in texts or []:
        clean = strip_signal_html(str(raw or ""))
        if len(clean) < 6:
            continue
        key = normalize_term(clean)
        if not key or key in seen_phrase_keys:
            continue
        seen_phrase_keys.add(key)
        phrases.append(clean)

    phrases.sort(key=len, reverse=True)

    seen_tokens: set[str] = set()
    for phrase in phrases:
        for tok in normalize_term(phrase).split():
            if len(tok) >= 2:
                seen_tokens.add(tok)

    blob = " ".join(phrases)
    return blob, phrases, len(seen_tokens)


def _rss_html_ratio(signals: Sequence[object]) -> float:
    texts = [str(getattr(s, "signal_text", None) or "") for s in signals or []]
    if not texts:
        return 0.0
    hits = sum(1 for t in texts if _GOOGLE_RSS_HTML_RE.search(t))
    return hits / len(texts)


def _extract_names_from_text(
    text: str,
    *,
    db_lookup: Optional[dict] = None,
) -> List[ExtractedName]:
    """Run headline / actor / scraper extractors on one clean string."""
    if not text or len(text) < 10:
        return []

    from app.scrapers.news_scraper import extract_company_from_article_text
    from app.services.company_name_inference import extract_company_name_from_headline
    from app.services.headline_parser import extract_actor

    out: List[ExtractedName] = []

    pair = extract_company_from_article_text(text, db_lookup=db_lookup)
    if pair and pair[0]:
        conf = 0.82 if known_industry_for_company_name(pair[0]) else 0.74
        out.append(ExtractedName(pair[0], "article_extractor", conf))

    actor = extract_actor(text)
    if actor:
        conf = 0.78 if known_industry_for_company_name(actor) else 0.68
        out.append(ExtractedName(actor, "headline_actor", conf))

    headline = extract_company_name_from_headline(text)
    if headline:
        conf = 0.70 if known_industry_for_company_name(headline) else 0.58
        out.append(ExtractedName(headline, "headline_subject", conf))

    return out


def extract_candidate_names(
    stored_name: str,
    clean_phrases: Sequence[str],
    *,
    db_lookup: Optional[dict] = None,
) -> List[ExtractedName]:
    """Collect name candidates from stored label + deduped signal phrases."""
    candidates: List[ExtractedName] = []
    name = (stored_name or "").strip()

    if name:
        junk, _ = is_junk(name)
        if not junk:
            conf = 0.88 if known_industry_for_company_name(name) else 0.62
            candidates.append(ExtractedName(name, "stored_name", conf))
        elif known_industry_for_company_name(name) or _looks_like_brand_label(name):
            candidates.append(ExtractedName(name, "stored_name_brand", 0.55))

    for phrase in list(clean_phrases or [])[:10]:
        candidates.extend(_extract_names_from_text(phrase, db_lookup=db_lookup))

    return _dedupe_name_candidates(candidates)


def _looks_like_brand_label(name: str) -> bool:
    from app.services.known_brands import is_allowlisted_company_name

    if is_allowlisted_company_name(name):
        return True
    words = name.split()
    if 1 <= len(words) <= 5 and name[0].isupper():
        return True
    return False


def _dedupe_name_candidates(candidates: List[ExtractedName]) -> List[ExtractedName]:
    """Merge by normalized name; keep highest confidence per name."""
    best: dict[str, ExtractedName] = {}
    for c in candidates:
        key = normalize_term(c.name)
        if not key:
            continue
        prev = best.get(key)
        if prev is None or c.confidence > prev.confidence:
            best[key] = c
    return sorted(best.values(), key=lambda x: (-x.confidence, -len(x.name)))


def _token_overlap(a: str, b: str) -> bool:
    import re

    ta = {t for t in re.findall(r"[a-z0-9]+", (a or "").lower()) if len(t) >= 3}
    tb = {t for t in re.findall(r"[a-z0-9]+", (b or "").lower()) if len(t) >= 3}
    return bool(ta and tb and (ta & tb))


def _rename_is_safe(stored_name: str, candidate: ExtractedName) -> bool:
    """Only rename when stored label is broken and candidate is a cleaner company name."""
    from app.services.company_name_inference import should_attempt_name_fix

    stored = (stored_name or "").strip()
    new = (candidate.name or "").strip()
    if not stored or not new or normalize_term(stored) == normalize_term(new):
        return False

    junk_new, _ = is_junk(new)
    if junk_new:
        return False

    stored_known = bool(
        known_industry_for_company_name(stored) or is_allowlisted_company_name(stored)
    )
    if stored_known and not _token_overlap(stored, new):
        return False

    # Do not replace a short clean legal name with a longer headline span.
    if not should_attempt_name_fix(stored) and len(stored.split()) <= 6:
        return False
    if len(new) > max(len(stored) * 1.35, len(stored) + 18):
        return False

    if should_attempt_name_fix(stored):
        return candidate.confidence >= 0.65

    if stored_known and _token_overlap(stored, new) and len(new) <= len(stored):
        return candidate.confidence >= RENAME_CONFIDENCE_MIN

    return False


def _pick_suggested_name(
    stored_name: str,
    candidates: Sequence[ExtractedName],
) -> Optional[str]:
    if not candidates:
        return None
    for cand in candidates:
        if _rename_is_safe(stored_name, cand):
            return cand.name
    return None


def _industry_alignment_score(
    stored_industry: str,
    name: str,
    text_blob: str,
) -> Tuple[float, str, Optional[str], List[str]]:
    """Score 0–1 how well name + text align with stored industry."""
    stored = (stored_industry or "").strip() or "Unknown"
    evidence: List[str] = []

    known = known_industry_for_company_name(name)
    if known:
        evidence.append(f"known_brand→{known}")
        if known == stored or stored.lower() in ("unknown", "new", "other", ""):
            return 0.95, known, known, evidence
        # Known brand in a different stored bucket — still valuable
        return 0.72, known, known, evidence + [f"stored={stored}"]

    if stored.lower() not in ("unknown", "new", "other", ""):
        scores = infer_industry_scores(text_blob, company_name=name)
        stored_hits = scores.get(stored, 0)
        if stored_hits > 0:
            evidence.append(f"keyword_hits_{stored}={stored_hits}")
        if text_matches_subject_inference(text_blob, stored):
            evidence.append(f"subject_inference:{stored}")
            stored_hits += 2
        max_hits = max(scores.values()) if scores else 0
        if stored_hits >= 2 and stored_hits >= max_hits:
            return min(0.9, 0.45 + stored_hits * 0.08), stored, known, evidence
        if stored_hits >= 1:
            return 0.42, stored, known, evidence

    inferred = infer_industry_from_text(f"{name} {text_blob}")
    evidence.append(f"inferred={inferred}")
    if inferred != "Unknown" and inferred == stored:
        return 0.75, inferred, known, evidence
    if inferred != "Unknown":
        return 0.35, inferred, known, evidence
    return 0.15, stored, known, evidence


def _buyer_intent_score(text_blob: str, industry: Optional[str]) -> float:
    if not text_blob or len(text_blob) < 20:
        return 0.0
    try:
        from app.services.inference_engine import analyze

        intent = analyze(text_blob[:4000], industry=industry)
        return float(intent.overall_intent or 0.0)
    except Exception:
        return 0.0


def _topic_relevance_score(
    *,
    alignment: float,
    intent: float,
    has_valid_name: bool,
    phrase_count: int,
    word_count: int,
) -> float:
    score = alignment * 0.55 + min(intent, 0.5) * 0.35
    if has_valid_name:
        score += 0.08
    if phrase_count >= 2:
        score += 0.04
    if word_count >= 12:
        score += 0.03
    return round(min(1.0, score), 3)


def _decide_disposition(
    *,
    stored_name: str,
    suggested_name: Optional[str],
    candidates: Sequence[ExtractedName],
    topic_score: float,
    intent: float,
    alignment: float,
    rss_ratio: float,
    industry_known: bool,
) -> Tuple[str, str]:
    junk_stored, junk_reason = is_junk(stored_name)
    best_name = (suggested_name or stored_name or "").strip()
    has_strong_name = any(
        c.confidence >= 0.65 and not is_junk(c.name)[0] for c in candidates
    )

    if suggested_name and normalize_term(suggested_name) != normalize_term(stored_name):
        if topic_score >= 0.35 or industry_known:
            return "rename", f"extracted clearer name {suggested_name!r} from signal text"

    if industry_known or topic_score >= 0.48 or intent >= 0.18:
        if rss_ratio >= 0.6 and topic_score < 0.65:
            return "enrich", "valid buyer; RSS-heavy signals need clean text / secondary pass"
        return "keep", "name and topic align with assigned vertical"

    if has_strong_name and (alignment >= 0.35 or intent >= 0.12):
        if rss_ratio >= 0.5:
            return "enrich", "recognizable name with thin RSS copy — re-scrape recommended"
        return "review", "recognizable name; weak topic match — manual or secondary pass"

    if topic_score >= 0.28:
        return "review", "borderline relevance — inspect before delete"

    if junk_stored and not has_strong_name and topic_score < 0.25:
        return "junk", junk_reason or "headline fragment with no buyer signal"

    if junk_stored and not has_strong_name and intent < 0.08 and topic_score < 0.22:
        return "junk", junk_reason or "headline fragment with no buyer signal"

    return "review", "insufficient evidence to auto-delete"


def evaluate_lead_relevance(
    company: object,
    signals: Sequence[object],
    *,
    db_lookup: Optional[dict] = None,
) -> LeadRelevanceReport:
    """
    Evaluate one company row + signals.

    ``company`` needs ``id``, ``name``, ``industry`` attributes.
    """
    company_id = int(getattr(company, "id", 0) or 0)
    stored_name = (getattr(company, "name", None) or "").strip()
    stored_industry = (getattr(company, "industry", None) or "").strip() or "Unknown"

    raw_texts = [str(getattr(s, "signal_text", None) or "") for s in signals or []]
    blob, phrases, word_count = dedupe_word_strings(raw_texts)
    rss_ratio = _rss_html_ratio(signals)

    candidates = extract_candidate_names(stored_name, phrases, db_lookup=db_lookup)
    suggested = _pick_suggested_name(stored_name, candidates)
    eval_name = suggested or stored_name or (candidates[0].name if candidates else "")

    alignment, inferred_text, known_ind, align_evidence = _industry_alignment_score(
        stored_industry, eval_name, blob
    )
    effective = effective_industry_for_lead(eval_name, stored_industry, signals)
    intent = _buyer_intent_score(blob, stored_industry if stored_industry != "Unknown" else effective)

    has_valid_name = bool(
        candidates
        and candidates[0].confidence >= 0.55
        and (
            known_industry_for_company_name(candidates[0].name)
            or not is_junk(candidates[0].name)[0]
        )
    )

    topic = _topic_relevance_score(
        alignment=alignment,
        intent=intent,
        has_valid_name=has_valid_name,
        phrase_count=len(phrases),
        word_count=word_count,
    )

    disposition, reason = _decide_disposition(
        stored_name=stored_name,
        suggested_name=suggested,
        candidates=candidates,
        topic_score=topic,
        intent=intent,
        alignment=alignment,
        rss_ratio=rss_ratio,
        industry_known=bool(known_ind),
    )

    evidence = list(align_evidence)
    if rss_ratio >= 0.5:
        evidence.append(f"rss_html_ratio={rss_ratio:.2f} (quality flag only)")
    evidence.append(f"topic_relevance={topic:.2f}")
    evidence.append(f"buyer_intent={intent:.3f}")

    return LeadRelevanceReport(
        company_id=company_id,
        stored_name=stored_name,
        stored_industry=stored_industry,
        suggested_name=suggested,
        extracted_names=candidates[:8],
        clean_text_blob=blob[:2000],
        deduped_phrases=phrases[:12],
        deduped_word_count=word_count,
        industry_from_name=known_ind,
        industry_from_text=inferred_text,
        effective_industry=effective,
        industry_alignment_score=round(alignment, 3),
        topic_relevance_score=topic,
        buyer_intent_score=round(intent, 3),
        rss_html_ratio=round(rss_ratio, 3),
        disposition=disposition,
        disposition_reason=reason,
        evidence=evidence,
    )


def should_delete_as_junk(report: LeadRelevanceReport) -> Tuple[bool, str]:
    """
    Replacement gate for RSS-only deletion: only True when disposition is junk
    AND topic score is very low (never because RSS ratio alone).
    """
    if report.disposition != "junk":
        return False, ""
    if report.topic_relevance_score >= 0.25:
        return False, "topic_relevance blocks auto-delete"
    if report.industry_from_name:
        return False, f"known brand {report.industry_from_name}"
    return True, report.disposition_reason
