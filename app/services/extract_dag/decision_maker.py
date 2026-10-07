"""Decision-maker extract DAG: posting/record leaves → titles → Hunter people → pick.

FIND does not run this. Apollo is not a node. A miss is valid.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Optional

from app.services.extract_dag.compile import (
    CompiledScript,
    LibraryWriter,
    compile_graph,
)
from app.services.extract_dag.graph import Compute, ExtractGraph, Fetch, Leaf
from app.services.extract_dag.library_decision_maker import LIBRARY
from app.services.extract_dag.review import AstReviewer
from app.services.job_decision_maker_agent import job_text as job_text_of

DECISION_MAKER_GRAPH = ExtractGraph(
    id="job_decision_maker",
    goal="Map a robot job to the person whose title owns that work, then use Hunter people for a real name/email.",
    nodes=(
        Leaf("employer", extractor="record.company_name", goal="Named employer"),
        Leaf("job_text", extractor="record.job_text", goal="Work description on the job"),
        Leaf("action", extractor="record.action", goal="Stored job function or verb"),
        Leaf("locality", extractor="record.locality", goal="Workplace label"),
        Leaf("domain", extractor="record.employer_domain", goal="Employer web domain, not ATS"),
        Leaf("page_name", extractor="record.page_name", goal="Name extracted from the posting"),
        Leaf("page_title", extractor="record.page_title", goal="Title extracted from the posting"),
        Compute(
            "job_function",
            deps=("job_text", "action"),
            goal="Classify the work into a title family (pharmacy, EVS, warehouse, plant).",
            output="function key",
        ),
        Compute(
            "target_titles",
            deps=("job_function", "job_text"),
            goal="Titles that own this work. Empty list is invalid; use operations defaults in the function.",
            output="list of titles",
        ),
        Compute(
            "departments",
            deps=("job_function",),
            goal="Hunter department filter for that work family.",
            output="department string",
        ),
        Compute(
            "page_person",
            deps=("page_name", "page_title"),
            goal="Name and title from the posting. None if the posting named nobody. Do not invent.",
            output="person dict or None",
        ),
        Fetch(
            "leadership_pages",
            deps=("employer", "domain"),
            fetcher="employer_leadership_pages",
            goal="HTML from the employer /leadership, /team, and /about URLs. Empty list on miss.",
        ),
        Compute(
            "leadership_people",
            deps=("leadership_pages",),
            goal="Names and titles extracted from leadership/team pages. Empty list if the pages name nobody. Do not invent.",
            output="list of people",
        ),
        Compute(
            "leadership_person",
            deps=("leadership_people", "target_titles", "locality", "job_function", "job_text"),
            goal="Pick a person extracted from the leadership/team page whose title owns this work. None if nobody fits. Do not invent.",
            output="person dict or None",
        ),
        Fetch(
            "hunter_people",
            deps=("employer", "domain", "departments", "locality", "leadership_person"),
            fetcher="hunter_domain_search",
            goal="Hunter.io domain search only when the leadership page did not name a title match. Not Apollo. Empty list on miss.",
        ),
        Compute(
            "decision_maker",
            deps=(
                "target_titles",
                "hunter_people",
                "page_person",
                "leadership_person",
                "locality",
                "job_function",
                "job_text",
            ),
            goal="Prefer a posting-named person whose title owns this work. Else a leadership-page person. Else pick a Hunter person whose title matches. None if nobody fits. Do not invent a name or mailbox.",
            output="person dict or None",
        ),
    ),
)


@lru_cache(maxsize=1)
def compiled_decision_maker() -> CompiledScript:
    return compile_graph(
        DECISION_MAKER_GRAPH,
        LibraryWriter(LIBRARY),
        AstReviewer(),
    )


def _record_get(row: Any, *names: str) -> str:
    if isinstance(row, dict):
        for name in names:
            val = row.get(name)
            if val:
                return str(val).strip()
        return ""
    for name in names:
        val = getattr(row, name, None)
        if val:
            return str(val).strip()
    return ""


def extract_leaf(node: Leaf, row: Any, extra: Optional[dict[str, Any]] = None) -> Any:
    """Read a leaf from a record or document. The graph names the extractor; code reads it."""
    extra = extra or {}
    if node.id in extra and extra[node.id] is not None:
        return extra[node.id]
    path = node.extractor or ""
    field = path.split(".", 1)[1] if path.startswith("record.") else node.id
    if field == "job_text":
        return job_text_of(row)
    if field in {"page_name", "page_title"}:
        from app.services.daily_jobs_report import _page_name_title

        name, title = _page_name_title(row)
        return name if field == "page_name" else title
    if field in {"company_name", "employer"}:
        return _record_get(row, "company_name", "employer")
    if field == "employer_domain":
        return extra.get("domain")
    return _record_get(row, field)


def job_leaves(row: Any, *, domain: Optional[str] = None) -> dict[str, Any]:
    extra = {"domain": domain}
    out: dict[str, Any] = {}
    for node in DECISION_MAKER_GRAPH.nodes:
        if isinstance(node, Leaf):
            out[node.id] = extract_leaf(node, row, extra)
    return out


def run_decision_maker_dag(
    row: Any,
    *,
    domain: Optional[str] = None,
    fetchers: dict[str, Callable[..., Any]] | None = None,
) -> dict[str, Any]:
    return compiled_decision_maker().run(job_leaves(row, domain=domain), fetchers)
