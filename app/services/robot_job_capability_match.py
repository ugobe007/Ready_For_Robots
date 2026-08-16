"""
Score existing Robot Jobs against a capability profile.

Integrity: never invent jobs or capabilities. Soft-rank economic mismatch
(can do ≠ should do) instead of hard-excluding.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.robot_capability_profile import (
    CapabilityProfile,
    build_capability_profile,
)
from app.services.robot_profile_extract import (
    extract_robot_profile,
    fetch_product_page,
)
from app.services.robot_url_safety import UrlSafetyError, assert_public_http_url

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_PATH = REPO_ROOT / "readyforrobots-new" / "client" / "src" / "data" / "rdd_demo_jobs.json"
TAPE_PATH = REPO_ROOT / "app" / "data" / "robot_job_match_tape.json"
MANIP_PATH = REPO_ROOT / "docs" / "product_sim" / "worksite" / "manipulation_open_world_25_ledger.json"
CORPUS_PATH = REPO_ROOT / "app" / "data" / "robot_job_match_corpus.json"

# Tape family → RDD families
TAPE_FAMILY_MAP: dict[str, list[str]] = {
    "transport": ["transport_amr", "mobile_manipulation"],
    "cart": ["transport_amr", "mobile_manipulation"],
    "pallet": ["manipulator", "mobile_manipulation"],
    "scrub": ["floor_scrub"],
    "inspect": ["inspection_mobile"],
    "gripper": ["manipulator", "mobile_manipulation"],
}

SCORE_THRESHOLD = 3.0
MATCHES_MIN = 3


@lru_cache(maxsize=1)
def load_match_corpus() -> tuple[dict[str, Any], ...]:
    """Prefer bundled corpus (Fly); else assemble from demo + tape + ledger."""
    if CORPUS_PATH.is_file():
        data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        jobs = data.get("jobs") or []
        if jobs:
            return tuple(jobs)

    rows: list[dict[str, Any]] = []

    if DEMO_PATH.is_file():
        demo = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
        for profile_key, jobs in (demo.get("jobs") or {}).items():
            profile = next(
                (p for p in demo.get("profiles") or [] if p.get("profile_key") == profile_key),
                {},
            )
            fam = profile.get("capability_family") or "transport_amr"
            for job in jobs:
                rows.append(
                    {
                        "job_key": job.get("job_key"),
                        "title": job.get("robot_compatible_task") or "",
                        "industry": (job.get("operating_context") or "").replace("_", " "),
                        "path": (job.get("requirements") or {}).get("path")
                        or f"{job.get('action', '')} → {job.get('target', '')}",
                        "company_name": job.get("company_name"),
                        "locality": job.get("locality"),
                        "families": [fam],
                        "actions": [job.get("action")] if job.get("action") else [],
                        "text": " ".join(
                            str(x)
                            for x in (
                                job.get("robot_compatible_task"),
                                job.get("why_job"),
                                job.get("observed_workflow"),
                                job.get("target"),
                                job.get("action"),
                            )
                            if x
                        ).lower(),
                        "source": "demo",
                        "tape_family": "transport" if "transport" in fam else "scrub",
                        "pure_amr_tote": (job.get("requirements") or {}).get("load_interface")
                        in {"tote", "cart"}
                        and fam == "transport_amr",
                        "unknowns": list(job.get("unknowns") or []),
                    }
                )

    if TAPE_PATH.is_file():
        tape = json.loads(TAPE_PATH.read_text(encoding="utf-8"))
        for job in tape.get("jobs") or []:
            fams = TAPE_FAMILY_MAP.get(job.get("family") or "", ["transport_amr"])
            title = job.get("title") or ""
            rows.append(
                {
                    "job_key": job.get("key"),
                    "title": title,
                    "industry": job.get("industry") or "",
                    "path": job.get("path") or "",
                    "company_name": None,
                    "locality": None,
                    "families": fams,
                    "actions": [],
                    "text": f"{title} {job.get('industry', '')} {job.get('path', '')}".lower(),
                    "source": "tape",
                    "tape_family": job.get("family"),
                    "pure_amr_tote": job.get("family") in {"transport", "cart"}
                    and not any(
                        w in title.lower()
                        for w in ("kit", "cnc", "load", "unload", "pallet", "stack", "replenish")
                    ),
                    "unknowns": [],
                }
            )

    if MANIP_PATH.is_file():
        manip = json.loads(MANIP_PATH.read_text(encoding="utf-8"))
        for job in manip.get("jobs") or []:
            workflow = job.get("workflow") or "manipulator"
            fams = (
                ["manipulator", "mobile_manipulation"]
                if workflow == "machine_tending"
                else ["manipulator"]
            )
            title = job.get("robot_compatible_task") or ""
            rows.append(
                {
                    "job_key": job.get("job_key"),
                    "title": title,
                    "industry": job.get("locality") or "Manufacturing",
                    "path": workflow.replace("_", " → ").upper(),
                    "company_name": job.get("company_name"),
                    "locality": job.get("locality"),
                    "families": fams,
                    "actions": [workflow],
                    "text": " ".join(
                        str(x)
                        for x in (
                            title,
                            job.get("why_job"),
                            workflow,
                            json.dumps(job.get("requirements") or {}),
                        )
                        if x
                    ).lower(),
                    "source": "manipulation_ledger",
                    "tape_family": "gripper" if workflow == "machine_tending" else "pallet",
                    "pure_amr_tote": False,
                    "unknowns": list(job.get("unknowns") or []),
                }
            )

    # Dedupe by job_key / title
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = (row.get("job_key") or row.get("title") or "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return tuple(out)


def score_job(profile: CapabilityProfile, job: dict[str, Any]) -> tuple[float, list[str]]:
    notes: list[str] = []
    score = 0.0
    profile_fams = [f["id"] for f in profile.families]
    job_fams = list(job.get("families") or [])
    cap_keys = {c.key for c in profile.capabilities}

    for i, fam in enumerate(profile_fams):
        if fam in job_fams:
            score += 3.0 if i == 0 else 2.0

    text = job.get("text") or ""
    title = (job.get("title") or "").lower()

    token_hits = (
        ("load_unload", ("load", "unload", "tend", "cnc", "spindle")),
        ("material_transport", ("tote", "cart", "replenish", "kit", "staging", "transport")),
        ("machine_interaction", ("cnc", "machine", "spindle", "fixture")),
        ("dexterous", ("grasp", "pick", "stack", "case", "part")),
        ("scrub", ("scrub", "floor", "clean")),
        ("inspect", ("inspect", "gauge", "panel", "route")),
    )
    for cap, needles in token_hits:
        if cap not in cap_keys:
            continue
        if any(n in text or n in title for n in needles):
            score += 2.0

    industry = (job.get("industry") or "").lower()
    if any(w in industry for w in ("manufactur", "machine", "aerospace", "fulfill", "warehous")):
        if "mobile" in cap_keys or "material_transport" in cap_keys or "load_unload" in cap_keys:
            score += 1.0

    # Can do ≠ should do: dual-arm mobile manip doing pure tote AMR work
    if job.get("pure_amr_tote") and (
        "dual_arm" in cap_keys or "dexterous" in cap_keys
    ) and "mobile_manipulation" in profile_fams:
        score -= 1.5
        notes.append(
            "Capable of tote/cart moves, but a dual-arm mobile manipulator may be economically better on manipulation tasks."
        )
        unknowns = list(job.get("unknowns") or [])
        if "Economic fit vs AMR" not in unknowns:
            unknowns = unknowns + ["Economic fit vs AMR"]
        job = {**job, "unknowns": unknowns}

    return score, notes


def match_jobs_for_profile(
    profile: CapabilityProfile,
    *,
    limit: int = 12,
) -> dict[str, Any]:
    if not profile.understood:
        return {
            "state": "could_not_understand",
            "robot_name": profile.robot_name,
            "capabilities": profile.to_dict()["capabilities"],
            "families": profile.families,
            "jobs": [],
            "job_count": 0,
        }

    scored: list[tuple[float, dict[str, Any], list[str]]] = []
    for job in load_match_corpus():
        s, notes = score_job(profile, job)
        if s >= SCORE_THRESHOLD:
            scored.append((s, job, notes))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:limit]
    jobs_out = []
    for s, job, notes in top:
        unknowns = list(job.get("unknowns") or [])
        if notes:
            for n in notes:
                if n not in unknowns:
                    unknowns.append(n)
        jobs_out.append(
            {
                "job_key": job.get("job_key"),
                "title": job.get("title"),
                "industry": job.get("industry"),
                "path": job.get("path"),
                "company_name": job.get("company_name"),
                "locality": job.get("locality"),
                "tape_family": job.get("tape_family") or "transport",
                "score": round(s, 2),
                "unknowns": unknowns,
                "source": job.get("source"),
            }
        )

    n = len(jobs_out)
    if n >= MATCHES_MIN:
        state = "matches"
    elif n >= 1:
        state = "thin_corpus"
    else:
        state = "thin_corpus"  # understood but empty — still not "no library"

    return {
        "state": state,
        "robot_name": profile.robot_name,
        "capabilities": profile.to_dict()["capabilities"],
        "families": profile.families,
        "jobs": jobs_out,
        "job_count": max(n, len(scored)),  # reported found count
    }


def match_robot_url(
    url: str,
    *,
    chip: str | None = None,
    fetcher=None,
    html: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Full path: URL → fetch → capability profile → corpus match.
    `html` / `description` skip network (tests). `chip` is recovery prior.
    """
    if chip and not url and not html and not description:
        profile = build_capability_profile(text="", chip=chip, robot_name="your robot")
        return match_jobs_for_profile(profile)

    source_url = None
    page_html = html
    fetched_at = None
    if page_html is None and description is None and url:
        safe = assert_public_http_url(url)
        source_url = safe
        page = fetch_product_page(safe, timeout=10.0, fetcher=fetcher)
        page_html = page["html"]
        source_url = page.get("url") or safe
        fetched_at = page.get("fetched_at")
    elif url:
        try:
            source_url = assert_public_http_url(url)
        except UrlSafetyError:
            source_url = url

    extraction = extract_robot_profile(
        html=page_html,
        description=description,
        source_url=source_url,
        fetched_at=fetched_at,
    )
    text = extraction.text_sample or description or ""
    # Also fold URL path tokens as weak evidence (generic words only)
    if source_url:
        text = f"{text}\n{source_url}"

    profile = build_capability_profile(
        text=text,
        robot_name=None,
        page_title=extraction.page_title,
        manufacturer=extraction.manufacturer,
        model=extraction.model,
        chip=chip,
    )
    # Prefer model/manufacturer naming
    if extraction.model and extraction.manufacturer:
        profile.robot_name = f"{extraction.manufacturer} {extraction.model}".strip()[:120]
    elif extraction.model:
        profile.robot_name = extraction.model[:120]
    elif extraction.manufacturer:
        profile.robot_name = extraction.manufacturer[:120]

    result = match_jobs_for_profile(profile)
    result["source_url"] = source_url
    result["content_hash"] = extraction.content_hash
    return result


def match_from_chip(chip: str, robot_name: str = "your robot") -> dict[str, Any]:
    profile = build_capability_profile(text="", chip=chip, robot_name=robot_name)
    return match_jobs_for_profile(profile)
