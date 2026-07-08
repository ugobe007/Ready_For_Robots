"""Bulk-send approved special-project outreach drafts (review-first, opt-in).

Mirrors the /targets/{id}/send endpoint but for a batch. Review-first contract:
a target is only eligible once a human has APPROVED it (t.approved == "yes"),
it has an email, a draft, and hasn't been sent. This script never approves on
your behalf — approval is a human action in /admin/special-projects. Scope
further narrows approved targets to verified-only vs all.

Env:
    SPECIAL_PROJECT_SLUG  default nimo-technology
    SEND_SCOPE            verified | all            (default verified)
    SEND_LIMIT            max sends this run         (default 0 = no limit)
    REPLY_TO             reply-to address           (e.g. yimengq@nimotechs.com)
    FROM_NAME            sender display name         (default "Cal · Ready For Robots")
    DRY_RUN              "1" to preview without sending

    fly ssh console -a ready-2-robot -C \
      "REPLY_TO=yimengq@nimotechs.com SEND_SCOPE=verified python3 scripts/send_special_project.py"
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.special_project import SpecialProject, SpecialProjectUpdate  # noqa: E402
from app.services.special_projects import recompute_project_rollup  # noqa: E402

SLUG = os.getenv("SPECIAL_PROJECT_SLUG", "nimo-technology")
SCOPE = (os.getenv("SEND_SCOPE") or "verified").strip().lower()
LIMIT = int(os.getenv("SEND_LIMIT") or "0")
REPLY_TO = (os.getenv("REPLY_TO") or "").strip() or None
FROM_NAME = (os.getenv("FROM_NAME") or "Cal · Ready For Robots").strip()
DRY_RUN = (os.getenv("DRY_RUN") or "").strip() in ("1", "true", "yes")


def _eligible(t, scope: str = SCOPE) -> bool:
    # Review-first: a human must have approved this target. The bulk sender
    # NEVER approves on the operator's behalf — that gate lives in the admin UI.
    if (t.approved or "").strip().lower() != "yes":
        return False
    if t.sent_at is not None:
        return False
    if not (t.contact_email or "").strip():
        return False
    if not (t.draft_subject or "").strip() or not (t.draft_body or "").strip():
        return False
    if scope == "verified" and t.contact_status != "verified":
        return False
    return True


def main() -> None:
    db = SessionLocal()
    try:
        p = db.query(SpecialProject).filter(SpecialProject.slug == SLUG).first()
        if p is None:
            raise SystemExit(f"project not found: {SLUG}")

        from app.services.cal_email_send import send_cal_email_via_resend

        candidates = [t for t in p.targets if _eligible(t)]
        candidates.sort(key=lambda t: t.sort_order)
        print(f"scope={SCOPE} candidates={len(candidates)} dry_run={DRY_RUN} reply_to={REPLY_TO} from={FROM_NAME}")

        sent = failed = 0
        for t in candidates:
            if LIMIT and sent >= LIMIT:
                break
            if DRY_RUN:
                print(f"  would send → {t.company} <{t.contact_email}> [{t.contact_status}]")
                continue
            try:
                send_cal_email_via_resend(
                    to_email=t.contact_email.strip(),
                    subject=t.draft_subject.strip(),
                    body_text=t.draft_body.strip(),
                    from_display_name=FROM_NAME,
                    reply_to=REPLY_TO,
                    idempotency_key=f"special-project/{p.id}/target/{t.id}",
                    include_demo=False,
                )
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"  FAILED → {t.company}: {exc}")
                continue
            now = datetime.now(timezone.utc)
            t.sent_at = now
            t.last_activity_at = now
            if t.stage == "targeted":
                t.stage = "contacted"
            db.add(
                SpecialProjectUpdate(
                    project_id=p.id,
                    title=f"Cal contacted {t.company}",
                    body=f"Sent outreach to {t.contact_email} — subject: “{t.draft_subject.strip()}”.",
                    category="outreach",
                )
            )
            sent += 1
            print(f"  sent → {t.company} <{t.contact_email}>")

        if not DRY_RUN:
            recompute_project_rollup(p)
            db.commit()
        print(f"done: sent={sent} failed={failed}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
