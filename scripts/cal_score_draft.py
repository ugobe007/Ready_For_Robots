#!/usr/bin/env python3
"""Score a Cal draft on the Stage 1 voice rubric.

Examples:
  python scripts/cal_score_draft.py --variant bottleneck_first --name "Performance Food Group" --industry "Food Distribution"
  python scripts/cal_score_draft.py --file path/to/draft.txt --company "PFG"
  echo "..." | python scripts/cal_score_draft.py --stdin --company "Acme"
  python scripts/cal_score_draft.py --variant bottleneck_first --name "Performance Food Group" --industry "Food Distribution" --gate
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _read_draft(args: argparse.Namespace) -> tuple[str, str | None]:
    if args.stdin:
        return sys.stdin.read(), args.company
    if args.file:
        return Path(args.file).read_text(encoding="utf-8"), args.company
    if args.variant:
        from app.services.agent_messaging import build_buyer_variant_body

        name = args.name or "Acme Logistics"
        industry = args.industry or "Logistics"
        body = build_buyer_variant_body(name, industry, args.variant)
        return body, name
    raise SystemExit("Provide --file, --stdin, or --variant")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a Cal draft (Stage 1 Evaluate).")
    parser.add_argument("--file", help="Path to draft text (optional Subject: header)")
    parser.add_argument("--stdin", action="store_true", help="Read draft from stdin")
    parser.add_argument(
        "--variant",
        choices=("workflow_first", "what_survives", "bottleneck_first"),
        help="Score a generated buyer variant instead of a file",
    )
    parser.add_argument("--name", help="Company name for --variant")
    parser.add_argument("--industry", help="Industry for --variant")
    parser.add_argument("--company", help="Company hint for relevance scoring")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Exit 1 if voice < 24/30 or Accuracy fails",
    )
    args = parser.parse_args()

    from app.services.cal_voice_rubric import format_rubric_report, score_cal_draft

    draft, company = _read_draft(args)
    result = score_cal_draft(draft, company_hint=company or args.company)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_rubric_report(result))
        if not args.gate:
            print("\nDraft preview (first 500 chars):\n")
            print(draft[:500].rstrip())
            if len(draft) > 500:
                print("…")

    if args.gate and not result.approved:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
