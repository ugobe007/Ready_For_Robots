"""
Score existing Robot Jobs against a capability profile.

Production URL path (surgical restore):
  scrape_robot_page → analyze_robot_capabilities (robot_ready / match-url)
  → map to CapabilityProfile → job corpus

Integrity: never invent jobs or capabilities. Soft-rank economic mismatch
(can do ≠ should do) instead of hard-excluding.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from app.services.robot_capability_profile import (
    CapabilityProfile,
    CapabilitySignal,
    build_capability_profile,
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

# match-url / robot_ready type → job families
READY_TYPE_FAMILIES: dict[str, list[str]] = {
    "warehouse/logistics": ["transport_amr", "mobile_manipulation"],
    "delivery/transport": ["transport_amr", "mobile_manipulation"],
    "disinfection/cleaning": ["floor_scrub"],
    "service robot": ["mobile_manipulation", "transport_amr"],
    "medical/healthcare": ["transport_amr", "mobile_manipulation"],
    "unknown": [],
}

READY_CAP_TO_SIGNAL: dict[str, tuple[str, str]] = {
    "autonomous navigation": ("mobile", "Autonomous navigation"),
    "payload delivery": ("carry", "Payload delivery"),
    "uv disinfection": ("scrub", "UV disinfection"),
    "temperature control": ("material_transport", "Temperature-controlled transport"),
    "multi-floor": ("mobile", "Multi-floor operation"),
    "human interaction": ("mobile", "Human-shared environments"),
    "cloud connected": ("industrial_runtime", "Cloud / fleet connected"),
    "hipaa compliant": ("inspect", "Healthcare compliance context"),
}

SCORE_THRESHOLD = 3.0
MATCHES_MIN = 3

ScrapeFn = Callable[[str], str]
AnalyzeFn = Callable[[str, str], dict[str, Any]]


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

    # Do not promote CNC/machine-tending from arms/humanoid alone
    text = (job.get("text") or "") + " " + (job.get("title") or "")
    if re.search(r"\bcnc\b|machine\s+tend", text, re.I) and "machine_interaction" not in cap_keys:
        score -= 2.0
        notes.append("Machine tending not confirmed for this robot — needs stronger evidence.")

    # R31: weeding laser ≠ shop-floor cutting laser. LaserWeeder must not
    # score CNC / laser/plasma load-unload from the token "laser".
    name_blob = f"{profile.robot_name or ''} {profile.robot_class or ''}"
    if re.search(r"laserweeder|laser\s+weeder|laser[- ]weed|farmdroid|weeding|agricult", name_blob, re.I):
        if re.search(
            r"laser\s*/\s*plasma|plasma\s+cut|cnc\s+laser|laser\s+cut|"
            r"cutting\s+machines|\bcnc\b|machine\s+tend",
            text,
            re.I,
        ):
            score -= 10.0
            notes.append("Weeding laser is not a cutting-laser or CNC tend cell.")

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


def _domain_from_url(url: str | None) -> str:
    host = (urlparse(url or "").hostname or "").lower().removeprefix("www.")
    return host or "robot"


def _company_label(domain: str) -> str:
    slug = (domain or "").split(".")[0]
    if not slug:
        return "your robot"
    if slug.endswith("robotics") and len(slug) > len("robotics"):
        stem = slug[: -len("robotics")]
        return f"{stem.replace('-', ' ').title()} Robotics"
    return slug.replace("-", " ").title()


def is_weak_robot_ready_profile(robot_caps: dict[str, Any] | None) -> bool:
    """Same gate as GET /api/leads/match-url."""
    caps = robot_caps or {}
    robot_type = str(caps.get("type") or "").strip().lower()
    use_case = str(caps.get("use_case") or "").strip().lower()
    capabilities = caps.get("capabilities") if isinstance(caps.get("capabilities"), list) else []
    profile_score = float(caps.get("profile_score") or 0)
    return (
        robot_type in {"", "unknown"}
        and use_case in {"", "general automation"}
        and len(capabilities) == 0
        and profile_score < 50
    )


def profile_from_robot_ready_caps(
    robot_caps: dict[str, Any],
    *,
    robot_name: str | None = None,
    page_text: str = "",
    submitted_domain: str | None = None,
) -> CapabilityProfile:
    """
    Map match-url / robot_ready capability dict → job-matcher CapabilityProfile.
    This is the single understanding bridge — no parallel research engine.
    """
    domain = submitted_domain or ""
    name = (robot_name or _company_label(domain) or "your robot").strip()[:120]
    rtype = str(robot_caps.get("type") or "Unknown").strip()
    use_case = str(robot_caps.get("use_case") or "").strip()
    ready_caps = robot_caps.get("capabilities") if isinstance(robot_caps.get("capabilities"), list) else []
    profile_score = float(robot_caps.get("profile_score") or 0)

    profile = CapabilityProfile(robot_name=name, robot_class=rtype.lower().replace(" ", "_") or None)
    seen: set[str] = set()

    def add(key: str, label: str, excerpt: str | None, conf: float = 0.8) -> None:
        if key in seen:
            return
        seen.add(key)
        profile.capabilities.append(
            CapabilitySignal(
                key=key,
                label=label,
                confidence=conf,
                excerpt=(excerpt or "")[:160] or None,
                truth_state="confirmed",
            )
        )

    # Type → primary signals
    tl = rtype.lower()
    if "clean" in tl or "disinfect" in tl:
        add("scrub", "Floor cleaning / disinfection", rtype)
        add("mobile", "Mobile / autonomous movement", rtype)
    elif "warehouse" in tl or "logistics" in tl or "delivery" in tl or "transport" in tl:
        add("mobile", "Mobile / autonomous movement", rtype)
        add("material_transport", "Material transport", rtype)
    elif "service" in tl:
        add("mobile", "Mobile / autonomous movement", rtype)
    elif "medical" in tl or "healthcare" in tl:
        add("mobile", "Mobile / autonomous movement", rtype)
        add("material_transport", "Material transport", use_case or rtype)

    if "warehouse" in use_case.lower() or "logistics" in use_case.lower():
        add("material_transport", "Material transport", use_case)
        add("mobile", "Mobile / autonomous movement", use_case)

    for cap in ready_caps:
        label = str(cap).strip()
        mapped = READY_CAP_TO_SIGNAL.get(label.lower())
        if mapped:
            add(mapped[0], mapped[1], label)
        else:
            # Keep unknown ready-caps as generic mobile evidence when score is decent
            if profile_score >= 50:
                add("mobile", label or "Capability signal", label, conf=0.55)

    # Light page-text assist only for humanoid / scrub / arm words already on the page
    # (does not invent — requires explicit language in scraped text from the same resolver)
    blob = (page_text or "").lower()
    if blob:
        if re.search(r"\bhumanoid\b|\bdigit\b", blob):
            add("humanoid", "Humanoid form", "humanoid")
            add("mobile", "Mobile / autonomous movement", "humanoid")
        if re.search(r"\bdual[- ]arm\b|\bdexterous\b", blob):
            add("dual_arm", "Dual-arm manipulation", "dual-arm")
            add("dexterous", "Dexterous hands / end effectors", "dexterous")
        if re.search(r"\btotes?\b", blob):
            add("tote_handling", "Tote handling", "tote")
        if re.search(r"\b(floor\s+scrub|scrubber)\b", blob):
            add("scrub", "Floor cleaning", "scrub")

    # Families from ready type + capability keys
    fam_scores: dict[str, float] = {}
    for fam in READY_TYPE_FAMILIES.get(tl, []) or READY_TYPE_FAMILIES.get(
        tl.replace(" ", "/"), []
    ):
        fam_scores[fam] = fam_scores.get(fam, 0) + 2.5
    # normalize type key
    for key, fams in READY_TYPE_FAMILIES.items():
        if key in tl or tl in key:
            for fam in fams:
                fam_scores[fam] = fam_scores.get(fam, 0) + 2.0

    keys = {c.key for c in profile.capabilities}
    if "scrub" in keys:
        fam_scores["floor_scrub"] = fam_scores.get("floor_scrub", 0) + 3.0
    if "inspect" in keys:
        fam_scores["inspection_mobile"] = fam_scores.get("inspection_mobile", 0) + 2.5
    if "dual_arm" in keys or "dexterous" in keys or "humanoid" in keys:
        fam_scores["mobile_manipulation"] = fam_scores.get("mobile_manipulation", 0) + 3.0
        fam_scores["manipulator"] = fam_scores.get("manipulator", 0) + 2.0
    if "mobile" in keys or "material_transport" in keys or "tote_handling" in keys or "carry" in keys:
        fam_scores["transport_amr"] = fam_scores.get("transport_amr", 0) + 2.0
        fam_scores["mobile_manipulation"] = fam_scores.get("mobile_manipulation", 0) + 1.5

    profile.families = [
        {"id": fam, "confidence": min(0.95, round(raw / 4.0, 2))}
        for fam, raw in sorted(fam_scores.items(), key=lambda kv: kv[1], reverse=True)
        if raw >= 1.5
    ][:5]

    profile.evidence_count = len(profile.capabilities)
    profile.understood = (not is_weak_robot_ready_profile(robot_caps)) and (
        profile.evidence_count >= 1 or bool(profile.families)
    )
    if profile.understood and not profile.families:
        # Fallback family so corpus can score
        profile.families = [{"id": "transport_amr", "confidence": 0.55}]
    return profile


def resolve_robot_ready_profile(
    url: str,
    *,
    page_text: str | None = None,
    robot_capabilities: dict[str, Any] | None = None,
    scraper: ScrapeFn | None = None,
    analyzer: AnalyzeFn | None = None,
) -> tuple[dict[str, Any], str, str]:
    """
    Run the match-url understanding path.
    Returns (robot_caps, page_text, submitted_domain).
    """
    # Pre-resolved caps (tests / client handoff) — no network, no robot_ready import
    if robot_capabilities is not None:
        domain = _domain_from_url(url)
        return robot_capabilities, page_text or "", domain

    from app.services.robot_ready_profile import analyze_robot_capabilities, scrape_robot_page

    safe = assert_public_http_url(url)
    domain = _domain_from_url(safe)

    if page_text is not None:
        text = page_text
    else:
        scrape = scraper or scrape_robot_page
        text = scrape(safe)
        if (text or "").lower().startswith("error scraping"):
            text = f"{domain} robotics automation solution from {domain}".strip()

    analyze = analyzer or analyze_robot_capabilities
    caps = analyze(domain, text)
    return caps, text, domain


def match_robot_url(
    url: str,
    *,
    chip: str | None = None,
    robot_capabilities: dict[str, Any] | None = None,
    page_text: str | None = None,
    robot_name: str | None = None,
    html: str | None = None,
    description: str | None = None,
    scraper: ScrapeFn | None = None,
    analyzer: AnalyzeFn | None = None,
    product_name: str | None = None,  # kept for API compat; unused (no parallel product picker)
    fetcher=None,  # legacy test hook — unused on restored path
) -> dict[str, Any]:
    """
    URL → scrape_robot_page → analyze_robot_capabilities → job corpus.

    `robot_capabilities` / `page_text` skip network (tests / pre-resolved).
    `html` / `description` are treated as page_text for tests.
    `chip` is recovery prior when understanding fails.
    """
    _ = product_name, fetcher  # API compat only

    if chip and not url and robot_capabilities is None and page_text is None and not html and not description:
        profile = build_capability_profile(text="", chip=chip, robot_name=robot_name or "your robot")
        out = match_jobs_for_profile(profile)
        out["research_stages"] = []
        out["company_name"] = None
        out["products"] = []
        out["needs_product_choice"] = False
        out["robot_capabilities"] = None
        return out

    # Test helpers: html/description become page text for the old analyzer
    if page_text is None and (html or description):
        from app.services.robot_profile_extract import _html_to_text

        page_text = description or (_html_to_text(html) if html else "")

    stages = [
        {"id": "identify_company", "label": "Identifying company", "status": "pending", "detail": None},
        {"id": "research_capabilities", "label": "Understanding capabilities", "status": "pending", "detail": None},
        {"id": "match_jobs", "label": "Searching jobs", "status": "pending", "detail": None},
    ]

    try:
        caps, text, domain = resolve_robot_ready_profile(
            url,
            page_text=page_text,
            robot_capabilities=robot_capabilities,
            scraper=scraper,
            analyzer=analyzer,
        )
    except UrlSafetyError:
        raise
    except Exception:
        if chip:
            return match_from_chip(chip, robot_name=robot_name or "your robot")
        return {
            "state": "could_not_understand",
            "robot_name": robot_name or "your robot",
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "company_name": None,
            "products": [],
            "needs_product_choice": False,
            "research_stages": stages,
            "source_url": url,
            "robot_capabilities": None,
        }

    company = _company_label(domain)
    stages[0]["status"] = "done"
    stages[0]["detail"] = company

    if is_weak_robot_ready_profile(caps):
        if chip:
            return match_from_chip(chip, robot_name=robot_name or company)
        stages[1]["status"] = "done"
        stages[1]["detail"] = "Insufficient profile"
        return {
            "state": "could_not_understand",
            "robot_name": robot_name or company,
            "company_name": company,
            "capabilities": [],
            "families": [],
            "jobs": [],
            "job_count": 0,
            "products": [],
            "needs_product_choice": False,
            "research_stages": stages,
            "source_url": url,
            "robot_capabilities": caps,
            "evidence_urls": [url],
        }

    profile = profile_from_robot_ready_caps(
        caps,
        robot_name=robot_name or company,
        page_text=text,
        submitted_domain=domain,
    )
    stages[1]["status"] = "done"
    stages[1]["detail"] = caps.get("type") or f"{len(profile.capabilities)} signals"

    result = match_jobs_for_profile(profile)
    stages[2]["status"] = "done"
    stages[2]["detail"] = f"{result.get('job_count') or 0} jobs"
    result["research_stages"] = stages
    result["company_name"] = company
    result["products"] = []
    result["needs_product_choice"] = False
    result["source_url"] = url
    result["evidence_urls"] = [url]
    result["robot_class"] = profile.robot_class
    result["robot_capabilities"] = caps
    return result


def match_from_chip(chip: str, robot_name: str = "your robot") -> dict[str, Any]:
    profile = build_capability_profile(text="", chip=chip, robot_name=robot_name)
    out = match_jobs_for_profile(profile)
    out["research_stages"] = []
    out["company_name"] = None
    out["products"] = []
    out["needs_product_choice"] = False
    out["robot_capabilities"] = None
    return out
