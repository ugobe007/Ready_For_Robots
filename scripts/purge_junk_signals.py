"""
purge_junk_signals.py
=====================
One-shot cleanup script: deletes Signal rows whose signal_text matches
listicle / advice-article patterns that are not real company-event news.

Example junk caught:
  "15 strategies to combat restaurants"
  "Top 10 ways to reduce hotel labor costs"
  "How to fight staffing shortages"

Run from the repo root:
    python scripts/purge_junk_signals.py [--dry-run]

Flags:
    --dry-run   Print what would be deleted, but don't commit changes.
    --confirm   Actually delete (required unless --dry-run is passed).
"""

import argparse
import re
import sys
import os

# Make sure the app module is importable from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.signal import Signal

# ── Same patterns as lead_filter.py ──────────────────────────────────────────
_JUNK_SIGNAL_PATTERNS = [
    r"^\d+\s+(?:ways?|strategies?|tips?|tricks?|ideas?|steps?|reasons?|mistakes?|secrets?|things?|questions?|examples?|factors?|hacks?|methods?|tactics?)\s+(?:to|for|that|you|on|about|every|when)",
    r"^top\s+\d+",
    r"^\d+\s+(?:best|great|key|simple|easy|proven|powerful|effective)",
    r"^how\s+to\b",
    r"^why\s+(?:you|your|every|hotels?|restaurants?|companies)",
    r"^what\s+(?:is|are|hotel|restaurant)\b",
    r"^the\s+(?:ultimate|complete|definitive|best|top)\s+guide",
    r"^(?:a\s+)?guide\s+to\b",
    r"combat\s+(?:restaurant|labor|wage|cost|inflation)",
    r"^(?:everything|all)\s+you\s+(?:need|should|must|want)",
]
_JUNK_RE = [re.compile(p, re.IGNORECASE) for p in _JUNK_SIGNAL_PATTERNS]


def is_junk(text: str) -> bool:
    head = (text or "").strip()[:200]
    return any(rx.search(head) for rx in _JUNK_RE)


def main():
    parser = argparse.ArgumentParser(description="Purge junk signals from the database.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true",
                       help="Print matches without deleting.")
    group.add_argument("--confirm", action="store_true",
                       help="Actually delete matched signals.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        signals = db.query(Signal).all()
        junk_signals = [s for s in signals if is_junk(s.signal_text)]

        print(f"\nTotal signals in DB : {len(signals)}")
        print(f"Junk signals found  : {len(junk_signals)}\n")

        if not junk_signals:
            print("Nothing to purge. ✓")
            return

        for s in junk_signals:
            preview = s.signal_text[:120].replace("\n", " ")
            print(f"  [id={s.id}] company_id={s.company_id}  type={s.signal_type}")
            print(f"    TEXT: {preview}")

        if args.dry_run:
            print(f"\n[DRY RUN] {len(junk_signals)} signals would be deleted. Re-run with --confirm to apply.")
        else:
            ids = [s.id for s in junk_signals]
            db.query(Signal).filter(Signal.id.in_(ids)).delete(synchronize_session=False)
            db.commit()
            print(f"\n✓ Deleted {len(junk_signals)} junk signals.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
