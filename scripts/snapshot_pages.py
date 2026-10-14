#!/usr/bin/env python3
"""
Snapshot robot pages for the offline benchmark (any benchmark file).

Writes the same layout the benchmark runner already reads:
    <out>/<id>/page.html, page.txt, metadata.json
plus <out>/manifest.json summarizing every page.

Usage (from the repo root on a Mac with normal internet):

    # Hold-out set, real browser rendering (recommended)
    python3 scripts/snapshot_pages.py \
        --benchmark tests/fixtures/robot_holdout_set.v1.json \
        --out tests/fixtures/robot_pages_holdout --render

    # Re-fetch only the originals that never loaded
    python3 scripts/snapshot_pages.py \
        --benchmark tests/fixtures/robot_benchmark_set.v2.json \
        --out tests/fixtures/robot_pages --render \
        --ids hc-01 con-04 hos-02 ag-01 insp-01 neg-01

    # Point one entry at a better URL (e.g., Hilti's Jaibot product page)
    python3 scripts/snapshot_pages.py --benchmark ... --out ... --render \
        --ids h-07 --url h-07=https://www.hilti.com/<jaibot-page>

--render uses a real headless Chrome (Playwright) so JavaScript-built pages
and most bot blocks work. One-time setup:
    pip3 install playwright beautifulsoup4 requests
    python3 -m playwright install chromium

This script only reads the benchmark file and writes snapshot files.
It never touches the database.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

THIN_WORDS = 150  # below this, the page is treated as not usable
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def extract_text(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def fetch_plain(url: str, timeout: int) -> dict[str, Any]:
    import requests

    try:
        r = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=timeout,
                         allow_redirects=True)
        ok = r.status_code == 200
        return {"status_code": r.status_code, "final_url": r.url,
                "html": r.text if ok else "", "error": None if ok else f"HTTP {r.status_code}",
                "method": "requests"}
    except Exception as e:  # network errors, SSL, DNS
        return {"status_code": 0, "final_url": url, "html": "", "error": str(e)[:200],
                "method": "requests"}


def fetch_rendered(url: str, timeout: int, browser) -> dict[str, Any]:
    page = browser.new_page(user_agent=BROWSER_UA)
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        try:  # let client-side content load, but don't hang on chatty sites
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        status = resp.status if resp else 0
        html = page.content()
        ok = 200 <= status < 300
        return {"status_code": status, "final_url": page.url,
                "html": html if ok else "", "error": None if ok else f"HTTP {status}",
                "method": "playwright"}
    except Exception as e:
        return {"status_code": 0, "final_url": url, "html": "", "error": str(e)[:200],
                "method": "playwright"}
    finally:
        page.close()


def entries(benchmark: dict[str, Any]) -> list[dict[str, Any]]:
    """All snapshot-able entries: robots, gap probes, negative controls."""
    out = []
    for key in ("robots", "taxonomy_gap_probes", "negative_controls"):
        for e in benchmark.get(key, []):
            out.append({
                "id": e["id"],
                "url": e["url"],
                "company": e.get("company") or e.get("description", ""),
                "product": e.get("target_product") or e.get("product") or "",
                "section": key,
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--benchmark", required=True, help="Path to benchmark/hold-out JSON")
    ap.add_argument("--out", required=True, help="Output directory for snapshots")
    ap.add_argument("--render", action="store_true", help="Use real headless Chrome")
    ap.add_argument("--ids", nargs="+", help="Only these IDs")
    ap.add_argument("--url", action="append", default=[],
                    help="Override a URL: ID=URL (repeatable)")
    ap.add_argument("--timeout", type=int, default=30)
    args = ap.parse_args()

    benchmark = json.loads(Path(args.benchmark).read_text())
    items = entries(benchmark)
    overrides = dict(o.split("=", 1) for o in args.url)
    for it in items:
        if it["id"] in overrides:
            it["original_url"] = it["url"]
            it["url"] = overrides[it["id"]]
    if args.ids:
        wanted = set(args.ids)
        missing = wanted - {i["id"] for i in items}
        if missing:
            print(f"Unknown IDs: {sorted(missing)}", file=sys.stderr)
            return 2
        items = [i for i in items if i["id"] in wanted]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    pw = browser = None
    if args.render:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Playwright not installed. Run:\n  pip3 install playwright\n"
                  "  python3 -m playwright install chromium", file=sys.stderr)
            return 2
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)

    results = []
    try:
        for it in items:
            print(f"{it['id']:8} {it['company'][:30]:30} {it['url']}")
            res = fetch_rendered(it["url"], args.timeout, browser) if browser \
                else fetch_plain(it["url"], args.timeout)
            if browser and not res["html"]:  # fall back once to a plain fetch
                plain = fetch_plain(it["url"], args.timeout)
                if plain["html"]:
                    res = plain
            text = extract_text(res["html"]) if res["html"] else ""
            words = len(text.split())
            status = ("OK" if res["html"] and words >= THIN_WORDS
                      else "THIN_CONTENT" if res["html"] else "FETCH_FAILED")

            d = out_dir / it["id"]
            d.mkdir(parents=True, exist_ok=True)
            (d / "page.html").write_text(res["html"], encoding="utf-8")
            (d / "page.txt").write_text(text, encoding="utf-8")
            meta = {
                "id": it["id"], "section": it["section"], "company": it["company"],
                "product": it["product"], "url": it["url"],
                "original_url": it.get("original_url"),
                "final_url": res["final_url"], "status_code": res["status_code"],
                "fetch_date": now_iso(), "method": res["method"],
                "word_count": words, "snapshot_status": status, "error": res["error"],
            }
            (d / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            results.append(meta)
            print(f"         -> {status} (HTTP {res['status_code']}, {words} words"
                  f"{', ' + res['error'] if res['error'] else ''})")
    finally:
        if browser:
            browser.close()
        if pw:
            pw.stop()

    manifest_path = out_dir / "manifest.json"
    prior = {}
    if manifest_path.exists():  # keep entries from earlier runs, replace re-fetched ones
        try:
            prior = {m["id"]: m for m in json.loads(manifest_path.read_text()).get("pages", [])}
        except Exception:
            prior = {}
    prior.update({m["id"]: m for m in results})
    manifest = {"benchmark": args.benchmark, "updated": now_iso(),
                "pages": sorted(prior.values(), key=lambda m: m["id"])}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    counts = {}
    for m in results:
        counts[m["snapshot_status"]] = counts.get(m["snapshot_status"], 0) + 1
    print("\nSummary:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    problems = [m for m in results if m["snapshot_status"] != "OK"]
    if problems:
        print("Needs attention (wrong URL, blocked, or too little text):")
        for m in problems:
            print(f"  {m['id']}: {m['snapshot_status']} - {m['error'] or str(m['word_count']) + ' words'}")
    print(f"\nWrote {len(results)} snapshots to {out_dir}/ and {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
