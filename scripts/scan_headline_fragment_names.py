#!/usr/bin/env python3
"""
Scan companies.name for headline / editorial artefacts (DB audit).

Catches rhetorical questions, ellipsis truncation, 'Inside X Y' decks, and
Nordic + sport + generic sector stubs — same heuristics as lead_filter + gate
helpers, so you can find rows to purge or review before/after a scraper run.

  python3 scripts/scan_headline_fragment_names.py
  python3 scripts/scan_headline_fragment_names.py --limit 3000
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from app.env_loader import database_url_is_template_or_sqlite

_shell_database_url = (os.environ.get("DATABASE_URL") or "").strip()
_root = Path(__file__).resolve().parents[1]
load_dotenv(_root / "frontend" / "nextjs" / ".env.local")
load_dotenv(_root / ".env", override=True)
_loaded_after_dotenv = (os.environ.get("DATABASE_URL") or "").strip()
if _shell_database_url and database_url_is_template_or_sqlite(_loaded_after_dotenv):
    os.environ["DATABASE_URL"] = _shell_database_url

from app.database import SessionLocal
from app.models.company import Company
from app.services.lead_filter import is_junk

_NORDIC_SPORT_STUB_FULL = re.compile(
    r"(?i)(swedish|norwegian|danish|finnish|icelandic|estonian|latvian|lithuanian)\s+"
    r"(sport|sports)\s+(airline|airlines|carrier|retailer|retailers|chain|chains|"
    r"brand|brands|group)\s*[\s.?!…]*",
)

_ANOMALY_RES = [
    re.compile(r"\?\s*$"),
    re.compile(r"\.{3,}"),
    re.compile(r"(?i)^inside\s+[A-Z]\w+\s+[A-Z]"),
]


def _anomaly_tags(name: str) -> list[str]:
    tags: list[str] = []
    for rx in _ANOMALY_RES:
        if rx.search(name):
            tags.append(rx.pattern[:48] + ("…" if len(rx.pattern) > 48 else ""))
    if _NORDIC_SPORT_STUB_FULL.fullmatch(name.strip()):
        tags.append("nordic+sport+role (full-string headline stub)")
    return tags


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5000, help="Max companies to scan (recent id desc)")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        rows = (
            db.query(Company.id, Company.name)
            .order_by(Company.id.desc())
            .limit(args.limit)
            .all()
        )
        hits = []
        for cid, name in rows:
            if not name:
                continue
            tags = _anomaly_tags(name)
            junk, jreason = is_junk(name)
            if tags or junk:
                hits.append((cid, name, tags, junk, jreason))
        print(f"Scanned {len(rows)} companies (limit={args.limit})")
        print(f"Rows with anomaly pattern and/or is_junk: {len(hits)}\n")
        for cid, name, tags, junk, jreason in hits[:200]:
            t = "; ".join(tags) if tags else "—"
            j = f"is_junk={junk} [{jreason[:60]}]" if junk else "is_junk=False"
            print(f"id={cid}  {j}")
            print(f"         tags: {t}")
            print(f"         {name!r}\n")
        if len(hits) > 200:
            print(f"… {len(hits) - 200} more (raise output limit in script)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
