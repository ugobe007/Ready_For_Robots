#!/usr/bin/env python3
"""
Run the full Ready For Robots harness loop once (snapshot → agent mission → notify).

Designed for daily automation via GitHub Actions or local launchd/cron.

Usage:
  python3 scripts/harness_daily.py
  python3 scripts/harness_daily.py --dry-run
  python3 scripts/harness_daily.py --skip-agent
  python3 scripts/harness_daily.py --mission missions/2026-06-16-daily-cycle
  python3 scripts/harness_daily.py --force   # re-run even if today's outcome exists

Prerequisites:
  pip install -r requirements-harness.txt
  pip install -r harness/requirements.txt
  pip install -r requirements.txt
  export ANTHROPIC_API_KEY=...   # unless --skip-agent
  DATABASE_URL or HARNESS_DATABASE_URL in .env for DB telemetry
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from scripts.harness_env import load_harness_env

load_harness_env(_root)

_TEMPLATE = _root / "missions" / "_template" / "daily-cycle-brief.md"


def _run(cmd: list[str], *, dry_run: bool = False) -> int:
    printable = " ".join(cmd)
    print(f"\n→ {printable}", flush=True)
    if dry_run:
        return 0
    return subprocess.call(cmd, cwd=_root)


def _today_slug() -> str:
    return f"{date.today().isoformat()}-daily-cycle"


def _ensure_mission(*, mission_dir: Path, dry_run: bool) -> None:
    brief = mission_dir / "brief.md"
    if brief.is_file():
        return
    if not _TEMPLATE.is_file():
        raise FileNotFoundError(f"Missing mission template: {_TEMPLATE}")
    body = _TEMPLATE.read_text(encoding="utf-8").format(
        date=date.today().isoformat(),
        mission_slug=mission_dir.name,
    )
    if dry_run:
        print(f"Would create {brief}")
        return
    mission_dir.mkdir(parents=True, exist_ok=True)
    brief.write_text(body, encoding="utf-8")
    print(f"Created {brief}")


def _pipeline_needs_refresh(api_base: str) -> bool:
    try:
        import httpx

        url = f"{api_base.rstrip('/')}/api/leads/pipeline"
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers={"Accept": "application/json"})
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        print(f"Could not check pipeline cache: {exc}", flush=True)
        return False

    if payload.get("cache_pending") is True:
        return True
    if not payload.get("built_at"):
        return True

    try:
        built = datetime.fromisoformat(str(payload["built_at"]).replace("Z", "+00:00"))
        age_hours = (datetime.now(timezone.utc) - built.astimezone(timezone.utc)).total_seconds() / 3600
        if age_hours > 26:
            print(f"Pipeline cache stale ({age_hours:.1f}h old)", flush=True)
            return True
    except (TypeError, ValueError):
        return True

    leads = payload.get("leads") or []
    if not leads:
        print("Pipeline feed empty", flush=True)
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one daily harness loop cycle")
    parser.add_argument(
        "--mission",
        help="Mission folder (default: missions/YYYY-MM-DD-daily-cycle)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print steps without executing")
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="Snapshot + optional cache refresh + notify only (no ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--skip-cache-refresh",
        action="store_true",
        help="Do not trigger remote pipeline cache rebuild",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even if today's outcome.md already exists",
    )
    parser.add_argument(
        "--api-base",
        default=__import__("os").getenv("API_BASE", "https://ready-2-robot.fly.dev"),
    )
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument("--max-budget-usd", type=float, default=5.0)
    args = parser.parse_args()

    mission_dir = Path(args.mission) if args.mission else _root / "missions" / _today_slug()
    if not mission_dir.is_absolute():
        mission_dir = _root / mission_dir

    outcome = mission_dir / "outcome.md"
    if outcome.is_file() and not args.force:
        print(f"Already completed today: {outcome}")
        print("Use --force to re-run or pass --mission for a different slug.")
        return 0

    _ensure_mission(mission_dir=mission_dir, dry_run=args.dry_run)

    py = sys.executable
    rc = _run([py, "scripts/harness_snapshot.py", "--api-base", args.api_base], dry_run=args.dry_run)
    if rc != 0:
        return rc

    if not args.skip_cache_refresh and _pipeline_needs_refresh(args.api_base):
        refresh_cmd = [
            py,
            "scripts/refresh_pipeline_cache.py",
            "--remote",
            "--wait",
            "--api-base",
            args.api_base,
        ]
        rc = _run(refresh_cmd, dry_run=args.dry_run)
        if rc != 0 and not args.dry_run:
            print("Cache refresh failed — continuing mission anyway.", flush=True)
        elif not args.dry_run:
            _run([py, "scripts/harness_snapshot.py", "--api-base", args.api_base])

    if not args.skip_agent:
        rc = _run(
            [
                py,
                "scripts/run_mission.py",
                "--mission",
                str(mission_dir.relative_to(_root)),
                "--max-turns",
                str(args.max_turns),
                "--max-budget-usd",
                str(args.max_budget_usd),
            ],
            dry_run=args.dry_run,
        )
        if rc != 0:
            return rc
    elif not outcome.is_file() and not args.dry_run:
        stub = mission_dir / "outcome.md"
        stub.write_text(
            f"# Outcome: {mission_dir.name}\n\n"
            f"**Result:** partial\n"
            f"**Note:** `--skip-agent` run at {datetime.now(timezone.utc).isoformat()} — snapshot only.\n",
            encoding="utf-8",
        )

    return _run(
        [
            py,
            "scripts/harness_notify.py",
            "--mission",
            str(mission_dir.relative_to(_root)),
        ],
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
