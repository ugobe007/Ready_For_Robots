"""Print a special project's target accounts as CSV to stdout.

    fly ssh console -a ready-2-robot -C "python3 scripts/export_special_project_csv.py" > leads.csv

Env:
    SPECIAL_PROJECT_SLUG  default nimo-technology
    ONLY_CONTACTED        "1" to include only targets Cal has contacted (default all)
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.special_project import SpecialProject  # noqa: E402

SLUG = os.getenv("SPECIAL_PROJECT_SLUG", "nimo-technology")
ONLY_CONTACTED = (os.getenv("ONLY_CONTACTED") or "").strip() in ("1", "true", "yes")

FIELDS = [
    "company",
    "segment",
    "best_fit_task",
    "fit",
    "contact_name",
    "contact_title",
    "contact_email",
    "email_status",
    "stage",
    "date_contacted",
    "outreach_sequence",
    "why_now_signal",
    "website",
    "outreach_subject",
]


def main() -> None:
    db = SessionLocal()
    try:
        p = db.query(SpecialProject).filter(SpecialProject.slug == SLUG).first()
        if p is None:
            raise SystemExit(f"project not found: {SLUG}")
        rows = sorted(p.targets, key=lambda t: t.sort_order)
        if ONLY_CONTACTED:
            rows = [t for t in rows if t.sent_at is not None]

        writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS)
        writer.writeheader()
        for t in rows:
            writer.writerow(
                {
                    "company": t.company or "",
                    "segment": t.segment or "",
                    "best_fit_task": t.best_fit_task or "",
                    "fit": {"H": "Hot", "W": "Warm", "C": "Cold"}.get(t.fit or "", t.fit or ""),
                    "contact_name": t.contact_name or "",
                    "contact_title": t.contact_title or "",
                    "contact_email": t.contact_email or "",
                    "email_status": t.contact_status or "",
                    "stage": t.stage or "",
                    "date_contacted": t.sent_at.strftime("%Y-%m-%d") if t.sent_at else "",
                    "outreach_sequence": t.sequence or "",
                    "why_now_signal": t.signal or "",
                    "website": t.website or "",
                    "outreach_subject": (t.draft_subject or "").strip(),
                }
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
