"""
Fetch-and-verify humanoid spec enrichment (dry-run by default).

For the sparsest humanoid_benchmarks rows, this script:
  1. Gathers candidate source URLs (seeded product_url + DuckDuckGo HTML
     search results — no search-API key required).
  2. Fetches each page and extracts readable text.
  3. Uses Claude to extract ONLY specs explicitly stated in the fetched
     text, returning a value + verbatim evidence quote + source URL per field.
  4. Prints a dry-run report. Writes NOTHING unless --apply is passed.

Credentials are read from frontend/nextjs/.env.local:
  DATABASE_URL, Claude_API_key (mapped to ANTHROPIC_API_KEY).

Usage:
  python scripts/enrich_humanoids_fetch_verify.py            # dry run, 24 sparsest
  python scripts/enrich_humanoids_fetch_verify.py --limit 5
  python scripts/enrich_humanoids_fetch_verify.py --slug fourier-gr1
  python scripts/enrich_humanoids_fetch_verify.py --apply    # write merged specs + rescore
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / "frontend" / "nextjs" / ".env.local"

# Scoring + metadata fields we want to fill, with kinds for prompting/coercion.
FIELD_KINDS: dict[str, str] = {
    "top_speed_mps": "numeric",
    "can_climb_stairs": "bool",
    "can_navigate_rough_terrain": "bool",
    "can_run": "bool",
    "payload_kg": "numeric",
    "finger_count": "numeric",
    "has_dexterous_hands": "bool",
    "autonomy_level": "enum",
    "commercial_deployments": "numeric",
    "has_sdk": "bool",
    "has_api": "bool",
    "has_estop": "bool",
    "safety_certified": "bool",
    "force_limited_joints": "bool",
    "collision_force_n": "numeric",
    "battery_life_h": "numeric",
    "charge_time_h": "numeric",
    "hot_swap_battery": "bool",
    "price_usd": "numeric",
    "has_support_sla": "bool",
    "height_cm": "numeric",
    "weight_kg": "numeric",
    "peak_torque_nm": "numeric",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
ANTHROPIC_MODEL = os.environ.get("ENRICH_MODEL", "claude-sonnet-4-5-20250929")

API_BASE = os.environ.get("ENRICH_API_BASE", "https://ready-2-robot.fly.dev/api/humanoid")
SCORING_KEYS = [
    "top_speed_mps", "can_climb_stairs", "can_navigate_rough_terrain", "can_run",
    "payload_kg", "finger_count", "has_dexterous_hands", "autonomy_level",
    "commercial_deployments", "has_sdk", "has_api", "has_estop", "safety_certified",
    "force_limited_joints", "collision_force_n", "battery_life_h", "charge_time_h",
    "hot_swap_battery", "price_usd", "has_support_sla",
]


def load_env() -> None:
    if not ENV_FILE.exists():
        sys.exit(f"Env file not found: {ENV_FILE}")
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val
    # Map the user's key names to what the SDK expects.
    claude = os.environ.get("Claude_API_key") or os.environ.get("CLAUDE_API_KEY")
    if claude and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = claude
    if not os.environ.get("DATABASE_URL"):
        sys.exit("DATABASE_URL not found in .env.local")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Claude_API_key not found in .env.local")


def load_robots() -> list[dict]:
    resp = requests.get(f"{API_BASE}/robots", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("robots") if isinstance(data, dict) else data
    return rows or []


def load_robot_single(slug: str) -> Optional[dict]:
    """Fetch one robot from the single endpoint (fresh — bypasses 3h list snapshot)."""
    resp = requests.get(f"{API_BASE}/robots/{slug}", timeout=30)
    if not resp.ok:
        return None
    r = resp.json()
    r = r.get("robot") if isinstance(r, dict) and "robot" in r else r
    specs = r.get("specs") or {}
    return {
        "model_slug": r.get("model_slug"),
        "name": r.get("name"),
        "vendor": r.get("vendor"),
        "status": r.get("status"),
        "product_url": r.get("product_url"),
        "specs": specs,
        "spec_fill_pct": _fill_pct(specs),
    }


def _fill_pct(specs: dict) -> float:
    present = sum(1 for k in SCORING_KEYS if specs.get(k) not in (None, ""))
    return round(100 * present / len(SCORING_KEYS), 1)


def sparsest_robots(limit: int, slug: Optional[str]) -> list[dict]:
    rows = load_robots()
    enriched = []
    for r in rows:
        specs = r.get("specs") or {}
        enriched.append({
            "model_slug": r.get("model_slug"),
            "name": r.get("name"),
            "vendor": r.get("vendor"),
            "status": r.get("status"),
            "product_url": r.get("product_url"),
            "specs": specs,
            "spec_fill_pct": _fill_pct(specs),
        })
    if slug:
        return [r for r in enriched if r["model_slug"] == slug][:1]
    enriched.sort(key=lambda g: (g["spec_fill_pct"], g["name"] or ""))
    return enriched[:limit]


def ddg_search(query: str, max_results: int = 4) -> list[str]:
    """DuckDuckGo HTML endpoint — returns result URLs, no API key needed."""
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if not resp.ok:
            return []
        urls: list[str] = []
        for m in re.finditer(r'href="(https?://[^"]*uddg=[^"]+)"', resp.text):
            raw = m.group(1)
            qs = urllib.parse.urlparse(raw).query
            params = urllib.parse.parse_qs(qs)
            target = params.get("uddg", [None])[0]
            if target and target not in urls:
                urls.append(target)
            if len(urls) >= max_results:
                break
        # Fallback: plain result-link pattern
        if not urls:
            for m in re.finditer(r'class="result__a"[^>]*href="(https?://[^"]+)"', resp.text):
                if m.group(1) not in urls:
                    urls.append(m.group(1))
                if len(urls) >= max_results:
                    break
        return urls
    except Exception as exc:
        print(f"      ddg search failed: {exc}")
        return []


def html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript|svg|head).*?</\1>", " ", html)
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_page(url: str, max_chars: int = 9000) -> Optional[str]:
    try:
        resp = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=15, allow_redirects=True
        )
        ctype = resp.headers.get("content-type", "")
        if not resp.ok or "html" not in ctype and "text" not in ctype:
            return None
        text = html_to_text(resp.text)
        return text[:max_chars] if text else None
    except Exception:
        return None


def gather_sources(robot: dict, use_ddg: bool = True) -> list[dict]:
    name, vendor = robot["name"], robot.get("vendor") or ""
    candidates: list[str] = []
    if robot.get("product_url"):
        candidates.append(robot["product_url"])
    if use_ddg:
        queries = [
            f"{vendor} {name} humanoid robot specifications",
            f"{name} robot payload speed battery datasheet",
        ]
        for q in queries:
            for u in ddg_search(q, max_results=3):
                if u not in candidates:
                    candidates.append(u)
            time.sleep(1.0)

    sources: list[dict] = []
    seen = set()
    for url in candidates[:6]:
        if url in seen:
            continue
        seen.add(url)
        text = fetch_page(url)
        if text and len(text) > 200:
            sources.append({"url": url, "text": text})
        if len(sources) >= 4:
            break
    return sources


def extract_specs(robot: dict, sources: list[dict]) -> dict:
    blocks = "\n\n".join(
        f"[SOURCE {i+1}] {s['url']}\n{s['text']}" for i, s in enumerate(sources)
    )
    field_list = "\n".join(f"  - {k} ({v})" for k, v in FIELD_KINDS.items())
    prompt = f"""You extract humanoid-robot specifications STRICTLY from provided source text.

Robot: {robot.get('vendor')} {robot.get('name')}

SOURCES:
{blocks}

Extract ONLY values explicitly stated in the source text for these fields:
{field_list}

Rules:
- Use ONLY facts present in the source text. Do NOT use prior knowledge or infer.
- Omit any field not explicitly supported by the text.
- numeric: a number (no units). bool: true/false. enum (autonomy_level): one of
  "teleoperated","semi_autonomous","autonomous".
- price_usd only if an actual price is stated. peak_torque_nm = headline peak
  single-joint actuator torque in N·m.
- For each extracted field include the source number and a short verbatim quote.

Return ONLY JSON:
{{"fields": {{"<field>": {{"value": <v>, "source": <int>, "quote": "<verbatim>"}}}}}}
If nothing is supported, return {{"fields": {{}}}}."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 1200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        if not resp.ok:
            print(f"      LLM HTTP {resp.status_code}: {resp.text[:200]}")
            return {}
        raw = resp.json()["content"][0]["text"].strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return {}
        data = json.loads(m.group())
        return data.get("fields", {}) or {}
    except Exception as exc:
        print(f"      LLM extraction failed: {exc}")
        return {}


def coerce(value: Any, kind: str) -> Any:
    if kind == "bool":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "yes", "1")
    if kind == "numeric":
        if isinstance(value, (int, float)):
            return value
        m = re.search(r"-?\d[\d,]*\.?\d*", str(value))
        return float(m.group().replace(",", "")) if m else None
    return value


def _host(url: str | None) -> str:
    if not url:
        return ""
    try:
        from urllib.parse import urlparse
        return (urlparse(url).hostname or "").lower().lstrip("www.")
    except Exception:
        return ""


def build_item(robot: dict, proposed: dict, sources: list[dict]) -> dict:
    """Build a clean, coerced, provenance-tagged item for review/apply."""
    official_host = _host(robot.get("product_url"))
    specs: dict[str, Any] = {}
    evidence: dict[str, dict] = {}
    for field, info in proposed.items():
        if field not in FIELD_KINDS:
            continue
        val = coerce(info.get("value"), FIELD_KINDS[field])
        if val is None:
            continue
        idx = info.get("source")
        url = sources[idx - 1]["url"] if isinstance(idx, int) and 1 <= idx <= len(sources) else None
        tier = "official" if (official_host and _host(url) == official_host) else "third_party"
        specs[field] = val
        evidence[field] = {"url": url, "quote": (info.get("quote") or "")[:200], "tier": tier}
    return {
        "slug": robot["model_slug"],
        "name": robot.get("name"),
        "vendor": robot.get("vendor"),
        "fill_before_pct": robot.get("spec_fill_pct"),
        "specs": specs,
        "evidence": evidence,
    }


def post_to_endpoint(endpoint: str, token: str, items: list[dict]) -> None:
    payload = {"items": [{"slug": i["slug"], "specs": i["specs"], "evidence": i["evidence"]}
                         for i in items if i["specs"]]}
    if not payload["items"]:
        print("No items with verified specs to apply.")
        return
    print(f"\nPOSTing {len(payload['items'])} item(s) to {endpoint} ...")
    resp = requests.post(endpoint, params={"token": token}, json=payload, timeout=120)
    print(f"  HTTP {resp.status_code}")
    try:
        print("  " + json.dumps(resp.json(), indent=2)[:2000])
    except Exception:
        print("  " + resp.text[:1000])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=24)
    ap.add_argument("--slug", type=str, default=None)
    ap.add_argument("--slugs", type=str, default=None,
                    help="Comma-separated slugs; fetched fresh from the single endpoint")
    ap.add_argument("--url-map", type=str, default=None,
                    help="JSON file {slug: url}; scrape these exact URLs (override product_url)")
    ap.add_argument("--json", dest="json_path", type=str, default=None,
                    help="Write structured proposals (with evidence) to this JSON file")
    ap.add_argument("--apply-endpoint", type=str, default=None,
                    help="POST verified specs to this admin endpoint (e.g. "
                         "https://ready-2-robot.fly.dev/api/humanoid/apply-verified-specs)")
    ap.add_argument("--token", type=str, default=os.environ.get("SCRAPER_CRON_TOKEN", ""),
                    help="Token for the apply endpoint")
    ap.add_argument("--no-ddg", action="store_true",
                    help="Use only the seeded product_url (skip DuckDuckGo — avoids throttling)")
    ap.add_argument("--require-url", action="store_true",
                    help="Skip robots that have no seeded product_url")
    args = ap.parse_args()

    load_env()
    sys.path.insert(0, str(REPO_ROOT))

    if args.url_map:
        import json as _json
        url_map = _json.load(open(args.url_map))
        targets = []
        for slug, url in url_map.items():
            r = load_robot_single(slug)
            if not r:
                print(f"  (skip {slug}: not found)")
                continue
            r["product_url"] = url  # override with user-supplied URL
            targets.append(r)
    elif args.slugs:
        wanted = [s.strip() for s in args.slugs.split(",") if s.strip()]
        targets = [r for r in (load_robot_single(s) for s in wanted) if r]
    else:
        targets = sparsest_robots(args.limit, args.slug)
    writing = bool(args.apply_endpoint)
    mode = f"APPLY via endpoint" if writing else "DRY RUN (no writes)"
    print(f"\n=== Humanoid fetch-verify enrichment — {mode} ===")
    print(f"Targets: {len(targets)} robots (model={ANTHROPIC_MODEL})\n")

    total_fields = 0
    items: list[dict] = []
    for g in targets:
        slug = g["model_slug"]
        robot = g
        if args.require_url and not robot.get("product_url"):
            continue
        print(f"--- {robot['vendor']} {robot['name']} ({slug}) — fill {g['spec_fill_pct']}% ---")
        sources = gather_sources(robot, use_ddg=not args.no_ddg)
        print(f"      fetched {len(sources)} source page(s): "
              + ", ".join(s["url"][:60] for s in sources) if sources else "      no source pages found")
        if not sources:
            items.append({"slug": slug, "name": robot.get("name"), "vendor": robot.get("vendor"),
                          "fill_before_pct": g["spec_fill_pct"], "specs": {}, "evidence": {}})
            continue
        proposed = extract_specs(robot, sources)
        item = build_item(robot, proposed, sources)
        if item["specs"]:
            for f, val in item["specs"].items():
                ev = item["evidence"].get(f, {})
                print(f"        + {f} = {val}   [{(ev.get('url') or '')[:45]}] \"{(ev.get('quote') or '')[:70]}\"")
            total_fields += len(item["specs"])
        else:
            print("        (no spec values supported by fetched text)")
        items.append(item)
        print()

    print("=== SUMMARY ===")
    for s in sorted(items, key=lambda x: -len(x["specs"])):
        print(f"  {len(s['specs']):>2} fields  {s['slug']}")
    robots_with = sum(1 for s in items if s["specs"])
    print(f"\nTotal proposed fields: {total_fields} across {robots_with}/{len(targets)} robots")

    if args.json_path:
        with open(args.json_path, "w") as fh:
            json.dump({"model": ANTHROPIC_MODEL, "items": items}, fh, indent=2)
        print(f"Wrote structured proposals to {args.json_path}")

    if writing:
        if not args.token:
            sys.exit("--apply-endpoint requires --token (or SCRAPER_CRON_TOKEN env).")
        post_to_endpoint(args.apply_endpoint, args.token, items)
    else:
        print("Dry run — nothing written. Re-run with --apply-endpoint + --token to commit.")


if __name__ == "__main__":
    main()
