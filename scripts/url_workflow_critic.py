#!/usr/bin/env python3
"""Drive OEM URLs through FIND identity and report logic breaks.

  python3 scripts/url_workflow_critic.py
  python3 scripts/url_workflow_critic.py --fixtures
  python3 scripts/url_workflow_critic.py --url https://www.lucidbots.com/
  python3 scripts/url_workflow_critic.py --corpus app/data/url_workflow_corpus.json
  python3 scripts/url_workflow_critic.py --out reports/url_workflow_critic.json

Catalog listing is the FIND path for indexed OEMs (no live scrape).
--live POSTs /api/robot-job-search (optional; Fly may 503).
Do not commit reports/.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.url_workflow_critic import (  # noqa: E402
    CORPUS_PATH,
    CriticReport,
    UrlCritique,
    critique_corpus,
    critique_url,
    format_report,
    load_corpus,
    overlay_live_search,
    run_fixture_suite,
)

FLY_API = os.getenv("RFR_FLY_API", "https://ready-2-robot.fly.dev").rstrip("/")


def _post_search(url: str, *, api: str, timeout: float = 90.0) -> tuple[int, dict[str, Any]]:
    payload = json.dumps({"url": url, "lookup_grain": "product"}).encode("utf-8")
    req = Request(
        f"{api.rstrip('/')}/api/robot-job-search",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return int(resp.status), body if isinstance(body, dict) else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"error": raw[:400]}
        return int(exc.code), body if isinstance(body, dict) else {"error": raw[:400]}
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return 0, {"error": str(exc)}


def _overlay_live(critique: UrlCritique, search: dict[str, Any], status: int) -> None:
    overlay_live_search(critique, search, status)


def main() -> int:
    parser = argparse.ArgumentParser(description="FIND URL workflow critic")
    parser.add_argument("--corpus", default=str(CORPUS_PATH), help="JSON corpus of OEM URLs")
    parser.add_argument("--url", action="append", default=[], help="Extra URL (repeatable)")
    parser.add_argument("--fixtures", action="store_true", help="Run break-class fixture suite only")
    parser.add_argument("--live", action="store_true", help="Also POST Fly /api/robot-job-search")
    parser.add_argument("--fly", default=FLY_API)
    parser.add_argument("--out", default="", help="Write JSON report (reports/ is gitignored)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print JSON instead of text")
    args = parser.parse_args()

    if args.fixtures and not args.url:
        suite = run_fixture_suite()
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(suite, indent=2) + "\n", encoding="utf-8")
        if args.as_json:
            print(json.dumps(suite, indent=2))
        else:
            print(json.dumps({"ok": suite["ok"], "cases": [c["id"] + "=" + str(c["ok"]) for c in suite["cases"]]}, indent=2))
            for case in suite["cases"]:
                flag = "PASS" if case["ok"] else "FAIL"
                print(f"[{flag}] fixture {case['id']} kinds={case['got_kinds']}")
        return 0 if suite["ok"] else 1

    report: CriticReport
    if args.url and not Path(args.corpus).is_file():
        critiques = [critique_url(u) for u in args.url]
        report = CriticReport(ok=all(c.ok for c in critiques), urls=critiques, source="cli")
    elif args.url:
        data = load_corpus(Path(args.corpus))
        by_url = {str(r.get("url") or ""): r for r in (data.get("urls") or [])}
        critiques = [critique_url(u, by_url.get(u)) for u in args.url]
        report = CriticReport(ok=all(c.ok for c in critiques), urls=critiques, source="cli")
    else:
        report = critique_corpus(corpus_path=Path(args.corpus))

    if args.live:
        for row in report.urls:
            status, payload = _post_search(row.url, api=args.fly)
            _overlay_live(row, payload, status)
        report.ok = all(c.ok for c in report.urls)
        report.source = f"{report.source}+live"

    if args.fixtures:
        suite = run_fixture_suite()
        report.fixtures = suite["cases"]
        if not suite["ok"]:
            report.ok = False

    payload = report.to_dict()
    if args.out:
        out = Path(args.out)
        if not out.is_absolute() and urlparse(str(out)).scheme == "":
            out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)

    if args.as_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(report), end="")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
