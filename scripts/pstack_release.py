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
RESEARCH_FAILED_RE = re.compile(r"research failed|failed to fetch", re.I)
STRAWBERRY_RE = re.compile(r"strawberry|agrobot|harvest\s*croo|harvestcroo", re.I)


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

    checks.append(
        _check(
            "release_helpers",
            "FIND_ABORT_FIXTURE" in release_ts and "CRM_LEFTOVER_FIXTURE" in release_ts,
            "pstackRelease.ts encodes the #173 abort and #172 leftover fixtures",
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
    else:
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
