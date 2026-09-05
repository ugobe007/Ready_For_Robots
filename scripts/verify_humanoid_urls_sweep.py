"""
Verification sweep for humanoid_benchmarks rows with no verification_status.

For each UNSET row we resolve its product_url and assign a status based on
evidence we can confirm automatically:

  VERIFIED            product_url resolves (HTTP 200, real page) AND the page
                      mentions the robot or vendor name (not a wrong/parked page)
  PARTIAL             product_url resolves but the page is JS-only/thin or the
                      name token can't be confirmed in static HTML (common for
                      SPA vendor sites) — link is live but unconfirmed
  NEEDS_VERIFICATION  no product_url, or the URL is dead (non-200 / network error)

Human-curated VERIFIED/PARTIAL/NEEDS_VERIFICATION rows are left untouched.

Usage (on the app box, has DATABASE_URL):
    python scripts/verify_humanoid_urls_sweep.py            # apply
    python scripts/verify_humanoid_urls_sweep.py --dry-run  # report only
"""
from __future__ import annotations

import re
import sys

import requests
from sqlalchemy import text

from app.database import SessionLocal

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

STOP = {
    "humanoid", "humanoids", "robot", "robots", "robotics", "robotic", "inc",
    "co", "ltd", "llc", "corp", "corporation", "company", "the", "ai", "lab",
    "labs", "research", "technologies", "technology", "tech", "intelligence",
    "automation", "global", "international", "group", "and", "gen", "platform",
    "next", "pro", "series",
}


def tokens(*parts: str) -> list[str]:
    out: list[str] = []
    for p in parts:
        for w in re.findall(r"[a-z0-9]+", (p or "").lower()):
            if len(w) >= 3 and w not in STOP and w not in out:
                out.append(w)
    return out


def fetch_text(url: str) -> tuple[int, str]:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15,
                         allow_redirects=True)
        html = re.sub(r"(?is)<(script|style|noscript|svg|head).*?</\1>", " ", r.text)
        txt = re.sub(r"(?s)<[^>]+>", " ", html)
        txt = re.sub(r"\s+", " ", txt)
        return r.status_code, txt
    except Exception as exc:  # noqa: BLE001
        return 0, f"ERR {type(exc).__name__}"


def classify(name: str, vendor: str, url: str | None) -> tuple[str, str]:
    if not (url or "").strip():
        return "NEEDS_VERIFICATION", "no product_url"
    code, txt = fetch_text(url)
    if code != 200:
        detail = txt if txt.startswith("ERR") else f"http {code}"
        return "NEEDS_VERIFICATION", f"dead link ({detail})"
    if len(txt) <= 300:
        return "PARTIAL", f"resolves; thin/JS page ({len(txt)} chars)"
    low = txt.lower()
    hits = [t for t in tokens(name, vendor) if t in low]
    if hits:
        return "VERIFIED", f"resolves; matched {','.join(hits[:4])}"
    return "PARTIAL", "resolves; name not in static HTML"


def main() -> None:
    dry = "--dry-run" in sys.argv
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT model_slug, name, vendor, product_url
            FROM humanoid_benchmarks
            WHERE verification_status IS NULL
               OR verification_status = ''
               OR upper(verification_status) = 'UNSET'
            ORDER BY model_slug
        """)).mappings().all()
        print(f"{'DRY-RUN ' if dry else ''}sweeping {len(rows)} UNSET rows\n")
        counts: dict[str, int] = {}
        for r in rows:
            status, why = classify(r["name"], r["vendor"], r["product_url"])
            counts[status] = counts.get(status, 0) + 1
            print(f"  [{status:18s}] {r['model_slug']:30s} {why}")
            if not dry:
                db.execute(text("""
                    UPDATE humanoid_benchmarks
                    SET verification_status = :s
                    WHERE model_slug = :slug
                """), {"s": status, "slug": r["model_slug"]})
        if not dry:
            db.commit()
        print("\nsummary:", counts)
        print("SWEEP_DONE")
    finally:
        db.close()


if __name__ == "__main__":
    main()
