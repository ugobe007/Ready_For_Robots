#!/usr/bin/env python3
"""Standalone chart generator (Manus generate_charts.py) using live API payload.

  PYTHONPATH=. python3 scripts/generate_humanoid_report_charts.py -d ./reports/charts
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--out-dir", type=Path, default=ROOT / "reports" / "charts")
    parser.add_argument("--top-n", type=int, default=12)
    args = parser.parse_args()

    from app.services.humanoid_intelligence_report import build_humanoid_intelligence_report_payload
    from app.services.humanoid_report_charts import generate_report_charts

    from generate_humanoid_report_pdf import _load_scored_robots

    rows = _load_scored_robots()

    payload = build_humanoid_intelligence_report_payload(rows, top_n=args.top_n)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    paths = generate_report_charts(payload, args.out_dir)
    print("Generated:", paths)
    return 0 if paths else 1


if __name__ == "__main__":
    raise SystemExit(main())
