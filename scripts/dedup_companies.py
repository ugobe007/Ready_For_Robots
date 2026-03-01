"""
dedup_companies.py
==================
One-time cleanup script:
  1. Removes duplicate Company rows (keeps lowest id per name).
  2. Re-points Signals from deleted duplicates to the canonical row.
  3. Purges companies with industry='Unknown' that were ingested by
     the regex fallback (robot/AI vendors) — run this AFTER deploying
     the fixed news_scraper.py so no new ones come in.
  4. Adds a unique index on companies.name (idempotent).

Run locally:
    $env:DATABASE_URL="postgresql+psycopg2://..."
    python scripts/dedup_companies.py

Run on Fly.io:
    flyctl ssh console -a ready-2-robot
    python scripts/dedup_companies.py
"""
import os
import sys

# Accept a raw postgres:// URL from env
_url = os.getenv("DATABASE_URL", "")
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql+psycopg2://", 1)
elif _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+psycopg2://", 1)

if not _url:
    print("ERROR: DATABASE_URL env var not set.", file=sys.stderr)
    sys.exit(1)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(_url, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
db = Session()

print("=== Step 1: Deduplicate companies (keep lowest id) ===")
# Find all names with >1 row
dup_query = text("""
    SELECT name, COUNT(*) AS cnt, MIN(id) AS keep_id
    FROM companies
    GROUP BY name
    HAVING COUNT(*) > 1
""")
dups = db.execute(dup_query).fetchall()
print(f"  Found {len(dups)} duplicate company names")

for row in dups:
    name, cnt, keep_id = row.name, row.cnt, row.keep_id
    # Get ids to delete
    all_ids = db.execute(
        text("SELECT id FROM companies WHERE name = :name"),
        {"name": name}
    ).fetchall()
    delete_ids = [r.id for r in all_ids if r.id != keep_id]

    # Re-point signals from duplicates to canonical id
    updated = db.execute(
        text("UPDATE signals SET company_id = :keep_id WHERE company_id = ANY(:del_ids)"),
        {"keep_id": keep_id, "del_ids": delete_ids}
    ).rowcount
    print(f"  [{name}] keeping id={keep_id}, deleting {delete_ids}, re-pointed {updated} signals")

    # Delete duplicate companies (cascade will also delete their (now-empty) scores/contacts)
    db.execute(
        text("DELETE FROM companies WHERE id = ANY(:del_ids)"),
        {"del_ids": delete_ids}
    )

db.commit()
print("  Dedup complete.\n")

print("=== Step 2: Remove Unknown-industry vendor companies ===")
# Only purge companies sourced from news_scraper + Unknown industry
# Keep any company that has a non-news source (manual seeds etc.)
unknown_count = db.execute(
    text("""
        SELECT COUNT(*) FROM companies
        WHERE industry = 'Unknown' AND source = 'news_scraper'
    """)
).scalar()
print(f"  Found {unknown_count} Unknown-industry / news_scraper companies")

if unknown_count > 0:
    confirm = input(f"  Delete these {unknown_count} rows? (y/N): ").strip().lower()
    if confirm == "y":
        # Signals cascade-delete via FK; if no cascade, delete explicitly
        db.execute(
            text("""
                DELETE FROM signals
                WHERE company_id IN (
                    SELECT id FROM companies
                    WHERE industry = 'Unknown' AND source = 'news_scraper'
                )
            """)
        )
        deleted = db.execute(
            text("""
                DELETE FROM companies
                WHERE industry = 'Unknown' AND source = 'news_scraper'
            """)
        ).rowcount
        db.commit()
        print(f"  Deleted {deleted} Unknown-industry companies and their signals.")
    else:
        print("  Skipped.")
else:
    print("  None to delete.")

print("\n=== Step 3: Add unique index on companies.name (idempotent) ===")
try:
    db.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_companies_name
        ON companies (name)
    """))
    db.commit()
    print("  Unique index created (or already existed).")
except Exception as e:
    db.rollback()
    print(f"  Could not add unique index: {e}")
    print("  You may need to run dedup again first if there are still duplicates.")

print("\n=== Done ===")
db.close()
