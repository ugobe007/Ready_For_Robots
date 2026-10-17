"""Facts from a source document, each with a quote that is in the text.

Same shape as robot extraction: a fact is kept only when its quote is in the
page. Rules then map those quotes onto the closed taxonomy. A buyer row opens
only when one quote names the work and another (or the same one) names a
taxonomy industry.

This does not write the database and does not fetch during a FIND request.
FIND, when ``RFR_FIND_SIGNAL_ROWS`` is on, reads the stored quote rows.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.services.buyer_opportunity.signal_buyer_rows import BUDGET_CONFIRMED
from app.services.robot_understanding_v1.taxonomy_extraction import validate_evidence

_ROWS_PATH = Path(__file__).with_name("source_quote_rows.json")

# First match wins. The phrase is the work, not a nearby noun.
_WORK_RULES: tuple[tuple[re.Pattern[str], str, str, str], ...] = (
    (
        re.compile(r"grocery (?:order[- ])?pickup|grocery order-picking|storage and retrieval robotics", re.I),
        "picking_packing_palletizing",
        "pick_pack",
        "Grocery pickup",
    ),
    (
        re.compile(r"palletiz\w*|order[- ]?pick(?:ing)?|pick and pack|case pick", re.I),
        "picking_packing_palletizing",
        "pick_pack",
        "Order picking",
    ),
    (
        re.compile(r"drone (?:food )?delivery|\bfood delivery\b", re.I),
        "delivery_transport",
        "transport",
        "Food delivery",
    ),
    (
        re.compile(r"automated makeline|peel, cut and core", re.I),
        "food_beverage_prep",
        "beverage",
        "Food prep",
    ),
    (
        re.compile(r"restroom clean\w*|floor (?:scrub|clean)\w*", re.I),
        "cleaning",
        "scrub",
        "Floor cleaning",
    ),
    (
        re.compile(r"surveillance robot|security patrol|high-frequency patrol", re.I),
        "security_patrol",
        "inspect",
        "Security patrol",
    ),
    (
        re.compile(r"shelf scan\w*", re.I),
        "inspection",
        "shelf_scan",
        "Shelf scan",
    ),
    (
        re.compile(r"disinfect\w*|uv sanit\w*", re.I),
        "disinfection",
        "disinfection",
        "Disinfection",
    ),
    (
        re.compile(r"machine tending", re.I),
        "machine_tending_assembly",
        "machine_tending",
        "Machine tending",
    ),
    (
        re.compile(r"\bweed(?:ing)?\b|\bharvest(?:ing)?\b", re.I),
        "agricultural_task",
        "agriculture",
        "Farm work",
    ),
)

_INDUSTRY_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bambulance surgery\b|\bambulatory surgery\b|\bsurgery centers?\b", re.I), "surgery_center"),
    (re.compile(r"\bhospitals?\b", re.I), "hospital"),
    (re.compile(r"\bairports?\b", re.I), "airport"),
    (re.compile(r"\bhotels?\b", re.I), "hotel"),
    (re.compile(r"quick-service|fast food|\bqsr\b", re.I), "qsr_fast_food"),
    (re.compile(r"\brestaurants?\b", re.I), "restaurant"),
    (re.compile(r"\bgrocery\b|\bgroceries\b", re.I), "grocery"),
    (re.compile(r"\bwarehouses?\b", re.I), "warehouse_distribution"),
    (re.compile(r"\bfarms?\b|\bfarming\b", re.I), "agriculture"),
    (re.compile(r"\bconstruction\b|\bjobsites?\b", re.I), "construction"),
    (re.compile(r"\bgovernment\b|\bministry\b", re.I), "government"),
)

# Named in the text, and not a taxonomy function. Recorded, never a row.
_UNMAPPED_WORK: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"autonomous shuttles?|automated transit", re.I), "passenger shuttle"),
    (re.compile(r"automated cold storage|cutting edge automation", re.I), "warehouse automation"),
    (re.compile(r"\bguest experience\b", re.I), "guest experience"),
    (re.compile(r"\bsmart farming\b", re.I), "smart farming"),
)

_CHROME = re.compile(
    r"skip to main|newsletter|sign up|sign in|cookie|all rights reserved|subscribe|"
    r"dive brief|people also ask|continue to site|next article|related articles",
    re.I,
)
_SELLER = re.compile(
    r"\b(manufacturing of|robot maker|design, development, and manufacturing|"
    r"robotics company dedicated to developing)\b",
    re.I,
)
_SITE = re.compile(
    r"\b(?:in|at|of)\s+(?:a\s+)?((?:[A-Z][a-z]+\s+){0,2}[A-Z][a-z]+(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)?)"
)
_DEADLINE = re.compile(
    r"\b(end of this year|three-month|by the end|deadline|due by|starting\s+"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2})\b",
    re.I,
)
_FULL_DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
)
_BUDGET = re.compile(r"\$\s?\d|\b\d+(?:\.\d+)?\s+million\b", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
_STOP_TOKENS = frozenset({"and", "the", "for", "with", "from", "new", "approves", "that", "this"})


def load_source_quote_rows() -> list[dict[str, Any]]:
    """Rows already read from source documents. No network, no database."""
    if not _ROWS_PATH.is_file():
        return []
    payload = json.loads(_ROWS_PATH.read_text())
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    return [row for row in rows or [] if isinstance(row, dict)]


def sentences(text: str) -> list[str]:
    raw = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+", raw)
    return [part.strip() for part in parts if len(part.strip()) >= 40]


def _chrome(sentence: str) -> bool:
    return bool(_CHROME.search(sentence)) or sentence.count(",") >= 8


def _article_sentence(sentence: str) -> str | None:
    """Drop nav chrome. Keep the article sentence that follows a 'Dive Brief:' label."""
    if sentence.count(",") >= 8:
        return None
    if not _CHROME.search(sentence):
        return sentence
    match = re.search(r"Dive Brief:\s*(.+)$", sentence)
    if match and len(match.group(1).strip()) >= 40:
        return match.group(1).strip()
    return None


def company_tokens(name: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z'&-]{3,}", name or "")
    return [word for word in words if word.lower() not in _STOP_TOKENS]


def _mentions_company(sentence: str, tokens: list[str]) -> bool:
    lowered = sentence.lower()
    return any(token.lower() in lowered for token in tokens)


def _about_this_buyer(sentence: str, previous: list[str], tokens: list[str]) -> bool:
    """A sidebar story that never names this company is not its work."""
    if _mentions_company(sentence, tokens):
        return True
    if re.search(r"\bthe (company|retailer|chain)\b", sentence, re.I):
        return True
    if previous and re.search(r"\b(it|its)\b", sentence, re.I):
        prev = previous[-1]
        if _mentions_company(prev, tokens) or re.search(r"\bthe (company|retailer|chain)\b", prev, re.I):
            return True
    return False


def _quote(sentence: str, page_text: str) -> str | None:
    if not validate_evidence(sentence, page_text):
        return None
    return sentence


def _focus(sentence: str, pattern: re.Pattern[str], page_text: str, limit: int = 260) -> str:
    """A long nav-less block still has to yield a quote a person can read."""
    if len(sentence) <= limit:
        return sentence
    match = pattern.search(sentence)
    if not match:
        return sentence
    start = max(0, match.start() - 90)
    end = min(len(sentence), match.end() + 140)
    if start:
        space = sentence.find(" ", start)
        if 0 <= space < match.start():
            start = space + 1
    if end < len(sentence):
        space = sentence.rfind(" ", match.end(), end)
        if space > match.end():
            end = space
    snippet = sentence[start:end].strip(" -")
    if pattern.search(snippet) and validate_evidence(snippet, page_text):
        return snippet
    return sentence


def _work(sentence: str) -> tuple[str, str, str] | None:
    for pattern, function, family, title in _WORK_RULES:
        if pattern.search(sentence):
            return function, family, title
    return None


def _industry(sentence: str) -> str | None:
    for pattern, industry in _INDUSTRY_RULES:
        if pattern.search(sentence):
            return industry
    return None


def _unmapped(sentence: str) -> str | None:
    for pattern, label in _UNMAPPED_WORK:
        if pattern.search(sentence):
            return label
    return None


def _seller(page_text: str, tokens: list[str]) -> bool:
    for sentence in sentences(page_text):
        if _SELLER.search(sentence) and _mentions_company(sentence, tokens):
            return True
    return False


def _fact(field: str, sentence: str, page_text: str, *, value: str | None = None) -> dict[str, Any] | None:
    quote = _quote(sentence, page_text)
    if quote is None:
        return None
    fact: dict[str, Any] = {"field": field, "quote": quote}
    if value:
        fact["value"] = value
    return fact


def _window(index: int, rows: list[str]) -> list[str]:
    return rows[index : index + 3]


def _pick(window: list[str], pattern: re.Pattern[str]) -> str | None:
    for sentence in window:
        if pattern.search(sentence):
            return sentence
    return None


def read_document(
    page_text: str,
    *,
    company_name: str,
    source_url: str | None = None,
    signal_date: str | None = None,
    company_id: int | str | None = None,
) -> dict[str, Any]:
    """Extract facts and open rows. Quotes are sentences from ``page_text``."""
    tokens = company_tokens(company_name)
    usable = [kept for sentence in sentences(page_text) if (kept := _article_sentence(sentence))]
    facts: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    seller = _seller(page_text, tokens)
    rows: list[dict[str, Any]] = []
    seen_functions: set[str] = set()

    for index, sentence in enumerate(usable):
        if "ROBOT TASK SIGNAL" in sentence:
            continue
        if not _about_this_buyer(sentence, usable[:index], tokens):
            continue
        work = _work(sentence)
        if work is None:
            unmapped = _unmapped(sentence)
            if unmapped and not any(gap.get("work") == unmapped for gap in gaps):
                quote = _quote(sentence, page_text)
                if quote:
                    gaps.append({"reason": "no_named_workflow", "work": unmapped, "quote": quote})
            continue
        function, family, title = work
        if function in seen_functions:
            continue
        seen_functions.add(function)
        work_fact = _fact("work", sentence, page_text, value=function)
        if work_fact is None:
            continue
        work_pattern = next(pattern for pattern, *_rest in _WORK_RULES if pattern.search(sentence))
        work_fact["quote"] = _focus(sentence, work_pattern, page_text)
        work_fact["title"] = title
        facts.append(work_fact)

        window = _window(index, usable)
        industry = _industry(sentence)
        industry_sentence = sentence if industry else None
        if industry is None:
            for follow in window[1:]:
                if not (_mentions_company(follow, tokens) or re.search(r"\bpilot", follow, re.I)):
                    continue
                industry = _industry(follow)
                if industry:
                    industry_sentence = follow
                    break
        industry_quote = None
        if industry and industry_sentence:
            industry_fact = _fact("industry", industry_sentence, page_text, value=industry)
            if industry_fact:
                industry_pattern = next(
                    pattern for pattern, key in _INDUSTRY_RULES if key == industry and pattern.search(industry_sentence)
                )
                industry_fact["quote"] = _focus(industry_sentence, industry_pattern, page_text)
                facts.append(industry_fact)
                industry_quote = industry_fact["quote"]
        site_sentence = _pick(window, _SITE)
        site_quote = None
        if site_sentence:
            site_fact = _fact("site", site_sentence, page_text)
            if site_fact:
                match = _SITE.search(site_sentence)
                if match:
                    site_fact["value"] = " ".join(match.group(1).split())
                site_fact["quote"] = _focus(site_sentence, _SITE, page_text)
                facts.append(site_fact)
                site_quote = site_fact["quote"]
        deadline_sentence = _pick(window, _DEADLINE)
        deadline_quote = None
        expiry = None
        if deadline_sentence:
            deadline_fact = _fact("deadline", deadline_sentence, page_text)
            if deadline_fact:
                full = _FULL_DATE.search(deadline_sentence)
                if full:
                    deadline_fact["value"] = full.group(0)
                    expiry = full.group(0)
                deadline_fact["quote"] = _focus(deadline_sentence, _DEADLINE, page_text)
                facts.append(deadline_fact)
                deadline_quote = deadline_fact["quote"]
        budget_sentence = next(
            (
                follow
                for follow in window
                if _BUDGET.search(follow) and not re.search(r"sold for", follow, re.I)
            ),
            None,
        )
        budget_quote = None
        if budget_sentence:
            budget_fact = _fact("budget", budget_sentence, page_text)
            if budget_fact:
                facts.append(budget_fact)
                budget_quote = budget_fact["quote"]
        contact_sentence = next(
            (
                follow
                for follow in window
                if _EMAIL.search(follow)
                and re.search(r"\bcontact\b", follow, re.I)
                and not re.search(r"reporter|tips\b", follow, re.I)
                and _mentions_company(follow, tokens)
            ),
            None,
        )
        contact_quote = None
        if contact_sentence:
            contact_fact = _fact("contact", contact_sentence, page_text)
            if contact_fact:
                contact_fact["value"] = _EMAIL.search(contact_sentence).group(0)
                facts.append(contact_fact)
                contact_quote = contact_fact["quote"]

        if seller:
            gaps.append(
                {
                    "reason": "seller_not_buyer",
                    "workflow": function,
                    "quote": work_fact["quote"],
                }
            )
            continue
        if not industry or not industry_sentence:
            note = None
            if function == "delivery_transport" and re.search(r"food delivery", sentence, re.I):
                note = (
                    "food delivery is not a taxonomy industry; "
                    "restaurant applies when the quote says restaurant"
                )
            gaps.append(
                {
                    "reason": "no_taxonomy_industry",
                    "workflow": function,
                    "quote": work_fact["quote"],
                    "note": note,
                }
            )
            continue
        rows.append(
            {
                "job_key": f"source-{company_id}-{function}",
                "title": title,
                "industry": industry,
                "path": title,
                "company_name": company_name,
                "locality": None,
                "tape_family": family,
                "source": "signal",
                "source_url": source_url,
                "readiness_label": BUDGET_CONFIRMED,
                "why_now": work_fact["quote"],
                "workflow": function,
                "signal_date": signal_date,
                "signal_expiry": expiry,
                "quotes": {
                    "work": work_fact["quote"],
                    "industry": industry_quote,
                    "site": site_quote,
                    "deadline": deadline_quote,
                    "budget": budget_quote,
                    "contact": contact_quote,
                },
                "unknowns": [],
            }
        )
    return {
        "company_name": company_name,
        "source_url": source_url,
        "seller": seller,
        "facts": facts,
        "gaps": gaps,
        "rows": rows,
    }


def named_workflow(text: str) -> str | None:
    """A posting names a workflow when a work rule matches. A job title does not.

    A ``ROBOT TASK SIGNAL`` line is our own stamp, not the employer's words.
    """
    for sentence in sentences(text) or [text or ""]:
        if _chrome(sentence) or "ROBOT TASK SIGNAL" in sentence:
            continue
        work = _work(sentence)
        if work:
            return work[0]
    return None


def publisher_from_batch_response(body: str) -> str | None:
    """Publisher URL from a Google News batchexecute body. None when it is absent."""
    plain = (body or "").replace("\\/", "/").replace('\\"', '"')
    match = re.search(r'\["garturlres","(https?:[^"]+)"', plain)
    if not match:
        return None
    url = match.group(1)
    if "news.google.com" in url:
        return None
    return url
