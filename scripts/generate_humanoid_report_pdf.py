#!/usr/bin/env python3
"""Generate the Humanoid Intelligence Report PDF locally (Manus / WeasyPrint pipeline).

Usage:
  PYTHONPATH=. python3 scripts/generate_humanoid_report_pdf.py -o reports/heir_report.pdf
  PYTHONPATH=. python3 scripts/generate_humanoid_report_pdf.py --html-only -o /tmp/report.html
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_scored_robots():
    try:
        from app.api.humanoid_benchmark import _fetch_scored_humanoids
        from app.db.session import SessionLocal
        from app.services.humanoid_catalog_cleanup import is_junk_humanoid_row

        db = SessionLocal()
        try:
            robots = _fetch_scored_humanoids(db)
            return [
                r for r in robots
                if not is_junk_humanoid_row(r["name"], r["vendor"], r["model_slug"])
            ]
        finally:
            db.close()
    except Exception:
        from app.services.humanoid_intelligence_report import build_humanoid_intelligence_report_payload
        from app.services.humanoid_scraper import SEED_ROBOTS, compute_scores

        out = []
        for robot in SEED_ROBOTS[:20]:
            scores = compute_scores(robot["specs"], status=robot["status"], vendor=robot["vendor"])
            out.append({**robot, **scores})
        return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HEIR intelligence report PDF from live DB or fixtures.")
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "reports" / "humanoid_intelligence_report.pdf")
    parser.add_argument("--top-n", type=int, default=12)
    parser.add_argument("--html-only", action="store_true", help="Write HTML only (no WeasyPrint)")
    args = parser.parse_args()

    from app.services.humanoid_intelligence_report import build_humanoid_intelligence_report_payload
    from app.services.humanoid_intelligence_report_render import (
        build_humanoid_intelligence_report_pdf_weasyprint,
        render_report_html,
    )

    rows = _load_scored_robots()
    if not rows:
        print("No robots in index — seed or connect DATABASE_URL.", file=sys.stderr)

    payload = build_humanoid_intelligence_report_payload(rows, top_n=args.top_n)
    if not payload.get("report"):
        print("No robots in index — nothing to render.", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.html_only:
        html = render_report_html(payload)
        out = args.output if args.output.suffix == ".html" else args.output.with_suffix(".html")
        out.write_text(html, encoding="utf-8")
        print(f"Wrote {out}")
        return 0

    pdf_bytes, filename = build_humanoid_intelligence_report_pdf_weasyprint(payload)
    out = args.output if args.output.suffix == ".pdf" else args.output / filename
    out.write_bytes(pdf_bytes)
    print(f"Wrote {out} ({len(pdf_bytes)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
