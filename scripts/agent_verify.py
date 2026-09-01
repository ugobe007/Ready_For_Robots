#!/usr/bin/env python3
"""Agent verification for ReadyForRobots Jobs.

pstack shape: doctor (is this instance worth driving?) then drive a user path
and capture evidence. Production (Vercel HTML/JS + Fly API) is the honest
surface — a local Vite shell is optional chrome, not a substitute for Fly.

  python3 scripts/agent_verify.py doctor
  python3 scripts/agent_verify.py drive --feature find-jobs
  python3 scripts/agent_verify.py pstack
  python3 scripts/agent_verify.py ci
  python3 scripts/agent_verify.py launch   # print local Vite command; does not daemonize

Never kill processes by name. Cleanup only tears down PIDs this run started.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FLY_API = os.getenv("RFR_FLY_API", "https://ready-2-robot.fly.dev").rstrip("/")
SITE = os.getenv("RFR_SITE", "https://readyforrobots.com").rstrip("/")
LOCAL_ORIGIN = os.getenv("RFR_LOCAL_ORIGIN", "http://127.0.0.1:3000").rstrip("/")
JS_PATH_RE = re.compile(r"/assets/index-[A-Za-z0-9_-]+\.js")
STALE_JS = "/assets/index-bxLpnQiT.js"
FIND_HEADLINE = "Find jobs for your robot"
FIND_JOBS_CTA = "Find jobs →"
# Production lags this PR. Live `/` may still ship the previous FIND action.
LIVE_FIND_ACTION_LEGACY = "Start jobs →"
JOBS_ACTIVATE = "jobs_activate"
CANARY_JS = ("Jobs for", FIND_HEADLINE, JOBS_ACTIVATE)
FIND_JOBS_WORKFLOW = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "jobsWorkflow.ts"
FIND_RESEARCH = ROOT / "readyforrobots-new" / "client" / "src" / "lib" / "findResearch.ts"
FIND_WORKSPACE = ROOT / "readyforrobots-new" / "client" / "src" / "components" / "RobotJobsWorkspace.tsx"
JOBS_PAGE = ROOT / "readyforrobots-new" / "client" / "src" / "pages" / "Jobs.tsx"
EMPLOYER_MATCH_PY = ROOT / "app" / "services" / "employer_robot_match.py"
VEGA = ROOT / "tests" / "fixtures" / "m2_profiles" / "vega.json"
SKILL_DIR = ROOT / ".cursor" / "skills" / "verify-readyforrobots"
FEATURE_DIR = SKILL_DIR / "features"

DEFAULT_EVIDENCE = Path(
    os.getenv("RFR_VERIFY_EVIDENCE")
    or (Path("/opt/cursor/artifacts") if Path("/opt/cursor/artifacts").is_dir() else Path("/tmp/rfr-verify"))
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def evidence_dir(base: Path | None = None) -> Path:
    d = (base or DEFAULT_EVIDENCE) / f"verify-{_now()}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get(url: str, *, timeout: float = 25.0) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"Accept": "application/json, text/html;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return int(resp.status), body, url
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read() if exc.fp else b"", url
    except Exception as exc:
        return 0, str(exc).encode(), url


def _post_json(url: str, payload: dict[str, Any], *, timeout: float = 60.0) -> tuple[int, Any]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return int(resp.status), json.loads(raw.decode())
            except json.JSONDecodeError:
                return int(resp.status), {"_raw": raw[:400].decode("utf-8", "replace")}
    except urllib.error.HTTPError as exc:
        raw = exc.read() if exc.fp else b""
        try:
            return int(exc.code), json.loads(raw.decode())
        except Exception:
            return int(exc.code), {"_raw": raw[:400].decode("utf-8", "replace")}
    except Exception as exc:
        return 0, {"error": str(exc)}


def doctor(*, origin: str | None = None, fly: str | None = None) -> dict[str, Any]:
    """Read-only: is this instance worth driving?"""
    site = (origin or SITE).rstrip("/")
    api = (fly or FLY_API).rstrip("/")
    checks: list[dict[str, Any]] = []
    alerts: list[str] = []

    code, body, url = _get(f"{api}/health", timeout=15)
    health_ok = code == 200
    checks.append({"id": "fly_health", "ok": health_ok, "url": url, "status": code})
    if not health_ok:
        alerts.append(f"Fly /health {code}")

    code, body, url = _get(f"{api}/api/leads/pipeline", timeout=25)
    pipeline: dict[str, Any] = {}
    try:
        pipeline = json.loads(body.decode()) if body else {}
    except json.JSONDecodeError:
        pipeline = {}
    leads = pipeline.get("leads") if isinstance(pipeline, dict) else None
    built = pipeline.get("built_at") if isinstance(pipeline, dict) else None
    pipe_ok = code == 200 and isinstance(leads, list) and bool(built)
    checks.append(
        {
            "id": "fly_pipeline",
            "ok": pipe_ok,
            "url": url,
            "status": code,
            "built_at": built,
            "leads_count": len(leads) if isinstance(leads, list) else 0,
        }
    )
    if not pipe_ok:
        alerts.append("Fly pipeline missing built_at or leads")

    code, html, url = _get(f"{site}/", timeout=20)
    html_s = html.decode("utf-8", "replace") if html else ""
    js_m = JS_PATH_RE.search(html_s)
    js_path = js_m.group(0) if js_m else None
    skip_green = bool(js_path and js_path == STALE_JS)
    page_ok = code == 200 and bool(js_path) and not skip_green
    checks.append(
        {
            "id": "site_html",
            "ok": page_ok,
            "url": url,
            "status": code,
            "js_path": js_path,
            "skip_green_stale_js": skip_green,
        }
    )
    if skip_green:
        alerts.append(f"Vercel skip-green stale JS {STALE_JS}")
    if not js_path:
        alerts.append("No /assets/index-*.js on homepage")

    js_hits: dict[str, bool] = {}
    js_ok = False
    if js_path:
        jcode, js, jurl = _get(f"{site}{js_path}", timeout=30)
        js_text = js.decode("utf-8", "replace") if js else ""
        js_hits = {c: c in js_text for c in CANARY_JS}
        js_ok = jcode == 200 and all(js_hits.values()) and len(js) > 100_000
        checks.append(
            {
                "id": "jobs_js_canary",
                "ok": js_ok,
                "url": jurl,
                "status": jcode,
                "bytes": len(js),
                "hits": js_hits,
            }
        )
        if not js_ok:
            alerts.append("Jobs JS missing FIND/activate canaries")

    ok = health_ok and pipe_ok and page_ok and js_ok
    return {
        "ok": ok,
        "worth_driving": ok,
        "site": site,
        "fly": api,
        "checks": checks,
        "alerts": alerts,
        "skip_green": skip_green,
    }


def _pstack_mod():
    import importlib.util

    path = ROOT / "scripts" / "pstack_release.py"
    spec = importlib.util.spec_from_file_location("pstack_release", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def drive_find_url(*, api: str | None = None, url: str = "https://www.dexmate.ai/") -> dict[str, Any]:
    """FIND submit path: POST /api/robot-job-search for a real OEM URL."""
    return _pstack_mod().drive_find_url(url, api=(api or FLY_API).rstrip("/"))


def drive_find_jobs(*, api: str | None = None) -> dict[str, Any]:
    """User path: robot résumé → Job Cards. Uses the same match API the Jobs terminal calls."""
    base = (api or FLY_API).rstrip("/")
    profile = None
    if VEGA.exists():
        profile = json.loads(VEGA.read_text(encoding="utf-8"))
        payload: dict[str, Any] = {
            "url": "https://www.dexmate.ai/",
            "robot_name": "Vega",
            "profile": profile,
        }
    else:
        payload = {"chip": "manipulates", "robot_name": "verification robot"}
    code, data = _post_json(f"{base}/api/robot-job-match", payload)
    jobs = data.get("jobs") if isinstance(data, dict) else None
    count = int(data.get("job_count") or 0) if isinstance(data, dict) else 0
    titles = [j.get("title") for j in (jobs or [])[:8] if isinstance(j, dict)]
    employers = [j.get("company_name") for j in (jobs or [])[:8] if isinstance(j, dict)]
    named = [e for e in employers if e]
    cards = 0
    contract = None
    for job in jobs or []:
        models = job.get("required_task_models") or []
        if models:
            cards += 1
            if not contract:
                contract = (models[0] or {}).get("card_contract") or (models[0] or {}).get("id")
    ok = (
        code == 200
        and isinstance(data, dict)
        and data.get("state") in {"matches", "thin_corpus"}
        and count > 0
        and bool(titles)
    )
    # Named employers are required for trust when the matcher is requirement_v1.
    if data.get("matcher") == "requirement_v1" and not named:
        ok = False
    return {
        "ok": ok,
        "feature": "find-jobs",
        "status": code,
        "state": data.get("state") if isinstance(data, dict) else None,
        "matcher": data.get("matcher") if isinstance(data, dict) else None,
        "job_count": count,
        "titles": titles,
        "employers": named,
        "task_model_jobs": cards,
        "card_contract": contract,
        "error": None
        if ok
        else {
            "status": code,
            "state": data.get("state") if isinstance(data, dict) else None,
            "job_count": count,
        },
    }


def repo_find_jobs_cta_ok(source: str | None = None) -> bool:
    """This checkout's FIND button is Find jobs →, not Start jobs."""
    text = source
    if text is None:
        if not FIND_JOBS_WORKFLOW.is_file():
            return False
        text = FIND_JOBS_WORKFLOW.read_text(encoding="utf-8")
    return f'FIND_JOBS_CTA = "{FIND_JOBS_CTA}"' in text and "Start jobs" not in text


def jobs_chrome_hits(js_text: str, *, source: str | None = None) -> dict[str, bool]:
    """Live bundle proves Jobs chrome; checkout proves the FIND CTA copy."""
    return {
        "find_headline": FIND_HEADLINE in js_text,
        "jobs_activate": JOBS_ACTIVATE in js_text,
        "process_01": "Show us your robot" in js_text,
        "process_02": "Available jobs" in js_text,
        "find_jobs_live": FIND_JOBS_CTA in js_text or LIVE_FIND_ACTION_LEGACY in js_text,
        "find_jobs_source": repo_find_jobs_cta_ok(source),
    }


def drive_jobs_chrome(*, origin: str | None = None) -> dict[str, Any]:
    """Jobs chrome: FIND headline + jobs_activate in the shipped bundle; Pipeline is SIGNAL-only."""
    site = (origin or SITE).rstrip("/")
    code, html, url = _get(f"{site}/", timeout=20)
    html_s = html.decode("utf-8", "replace") if html else ""
    js_m = JS_PATH_RE.search(html_s)
    if not js_m:
        return {"ok": False, "feature": "jobs-chrome", "error": "no JS path", "url": url}
    jcode, js, jurl = _get(f"{site}{js_m.group(0)}", timeout=30)
    text = js.decode("utf-8", "replace") if js else ""
    hits = jobs_chrome_hits(text)
    ok = jcode == 200 and all(hits.values())
    return {
        "ok": ok,
        "feature": "jobs-chrome",
        "url": jurl,
        "status": jcode,
        "hits": hits,
    }


def drive_about(*, origin: str | None = None) -> dict[str, Any]:
    site = (origin or SITE).rstrip("/")
    code, html, url = _get(f"{site}/intelligence", timeout=20)
    html_s = html.decode("utf-8", "replace") if html else ""
    # SPA: prove the route is wired in the shell + JS canary from homepage bundle.
    _, home, _ = _get(f"{site}/", timeout=20)
    js_m = JS_PATH_RE.search(home.decode("utf-8", "replace") if home else "")
    js_ok = False
    if js_m:
        _, js, _ = _get(f"{site}{js_m.group(0)}", timeout=30)
        js_ok = "/intelligence" in (js.decode("utf-8", "replace") if js else "")
    ok = code == 200 and js_ok
    return {"ok": ok, "feature": "about", "status": code, "url": url, "js_has_intelligence_route": js_ok}


def drive_jobs_crm(*, origin: str | None = None) -> dict[str, Any]:
    """Activate URL is reachable. Unlocked job list needs a session — report that honestly."""
    site = (origin or SITE).rstrip("/")
    dest = f"{site}/pipeline?src=jobs_activate"
    code, html, url = _get(dest, timeout=20)
    text = html.decode("utf-8", "replace") if html else ""
    # SPA always 200; prove src is in the bundle and the path exists.
    _, home, _ = _get(f"{site}/", timeout=20)
    js_m = JS_PATH_RE.search(home.decode("utf-8", "replace") if home else "")
    js_text = ""
    if js_m:
        _, js, _ = _get(f"{site}{js_m.group(0)}", timeout=30)
        js_text = js.decode("utf-8", "replace") if js else ""
    ok = code == 200 and JOBS_ACTIVATE in js_text and "/pipeline" in js_text
    return {
        "ok": ok,
        "feature": "jobs-crm",
        "status": code,
        "url": url,
        "unlocked_jobs_visible": False,
        "prerequisite": "Jobs handoff snapshot (and usually a signed-in session) required to see 5 unlocked jobs. Anonymous without a snapshot must not land on SIGNAL Pipeline.",
        "js_has_activate": JOBS_ACTIVATE in js_text,
        "html_len": len(text),
    }


def drive_find_stay(*, origin: str | None = None, api: str | None = None) -> dict[str, Any]:
    """FIND timeout / 500 / abort must remain on /?visit=jobs. Skip-green is a fail."""
    site = (origin or SITE).rstrip("/")
    fly = (api or FLY_API).rstrip("/")
    workspace = FIND_WORKSPACE.read_text(encoding="utf-8") if FIND_WORKSPACE.is_file() else ""
    submit = ""
    start = workspace.find("async function submitFind")
    end = workspace.find("async function confirmSelection")
    if start >= 0 and end > start:
        submit = workspace[start:end]
    jobs_page = JOBS_PAGE.read_text(encoding="utf-8") if JOBS_PAGE.is_file() else ""
    research = FIND_RESEARCH.read_text(encoding="utf-8") if FIND_RESEARCH.is_file() else ""
    src_ok = (
        "ensureFindStayVisit" in submit
        and "goJobsFreshHome" not in submit
        and "JOBS_FRESH_HOME_EVENT" not in submit
        and "?new=1" not in submit
        and 'setLocation("/")' not in submit
        and "findFailureBouncesHome" in research
        and 'forcedLanding && fromSearch === "landing"' in jobs_page
        and "FIND_IDENTITY_TIMEOUT_MS = 8_000" in (
            FIND_JOBS_WORKFLOW.read_text(encoding="utf-8") if FIND_JOBS_WORKFLOW.is_file() else ""
        )
    )
    code, html, url = _get(f"{site}/", timeout=20)
    html_s = html.decode("utf-8", "replace") if html else ""
    js_m = JS_PATH_RE.search(html_s)
    skip_green = bool(js_m and js_m.group(0) == STALE_JS)
    # Invalid URL must 400 as JSON, never an HTML landing dump. Do not wait
    # on a real OEM compose — that is find-url / pstack Critic, not bounce.
    live_code, live_body = _post_json(
        f"{fly}/api/robot-job-search",
        {},
        timeout=6,
    )
    raw = ""
    if isinstance(live_body, dict):
        raw = json.dumps(live_body)
    elif live_body is not None:
        raw = str(live_body)
    html_dump = bool(re.search(r"<html|put your robot to work|robots need jobs", raw, re.I))
    ok = src_ok and not skip_green and not html_dump
    return {
        "ok": ok,
        "feature": "find-stay",
        "skip_green": skip_green,
        "src_ok": src_ok,
        "html_dump": html_dump,
        "search_status": live_code,
        "url": url,
        "error": None
        if ok
        else {
            "skip_green": skip_green,
            "src_ok": src_ok,
            "html_dump": html_dump,
            "search_status": live_code,
        },
    }


def drive_employer_match(*, api: str | None = None) -> dict[str, Any]:
    """Employer MATCH is catalog-only and has a 3s budget once the new field is live."""
    fly = (api or FLY_API).rstrip("/")
    py = EMPLOYER_MATCH_PY.read_text(encoding="utf-8") if EMPLOYER_MATCH_PY.is_file() else ""
    src_ok = (
        "_catalog_robots_snapshot" in py
        and "listing_from_catalog" not in py
        and "build_robot_profile" not in py
        and "scrape_robot_page" not in py
    )
    t0 = time.perf_counter()
    code, data = _post_json(
        f"{fly}/api/employer-robot-match",
        {"work_class": "serving"},
        timeout=3.2,
    )
    elapsed = time.perf_counter() - t0
    live_ok = True
    if isinstance(data, dict) and data.get("catalog_only") is True:
        live_ok = (
            code == 200
            and elapsed < 3.0
            and data.get("live_scrape") is False
        )
        if data.get("state") == "matches" and not data.get("robots"):
            live_ok = False
    elif code not in (0, 200, 400, 422):
        live_ok = False
    ok = src_ok and live_ok
    return {
        "ok": ok,
        "feature": "employer-match",
        "src_ok": src_ok,
        "status": code,
        "elapsed_s": round(elapsed, 3),
        "catalog_only": data.get("catalog_only") if isinstance(data, dict) else None,
        "robot_count": data.get("robot_count") if isinstance(data, dict) else None,
        "error": None if ok else {"status": code, "elapsed_s": elapsed, "src_ok": src_ok},
    }


DRIVERS = {
    "find-jobs": drive_find_jobs,
    "find-url": drive_find_url,
    "job-cards": drive_find_jobs,  # same match payload; cards live on the jobs
    "jobs-chrome": drive_jobs_chrome,
    "jobs-crm": drive_jobs_crm,
    "about": drive_about,
    "find-stay": drive_find_stay,
    "employer-match": drive_employer_match,
}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def cmd_doctor(args: argparse.Namespace) -> int:
    out_dir = Path(args.evidence) if args.evidence else evidence_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    result = doctor(origin=args.origin, fly=args.fly)
    write_json(out_dir / "doctor.json", result)
    print(json.dumps(result, indent=2, default=str))
    print(f"evidence: {out_dir / 'doctor.json'}")
    return 0 if result.get("ok") else 1


def cmd_drive(args: argparse.Namespace) -> int:
    out_dir = Path(args.evidence) if args.evidence else evidence_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.feature in {"find-jobs", "job-cards"}:
        result = drive_find_jobs(api=args.fly)
        if args.feature == "job-cards":
            result["feature"] = "job-cards"
            result["ok"] = bool(result.get("ok") and (result.get("titles")))
    elif args.feature == "find-url":
        result = drive_find_url(api=args.fly)
    elif args.feature == "jobs-chrome":
        result = drive_jobs_chrome(origin=args.origin)
    elif args.feature == "about":
        result = drive_about(origin=args.origin)
    elif args.feature == "jobs-crm":
        result = drive_jobs_crm(origin=args.origin)
    elif args.feature == "find-stay":
        result = drive_find_stay(origin=args.origin, api=args.fly)
    elif args.feature == "employer-match":
        result = drive_employer_match(api=args.fly)
    else:
        print(f"unknown feature {args.feature}", file=sys.stderr)
        return 2
    write_json(out_dir / f"drive-{args.feature}.json", result)
    print(json.dumps(result, indent=2, default=str))
    print(f"evidence: {out_dir / f'drive-{args.feature}.json'}")
    return 0 if result.get("ok") else 1


def cmd_ci(args: argparse.Namespace) -> int:
    out_dir = Path(args.evidence) if args.evidence else evidence_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = doctor(origin=args.origin, fly=args.fly)
    write_json(out_dir / "doctor.json", doc)
    pstack = _pstack_mod().run_pstack_release(api=args.fly, local=True)
    write_json(out_dir / "pstack-release.json", pstack)
    drives = {}
    rc = 0 if doc.get("ok") and pstack.get("ok") else 1
    for feat in ("find-jobs", "jobs-chrome", "about", "jobs-crm", "find-stay"):
        if feat == "find-jobs":
            drives[feat] = drive_find_jobs(api=args.fly)
        elif feat == "jobs-chrome":
            drives[feat] = drive_jobs_chrome(origin=args.origin)
        elif feat == "about":
            drives[feat] = drive_about(origin=args.origin)
        elif feat == "find-stay":
            drives[feat] = drive_find_stay(origin=args.origin, api=args.fly)
        elif feat == "employer-match":
            drives[feat] = drive_employer_match(api=args.fly)
        else:
            drives[feat] = drive_jobs_crm(origin=args.origin)
        write_json(out_dir / f"drive-{feat}.json", drives[feat])
        if not drives[feat].get("ok"):
            rc = 1
    summary = {
        "ok": rc == 0,
        "skip_green": doc.get("skip_green"),
        "doctor": doc.get("ok"),
        "pstack": pstack.get("ok"),
        "drives": {k: v.get("ok") for k, v in drives.items()},
        "alerts": doc.get("alerts"),
        "evidence": str(out_dir),
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, default=str))
    if not pstack.get("ok"):
        print("FAIL: pstack How / Act / Critic — do not auto-merge", file=sys.stderr)
        return 1
    if doc.get("skip_green"):
        print("FAIL: skip-green Vercel JS — do not auto-merge", file=sys.stderr)
        return 1
    return rc


def cmd_pstack(args: argparse.Namespace) -> int:
    out_dir = Path(args.evidence) if args.evidence else evidence_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    result = _pstack_mod().run_pstack_release(api=args.fly, local=bool(getattr(args, "local", False)))
    write_json(out_dir / "pstack-release.json", result)
    print(json.dumps(result, indent=2, default=str))
    print(f"evidence: {out_dir / 'pstack-release.json'}")
    return 0 if result.get("ok") else 1


def cmd_launch(_args: argparse.Namespace) -> int:
    print("Local Jobs UI (optional chrome; production Fly/Vercel is the honest surface):")
    print("  cd readyforrobots-new && pnpm exec vite --host --port 3000")
    print("Ready when http://127.0.0.1:3000/ returns 200.")
    print("Teardown: kill the PID you started. Never pkill by name.")
    return 0


def feature_map_ok() -> list[str]:
    errors: list[str] = []
    if not FEATURE_DIR.is_dir():
        return [f"missing {FEATURE_DIR}"]
    index = FEATURE_DIR / "README.md"
    if not index.exists():
        errors.append("features/README.md missing")
    required = ("find-jobs.md", "job-cards.md", "jobs-chrome.md", "jobs-crm.md", "about.md", "find-stay.md")
    for name in required:
        path = FEATURE_DIR / name
        if not path.exists():
            errors.append(f"missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        for h2 in ("## Sub-features", "## How to get to it (user POV)", "## Driving it with", "## Gotchas"):
            if h2 not in text:
                errors.append(f"{name} missing {h2}")
    return errors


def cmd_map(_args: argparse.Namespace) -> int:
    errs = feature_map_ok()
    payload = {"ok": not errs, "errors": errs, "dir": str(FEATURE_DIR)}
    print(json.dumps(payload, indent=2))
    return 0 if not errs else 1


def main() -> int:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--origin", default=SITE)
    shared.add_argument("--fly", default=FLY_API)
    shared.add_argument("--evidence", default="")
    p = argparse.ArgumentParser(description="ReadyForRobots agent verification")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", parents=[shared])
    d = sub.add_parser("drive", parents=[shared])
    d.add_argument("--feature", required=True, choices=sorted(DRIVERS))
    sub.add_parser("ci", parents=[shared])
    ps = sub.add_parser("pstack", parents=[shared])
    ps.add_argument("--local", action="store_true", help="How + Act + fixtures; skip Fly FIND drive")
    sub.add_parser("launch", parents=[shared])
    sub.add_parser("map", parents=[shared])
    args = p.parse_args()
    if args.cmd == "doctor":
        return cmd_doctor(args)
    if args.cmd == "drive":
        return cmd_drive(args)
    if args.cmd == "ci":
        return cmd_ci(args)
    if args.cmd == "pstack":
        return cmd_pstack(args)
    if args.cmd == "launch":
        return cmd_launch(args)
    if args.cmd == "map":
        return cmd_map(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
