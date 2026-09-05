"""Resolve contact emails for a special project's targets (Hunter, best-effort).

Fills contact_email / contact_name / contact_title / contact_status for every
target that doesn't already have an email. Fails soft when Hunter is disabled.

    fly ssh console -a ready-2-robot -C "python3 scripts/enrich_special_project.py"
    SPECIAL_PROJECT_SLUG=nimo-technology python3 scripts/enrich_special_project.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.special_project import SpecialProject  # noqa: E402
from app.services.special_projects import enrich_target_email  # noqa: E402

SLUG = os.getenv("SPECIAL_PROJECT_SLUG", "nimo-technology")


def main() -> None:
    db = SessionLocal()
    try:
        p = db.query(SpecialProject).filter(SpecialProject.slug == SLUG).first()
        if p is None:
            raise SystemExit(f"project not found: {SLUG}")
        attempted = enriched = 0
        for t in p.targets:
            if (t.contact_email or "").strip():
                continue
            attempted += 1
            if enrich_target_email(t):
                enriched += 1
        db.commit()
        verified = sum(1 for t in p.targets if t.contact_status == "verified")
        guessed = sum(1 for t in p.targets if t.contact_status == "guessed")
        with_email = sum(1 for t in p.targets if (t.contact_email or "").strip())
        print(
            f"attempted={attempted} enriched={enriched} verified={verified} "
            f"guessed={guessed} with_email={with_email} total={len(p.targets)}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
