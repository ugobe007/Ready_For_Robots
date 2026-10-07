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
        Leaf("page_name", extractor="record.page_name", goal="Name on the posting if any"),
        Leaf("page_title", extractor="record.page_title", goal="Title on the posting if any"),
        Compute(
            "job_function",
            deps=("job_text", "action"),
            goal="Classify the work into a title family (pharmacy, EVS, warehouse, plant). Never invent a person.",
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
        Fetch(
            "hunter_people",
            deps=("employer", "domain", "departments", "locality"),
            fetcher="hunter_domain_search",
            goal="Hunter.io people at this employer. Not Apollo. Empty list on miss.",
        ),
        Compute(
            "decision_maker",
            deps=("target_titles", "hunter_people", "locality", "job_function", "job_text"),
            goal="Pick the Hunter person whose title matches the work. None if nobody fits. Do not invent a name or mailbox.",
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


def job_leaves(row: Any, *, domain: Optional[str] = None) -> dict[str, Any]:
    from app.services.daily_jobs_report import _page_name_title

    name, title = _page_name_title(row)
    if isinstance(row, dict):
        employer = str(row.get("company_name") or row.get("employer") or "").strip()
        action = str(row.get("action") or "").strip()
        locality = str(row.get("locality") or "").strip()
    else:
        employer = str(getattr(row, "company_name", "") or "").strip()
        action = str(getattr(row, "action", "") or "").strip()
        locality = str(getattr(row, "locality", "") or "").strip()
    return {
        "employer": employer,
        "job_text": job_text_of(row),
        "action": action,
        "locality": locality,
        "domain": domain,
        "page_name": name,
        "page_title": title,
    }


def run_decision_maker_dag(
    row: Any,
    *,
    domain: Optional[str] = None,
    fetchers: dict[str, Callable[..., Any]] | None = None,
) -> dict[str, Any]:
    return compiled_decision_maker().run(job_leaves(row, domain=domain), fetchers)
