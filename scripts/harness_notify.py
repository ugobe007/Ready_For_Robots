#!/usr/bin/env python3
"""
Write (and optionally email) a harness mission notification for the operator.

Usage:
  python3 scripts/harness_notify.py --mission missions/2026-06-23-friction-baseline
  python3 scripts/harness_notify.py --mission missions/2026-06-23-friction-baseline --no-email
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from scripts.harness_env import load_harness_env

load_harness_env(_root)

DEFAULT_NOTIFY_EMAIL = "ugobe07@gmail.com"


def _git_lines(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


def _notify_email() -> str:
    explicit = (os.getenv("HARNESS_NOTIFY_EMAIL") or "").strip()
    if explicit:
        return explicit
    admins = (os.getenv("ADMIN_EMAILS") or "").strip()
    if admins:
        return admins.split(",")[0].strip()
    owner = (os.getenv("OWNER_EMAIL") or os.getenv("REPORT_DOWNLOAD_NOTIFY_EMAIL") or "").strip()
    if owner:
        return owner
    return DEFAULT_NOTIFY_EMAIL


def _read_outcome(mission_dir: Path) -> str:
    outcome = mission_dir / "outcome.md"
    if outcome.is_file():
        return outcome.read_text(encoding="utf-8")
    return "(no outcome.md yet)"


def build_notification(mission_dir: Path) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    branch = _git_lines(["rev-parse", "--abbrev-ref", "HEAD"])
    commit = _git_lines(["rev-parse", "--short", "HEAD"])
    log = _git_lines(["log", "-5", "--oneline"])
    diff_stat = _git_lines(["diff", "--stat", "origin/main...HEAD"])
    if not diff_stat:
        diff_stat = _git_lines(["diff", "--stat", "HEAD~3..HEAD"])

    outcome = _read_outcome(mission_dir)
    snapshot_path = _root / "reports" / "harness_snapshot_latest.json"
    snapshot_note = "present" if snapshot_path.is_file() else "missing — run harness_snapshot.py"

    return f"""# Harness notification — {mission_dir.name}

**Time:** {now}
**Mission:** `{mission_dir}`
**Branch:** {branch} @ `{commit}`
**Snapshot:** {snapshot_note}

## Recent commits

```
{log or "(none)"}
```

## Diff stat (vs origin/main or last 3 commits)

```
{diff_stat or "(clean or unpushed)"}
```

## Mission outcome

{outcome}

---
Autonomous harness run. Review when convenient: https://github.com/ugobe007/Ready_For_Robots/commits/main
"""


def _send_email(*, subject: str, body: str) -> dict:
    to = _notify_email()
    api_key = (os.getenv("RESEND_API_KEY") or "").strip()
    if not api_key:
        return {
            "sent": False,
            "to": to,
            "reason": "RESEND_API_KEY not set — add GitHub secret RESEND_API_KEY (same value as Fly)",
        }
    try:
        from app.services.resend_email import ResendEmailError, send_email_via_resend

        result = send_email_via_resend(
            to_email=to,
            subject=subject,
            body_text=body,
            from_display_name="ReadyForRobots Harness",
        )
        return {"sent": True, "to": to, "id": result.get("id")}
    except ResendEmailError as exc:
        return {"sent": False, "to": to, "reason": str(exc)}
    except Exception as exc:
        return {"sent": False, "to": to, "reason": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Notify operator of harness mission completion")
    parser.add_argument("--mission", help="Mission folder path")
    parser.add_argument("--no-email", action="store_true", help="Write report file only")
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Send a short test message (no mission folder required)",
    )
    args = parser.parse_args()

    if args.test_email:
        body = (
            f"ReadyForRobots harness email test\n\n"
            f"Time: {datetime.now(timezone.utc).isoformat()}\n"
            f"Recipient: {_notify_email()}\n"
        )
        result = _send_email(subject="[RFR Harness] Email test", body=body)
        print("Email:", result)
        return 0 if result.get("sent") else 1

    if not args.mission:
        parser.error("--mission is required unless --test-email is set")

    mission_dir = Path(args.mission)
    if not mission_dir.is_absolute():
        mission_dir = _root / mission_dir

    body = build_notification(mission_dir)
    reports = _root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    out_path = reports / "harness_notification_latest.md"
    out_path.write_text(body, encoding="utf-8")
    print(f"Wrote {out_path}")

    if args.no_email:
        return 0

    subject = f"[RFR Harness] {mission_dir.name} complete"
    email_result = _send_email(subject=subject, body=body)
    print("Email:", email_result)
    if not email_result.get("sent"):
        print(
            "WARNING: Daily harness email not delivered — check RESEND_API_KEY on GitHub Actions.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
