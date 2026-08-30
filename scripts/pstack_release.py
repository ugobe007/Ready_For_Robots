#!/usr/bin/env python3
"""pstack release gate — How / Act / Critic for Jobs PRs.

This is the merge authority for FIND / Job Cards / CRM / matching.
Protocol chrome on `/` or Jobs CRM is not a pass.

  python3 scripts/pstack_release.py --local
  python3 scripts/pstack_release.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FLY_API = os.getenv("RFR_FLY_API", "https://ready-2-robot.fly.dev").rstrip("/")
WORKSPACE = ROOT / "readyforrobots-new" / "client" / "src" / "components" / "RobotJobsWorkspace.tsx"
CRM_DESK = ROOT / "readyforrobots-new" / "client" / "src" / "components" / "JobsCrmDesk.tsx"
IDENTITY = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "robotUrlIdentity.ts"
FIND_RESEARCH = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "findResearch.ts"
CRM_ACCOUNT = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsCrmAccount.ts"
HANDOFF = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsHandoffSnapshot.ts"
PSTACK_SITE = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "pstackSite.ts"
PSTACK_RELEASE_TS = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "pstackRelease.ts"
JOBS_PAGE = ROOT / "readyforrobots-new" / "client" / "src" / "pages" / "Jobs.tsx"
PROTOCOL_PY = ROOT / "app" / "services" / "pstack_protocol.py"
MATCHER = ROOT / "app" / "services" / "robot_job_capability_match.py"
SEARCH_API = ROOT / "app" / "api" / "robot_job_search.py"

DEXMATE = "https://www.dexmate.ai/"
GREENFIELD = "https://www.greenfieldincorporated.com/"
DILIGENT = "https://www.diligentrobots.com/"
RESEARCH_FAILED_RE = re.compile(r"research failed|failed to fetch", re.I)
STRAWBERRY_RE = re.compile(r"strawberry|agrobot|harvest\s*croo|harvestcroo", re.I)
HUMAN_EMPTY_RE = re.compile(r"no humanoid jobs for this robot yet", re.I)
HEALTHCARE_CLASSES = frozenset(
    {
        "healthcare",
        "healthcare_robot",
        "medical_robot",
        "clinical_robot",
        "hospital_robot",
    }
)
REQUIRED_CRITIC_GATE_IDS = (
    "find",
    "find_abort",
    "find_identity",
    "crm_leftover",
    "job_cards",
    "wall",
    "matcher",
    "oem_extract",
    "class_picker",
    "healthcare_class",
    "ontology_industry_language",
)
CLASS_OPTIONS_TS = (
    ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "robotClassOptions.ts"
)
CLASS_QUALIFY = ROOT / "app" / "services" / "robot_class_qualify.py"
WORKFLOW_TS = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsWorkflow.ts"
WORKFLOW_TEST = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsWorkflow.test.ts"
OEM_SKU_SEED = ROOT / "app" / "data" / "vendor_robots_oem_sku_seed.json"
KNOWN_OEM_JSON = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "knownOemLineups.json"
JOB_CORPUS = ROOT / "app" / "data" / "robot_job_match_corpus.json"
HEALTHCARE_TEST = ROOT / "tests" / "test_healthcare_class_jobs.py"
RELEASE_YAML = ROOT / "pstack" / "release.yaml"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _slice(src: str, start: str, end: str) -> str:
    i = src.find(start)
    j = src.find(end)
    if i < 0:
        return ""
    if j < 0 or j <= i:
        return src[i:]
    return src[i:j]


def _check(cid: str, ok: bool, prove: str, detail: str = "") -> dict[str, Any]:
    row = {"id": cid, "ok": ok, "prove": prove}
    if detail:
        row["detail"] = detail
    return row


def _post_json(url: str, payload: dict[str, Any], *, timeout: float = 90.0) -> tuple[int, Any]:
    data = json.dumps(payload).encode()
    req = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return int(resp.status), json.loads(raw.decode())
            except json.JSONDecodeError:
                return int(resp.status), {"_raw": raw[:400].decode("utf-8", "replace")}
    except HTTPError as exc:
        raw = exc.read() if exc.fp else b""
        try:
            return int(exc.code), json.loads(raw.decode())
        except Exception:
            return int(exc.code), {"_raw": raw[:400].decode("utf-8", "replace")}
    except Exception as exc:
        return 0, {"error": str(exc)}


def _get(url: str, *, timeout: float = 25.0) -> tuple[int, Any]:
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return int(resp.status), json.loads(raw.decode())
            except json.JSONDecodeError:
                return int(resp.status), {"_raw": raw[:400].decode("utf-8", "replace")}
    except HTTPError as exc:
        raw = exc.read() if exc.fp else b""
        try:
            return int(exc.code), json.loads(raw.decode())
        except Exception:
            return int(exc.code), {"_raw": raw[:400].decode("utf-8", "replace")}
    except Exception as exc:
        return 0, {"error": str(exc)}


def phase_how() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    owners = {
        "workspace": WORKSPACE,
        "crm_desk": CRM_DESK,
        "identity": IDENTITY,
        "find_research": FIND_RESEARCH,
        "crm_account": CRM_ACCOUNT,
        "handoff": HANDOFF,
        "pstack_site": PSTACK_SITE,
        "pstack_release": PSTACK_RELEASE_TS,
        "jobs_page": JOBS_PAGE,
        "protocol_py": PROTOCOL_PY,
        "matcher": MATCHER,
        "search_api": SEARCH_API,
        "readme": ROOT / "pstack" / "README.md",
        "release_yaml": ROOT / "pstack" / "release.yaml",
    }
    missing = [name for name, path in owners.items() if not path.is_file()]
    checks.append(
        _check(
            "owners",
            not missing,
            "FIND / matcher / search / identity / CRM desk files exist",
            "" if not missing else f"missing {missing}",
        )
    )

    jobs_page = _read(JOBS_PAGE) if JOBS_PAGE.is_file() else ""
    find_is_home = "RobotJobsWorkspace" in jobs_page and not re.search(
        r'["\']\/experiment["\']', jobs_page
    )
    checks.append(
        _check(
            "find_route",
            find_is_home,
            "FIND is / via RobotJobsWorkspace on pages/Jobs.tsx",
        )
    )

    desk = _read(CRM_DESK) if CRM_DESK.is_file() else ""
    readme = _read(ROOT / "pstack" / "README.md") if (ROOT / "pstack" / "README.md").is_file() else ""
    chrome_ok = (
        "JobsPstackProtocol" not in desk
        and "release gate" in readme.lower()
        and "not a banner" in readme.lower()
    )
    checks.append(
        _check(
            "chrome_not_gate",
            chrome_ok,
            "Jobs CRM has no protocol chrome; pstack README is the release gate",
        )
    )

    matcher = _read(MATCHER) if MATCHER.is_file() else ""
    protocol = _read(PROTOCOL_PY) if PROTOCOL_PY.is_file() else ""
    checks.append(
        _check(
            "matcher_owner",
            "def match_jobs_for_profile" in matcher
            and "robot_job_capability_match.py" in protocol
            and "Do not call Vercel AI Gateway" in protocol,
            "Matcher stays code; protocol does not call a gateway",
        )
    )
    ok = all(c["ok"] for c in checks)
    return {"phase": "how", "ok": ok, "checks": checks}


def phase_act() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    workspace = _read(WORKSPACE) if WORKSPACE.is_file() else ""
    submit = _slice(workspace, "async function submitFind", "async function confirmSelection")
    identity = _read(IDENTITY) if IDENTITY.is_file() else ""
    account = _read(CRM_ACCOUNT) if CRM_ACCOUNT.is_file() else ""
    handoff = _read(HANDOFF) if HANDOFF.is_file() else ""
    desk = _read(CRM_DESK) if CRM_DESK.is_file() else ""
    release_ts = _read(PSTACK_RELEASE_TS) if PSTACK_RELEASE_TS.is_file() else ""

    checks.append(
        _check(
            "bind_url",
            "bindSubmittedRobot(submitUrl)" in submit
            and "stillThisSubmit" in submit
            and "function bindSubmittedRobot" in workspace,
            "submitFind binds the submitted URL and ignores stale responses",
        )
    )

    research = _read(FIND_RESEARCH) if FIND_RESEARCH.is_file() else ""
    interrupt_slice = ""
    interrupt_at = research.find("FIND_RESEARCH_INTERRUPTED_MESSAGE")
    if interrupt_at >= 0:
        interrupt_slice = research[interrupt_at : interrupt_at + 160]
    silent_helper = (
        "export function isSilentFindError" in identity
        and "export function findUserFacingError" in identity
        and "failed to fetch" in identity.lower()
        and "isFailedToFetchError" in research
        and "Research was interrupted" in research
        and "Failed to fetch" not in interrupt_slice
    )
    abort_contract = (
        "shouldIgnoreStaleFindError" in submit
        and "isAbortError(err, ac.signal)" in submit
        and "FIND_RESEARCH_INTERRUPTED_MESSAGE" in submit
        and "lookupFailedMessage" in submit
    )
    checks.append(
        _check(
            "silent_abort",
            abort_contract and silent_helper,
            "FIND catch ignores stale gens; abort is interrupted copy, never Failed to fetch / Research failed",
        )
    )

    set_error_block = _slice(submit, "} catch (err)", "finally")
    abort_at = set_error_block.find("isAbortError")
    fail_at = set_error_block.find("lookupFailedMessage")
    leak = bool(
        set_error_block
        and "setError" in set_error_block
        and (abort_at < 0 or fail_at < 0 or abort_at > fail_at)
    )
    checks.append(
        _check(
            "abort_before_set_error",
            not leak and "FIND_RESEARCH_INTERRUPTED_MESSAGE" in set_error_block,
            "submitFind catch must not paint lookupFailedMessage until abort is ruled out",
        )
    )

    checks.append(
        _check(
            "handoff",
            "beginJobsHandoffForUrl" in workspace
            and "beginJobsHandoffForUrl" in handoff
            and "honest empty" in handoff.lower(),
            "New FIND URL overwrites the previous robot handoff before search returns",
        )
    )

    checks.append(
        _check(
            "crm_desk",
            "export function crmDeskForCurrentRobot" in account
            and "crmDeskForCurrentRobot" in desk
            and "accountRows[0]?.robot_name" not in account
            and "accountRows[0]?.robot_url" not in account,
            "CRM desk is keyed to the submitted URL, never accountRows[0]",
        )
    )

    checks.append(
        _check(
            "no_signal_hop",
            "fetchRobotJobMatch" not in workspace
            and "robot-job-match" not in desk
            and "JobsPstackProtocol" not in desk,
            "FIND uses robot-job-search; CRM desk is not the matcher and has no protocol chrome",
        )
    )

    qualify = _slice(workspace, "async function qualifyActive", "function revealJobs")
    class_picker_act = (
        "fetchRobotJobSearch" in qualify
        and "assertedClass: chosen" in qualify
        and "qualifySearchLookupGrain" in qualify
        and "lookupGrain: grain" in qualify
        and "needsClassChoice: false" in qualify
        and "if (!a) return" not in qualify
        and "CLASS_PICKER_PROMPT" in workspace
        and "What kind of robot is" not in workspace
        and "kid of robot" not in workspace.lower()
        and "classJobsEmptyCopy" in workspace
        and "shouldShowClassPicker(active)" in workspace
    )
    checks.append(
        _check(
            "class_picker",
            class_picker_act,
            "Class-picker click starts robot-job-search and cannot silently no-op",
        )
    )

    checks.append(
        _check(
            "release_helpers",
            "FIND_ABORT_FIXTURE" in release_ts
            and "CRM_LEFTOVER_FIXTURE" in release_ts
            and "CLASS_PICKER_FIXTURE" in release_ts
            and "HEALTHCARE_CLASS_FIXTURE" in release_ts
            and "diligentMustNotBeHumanoidEmpty" in release_ts,
            "pstackRelease.ts encodes abort, leftover, class-picker, and Diligent healthcare fixtures",
        )
    )

    ok = all(c["ok"] for c in checks)
    return {"phase": "act", "ok": ok, "checks": checks}


def _identity_blob(data: Any) -> str:
    if not isinstance(data, dict):
        return str(data)
    parts = [
        str(data.get("company_name") or ""),
        str(data.get("robot_name") or ""),
        str(data.get("url") or ""),
        str((data.get("profile") or {}).get("company") if isinstance(data.get("profile"), dict) else ""),
        json.dumps(data.get("error") or ""),
        json.dumps(data.get("detail") or ""),
        json.dumps(data.get("state") or ""),
    ]
    return " ".join(parts)


def drive_find_url(url: str, *, api: str) -> dict[str, Any]:
    """Critic: the same POST FIND calls, plus listing identity for Greenfield."""
    base = api.rstrip("/")
    search_code, search = _post_json(
        f"{base}/api/robot-job-search",
        {"url": url, "lookup_grain": "product"},
        timeout=90.0,
    )
    listing_code, listing = _get(
        f"{base}/api/oem-listing?url={quote(url, safe='')}",
        timeout=20.0,
    )
    blob = _identity_blob(search) + " " + _identity_blob(listing)
    research_failed = bool(RESEARCH_FAILED_RE.search(blob)) or (
        search_code == 0 and RESEARCH_FAILED_RE.search(str(search))
    )
    host = "greenfieldincorporated" if "greenfield" in url else "dexmate"
    host_hit = host in blob.lower() or host in url.lower()
    strawberry = bool(STRAWBERRY_RE.search(blob)) if "greenfield" in url else False
    state = search.get("state") if isinstance(search, dict) else None
    company = (
        (search.get("company_name") if isinstance(search, dict) else None)
        or (
            ((search.get("profile") or {}).get("company") or {}).get("name")
            if isinstance(search, dict) and isinstance(search.get("profile"), dict)
            else None
        )
        or (listing.get("vendor_name") if isinstance(listing, dict) else None)
    )
    search_ok = search_code == 200 and isinstance(search, dict)
    listing_ok = listing_code == 200 and isinstance(listing, dict)
    if "greenfield" in url:
        ok = not research_failed and not strawberry and (search_ok or listing_ok)
    else:
        ok = not research_failed and search_code != 0 and (search_ok or listing_ok)
    if research_failed or strawberry:
        ok = False
    return {
        "ok": ok,
        "feature": "find-url",
        "url": url,
        "search_status": search_code,
        "listing_status": listing_code,
        "state": state,
        "company_name": company,
        "host_expected": host,
        "host_mentioned": host_hit,
        "research_failed": research_failed,
        "forbidden_identity": strawberry,
        "error": None
        if ok
        else {
            "search_status": search_code,
            "research_failed": research_failed,
            "forbidden_identity": strawberry,
            "search": search if search_code != 200 else {"state": state, "company_name": company},
        },
    }


def _ts_class_option_ids(src: str) -> list[str]:
    block = _slice(src, "export const DEFAULT_CLASS_OPTIONS", "export const CLASS_OPTION_IDS")
    return re.findall(r'\bid:\s*"([a-z_]+)"', block)


def _py_class_option_ids(src: str) -> list[str]:
    block = _slice(src, "CLASS_OPTIONS: list[dict[str, str]] = [", "def public_class_options")
    return re.findall(r'"id":\s*"([a-z_]+)"', block)


def _diligent_catalog_classes() -> list[str]:
    classes: list[str] = []
    if OEM_SKU_SEED.is_file():
        try:
            payload = json.loads(_read(OEM_SKU_SEED))
        except json.JSONDecodeError:
            payload = []
        rows = payload.get("vendors") if isinstance(payload, dict) else payload
        for vendor in rows if isinstance(rows, list) else []:
            if not isinstance(vendor, dict):
                continue
            domains = " ".join(str(d) for d in (vendor.get("domains") or []))
            if "diligentrobots.com" not in domains.lower() and "diligent" not in str(
                vendor.get("vendor_name") or ""
            ).lower():
                continue
            for robot in vendor.get("robots") or []:
                if not isinstance(robot, dict):
                    continue
                if str(robot.get("name") or "").strip().lower() != "moxi":
                    continue
                classes.append(str(robot.get("primary_class") or "").lower())
                for claim in robot.get("catalog_claims") or []:
                    if isinstance(claim, dict) and claim.get("predicate") == "product_class":
                        classes.append(str(claim.get("value") or "").lower())
    if KNOWN_OEM_JSON.is_file():
        try:
            listing = json.loads(_read(KNOWN_OEM_JSON))
        except json.JSONDecodeError:
            listing = {}
        row = listing.get("diligentrobots.com") if isinstance(listing, dict) else None
        if isinstance(row, dict):
            for robot in row.get("robots") or []:
                if isinstance(robot, dict):
                    classes.append(str(robot.get("display_class") or "").lower())
    return [c for c in classes if c]


def _named_healthcare_corpus_jobs() -> int:
    if not JOB_CORPUS.is_file():
        return 0
    try:
        rows = json.loads(_read(JOB_CORPUS))
    except json.JSONDecodeError:
        return 0
    if isinstance(rows, dict):
        rows = rows.get("jobs") or rows.get("items") or []
    n = 0
    for job in rows if isinstance(rows, list) else []:
        if not isinstance(job, dict):
            continue
        family = str(job.get("tape_family") or "").lower()
        source = str(job.get("source") or "").lower()
        if family not in {"clinical_delivery", "resident_services"} and "healthcare" not in source:
            continue
        if str(job.get("company_name") or "").strip():
            n += 1
    return n


def healthcare_class_fixture() -> tuple[bool, str]:
    """Source/fixture Critic: Diligent is healthcare, Healthcare tile exists, named jobs exist."""
    misses: list[str] = []
    site = _read(PSTACK_SITE) if PSTACK_SITE.is_file() else ""
    protocol = _read(PROTOCOL_PY) if PROTOCOL_PY.is_file() else ""
    release_ts = _read(PSTACK_RELEASE_TS) if PSTACK_RELEASE_TS.is_file() else ""
    release_yaml = _read(RELEASE_YAML) if RELEASE_YAML.is_file() else ""
    class_ts = _read(CLASS_OPTIONS_TS) if CLASS_OPTIONS_TS.is_file() else ""
    class_py = _read(CLASS_QUALIFY) if CLASS_QUALIFY.is_file() else ""
    workflow = _read(WORKFLOW_TS) if WORKFLOW_TS.is_file() else ""
    workflow_test = _read(WORKFLOW_TEST) if WORKFLOW_TEST.is_file() else ""
    hc_test = _read(HEALTHCARE_TEST) if HEALTHCARE_TEST.is_file() else ""

    gate_ids = re.findall(r'id:\s*"([a-z_]+)"', _slice(site, "export const CRITIC_GATES", "export const CRITIC_HELDOUT"))
    if not gate_ids:
        gate_ids = re.findall(r'"id":\s*"([a-z_]+)"', protocol)
    if tuple(gate_ids) != REQUIRED_CRITIC_GATE_IDS:
        misses.append(f"criticGateIds={gate_ids}")
    if "healthcare_class" not in site or "healthcare_class" not in protocol:
        misses.append("healthcare_class missing from site/protocol")
    if DILIGENT not in site or DILIGENT not in protocol:
        misses.append("held-out diligentrobots.com missing")
    if "HEALTHCARE_CLASS_FIXTURE" not in release_ts or "diligentMustNotBeHumanoidEmpty" not in release_ts:
        misses.append("HEALTHCARE_CLASS_FIXTURE missing")
    if "healthcare_class" not in release_yaml or DILIGENT not in release_yaml:
        misses.append("release.yaml missing healthcare_class / Diligent URL")

    ts_ids = _ts_class_option_ids(class_ts)
    py_ids = _py_class_option_ids(class_py)
    extra = ("mining", "warehouse", "logistics", "factory", "hospitality", "food_prep", "serving", "cleaning")
    if "healthcare" not in ts_ids or "healthcare" not in py_ids:
        misses.append("Healthcare class id missing")
    for tile in extra:
        if tile not in ts_ids or tile not in py_ids:
            misses.append(f"{tile} class id missing")
    if "medical" in ts_ids or "hotel" in ts_ids:
        misses.append(f"aliased industries leaked as FIND tiles={ts_ids}")
    if len(ts_ids) != 20:
        misses.append(f"class picker tiles={ts_ids}")
    if '"healthcare"' not in workflow or "healthcare" not in class_py:
        misses.append("FIND_TILE / workflow missing healthcare")
    if '"food_prep"' not in workflow or "food_prep" not in class_py:
        misses.append("FIND_TILE / workflow missing food_prep")
    if '"serving"' not in workflow or "serving" not in class_py:
        misses.append("FIND_TILE / workflow missing serving")
    if '"cleaning"' not in workflow or "cleaning" not in class_py:
        misses.append("FIND_TILE / workflow missing cleaning")
    if "No ${label} jobs for this robot yet." not in workflow:
        misses.append("class empty-copy template missing")
    if 'healthcare: "Healthcare"' not in workflow:
        misses.append("Healthcare class title missing")
    if 'food_prep: "Food prep"' not in workflow:
        misses.append("Food prep class title missing")
    if 'serving: "Serving"' not in workflow:
        misses.append("Serving class title missing")
    if 'cleaning: "Cleaning"' not in workflow:
        misses.append("Cleaning class title missing")
    if "No healthcare jobs for this robot yet." not in workflow_test:
        misses.append("healthcare empty copy test missing")
    if "No food prep jobs for this robot yet." not in workflow_test:
        misses.append("food_prep empty copy test missing")
    if "No serving jobs for this robot yet." not in workflow_test:
        misses.append("serving empty copy test missing")
    if "No cleaning jobs for this robot yet." not in workflow_test:
        misses.append("cleaning empty copy test missing")
    if "No healthcare jobs for this robot yet." not in release_ts:
        misses.append("fixture empty copy missing")
    if "No humanoid jobs for this robot yet." not in release_ts:
        misses.append("fixture must forbid humanoid empty copy")

    classes = _diligent_catalog_classes()
    if not classes:
        misses.append("Diligent/Moxi catalog missing")
    elif any(c == "humanoid" for c in classes):
        misses.append(f"Diligent catalog class is humanoid ({classes})")
    elif not any(c in HEALTHCARE_CLASSES for c in classes):
        misses.append(f"Diligent catalog is not healthcare ({classes})")

    named = _named_healthcare_corpus_jobs()
    if named <= 0:
        misses.append("healthcare corpus has 0 named-employer jobs")

    if not HEALTHCARE_TEST.is_file():
        misses.append("tests/test_healthcare_class_jobs.py missing")
    else:
        if "humanoid" not in hc_test.lower():
            misses.append("healthcare pytest does not forbid humanoid")
        if "diligentrobots.com" not in hc_test:
            misses.append("healthcare pytest does not drive Diligent URL")
        if "job_count" not in hc_test:
            misses.append("healthcare pytest does not require jobs")

    return (not misses, "; ".join(misses))


REQUIRED_HEALTHCARE_ONTOLOGY_WORDS = (
    "hospital",
    "clinical",
    "pharmacy",
    "nursing",
    "patient",
    "linen",
    "med-surg",
    "unit-delivery",
)

# Distinctive industry work words. Missing any of these fails the critic
# so we do not repeat the Diligent/humanoid miss when vocabulary is absent.
REQUIRED_INDUSTRY_ONTOLOGY_WORDS = {
    "mining": ("haul truck", "stope", "longwall", "overburden", "haulage"),
    "warehouse": ("fulfillment", "pick station", "tote", "distribution center"),
    "logistics": ("3pl", "cross-dock", "sortation"),
    "factory": ("machine tend", "cnc", "workpiece", "assembly line"),
    "hospitality": ("guest room", "bellhop", "room service", "concierge"),
    "hotel": ("housekeeping", "luggage", "guest delivery"),
    "food_prep": (
        "fry station",
        "fryer",
        "make line",
        "bowl assembly",
        "grill",
        "prep cook",
        "qsr",
        "fast casual",
        "kitchen automation",
        "ingredient dosing",
        "tortilla",
        "assembly line kitchen",
        "hotel kitchen",
        "casino kitchen",
        "airport kitchen",
    ),
    "serving": (
        "table service",
        "bussing",
        "food runner",
        "waitstaff",
        "dining room",
        "cocktail server",
        "hotel dining",
        "mall food court",
    ),
    "cleaning": (
        "janitor",
        "custodian",
        "restroom",
        "restroom cleaning",
        "floor cleaning",
        "commercial cleaning",
        "floor scrubbing",
        "data center janitor",
    ),
}

REQUIRED_INDUSTRY_FIND_CLASSES = {
    "mining": "mining",
    "warehouse": "warehouse",
    "logistics": "logistics",
    "factory": "factory",
    "hospitality": "hospitality",
    "food_prep": "food_prep",
    "serving": "serving",
    "cleaning": "cleaning",
}


def ontology_industry_language_fixture() -> tuple[bool, str]:
    """Critic: industry work words and task models live in ontology files, not FIND-only lists."""
    misses: list[str] = []
    ont_lang = ROOT / "ontology" / "industry_work_language.v1.json"
    vertical = ROOT / "ontology" / "vertical_ontology.v1.json"
    tasks = ROOT / "ontology" / "task_model_ontology.v1.json"
    rules_md = ROOT / "ontology" / "ROBOT_INFERENCE_RULES.md"
    rules_json = ROOT / "ontology" / "inference_rules.v1.json"
    qualify = ROOT / "app" / "services" / "robot_class_qualify.py"
    if not ont_lang.is_file():
        return False, "ontology/industry_work_language.v1.json missing"
    blob_lang = _read(ont_lang).lower()
    blob_vert = _read(vertical).lower() if vertical.is_file() else ""
    blob_tasks = _read(tasks).lower() if tasks.is_file() else ""
    blob_rules = (_read(rules_md) + _read(rules_json)).lower()
    blob_qualify = _read(qualify) if qualify.is_file() else ""
    for word in REQUIRED_HEALTHCARE_ONTOLOGY_WORDS:
        if word not in blob_lang:
            misses.append(f"industry_work_language missing {word}")
        if word not in blob_vert and word not in blob_tasks:
            misses.append(f"{word} missing from vertical_ontology and task_model_ontology")
    if "hospital_logistics_transport" not in blob_tasks:
        misses.append("hospital_logistics_transport task model missing")
    if "r33" not in blob_rules:
        misses.append("R33 missing from inference rules")
    if "work_language_task_model" not in blob_lang:
        misses.append("inference_order missing work_language_task_model")
    if "infer_class_from_work_language" not in blob_qualify:
        misses.append("FIND class qualify does not read ontology work language")
    if "industry_class_aliases" not in blob_qualify:
        misses.append("FIND class qualify does not read ontology aliases")
    try:
        data = json.loads(_read(ont_lang))
    except json.JSONDecodeError:
        return False, "industry_work_language.v1.json is not valid JSON"
    rows = {str(r.get("id") or ""): r for r in (data.get("industries") or []) if isinstance(r, dict)}
    for industry_id, words in REQUIRED_INDUSTRY_ONTOLOGY_WORDS.items():
        row = rows.get(industry_id) or {}
        blob = " ".join(
            str(x).lower()
            for x in list(row.get("work_words") or []) + list(row.get("class_signals") or [])
        )
        for word in words:
            if word not in blob:
                misses.append(f"{industry_id} missing work word {word}")
        if not (row.get("task_model_ids") or []):
            misses.append(f"{industry_id} missing task_model_ids")
    for industry_id, find_class in REQUIRED_INDUSTRY_FIND_CLASSES.items():
        row = rows.get(industry_id) or {}
        if (row.get("find_class") or "") != find_class:
            misses.append(f"{industry_id} find_class={row.get('find_class')} want {find_class}")
    hotel = rows.get("hotel") or {}
    if (hotel.get("find_class") or "") != "hospitality":
        misses.append("hotel must alias find_class=hospitality")
    serving = rows.get("serving") or {}
    if (serving.get("find_class") or "") != "serving":
        misses.append("serving must find_class=serving")
    cleaning = rows.get("cleaning") or {}
    if (cleaning.get("find_class") or "") != "cleaning":
        misses.append("cleaning must find_class=cleaning")
    warehouse = rows.get("warehouse") or {}
    if warehouse.get("outranks_morphology"):
        misses.append("warehouse must not outrank humanoid morphology")
    factory = rows.get("factory") or {}
    if factory.get("outranks_morphology"):
        misses.append("factory must not outrank humanoid morphology")
    logistics = rows.get("logistics") or {}
    if logistics.get("outranks_morphology"):
        misses.append("logistics must not outrank humanoid morphology")
    hc = rows.get("hospitality") or {}
    if "humanoid" not in {str(x).lower() for x in (hc.get("outranks_morphology") or [])}:
        misses.append("hospitality must outrank humanoid morphology")
    if "mining_haulage_policy" not in blob_tasks:
        misses.append("mining_haulage_policy task model missing")
    if "warehouse_pick_place_policy" not in blob_tasks:
        misses.append("warehouse_pick_place_policy task model missing")
    if "hotel_guest_service_policy" not in blob_tasks:
        misses.append("hotel_guest_service_policy task model missing")
    if "food_prep_station_policy" not in blob_tasks:
        misses.append("food_prep_station_policy task model missing")
    if "dining_floor_service_policy" not in blob_tasks:
        misses.append("dining_floor_service_policy task model missing")
    if "commercial_cleaning_policy" not in blob_tasks:
        misses.append("commercial_cleaning_policy task model missing")
    if "machine_tending_load_unload" not in blob_tasks:
        misses.append("machine_tending_load_unload task model missing")
    if '"id": "mining"' not in blob_qualify:
        misses.append("FIND class qualify missing mining tile")
    return (not misses, "; ".join(misses))


def drive_diligent_healthcare(*, api: str) -> dict[str, Any]:
    """Live FIND: Diligent must not be a humanoid empty; Healthcare class returns named jobs."""
    base = api.rstrip("/")
    search_code, search = _post_json(
        f"{base}/api/robot-job-search",
        {"url": DILIGENT, "lookup_grain": "product"},
        timeout=90.0,
    )
    class_code, class_out = _post_json(
        f"{base}/api/robot-job-search",
        {
            "url": DILIGENT,
            "asserted_class": "healthcare",
            "lookup_grain": "robot_type",
        },
        timeout=90.0,
    )
    search_blob = json.dumps(search, default=str).lower() if search is not None else ""
    class_blob = json.dumps(class_out, default=str).lower() if class_out is not None else ""
    cls = (
        str(search.get("robot_class") or "").lower()
        if isinstance(search, dict)
        else ""
    )
    class_cls = (
        str(class_out.get("robot_class") or "").lower()
        if isinstance(class_out, dict)
        else ""
    )
    options = search.get("class_options") if isinstance(search, dict) else None
    option_ids = {
        str(row.get("id") or "").lower()
        for row in (options or [])
        if isinstance(row, dict)
    }
    humanoid = "humanoid" in cls.split() or cls == "humanoid" or cls.endswith("_humanoid")
    if cls == "humanoid" or "humanoid" in cls:
        humanoid = True
    human_empty = bool(HUMAN_EMPTY_RE.search(search_blob) or HUMAN_EMPTY_RE.search(class_blob))
    healthcare_direct = cls in HEALTHCARE_CLASSES
    incomplete_ok = bool(
        isinstance(search, dict) and search.get("needs_class_choice")
    ) and "healthcare" in option_ids
    identity_ok = healthcare_direct or incomplete_ok
    class_jobs = class_out.get("jobs") if isinstance(class_out, dict) else None
    named = [
        j
        for j in (class_jobs or [])
        if isinstance(j, dict) and str(j.get("company_name") or "").strip()
    ]
    class_humanoid = "humanoid" in class_cls
    class_ok = (
        class_code == 200
        and isinstance(class_out, dict)
        and len(named) > 0
        and not class_humanoid
        and not HUMAN_EMPTY_RE.search(class_blob)
    )
    search_ok = search_code == 200 and isinstance(search, dict)
    ok = (
        search_ok
        and not humanoid
        and not human_empty
        and identity_ok
        and class_ok
    )
    return {
        "ok": ok,
        "feature": "healthcare_class",
        "url": DILIGENT,
        "search_status": search_code,
        "class_status": class_code,
        "robot_class": cls,
        "class_search_robot_class": class_cls,
        "needs_class_choice": search.get("needs_class_choice") if isinstance(search, dict) else None,
        "healthcare_option": "healthcare" in option_ids,
        "humanoid": humanoid,
        "humanoid_empty": human_empty,
        "named_employer_jobs": len(named),
        "error": None
        if ok
        else {
            "search_status": search_code,
            "class_status": class_code,
            "robot_class": cls,
            "humanoid": humanoid,
            "humanoid_empty": human_empty,
            "identity_ok": identity_ok,
            "named_employer_jobs": len(named),
            "search_state": search.get("state") if isinstance(search, dict) else None,
        },
    }


def phase_critic(*, api: str, local: bool) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    identity = _read(IDENTITY) if IDENTITY.is_file() else ""
    release_ts = _read(PSTACK_RELEASE_TS) if PSTACK_RELEASE_TS.is_file() else ""
    site = _read(PSTACK_SITE) if PSTACK_SITE.is_file() else ""
    protocol = _read(PROTOCOL_PY) if PROTOCOL_PY.is_file() else ""

    checks.append(
        _check(
            "find_abort",
            "isSilentFindError" in identity
            and "findUserFacingError" in identity
            and "FIND_ABORT_FIXTURE" in release_ts
            and "find_abort" in site
            and "find_abort" in protocol,
            "AbortError and Failed to fetch do not become Research failed",
        )
    )
    checks.append(
        _check(
            "find_identity",
            "canonicalRobotUrl" in identity
            and "find_identity" in site
            and "greenfieldincorporated" in _read(ROOT / "tests" / "test_jobs_oem_listing.py"),
            "Submitted URL is the identity key; Greenfield is not a strawberry OEM",
        )
    )
    checks.append(
        _check(
            "crm_leftover",
            "crm_leftover" in site
            and "CRM_LEFTOVER_FIXTURE" in release_ts
            and "strawberry robot" in _read(ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsCrmAccount.test.ts"),
            "CRM leftover strawberry robot fixture is required on Jobs PRs",
        )
    )
    oem_discover = (
        _read(ROOT / "app" / "services" / "oem_sku_discover.py")
        if (ROOT / "app" / "services" / "oem_sku_discover.py").is_file()
        else ""
    )
    oem_test = (
        _read(ROOT / "tests" / "test_unknown_oem_extract.py")
        if (ROOT / "tests" / "test_unknown_oem_extract.py").is_file()
        else ""
    )
    checks.append(
        _check(
            "oem_extract",
            "oem_extract" in site
            and "oem_extract" in protocol
            and "CRITIC_HELDOUT_FIND_URLS" in protocol
            and "is_site_chrome_name" in oem_discover
            and "CRITIC_HELDOUT_FIND_URLS" in oem_test,
            "unknown OEM picker is evidence-only; chrome names are not SKUs",
        )
    )
    workspace = _read(WORKSPACE) if WORKSPACE.is_file() else ""
    qualify = _slice(workspace, "async function qualifyActive", "function revealJobs")
    class_picker_src = (
        "class_picker" in site
        and "class_picker" in protocol
        and "CLASS_PICKER_FIXTURE" in release_ts
        and "CLASS_PICKER_PROMPT" in workspace
        and "qualifySearchLookupGrain" in qualify
        and "needsClassChoice: false" in qualify
        and "if (!a) return" not in qualify
        and "What kind of robot is" not in workspace
    )
    checks.append(
        _check(
            "class_picker",
            class_picker_src,
            "Class-picker click is not a no-op; Agriculture starts robot-job-search",
        )
    )
    fixture_ok, fixture_detail = healthcare_class_fixture()
    checks.append(
        _check(
            "healthcare_class",
            fixture_ok,
            "Diligent/Moxi is healthcare, Healthcare tile exists, named hospital jobs exist",
            fixture_detail,
        )
    )
    ont_ok, ont_detail = ontology_industry_language_fixture()
    checks.append(
        _check(
            "ontology_industry_language",
            ont_ok,
            "Healthcare work words live in ontology files and FIND qualify reads them; other industries keep distinctive words + find_class",
            ont_detail,
        )
    )

    drives: list[dict[str, Any]] = []
    if local:
        checks.append(
            _check(
                "find_drive",
                True,
                "FIND URL drive skipped (--local)",
                "skipped",
            )
        )
        checks.append(
            _check(
                "healthcare_class:live",
                True,
                "Diligent FIND drive skipped (--local)",
                "skipped",
            )
        )
    else:
        wait_for_fly_health(api)
        for url in (DEXMATE, GREENFIELD):
            drive = drive_find_url(url, api=api)
            drives.append(drive)
            checks.append(
                _check(
                    f"find_drive:{url}",
                    bool(drive.get("ok")),
                    f"POST /api/robot-job-search {url} is not Research failed / leftover identity",
                    "" if drive.get("ok") else json.dumps(drive.get("error"), default=str)[:500],
                )
            )
        diligent = drive_diligent_healthcare(api=api)
        drives.append(diligent)
        checks.append(
            _check(
                "healthcare_class:live",
                bool(diligent.get("ok")),
                "Live FIND Diligent is not humanoid empty; Healthcare class returns named employers",
                "" if diligent.get("ok") else json.dumps(diligent.get("error"), default=str)[:500],
            )
        )

    ok = all(c["ok"] for c in checks)
    return {"phase": "critic", "ok": ok, "checks": checks, "drives": drives}


def run_pstack_release(*, api: str | None = None, local: bool = False) -> dict[str, Any]:
    how = phase_how()
    act = phase_act()
    critic = phase_critic(api=(api or FLY_API), local=local)
    ok = how["ok"] and act["ok"] and critic["ok"]
    return {
        "ok": ok,
        "protocol": "pstack",
        "authority": "release_gate",
        "chrome_required": False,
        "how": how,
        "act": act,
        "critic": critic,
        "local": local,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="pstack How / Act / Critic release gate")
    p.add_argument("--local", action="store_true", help="How + Act + fixtures; skip Fly FIND drive")
    p.add_argument("--fly", default=FLY_API)
    p.add_argument("--evidence", default="")
    args = p.parse_args()
    result = run_pstack_release(api=args.fly, local=args.local)
    if args.evidence:
        out = Path(args.evidence)
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "pstack-release.json", result)
        print(f"evidence: {out / 'pstack-release.json'}")
    print(json.dumps(result, indent=2, default=str))
    if not result["ok"]:
        print("FAIL: pstack How / Act / Critic — Jobs PR must not merge", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
