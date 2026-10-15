"""Per-company industry check for synonym rows with needs_company_check = yes.

For each company, read its own website (homepage plus one about page) and pick
industries from that row's candidate_industries, each with an evidence quote.
A pick counts only if the industry is a candidate and its quote is a passage of
the fetched page text (same normalized check as the robot classifier). With no
valid pick the company goes to the review list, with the row's default as a
suggestion. Writes nothing to the database.
"""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterable
from urllib.parse import urljoin, urlsplit

from app.services.buyer_opportunity.backfill_report import classify_companies, load_synonyms
from app.services.robot_understanding_v1.taxonomy_extraction import load_taxonomy, validate_evidence

CHECK_MODEL = "claude-sonnet-4-6"
MIN_QUOTE_WORDS = 4
PAGE_TEXT_CAP = 12_000
ABOUT_LINK = re.compile(r"\b(about|who we are|our company|company overview|our story)\b", re.I)
ABOUT_PATHS = ("/about", "/about-us", "/company")
TOOL_NAME = "choose_industries"


@dataclass
class CompanyToCheck:
    company_id: int
    name: str
    domain: str | None
    raw_value: str
    candidates: list[str]
    default: list[str]
    notes: str = ""


@dataclass
class SitePage:
    url: str
    text: str


@dataclass
class Decision:
    company_id: int
    name: str
    domain: str | None
    raw_value: str
    status: str  # "decided" | "review"
    industries: list[str] = field(default_factory=list)
    evidence: list[dict[str, str]] = field(default_factory=list)
    suggestion: list[str] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)
    reason: str = ""
    rejected: list[dict[str, str]] = field(default_factory=list)
    pages: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def companies_to_check(conn, synonyms: dict[str, dict[str, Any]] | None = None) -> list[CompanyToCheck]:
    synonyms = synonyms if synonyms is not None else load_synonyms()
    out = []
    for item in classify_companies(conn, synonyms):
        if item["bucket"] != "needs_company_check":
            continue
        c, entry = item["company"], item["entry"]
        out.append(CompanyToCheck(
            company_id=c["id"], name=c["name"], domain=item["domain"], raw_value=entry["raw_value"],
            candidates=entry["candidates"], default=entry["default"], notes=entry["notes"],
        ))
    return out


def _same_site(url: str, domain: str) -> bool:
    host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
    return host == domain or host.endswith("." + domain)


def gather_site_pages(domain: str, fetch: Callable[[str], Any]) -> list[SitePage]:
    """Homepage plus the first about page that has text. Only the company's own host."""
    pages: list[SitePage] = []
    home = fetch(f"https://{domain}/")
    home_text = (getattr(home, "text", "") or "").strip()
    if home_text:
        pages.append(SitePage(getattr(home, "final_url", None) or f"https://{domain}/", home_text))
    about_urls = [
        urljoin(f"https://{domain}/", href)
        for href, anchor in (getattr(home, "links", None) or [])
        if ABOUT_LINK.search(anchor or "") or ABOUT_LINK.search(urlsplit(href or "").path.replace("-", " "))
    ]
    about_urls += [f"https://{domain}{p}" for p in ABOUT_PATHS]
    seen = {p.url.rstrip("/") for p in pages}
    for url in dict.fromkeys(about_urls):
        if url.rstrip("/") in seen or not _same_site(url, domain):
            continue
        page = fetch(url)
        text = (getattr(page, "text", "") or "").strip()
        if text and text != home_text:
            pages.append(SitePage(getattr(page, "final_url", None) or url, text))
            break
    return pages


def build_prompt(company: CompanyToCheck, pages: list[SitePage], taxonomy: dict[str, Any]) -> str:
    industries = taxonomy["industries"]
    lines = [
        f"Company: {company.name} ({company.domain})",
        f"Industry label in our database: {company.raw_value!r}",
        "",
        "INDUSTRY DEFINITION:",
        industries["_definition"],
        "",
        "Choose which of these industries this company is in, using only its own website text below:",
        *[f"- {key}: {industries[key]}" for key in company.candidates],
    ]
    if company.notes:
        lines += ["", f"Mapping note: {company.notes}"]
    lines += [
        "",
        "RULES:",
        "1. Pick an industry only if the website text shows the company itself operates in it.",
        "   The industry of the company's customers does not count.",
        "2. For every pick, quote ONE contiguous passage copied exactly from the page text,",
        f"   at least {MIN_QUOTE_WORDS} words, character for character. No '...', no rewording.",
        "3. If the text does not clearly support any candidate, return no picks and say why.",
        "",
    ]
    for page in pages:
        lines += [f"PAGE {page.url}:", page.text[:PAGE_TEXT_CAP], ""]
    return "\n".join(lines)


def _tool(candidates: list[str]) -> dict[str, Any]:
    return {
        "name": TOOL_NAME,
        "description": "Industries the company is in, each with an exact quote from its website.",
        "input_schema": {
            "type": "object",
            "properties": {
                "picks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "industry": {"type": "string", "enum": candidates},
                            "quote": {"type": "string"},
                        },
                        "required": ["industry", "quote"],
                    },
                },
                "no_pick_reason": {"type": "string"},
            },
            "required": ["picks"],
        },
    }


def anthropic_chooser(client: Any = None) -> Callable[[CompanyToCheck, list[SitePage], dict[str, Any]], dict[str, Any]]:
    if client is None:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def choose(company: CompanyToCheck, pages: list[SitePage], taxonomy: dict[str, Any]) -> dict[str, Any]:
        response = client.messages.create(
            model=CHECK_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": build_prompt(company, pages, taxonomy)}],
            tools=[_tool(company.candidates)],
            tool_choice={"type": "tool", "name": TOOL_NAME},
        )
        result = next((b.input for b in response.content if b.type == "tool_use" and b.name == TOOL_NAME), None)
        return result or {"picks": [], "no_pick_reason": "model returned no tool call"}

    return choose


def check_company(
    company: CompanyToCheck,
    *,
    fetch: Callable[[str], Any],
    choose: Callable[[CompanyToCheck, list[SitePage], dict[str, Any]], dict[str, Any]],
    taxonomy: dict[str, Any] | None = None,
) -> Decision:
    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    decision = Decision(
        company_id=company.company_id, name=company.name, domain=company.domain,
        raw_value=company.raw_value, status="review", suggestion=list(company.default),
        candidates=list(company.candidates),
    )
    if not company.domain:
        decision.reason = "no website on record"
        return decision
    try:
        pages = gather_site_pages(company.domain, fetch)
    except Exception as exc:
        decision.reason = f"website fetch failed: {type(exc).__name__}"
        return decision
    decision.pages = [p.url for p in pages]
    if not pages:
        decision.reason = "website returned no readable text"
        return decision
    try:
        result = choose(company, pages, taxonomy)
    except Exception as exc:
        decision.reason = f"model call failed: {type(exc).__name__}"
        return decision

    for pick in result.get("picks") or []:
        industry = str(pick.get("industry") or "").strip()
        quote = " ".join(str(pick.get("quote") or "").split())
        page = next((p for p in pages if validate_evidence(quote, p.text)), None)
        if industry not in company.candidates:
            why = "not a candidate"
        elif len(quote.split()) < MIN_QUOTE_WORDS:
            why = f"quote shorter than {MIN_QUOTE_WORDS} words"
        elif page is None:
            why = "quote not found on the fetched pages"
        else:
            if industry not in decision.industries:
                decision.industries.append(industry)
                decision.evidence.append({"industry": industry, "quote": quote, "url": page.url})
            continue
        decision.rejected.append({"industry": industry, "quote": quote, "why": why})

    if decision.industries:
        decision.status = "decided"
    elif decision.rejected:
        decision.reason = "no pick had a quote found on the site"
    else:
        decision.reason = str(result.get("no_pick_reason") or "the site text supports no candidate").strip()
    return decision


def run_checks(
    companies: Iterable[CompanyToCheck],
    *,
    fetch: Callable[[str], Any],
    choose: Callable[[CompanyToCheck, list[SitePage], dict[str, Any]], dict[str, Any]],
    taxonomy: dict[str, Any] | None = None,
    workers: int = 4,
) -> list[Decision]:
    from concurrent.futures import ThreadPoolExecutor

    taxonomy = taxonomy if taxonomy is not None else load_taxonomy()
    companies = list(companies)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        return list(pool.map(lambda c: check_company(c, fetch=fetch, choose=choose, taxonomy=taxonomy), companies))


def decisions_by_company(payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(d["company_id"]): d for d in payload.get("decisions") or []}


def render_review_markdown(payload: dict[str, Any]) -> str:
    decisions = payload.get("decisions") or []
    decided = [d for d in decisions if d["status"] == "decided"]
    review = [d for d in decisions if d["status"] != "decided"]
    lines = [
        "# Industry company check (website evidence, nothing written)",
        "",
        f"Taxonomy {payload.get('taxonomy_version')}. Model {payload.get('model')}. "
        f"Checked {len(decisions)}: decided {len(decided)}, review {len(review)}.",
        "",
        "## Review list",
        "",
    ]
    lines += [
        f"- {d['name']} ({d.get('domain') or 'no website'}, {d['raw_value']}): "
        f"suggest {', '.join(d.get('suggestion') or []) or 'none'}; candidates {', '.join(d.get('candidates') or [])}. "
        f"{d.get('reason') or ''}".rstrip()
        for d in review
    ] or ["- none"]
    lines += ["", "## Decided", ""]
    for d in decided:
        lines.append(f"- {d['name']} ({d.get('domain')}, {d['raw_value']}): {', '.join(d['industries'])}")
        for ev in d.get("evidence") or []:
            lines.append(f"  - {ev['industry']}: \"{ev['quote']}\" ({ev['url']})")
    if not decided:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
