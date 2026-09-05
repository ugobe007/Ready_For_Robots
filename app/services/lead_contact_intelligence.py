"""Lead contact intelligence.

Adds phone + LinkedIn person research for buyer leads and records why a profile
was selected (or why manual disambiguation is needed).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional, Sequence
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.services.company_domain import normalize_website_domain
from app.services.shared_api_cache import shared_cache_get, shared_cache_set

logger = logging.getLogger(__name__)

_PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
_PHONE_HINT_RE = re.compile(r"(?i)\b(phone|call|tel|telephone|reach us|contact us)\b")
_ROBOT_HISTORY_RE = re.compile(r"(?i)\b(robot|robotic|automation|amr|agv|cobot|deployment|pilot|rollout)\b")
_COMPETITOR_RE = re.compile(r"(?i)\b(competitor|rival|peer|vs\.|versus)\b")

_TITLE_TOKENS = {
    "ceo", "coo", "cto", "cfo", "president", "vp", "director", "head",
    "operations", "automation", "engineering", "procurement", "supply", "manufacturing",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _compact(value: str, max_len: int = 220) -> str:
    text = _normalize_text(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "..."


def _normalize_phone(raw: str) -> Optional[str]:
    candidate = (raw or "").strip()
    digits = re.sub(r"\D", "", candidate)
    if len(digits) < 10 or len(digits) > 15:
        return None
    if candidate.strip().startswith("+"):
        return "+" + digits
    if len(digits) == 10:
        return f"+1{digits}"
    return "+" + digits


def _extract_phone_candidates_from_text(text: str, source: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not text:
        return out
    for match in _PHONE_RE.finditer(text):
        raw = match.group(0)
        normalized = _normalize_phone(raw)
        if not normalized:
            continue
        window_start = max(0, match.start() - 80)
        window_end = min(len(text), match.end() + 80)
        window = text[window_start:window_end]
        score = 0.45
        reasons = ["Phone-like number pattern found"]
        if _PHONE_HINT_RE.search(window):
            score += 0.25
            reasons.append("Contact language appears near number")
        if "ext" in window.lower() or "x" in window.lower():
            score += 0.05
        out.append(
            {
                "phone": normalized,
                "raw": raw.strip(),
                "source": source,
                "score": min(0.99, round(score, 3)),
                "evidence": _compact(window, 180),
                "reasons": reasons,
            }
        )
    return out


def _fetch_html(url: str, *, timeout: float) -> Optional[str]:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "ReadyForRobots/1.0 (lead contact intelligence)"},
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return None
    if response.status_code >= 400:
        return None
    content_type = (response.headers.get("content-type") or "").lower()
    if content_type and "html" not in content_type and "xhtml" not in content_type:
        return None
    return response.text[:260_000]


def _website_urls_for_phone_lookup(website: Optional[str]) -> list[str]:
    if not website:
        return []
    base = website if "://" in website else f"https://{website}"
    parsed = urlparse(base)
    if not parsed.netloc:
        return []
    root = f"{parsed.scheme}://{parsed.netloc}"
    return [
        root,
        urljoin(root, "/contact"),
        urljoin(root, "/about"),
        urljoin(root, "/team"),
    ]


def _extract_phone_candidates_from_website(website: Optional[str], *, timeout: float) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for url in _website_urls_for_phone_lookup(website):
        if url in seen_urls:
            continue
        seen_urls.add(url)
        html = _fetch_html(url, timeout=timeout)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = str(anchor.get("href") or "")
            if not href.lower().startswith("tel:"):
                continue
            raw = href.split("tel:", 1)[-1]
            normalized = _normalize_phone(raw)
            if not normalized:
                continue
            out.append(
                {
                    "phone": normalized,
                    "raw": raw,
                    "source": url,
                    "score": 0.92,
                    "evidence": "tel: link on company website",
                    "reasons": ["Direct tel link on company website"],
                }
            )
        page_text = soup.get_text(" ", strip=True)
        out.extend(_extract_phone_candidates_from_text(page_text, url))
    return out


def _dedupe_phone_candidates(candidates: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in candidates:
        phone = str(row.get("phone") or "").strip()
        if not phone:
            continue
        current = best.get(phone)
        if current is None or float(row.get("score") or 0) > float(current.get("score") or 0):
            best[phone] = dict(row)
    return sorted(best.values(), key=lambda item: float(item.get("score") or 0), reverse=True)


def _google_search_results(query: str, *, timeout: float, max_results: int = 8) -> list[dict[str, str]]:
    if not query:
        return []
    cache_key = f"google:{query.lower().strip()}"
    cached = shared_cache_get("lead_contact_intel_search", cache_key)
    if isinstance(cached, list):
        return cached

    try:
        response = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": str(max(1, min(max_results, 10))), "hl": "en"},
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return []

    if response.status_code >= 400:
        return []

    soup = BeautifulSoup(response.text[:320_000], "html.parser")
    results: list[dict[str, str]] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "")
        if href.startswith("/url?"):
            parsed = urlparse(href)
            target = (parse_qs(parsed.query).get("q") or [""])[0]
        else:
            target = href
        if not target:
            continue
        low = target.lower()
        if "linkedin.com/in/" not in low:
            continue
        clean_url = target.split("?", 1)[0].rstrip("/")
        if clean_url.lower() in seen:
            continue
        seen.add(clean_url.lower())
        title = ""
        parent = anchor.find_parent()
        if parent is not None:
            h3 = parent.find("h3")
            if h3:
                title = _normalize_text(h3.get_text(" ", strip=True))
        snippet = ""
        if parent is not None:
            snippet = _compact(parent.get_text(" ", strip=True), 260)
        results.append(
            {
                "url": clean_url,
                "title": title,
                "snippet": snippet,
            }
        )
        if len(results) >= max_results:
            break

    shared_cache_set("lead_contact_intel_search", cache_key, results, ttl_sec=12 * 60 * 60)
    return results


def _name_tokens(name: str) -> list[str]:
    return [tok.lower() for tok in re.findall(r"[a-zA-Z]+", name or "") if len(tok) > 1]


def _score_linkedin_candidate(
    candidate: dict[str, str],
    *,
    person_name: str,
    company_name: str,
    person_title: Optional[str],
) -> tuple[float, list[str]]:
    score = 0.2
    reasons: list[str] = []

    url = (candidate.get("url") or "").lower()
    title = (candidate.get("title") or "").lower()
    snippet = (candidate.get("snippet") or "").lower()
    haystack = f"{title} {snippet}"

    tokens = _name_tokens(person_name)
    if tokens and all(tok in url or tok in haystack for tok in tokens[:2]):
        score += 0.34
        reasons.append("Name tokens match URL/title")

    company_tokens = [tok for tok in _name_tokens(company_name) if tok not in {"inc", "llc", "ltd", "corp", "co"}]
    if company_tokens and any(tok in haystack for tok in company_tokens[:3]):
        score += 0.28
        reasons.append("Prospective company appears in result context")

    title_tokens = [tok for tok in _name_tokens(person_title or "") if tok in _TITLE_TOKENS]
    if title_tokens and any(tok in haystack for tok in title_tokens):
        score += 0.16
        reasons.append("Role/title words match result context")

    if "linkedin.com/in/" in url:
        score += 0.08
    if "profile" in snippet:
        score += 0.04

    return min(0.99, round(score, 3)), reasons


def _dedupe_people(raw_people: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in raw_people:
        full_name = _normalize_text(row.get("name"))
        first = _normalize_text(row.get("first_name"))
        last = _normalize_text(row.get("last_name"))
        if full_name and not (first and last):
            parts = full_name.split()
            if len(parts) >= 2:
                first, last = parts[0], parts[-1]
        if not first or not last:
            continue
        key = (first.lower(), last.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "first_name": first,
                "last_name": last,
                "name": f"{first} {last}",
                "title": _normalize_text(row.get("title")) or None,
                "source_url": row.get("source_url"),
            }
        )
    return out


def _decision_makers_from_company(company: Any, contacts: Sequence[Any] | None) -> list[dict[str, Any]]:
    meta = company.crm_metadata if isinstance(getattr(company, "crm_metadata", None), dict) else {}
    raw_people: list[dict[str, Any]] = []
    for row in meta.get("decision_makers") or []:
        if not isinstance(row, dict):
            continue
        raw_people.append(
            {
                "name": row.get("name"),
                "title": row.get("title"),
                "source_url": row.get("source_url"),
            }
        )
    lead_inf = meta.get("lead_inference") if isinstance(meta.get("lead_inference"), dict) else {}
    for row in lead_inf.get("decision_makers") or []:
        if not isinstance(row, dict):
            continue
        raw_people.append(
            {
                "name": row.get("name"),
                "title": row.get("title"),
                "source_url": row.get("source_url"),
            }
        )

    for c in contacts or []:
        first = _normalize_text(getattr(c, "first_name", None))
        last = _normalize_text(getattr(c, "last_name", None))
        if first and last:
            raw_people.append(
                {
                    "first_name": first,
                    "last_name": last,
                    "title": _normalize_text(getattr(c, "title", None)) or None,
                    "source_url": getattr(c, "linkedin_url", None),
                }
            )

    return _dedupe_people(raw_people)[:4]


def _build_disambiguation_payload(
    *,
    person: dict[str, Any],
    company_name: str,
    candidates: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    shortlist = list(candidates)[:4]
    return {
        "status": "required",
        "target_person": person.get("name"),
        "target_company": company_name,
        "reason": "Multiple plausible LinkedIn profiles detected",
        "script": [
            "Open each candidate LinkedIn profile URL and confirm current employer matches the target company.",
            "Prefer profiles where role title aligns with operations, automation, engineering, or procurement decision authority.",
            "Check timeline recency (current role) and public activity related to robotics/automation deployments.",
            "Record final pick with one-sentence justification and keep runner-up as fallback contact.",
        ],
        "candidates": shortlist,
    }


def _discover_linkedin_profiles(
    *,
    company_name: str,
    people: Sequence[dict[str, Any]],
    timeout: float,
) -> dict[str, Any]:
    if not people:
        return {
            "status": "no_people",
            "best_profile": None,
            "people": [],
            "disambiguation": None,
        }

    person_rows: list[dict[str, Any]] = []
    best_global: Optional[dict[str, Any]] = None
    disambiguation: Optional[dict[str, Any]] = None

    for person in people:
        name = str(person.get("name") or "").strip()
        if not name:
            continue
        query = f"site:linkedin.com/in \"{name}\" \"{company_name}\""
        results = _google_search_results(query, timeout=timeout)
        ranked: list[dict[str, Any]] = []
        for row in results:
            score, reasons = _score_linkedin_candidate(
                row,
                person_name=name,
                company_name=company_name,
                person_title=person.get("title"),
            )
            ranked.append(
                {
                    "url": row.get("url"),
                    "title": row.get("title"),
                    "snippet": row.get("snippet"),
                    "score": score,
                    "reasons": reasons,
                    "query": query,
                }
            )
        ranked.sort(key=lambda item: float(item.get("score") or 0), reverse=True)

        best_for_person = ranked[0] if ranked else None
        confidence = "low"
        if best_for_person:
            top_score = float(best_for_person.get("score") or 0)
            second_score = float(ranked[1].get("score") or 0) if len(ranked) > 1 else 0.0
            delta = top_score - second_score
            if top_score >= 0.78 and delta >= 0.18:
                confidence = "high"
            elif top_score >= 0.62 and delta >= 0.12:
                confidence = "medium"
            else:
                confidence = "low"
            if len(ranked) > 1 and delta < 0.12 and top_score >= 0.55 and disambiguation is None:
                disambiguation = _build_disambiguation_payload(
                    person=person,
                    company_name=company_name,
                    candidates=ranked,
                )

        person_row = {
            "person": person,
            "best_profile": best_for_person,
            "candidates": ranked[:5],
            "confidence": confidence,
        }
        person_rows.append(person_row)

        if best_for_person and (
            best_global is None
            or float(best_for_person.get("score") or 0) > float(best_global.get("score") or 0)
        ):
            best_global = {
                **best_for_person,
                "person": name,
                "person_title": person.get("title"),
                "confidence": confidence,
            }

    status = "ready" if best_global else "not_found"
    if disambiguation:
        status = "needs_disambiguation"

    return {
        "status": status,
        "best_profile": best_global,
        "people": person_rows,
        "disambiguation": disambiguation,
    }


def _build_sales_intuition(
    *,
    company: Any,
    signals: Sequence[Any],
    crm_meta: dict[str, Any],
) -> dict[str, Any]:
    lead_inf = crm_meta.get("lead_inference") if isinstance(crm_meta.get("lead_inference"), dict) else {}
    specific_problem = _normalize_text(lead_inf.get("specific_problem"))
    why_items = [str(item) for item in (lead_inf.get("why_lead") or []) if str(item).strip()][:4]

    robot_history: list[dict[str, Any]] = []
    for sig in signals[:16]:
        text = _normalize_text(getattr(sig, "signal_text", ""))
        if not text or not _ROBOT_HISTORY_RE.search(text):
            continue
        robot_history.append(
            {
                "signal_type": getattr(sig, "signal_type", None),
                "summary": _compact(text, 180),
                "source_url": getattr(sig, "source_url", None),
            }
        )
        if len(robot_history) >= 4:
            break

    procurement = lead_inf.get("procurement") if isinstance(lead_inf.get("procurement"), dict) else {}
    timetable = lead_inf.get("timetable") if isinstance(lead_inf.get("timetable"), dict) else {}
    app_areas = [str(item) for item in (lead_inf.get("application_areas") or []) if str(item).strip()][:4]

    opportunity_points: list[str] = []
    if procurement.get("has_rfp"):
        opportunity_points.append("Formal procurement language suggests active vendor selection")
    if timetable.get("window"):
        opportunity_points.append(f"Timeline signal: {timetable.get('window')}")
    if app_areas:
        opportunity_points.append(f"Automation scope includes: {', '.join(app_areas[:3])}")
    if not opportunity_points:
        opportunity_points.append("Lead has qualifying automation intent but still needs tighter buying-process evidence")

    competitor_clues: list[dict[str, Any]] = []
    research_evidence = crm_meta.get("research_evidence") if isinstance(crm_meta.get("research_evidence"), list) else []
    for item in research_evidence[:10]:
        if not isinstance(item, dict):
            continue
        title = _normalize_text(item.get("title"))
        summary = _normalize_text(item.get("summary"))
        blob = f"{title} {summary}"
        if _COMPETITOR_RE.search(blob) or str(item.get("update_type") or "") in {"deployment", "partnership"}:
            competitor_clues.append(
                {
                    "title": _compact(title, 140),
                    "summary": _compact(summary, 170),
                    "source_url": item.get("source_url"),
                    "source_domain": item.get("source_domain"),
                }
            )
        if len(competitor_clues) >= 3:
            break

    for sig in signals[:12]:
        text = _normalize_text(getattr(sig, "signal_text", ""))
        if text and _COMPETITOR_RE.search(text):
            competitor_clues.append(
                {
                    "title": "Competitor usage mention",
                    "summary": _compact(text, 170),
                    "source_url": getattr(sig, "source_url", None),
                    "source_domain": normalize_website_domain(getattr(sig, "source_url", None)),
                }
            )
        if len(competitor_clues) >= 3:
            break

    return {
        "why_sales_lead": {
            "specific_problem": specific_problem or None,
            "reasons": why_items,
        },
        "robot_history": robot_history,
        "larger_opportunity": {
            "industry": getattr(company, "industry", None),
            "points": opportunity_points,
        },
        "competitor_robot_usage": competitor_clues,
    }


def enrich_company_contact_intelligence(
    company: Any,
    signals: Sequence[Any],
    *,
    contacts: Sequence[Any] | None = None,
    timeout: float = 3.5,
) -> dict[str, Any]:
    """Build contact intelligence payload for CRM metadata."""
    crm_meta = company.crm_metadata if isinstance(getattr(company, "crm_metadata", None), dict) else {}
    company_name = str(getattr(company, "name", "") or "").strip()

    signal_text_blob = "\n".join(
        _normalize_text(getattr(sig, "signal_text", ""))
        for sig in (signals or [])[:20]
        if _normalize_text(getattr(sig, "signal_text", ""))
    )
    phone_candidates = _extract_phone_candidates_from_text(signal_text_blob, "signal_text")
    phone_candidates.extend(
        _extract_phone_candidates_from_website(getattr(company, "website", None), timeout=timeout)
    )
    deduped_phones = _dedupe_phone_candidates(phone_candidates)

    people = _decision_makers_from_company(company, contacts)
    linkedin = _discover_linkedin_profiles(
        company_name=company_name,
        people=people,
        timeout=timeout,
    )

    status = "ready"
    if not deduped_phones and not linkedin.get("best_profile"):
        status = "partial"

    return {
        "updated_at": _utcnow(),
        "status": status,
        "phone": {
            "best": deduped_phones[0] if deduped_phones else None,
            "candidates": deduped_phones[:6],
        },
        "linkedin": linkedin,
        "sales_intuition": _build_sales_intuition(
            company=company,
            signals=list(signals or []),
            crm_meta=crm_meta,
        ),
        "data_sources": {
            "google_search": True,
            "website_contact_pages": bool(getattr(company, "website", None)),
            "signal_text": bool(signal_text_blob),
            "decision_makers_count": len(people),
        },
    }
