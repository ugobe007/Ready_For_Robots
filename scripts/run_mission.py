#!/usr/bin/env python3
"""
Run a single RFR harness mission via Claude Agent SDK.

Prerequisites:
  pip install -r requirements-harness.txt
  export ANTHROPIC_API_KEY=...

Usage:
  python3 scripts/harness_snapshot.py
  python3 scripts/run_mission.py --mission missions/2026-06-23-friction-baseline

Dry-run (print prompt only):
  python3 scripts/run_mission.py --mission missions/2026-06-23-friction-baseline --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))


def _load_mission_brief(mission_dir: Path) -> str:
    brief = mission_dir / "brief.md"
    if not brief.is_file():
        raise FileNotFoundError(f"Missing {brief}")
    return brief.read_text(encoding="utf-8")


def _latest_snapshot_text() -> str:
    latest = _root / "reports" / "harness_snapshot_latest.json"
    if not latest.is_file():
        return "(no harness snapshot — run scripts/harness_snapshot.py first)"
    return latest.read_text(encoding="utf-8")


def _market_thesis_text() -> str:
    thesis = _root / "docs" / "market_thesis.md"
    if not thesis.is_file():
        return "(no market thesis — see docs/market_thesis.md)"
    return thesis.read_text(encoding="utf-8")


def _build_prompt(mission_dir: Path) -> str:
    brief = _load_mission_brief(mission_dir)
    snapshot = _latest_snapshot_text()
    thesis = _market_thesis_text()
    return f"""You are the Ready For Robots Orchestrator. Follow AGENTS.md and CLAUDE.md.

## Mission brief

{brief}

## Market thesis (read before orienting)

{thesis}

## Latest harness snapshot

```json
{snapshot}
```

## Instructions

1. Run `python3 scripts/harness_snapshot.py` if snapshot is missing or stale (>6h pipeline cache).
2. Orient against north star (names/events first) and `docs/market_thesis.md` backlog.
3. Execute this mission using the assigned subagent role from the brief.
4. Run verification gates from `harness/gates.yaml` where applicable.
5. **Autonomous mode:** commit, push, and deploy when the mission requires it — do not wait for human approval.
6. Write `missions/{mission_dir.name}/outcome.md` with metrics delta and follow-ups.
7. Run `python3 scripts/harness_notify.py --mission missions/{mission_dir.name}` when finished.

Red lines: no force push, no committing `reports/`, no parallel local+Fly cache refresh, no `.env` commits.

Begin.
"""


async def _run_agent(prompt: str, *, max_turns: int, max_budget_usd: float) -> int:
    try:
        from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
    except ImportError:
        print(
            "claude-agent-sdk not installed. Run: pip install -r requirements-harness.txt",
            file=sys.stderr,
        )
        return 1

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Write", "Glob", "Grep", "Bash"],
        setting_sources=["project"],
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        cwd=str(_root),
    )

    exit_code = 0
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            if message.subtype == "success":
                print("\n--- Mission result ---\n")
                print(message.result or "")
            else:
                print(f"\nMission stopped: {message.subtype}", file=sys.stderr)
                exit_code = 1
            cost = getattr(message, "total_cost_usd", None)
            if cost is not None:
                print(f"Cost: ${cost:.4f}")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an RFR harness mission")
    parser.add_argument(
        "--mission",
        required=True,
        help="Path to mission folder containing brief.md",
    )
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument("--max-budget-usd", type=float, default=5.0)
    parser.add_argument("--dry-run", action="store_true", help="Print prompt only")
    args = parser.parse_args()

    mission_dir = Path(args.mission)
    if not mission_dir.is_absolute():
        mission_dir = _root / mission_dir

    if not (os.getenv("ANTHROPIC_API_KEY") or "").strip() and not args.dry_run:
        print("ANTHROPIC_API_KEY is not set.", file=sys.stderr)
        return 1

    prompt = _build_prompt(mission_dir)
    if args.dry_run:
        print(prompt)
        return 0

    return asyncio.run(
        _run_agent(prompt, max_turns=args.max_turns, max_budget_usd=args.max_budget_usd)
    )


if __name__ == "__main__":
    raise SystemExit(main())
