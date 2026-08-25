#!/usr/bin/env python3
"""Agent verification for ReadyForRobots Jobs.

pstack shape: doctor (is this instance worth driving?) then drive a user path
and capture evidence. Production (Vercel HTML/JS + Fly API) is the honest
surface — a local Vite shell is optional chrome, not a substitute for Fly.

  python3 scripts/agent_verify.py doctor
  python3 scripts/agent_verify.py drive --feature find-jobs
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
JOBS_ACTIVATE = "jobs_activate"
CANARY_JS = ("Jobs for", FIND_HEADLINE, JOBS_ACTIVATE)
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
    hits = {
        "find_headline": FIND_HEADLINE in text,
        "jobs_activate": JOBS_ACTIVATE in text,
        "process_01": "Show us your robot" in text,
        "process_02": "Here are its jobs" in text,
        "start_jobs": "Start jobs" in text,
    }
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


DRIVERS = {
    "find-jobs": drive_find_jobs,
    "job-cards": drive_find_jobs,  # same match payload; cards live on the jobs
    "jobs-chrome": drive_jobs_chrome,
    "jobs-crm": drive_jobs_crm,
    "about": drive_about,
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
    elif args.feature == "jobs-chrome":
        result = drive_jobs_chrome(origin=args.origin)
    elif args.feature == "about":
        result = drive_about(origin=args.origin)
    elif args.feature == "jobs-crm":
        result = drive_jobs_crm(origin=args.origin)
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
    drives = {}
    rc = 0 if doc.get("ok") else 1
    for feat in ("find-jobs", "jobs-chrome", "about", "jobs-crm"):
        if feat == "find-jobs":
            drives[feat] = drive_find_jobs(api=args.fly)
        elif feat == "jobs-chrome":
            drives[feat] = drive_jobs_chrome(origin=args.origin)
        elif feat == "about":
            drives[feat] = drive_about(origin=args.origin)
        else:
            drives[feat] = drive_jobs_crm(origin=args.origin)
        write_json(out_dir / f"drive-{feat}.json", drives[feat])
        if not drives[feat].get("ok"):
            rc = 1
    summary = {
        "ok": rc == 0,
        "skip_green": doc.get("skip_green"),
        "doctor": doc.get("ok"),
        "drives": {k: v.get("ok") for k, v in drives.items()},
        "alerts": doc.get("alerts"),
        "evidence": str(out_dir),
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, default=str))
    if doc.get("skip_green"):
        print("FAIL: skip-green Vercel JS — do not auto-merge", file=sys.stderr)
        return 1
    return rc


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
    required = ("find-jobs.md", "job-cards.md", "jobs-chrome.md", "jobs-crm.md", "about.md")
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
    sub.add_parser("launch", parents=[shared])
    sub.add_parser("map", parents=[shared])
    args = p.parse_args()
    if args.cmd == "doctor":
        return cmd_doctor(args)
    if args.cmd == "drive":
        return cmd_drive(args)
    if args.cmd == "ci":
        return cmd_ci(args)
    if args.cmd == "launch":
        return cmd_launch(args)
    if args.cmd == "map":
        return cmd_map(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
