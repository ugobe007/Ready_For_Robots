"""Seed (or refresh) the NIMO Technology special project + initial workflow updates.

Idempotent by slug. Run locally with DATABASE_URL set, or on Fly:

    fly ssh console -a ready-2-robot -C "python3 scripts/seed_special_project_nimo.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.special_project import SpecialProject, SpecialProjectUpdate  # noqa: E402
from app.services.special_projects import unique_slug  # noqa: E402

SLUG = "nimo-technology"

CONFIG = {
    "motion": "No-cost validation pilot (classic PoC) — qualify on fit + willingness, not budget.",
    "icp_hot": ["Ghost / cloud kitchens", "QSR innovation labs"],
    "best_fit_tasks": ["Fry-station tending", "Wok / grill hand", "Prep + plating", "Dishroom loading"],
    "personas": ["Ghost-kitchen founder / Head of Ops", "VP Innovation / Culinary R&D", "COO / VP Operations"],
    "qualification": "BETA-READY rubric ≥ 7/10 (task match, environment, champion & speed, commitment, pain & volume)",
}

METRICS = {
    "target_accounts": 50,
    "contacted": 0,
    "replies": 0,
    "discovery_calls": 0,
    "beta_sites": 0,
}

PIPELINE = {
    "targeted": 50,
    "contacted": 0,
    "replied": 0,
    "discovery": 0,
    "demo": 0,
    "pilot_signed": 0,
    "validated": 0,
}

UPDATES = [
    {
        "category": "milestone",
        "title": "Beta GTM playbook built",
        "body": "Strategy, ~50 ranked beta-host targets, and 3-touch Cal outreach sequences ready. "
        "Motion: no-cost validation pilot with reference rights.",
    },
    {
        "category": "note",
        "title": "Target list seeded (50 accounts)",
        "body": "Ghost/cloud kitchens and QSR innovation labs prioritized as HOT beta hosts.",
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        project = db.query(SpecialProject).filter(SpecialProject.slug == SLUG).first()
        if project is None:
            project = SpecialProject(slug=unique_slug(db, "NIMO Technology"))
            db.add(project)
        project.name = "NIMO Technology"
        project.company_website = "https://nimotechs.com"
        project.robot_description = (
            "Tactile-first kitchen humanoid — dexterous manipulation for high-heat, high-touch cooking tasks."
        )
        project.summary = (
            "Ready For Robots is running Cal, an autonomous sales pipeline, to find early beta hosts willing to "
            "run a no-cost validation pilot of NIMO's tactile kitchen humanoid."
        )
        project.status = "outreach"
        project.config = CONFIG
        project.metrics = METRICS
        project.pipeline = PIPELINE
        db.flush()

        if not project.updates:
            for u in UPDATES:
                db.add(SpecialProjectUpdate(project_id=project.id, **u))

        db.commit()
        db.refresh(project)
        print(f"NIMO project ready: id={project.id} slug={project.slug}")
        print(f"Client portal path: /p/{project.share_token}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
