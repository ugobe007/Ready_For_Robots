#!/usr/bin/env python3
"""Fold missions + optional snapshot + deploy truth into compiled memory.

Chat is not memory. Agents read reports/compiled_memory_latest.json (not committed).

  python3 scripts/harness_compile_memory.py
  python3 scripts/harness_compile_memory.py --stdout
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from scripts.harness_vercel_truth import (  # noqa: E402
    classify_frontend_deploy_run,
    vercel_production_is_a_lie,
)

REPORTS = _root / "reports"
OUT_PATH = REPORTS / "compiled_memory_latest.json"
MISSIONS = _root / "missions"
FOLLOWUP_RE = re.compile(r"^[-*]\s+(.+)$")


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _parse_outcome(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    title = ""
    for line in text.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            break
    followups: list[str] = []
    in_follow = False
    for line in text.splitlines():
        if re.match(r"^##\s+Follow", line, re.I):
            in_follow = True
            continue
        if in_follow and line.startswith("## "):
            break
        if in_follow:
            m = FOLLOWUP_RE.match(line.strip())
            if m:
                followups.append(m.group(1).strip())
    return {
        "slug": path.parent.name,
        "title": title,
        "followups": followups[:8],
        "mtime": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def recent_missions(limit: int = 8) -> list[dict[str, Any]]:
    outcomes = sorted(
        MISSIONS.glob("*/outcome.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [_parse_outcome(p) for p in outcomes[:limit]]


def _gh_latest_frontend_deploy() -> dict[str, Any] | None:
    env = os.environ.copy()
    try:
        raw = subprocess.check_output(
            [
                "gh",
                "run",
                "list",
                "--workflow",
                "deploy-frontend.yml",
                "--branch",
                "main",
                "--limit",
                "1",
                "--json",
                "conclusion,startedAt,updatedAt,displayTitle,databaseId,url",
            ],
            cwd=_root,
            env=env,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=20,
        )
    except Exception:
        return None
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not rows:
        return None
    row = rows[0]
    started = row.get("startedAt")
    updated = row.get("updatedAt")
    duration_s = None
    if started and updated:
        try:
            t0 = datetime.fromisoformat(started.replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            duration_s = (t1 - t0).total_seconds()
        except ValueError:
            duration_s = None
    label = classify_frontend_deploy_run(
        conclusion=row.get("conclusion"),
        duration_seconds=duration_s,
    )
    return {
        "conclusion": row.get("conclusion"),
        "duration_s": duration_s,
        "label": label,
        "lie": vercel_production_is_a_lie(label),
        "title": row.get("displayTitle"),
        "url": row.get("url"),
    }


def pick_next_mission(
    *,
    vercel: dict[str, Any] | None,
    followups: list[str],
) -> dict[str, str]:
    if vercel and vercel.get("lie"):
        return {
            "slug": "vercel-production-cli-secrets",
            "why": (
                "Deploy frontend to Vercel skip-greened (missing VERCEL_TOKEN / "
                "VERCEL_ORG_ID / VERCEL_PROJECT_ID). Production HTML did not move. "
                "Do not hunt another Jobs UI leak until --prod is real."
            ),
        }
    if followups:
        return {
            "slug": "jobs-path-followup",
            "why": followups[0][:280],
        }
    return {
        "slug": "jobs-workflow-smoke",
        "why": "No P0 deploy lie and no leftover follow-up — smoke FIND → cards → CRM on production.",
    }


def compile_memory() -> dict[str, Any]:
    missions = recent_missions()
    followups: list[str] = []
    for row in missions:
        followups.extend(row.get("followups") or [])
    snapshot = _read_json(REPORTS / "harness_snapshot_latest.json")
    vercel = _gh_latest_frontend_deploy()
    db = None
    if snapshot:
        db = (snapshot.get("database") or snapshot.get("telemetry") or {}).get("status")
        if db is None:
            db = snapshot.get("database")
    payload = {
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "head": _git(["rev-parse", "--short", "HEAD"]),
        "jobs_loop": {
            "center": "JOBS_WORKFLOW",
            "stages": ["FIND", "JOB_CARDS", "CRM", "WATCH"],
            "charter": "docs/product_integrity_loop.md",
        },
        "deploys": {
            "vercel_frontend_gha": vercel,
            "note": (
                "A GHA success under 30s is not a Vercel production deploy. "
                "Fly production is a separate workflow."
            ),
        },
        "database": {"snapshot_status": db, "snapshot_present": snapshot is not None},
        "recent_missions": missions,
        "open_followups": followups[:12],
        "next_mission": pick_next_mission(vercel=vercel, followups=followups),
        "red_lines": [
            "Hourly observe does not merge PRs",
            "Do not invent jobs or labor dollars",
            "Freeze SIGNAL/Cal as core",
        ],
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    payload = compile_memory()
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.stdout:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Wrote {OUT_PATH}")
        nxt = payload.get("next_mission") or {}
        print(f"next_mission: {nxt.get('slug')} — {nxt.get('why', '')[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
