#!/usr/bin/env python3
"""
Harness diagnostics — site health, frontend conventions, conversion metrics.

Used by harness_snapshot.py (JSON) and harness_notify.py (daily operator report).

Usage:
  python3 scripts/harness_diagnostics.py
  python3 scripts/harness_diagnostics.py --check site
  python3 scripts/harness_diagnostics.py --check code --fail-on-violations
  python3 scripts/harness_diagnostics.py --check conversion
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from scripts.harness_env import load_harness_env

load_harness_env(_root)

FLY_API = "https://ready-2-robot.fly.dev"
MARKETING_SITE = "https://readyforrobots.com"
FRONTEND_ROOT = _root / "readyforrobots-new" / "client"

# Public read endpoints must use getPublicReadApiBase() on the marketing domain (see apiBase.ts).
PUBLIC_READ_ENDPOINTS = (
    "/api/humanoid/robots",
    "/api/humanoid/intelligence-report",
    "/api/leads/pipeline",
    "/api/leads/homepage",
    "/api/leads/summary",
)

PUBLIC_READ_GLOBS = ("**/pages/*.tsx", "**/components/**/*.tsx", "**/lib/**/*.ts")

# Authenticated or write paths — getApiBase() is correct.
PUBLIC_READ_ALLOWLIST_SUBSTRINGS = (
    "/api/crm/",
    "/api/admin/",
    "/api/billing/checkout",
    "/api/user/",
    "/api/scout/",
    "/api/sales/",
    "/api/integrations",
    "/api/marketplace/",
    "/api/newsletter/subscribe",
    "/api/leads/report-download",
    "/api/robot-companies/",
    "/api/waitlist/",
    "/api/proposals/",
    "/api/calendar/",
    "/api/humanoid/robots/",  # single-robot detail — low traffic, ok via proxy
)


def _fetch_probe(url: str, *, timeout: float = 15.0, retries: int = 1) -> dict[str, Any]:
    # Retry once on transient failures (timeout / 5xx). The single shared-CPU web
    # machine can briefly saturate during the daily heavy jobs; one blip should not
    # raise a P0 fundability alert when the endpoint is actually healthy on retry.
    attempt = 0
    last: dict[str, Any] = {}
    while attempt <= max(retries, 0):
        last = _fetch_probe_once(url, timeout=timeout)
        if last.get("ok"):
            if attempt:
                last["recovered_after_retry"] = attempt
            return last
        transient = "HTTP 5" in str(last.get("error") or "") or "timed out" in str(
            last.get("error") or ""
        ).lower() or "timeout" in str(last.get("error") or "").lower()
        if not transient:
            return last
        attempt += 1
        if attempt <= max(retries, 0):
            time.sleep(2.0)
    return last


def _fetch_probe_once(url: str, *, timeout: float = 15.0) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        import httpx

        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"Accept": "application/json"})
            latency_ms = round((time.perf_counter() - t0) * 1000)
            if resp.status_code >= 400:
                return {"ok": False, "latency_ms": latency_ms, "error": f"HTTP {resp.status_code}"}
            if resp.text.strip().startswith("<"):
                return {"ok": False, "latency_ms": latency_ms, "error": "non-json (html) response"}
            data = resp.json()
            out: dict[str, Any] = {"ok": True, "latency_ms": latency_ms, "url": url}
            if isinstance(data, dict):
                robots = data.get("robots")
                if isinstance(robots, list):
                    out["robots_count"] = len(robots)
                if data.get("stale"):
                    out["stale"] = True
                if data.get("source"):
                    out["source"] = data.get("source")
                if data.get("built_at"):
                    out["built_at"] = data.get("built_at")
                if data.get("cache_pending") is not None:
                    out["cache_pending"] = data.get("cache_pending")
                leads = data.get("leads")
                if isinstance(leads, list):
                    out["leads_count"] = len(leads)
                if data.get("enabled") is not None:
                    out["billing_enabled"] = data.get("enabled")
            return out
    except Exception as exc:
        return {
            "ok": False,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "url": url,
            "error": str(exc),
        }


def _page_probe(path: str) -> dict[str, Any]:
    url = f"{MARKETING_SITE}{path}"
    t0 = time.perf_counter()
    try:
        import httpx

        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(url)
            return {
                "ok": resp.status_code < 400,
                "status": resp.status_code,
                "latency_ms": round((time.perf_counter() - t0) * 1000),
                "path": path,
            }
    except Exception as exc:
        return {"ok": False, "path": path, "error": str(exc)}


def check_site_health(*, api_base: str = FLY_API) -> dict[str, Any]:
    base = api_base.rstrip("/")
    alerts: list[str] = []
    recommendations: list[str] = []

    fly_robots = _fetch_probe(f"{base}/api/humanoid/robots")
    vercel_robots = _fetch_probe(f"{MARKETING_SITE}/api/humanoid/robots")
    pipeline = _fetch_probe(f"{base}/api/leads/pipeline", timeout=25)
    billing = _fetch_probe(f"{base}/api/billing/config", timeout=10)
    checkout_auth = _probe_checkout_requires_auth(api_base=base)
    pages = {
        "robots": _page_probe("/robots"),
        "pricing": _page_probe("/pricing"),
        "pipeline": _page_probe("/pipeline"),
        "signup": _page_probe("/signup"),
    }

    if not fly_robots.get("ok"):
        alerts.append(f"Robots API (Fly) failed: {fly_robots.get('error')}")
    elif (fly_robots.get("latency_ms") or 0) > 5000:
        alerts.append(f"Robots API (Fly) slow: {fly_robots['latency_ms']}ms")
    elif not fly_robots.get("robots_count"):
        alerts.append("Robots API returned zero robots")

    vercel_ms = vercel_robots.get("latency_ms") or 0
    fly_ms = fly_robots.get("latency_ms") or 0
    if vercel_robots.get("ok") and vercel_ms > max(8000, fly_ms * 3):
        alerts.append(
            f"Vercel /api proxy for robots is slow ({vercel_ms}ms vs Fly {fly_ms}ms) — "
            "public pages should use getPublicReadApiBase()"
        )
        recommendations.append(
            "Keep /robots and other public reads on Fly direct; reserve Vercel /api proxy for auth writes."
        )

    if not pipeline.get("ok"):
        alerts.append(f"Pipeline API failed: {pipeline.get('error')}")
    elif pipeline.get("cache_pending"):
        alerts.append("Pipeline cache_pending — feed rebuild in progress or stale")
    elif not pipeline.get("leads_count"):
        alerts.append("Pipeline feed empty — blocks signup value proof")

    if billing.get("ok") and not billing.get("billing_enabled"):
        alerts.append("Stripe billing disabled — upgrades cannot convert to revenue")
        recommendations.append("Enable STRIPE_SECRET_KEY + price IDs on Fly for Pro checkout.")

    if billing.get("ok") and billing.get("billing_enabled") and not checkout_auth.get("ok"):
        alerts.append(
            "Billing checkout API accepts unauthenticated POST — anonymous users could reach Stripe"
        )
        recommendations.append("Ensure POST /api/billing/checkout returns 401 without Authorization header.")

    for name, probe in pages.items():
        if not probe.get("ok"):
            alerts.append(f"Page /{name} unhealthy: {probe.get('error') or probe.get('status')}")

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "fly_robots": fly_robots,
        "vercel_robots_proxy": vercel_robots,
        "pipeline": pipeline,
        "billing": billing,
        "checkout_auth_probe": checkout_auth,
        "pages": pages,
        "alerts": alerts,
        "recommendations": recommendations,
        "healthy": not alerts,
    }


def _scan_file_for_api_violations(path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    if "getPublicReadApiBase" in text:
        return []
    if "getApiBase()" not in text:
        return []

    violations: list[dict[str, str]] = []
    try:
        rel = str(path.relative_to(_root))
    except ValueError:
        rel = path.name
    for endpoint in PUBLIC_READ_ENDPOINTS:
        if endpoint not in text:
            continue
        if any(allow in text for allow in PUBLIC_READ_ALLOWLIST_SUBSTRINGS if allow in endpoint):
            continue
        # Skip if only detail sub-path (e.g. /robots/{slug})
        if endpoint == "/api/humanoid/robots" and "/api/humanoid/robots/" in text:
            if text.count("/api/humanoid/robots") == text.count("/api/humanoid/robots/"):
                continue
        violations.append(
            {
                "file": rel,
                "endpoint": endpoint,
                "fix": "Use getPublicReadApiBase() for this public read (see client/src/lib/apiBase.ts)",
            }
        )
    return violations


def _check_pricing_checkout_auth_gate() -> dict[str, Any]:
    """Static checks — logged-out users must not auto-start Stripe from stale localStorage intent."""
    pricing = FRONTEND_ROOT / "src" / "pages" / "Pricing.tsx"
    issues: list[str] = []
    if not pricing.is_file():
        return {"ok": False, "issues": ["Pricing.tsx missing"]}
    text = pricing.read_text(encoding="utf-8")
    if re.search(r'params\.get\("upgrade"\)\s*\|\|\s*peekPendingPlan\(\)', text):
        issues.append("Pricing auto-checkout uses peekPendingPlan() — can skip auth before Stripe")
    if "setLocation(checkoutAuthHref" in text:
        issues.append("Pricing uses setLocation(checkoutAuthHref) — use signupHrefForCheckout + window.location.assign")
    if "beginCheckout" in text and not re.search(r"if\s*\(\s*authLoading\s*\)", text):
        issues.append("beginCheckout must wait for authLoading before starting checkout")
    if "signupHrefForCheckout" not in text:
        issues.append("Pricing must redirect unauthenticated checkout to signupHrefForCheckout")
    return {"ok": not issues, "issues": issues}


def _probe_checkout_requires_auth(*, api_base: str = FLY_API) -> dict[str, Any]:
    """POST /api/billing/checkout without a token must reject (never return a Stripe URL)."""
    url = f"{api_base.rstrip('/')}/api/billing/checkout"
    try:
        import httpx

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json={"tier": "pro"})
            ok = resp.status_code in (401, 403)
            return {"ok": ok, "status": resp.status_code, "url": url}
    except Exception as exc:
        return {"ok": False, "url": url, "error": str(exc)}


def _check_supply_match_quality_gate() -> dict[str, Any]:
    """Supply Cal emails must reuse pipeline junk/buyer gates — not raw term overlap."""
    rc_path = _root / "app" / "api" / "robot_companies.py"
    assembly_path = _root / "app" / "services" / "cal_assembly_agent.py"
    persona_path = _root / "app" / "services" / "cal_persona.py"
    issues: list[str] = []
    if not rc_path.is_file():
        return {"ok": False, "issues": ["robot_companies.py missing"]}
    text = rc_path.read_text(encoding="utf-8")
    if "_supply_buyer_lead_eligible" not in text:
        issues.append("Missing _supply_buyer_lead_eligible — supply emails may cite junk leads")
    if "_supply_buyer_lead_eligible(" not in text:
        issues.append("_match_buyer_leads must call _supply_buyer_lead_eligible")
    supply_path = _root / "app" / "services" / "supply_autonomy.py"
    if supply_path.is_file():
        supply_text = supply_path.read_text(encoding="utf-8")
        if "SUPPLY_AUTONOMY_MIN_MATCHES" not in supply_text:
            issues.append("supply_autonomy missing SUPPLY_AUTONOMY_MIN_MATCHES guard")
        if "assemble_supply_outreach" not in supply_text:
            issues.append("supply_autonomy must call Cal assembly agent before send")
    if not assembly_path.is_file():
        issues.append("cal_assembly_agent.py missing — no pre-send review")
    if not persona_path.is_file():
        issues.append("cal_persona.py missing — Cal has no defined personality")
    return {"ok": not issues, "issues": issues}


def check_code_conventions() -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    if FRONTEND_ROOT.is_dir():
        for pattern in PUBLIC_READ_GLOBS:
            for path in FRONTEND_ROOT.glob(pattern):
                if path.suffix not in {".tsx", ".ts"}:
                    continue
                violations.extend(_scan_file_for_api_violations(path))

    auth_next = _root / "readyforrobots-new" / "client" / "src" / "lib" / "authNext.ts"
    auth_patterns_ok = auth_next.is_file() and "navigateAfterAuth" in auth_next.read_text(encoding="utf-8")

    login_tsx = _root / "readyforrobots-new" / "client" / "src" / "pages" / "Login.tsx"
    login_ok = True
    if login_tsx.is_file():
        login_text = login_tsx.read_text(encoding="utf-8")
        if "resolvePostAuthPath" in login_text and "resolvePostAuthPath" not in login_text.split("import", 1)[0]:
            if not re.search(r"import\s*\{[^}]*resolvePostAuthPath", login_text):
                login_ok = False

    open_challenges = _parse_open_conversion_challenges()
    checkout_gate = _check_pricing_checkout_auth_gate()
    supply_gate = _check_supply_match_quality_gate()
    alerts: list[str] = []
    if violations:
        alerts.append(f"{len(violations)} public-read API routing violation(s)")
    if not auth_patterns_ok:
        alerts.append("authNext.ts missing navigateAfterAuth — checkout redirect may drop ?upgrade=pro")
    if not login_ok:
        alerts.append("Login.tsx uses resolvePostAuthPath without importing it")
    for issue in checkout_gate.get("issues") or []:
        alerts.append(f"Checkout auth gate: {issue}")
    for issue in supply_gate.get("issues") or []:
        alerts.append(f"Supply match gate: {issue}")
    if open_challenges:
        alerts.append(f"{len(open_challenges)} open conversion challenge(s) on the board")

    recommendations = []
    if violations:
        recommendations.append("Run harness code gate before deploy; fix getPublicReadApiBase violations first.")
    if not checkout_gate.get("ok"):
        recommendations.append(
            "Fix Pricing checkout: unauthenticated users → signup/login; auto-resume only on ?upgrade= after auth."
        )
    if not supply_gate.get("ok"):
        recommendations.append(
            "Fix supply buyer matching: apply classify_lead + buyer-intent gate before Cal cites leads in vendor emails."
        )
    if open_challenges:
        top = open_challenges[0]
        recommendations.append(f"Next conversion build: #{top['rank']} {top['title']}")

    return {
        "violations": violations[:25],
        "violation_count": len(violations),
        "auth_helpers_ok": auth_patterns_ok,
        "login_import_ok": login_ok,
        "checkout_auth_gate_ok": checkout_gate.get("ok"),
        "checkout_auth_gate": checkout_gate,
        "supply_match_gate_ok": supply_gate.get("ok"),
        "supply_match_gate": supply_gate,
        "open_conversion_challenges": open_challenges,
        "alerts": alerts,
        "recommendations": recommendations,
        "healthy": (
            not violations
            and auth_patterns_ok
            and login_ok
            and checkout_gate.get("ok")
            and supply_gate.get("ok")
        ),
    }


def _parse_open_conversion_challenges(markdown: str | None = None) -> list[dict[str, Any]]:
    if markdown is None:
        path = _root / "docs" / "conversion_agent_challenges.md"
        if not path.is_file():
            return []
        markdown = path.read_text(encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        if "| Open |" not in line and "| open |" not in line.lower():
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 4:
            continue
        rank_match = re.match(r"(\d+)", parts[0])
        rows.append(
            {
                "rank": int(rank_match.group(1)) if rank_match else 0,
                "title": parts[1] if len(parts) > 1 else "",
                "agent": parts[2] if len(parts) > 2 else "",
            }
        )
    return sorted(rows, key=lambda r: r.get("rank") or 999)


def check_conversion_metrics(db=None) -> dict[str, Any]:
    """Signup and revenue proxies from Postgres (when DATABASE_URL is set)."""
    block: dict[str, Any] = {"available": False, "alerts": [], "recommendations": []}
    if db is None:
        block["reason"] = "DATABASE_URL not configured"
        return block

    try:
        from sqlalchemy import text

        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        total_users = db.execute(text("SELECT COUNT(*) FROM user_profiles")).scalar() or 0
        users_7d = db.execute(
            text("SELECT COUNT(*) FROM user_profiles WHERE created_at >= :since"),
            {"since": week_ago},
        ).scalar() or 0
        paid_users = db.execute(
            text(
                """
                SELECT COUNT(*) FROM user_profiles
                WHERE LOWER(COALESCE(billing_tier, '')) IN ('pro', 'premium', 'paid', 'starter')
                """
            )
        ).scalar() or 0
        active_paid = db.execute(
            text(
                """
                SELECT COUNT(*) FROM user_profiles
                WHERE LOWER(COALESCE(billing_tier, '')) IN ('pro', 'premium', 'paid')
                  AND COALESCE(stripe_subscription_status, '') IN ('active', 'trialing')
                """
            )
        ).scalar() or 0
        crm_accounts = db.execute(text("SELECT COUNT(*) FROM crm_accounts")).scalar() or 0
        crm_accounts_7d = db.execute(
            text("SELECT COUNT(*) FROM crm_accounts WHERE created_at >= :since"),
            {"since": week_ago},
        ).scalar() or 0
        waitlist = 0
        try:
            waitlist = db.execute(text("SELECT COUNT(*) FROM waitlist_signups")).scalar() or 0
        except Exception:
            pass

        # Signup funnel (conversion board #20) — client-side start/complete/first-save
        # events reveal where the funnel drops. Best-effort: table may not exist yet.
        funnel_7d: dict[str, int] = {}
        try:
            rows = db.execute(
                text(
                    """
                    SELECT event_type, COUNT(*) AS n
                    FROM site_analytics_events
                    WHERE event_type IN ('signup_start', 'signup_complete', 'first_save')
                      AND created_at >= :since
                    GROUP BY event_type
                    """
                ),
                {"since": week_ago},
            ).fetchall()
            funnel_7d = {str(r[0]): int(r[1]) for r in rows}
        except Exception:
            funnel_7d = {}

        block.update(
            {
                "available": True,
                "signups_total": int(total_users),
                "signups_7d": int(users_7d),
                "paid_tier_users": int(paid_users),
                "active_subscriptions": int(active_paid),
                "crm_accounts_total": int(crm_accounts),
                "crm_accounts_7d": int(crm_accounts_7d),
                "founding_waitlist": int(waitlist),
                "signup_funnel_7d": {
                    "signup_start": funnel_7d.get("signup_start", 0),
                    "signup_complete": funnel_7d.get("signup_complete", 0),
                    "first_save": funnel_7d.get("first_save", 0),
                },
            }
        )

        if users_7d == 0:
            block["alerts"].append("Zero new signups in 7 days — prioritize conversion missions")
            block["recommendations"].append(
                "Ship one ProductSurface item from docs/conversion_agent_challenges.md (#20 instrumentation or signup friction)."
            )
        if total_users > 0 and active_paid == 0:
            block["alerts"].append("Signed-up users but no active paid subscriptions — verify Stripe checkout flow")
            block["recommendations"].append(
                "Test /pricing?upgrade=pro end-to-end; confirm navigateAfterAuth preserves upgrade param."
            )
        if crm_accounts_7d == 0 and users_7d > 0:
            block["alerts"].append("New signups but no new CRM accounts — activation gap after signup")
            block["recommendations"].append("Improve post-auth landing and FirstSaveGuide on /pipeline.")

        block["healthy"] = not block["alerts"]
        return block
    except Exception as exc:
        return {"available": False, "error": str(exc), "alerts": [], "recommendations": []}


def build_diagnostics(*, api_base: str = FLY_API, db=None) -> dict[str, Any]:
    site = check_site_health(api_base=api_base)
    code = check_code_conventions()
    conversion = check_conversion_metrics(db)

    all_alerts = (
        site.get("alerts", [])
        + code.get("alerts", [])
        + conversion.get("alerts", [])
    )
    all_recs: list[str] = []
    for block in (site, code, conversion):
        for rec in block.get("recommendations") or []:
            if rec not in all_recs:
                all_recs.append(rec)

    priority_actions = _prioritize_for_fundability(site, code, conversion, all_recs)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "site_health": site,
        "code_review": code,
        "conversion": conversion,
        "alerts": all_alerts,
        "recommendations": all_recs,
        "priority_actions": priority_actions,
        "healthy": site.get("healthy") and code.get("healthy") and conversion.get("healthy", True),
    }


def _prioritize_for_fundability(
    site: dict,
    code: dict,
    conversion: dict,
    recs: list[str],
) -> list[str]:
    actions: list[str] = []
    if conversion.get("signups_7d", 0) == 0 and conversion.get("available"):
        actions.append("P0: Drive signups — anonymous value on /pipeline then OAuth signup with ?next= preserved")
    if site.get("alerts"):
        for a in site["alerts"][:2]:
            actions.append(f"P0: Site — {a}")
    if not conversion.get("active_subscriptions") and conversion.get("signups_total", 0) > 5:
        actions.append("P1: Revenue — fix Pro checkout (/pricing?upgrade=pro → Stripe)")
    if code.get("violation_count"):
        actions.append(f"P1: Performance — fix {code['violation_count']} getPublicReadApiBase violation(s)")
    for ch in (code.get("open_conversion_challenges") or [])[:2]:
        actions.append(f"P2: Conversion board #{ch.get('rank')} — {ch.get('title')}")
    for rec in recs[:3]:
        if rec not in actions:
            actions.append(rec)
    return actions[:8]


def render_daily_report_markdown(
    *,
    snapshot: dict | None,
    diagnostics: dict,
    mission_name: str = "",
    outcome_md: str = "",
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    conv = diagnostics.get("conversion") or {}
    site = diagnostics.get("site_health") or {}
    code = diagnostics.get("code_review") or {}

    lines = [
        f"# ReadyForRobots daily report — {datetime.now(timezone.utc).date().isoformat()}",
        "",
        f"**Generated:** {now}",
        f"**Mission:** `{mission_name or 'harness-daily'}`",
        "",
        "## Executive summary (signups & revenue)",
        "",
    ]

    if conv.get("available"):
        lines.extend(
            [
                f"- **Signups (7d / total):** {conv.get('signups_7d', 0)} / {conv.get('signups_total', 0)}",
                f"- **Active paid subscriptions:** {conv.get('active_subscriptions', 0)} "
                f"(paid tier rows: {conv.get('paid_tier_users', 0)})",
                f"- **CRM accounts (7d / total):** {conv.get('crm_accounts_7d', 0)} / {conv.get('crm_accounts_total', 0)}",
                f"- **Founding waitlist:** {conv.get('founding_waitlist', 0)}",
            ]
        )
        funnel = conv.get("signup_funnel_7d") or {}
        start = funnel.get("signup_start", 0)
        complete = funnel.get("signup_complete", 0)
        saved = funnel.get("first_save", 0)
        s2c = f"{round((complete / start) * 100)}%" if start else "—"
        c2s = f"{round((saved / complete) * 100)}%" if complete else "—"
        lines.append(
            f"- **Signup funnel (7d):** start {start} → complete {complete} ({s2c}) "
            f"→ first-save {saved} ({c2s})"
        )
        lines.append("")
    else:
        lines.append(f"- Conversion DB metrics unavailable ({conv.get('reason') or conv.get('error') or 'no DB'})")
        lines.append("")

    priority = diagnostics.get("priority_actions") or []
    if priority:
        lines.append("**Top priorities for fundability:**")
        for i, action in enumerate(priority, 1):
            lines.append(f"{i}. {action}")
        lines.append("")

    lines.extend(["## Site health", ""])
    fly = site.get("fly_robots") or {}
    vercel = site.get("vercel_robots_proxy") or {}
    pipe = site.get("pipeline") or {}
    lines.append(
        f"- **Robots API (Fly):** {'OK' if fly.get('ok') else 'FAIL'} — "
        f"{fly.get('robots_count', '?')} robots, {fly.get('latency_ms', '?')}ms"
        + (" (stale seed)" if fly.get("stale") else "")
    )
    lines.append(
        f"- **Robots via Vercel proxy:** {'OK' if vercel.get('ok') else 'FAIL'} — {vercel.get('latency_ms', '?')}ms"
    )
    lines.append(
        f"- **Pipeline cache:** {'OK' if pipe.get('ok') else 'FAIL'} — "
        f"{pipe.get('leads_count', '?')} leads"
        + (" (pending rebuild)" if pipe.get("cache_pending") else "")
    )
    billing = site.get("billing") or {}
    lines.append(f"- **Stripe billing:** {'enabled' if billing.get('billing_enabled') else 'disabled or unknown'}")
    for pname, probe in (site.get("pages") or {}).items():
        status = "OK" if probe.get("ok") else "FAIL"
        lines.append(f"- **Page /{pname}:** {status} ({probe.get('latency_ms', '?')}ms)")

    site_alerts = site.get("alerts") or []
    if site_alerts:
        lines.extend(["", "**Site alerts:**"])
        for a in site_alerts:
            lines.append(f"- {a}")

    lines.extend(["", "## Code review", ""])
    lines.append(
        f"- **Public-read API violations:** {code.get('violation_count', 0)} "
        f"(auth helpers OK: {code.get('auth_helpers_ok')})"
    )
    for v in (code.get("violations") or [])[:8]:
        lines.append(f"  - `{v.get('file')}` → {v.get('endpoint')}")
    open_ch = code.get("open_conversion_challenges") or []
    if open_ch:
        lines.append("- **Open conversion challenges:**")
        for ch in open_ch[:5]:
            lines.append(f"  - #{ch.get('rank')} {ch.get('title')} ({ch.get('agent')})")

    lines.extend(["", "## Agent mission", ""])
    if outcome_md.strip():
        lines.append(outcome_md.strip())
    else:
        lines.append("(no outcome.md — run harness_daily.py or check GitHub Actions)")

    if snapshot:
        api = snapshot.get("api") or {}
        pal = api.get("pipeline") or {}
        lines.extend(
            [
                "",
                "## Snapshot metrics",
                f"- Pipeline leads: {pal.get('leads_count', '?')} · built_at: {pal.get('built_at') or 'n/a'}",
            ]
        )
        junk = (snapshot.get("intelligence") or {}).get("junk_reasons") or {}
        if junk.get("available"):
            lines.append(f"- Junk rate (sample): {junk.get('junk_rate', 0):.0%}")

    lines.extend(
        [
            "",
            "---",
            "Autonomous harness · [conversion board](docs/conversion_agent_challenges.md) · "
            "Reply in Cursor to scope the next revenue build.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness site/code/conversion diagnostics")
    parser.add_argument(
        "--check",
        choices=("all", "site", "code", "conversion"),
        default="all",
    )
    parser.add_argument("--api-base", default=FLY_API)
    parser.add_argument(
        "--fail-on-violations",
        action="store_true",
        help="Exit 1 if code convention violations exist",
    )
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    db = None
    if args.check in ("all", "conversion"):
        try:
            from scripts.harness_snapshot import _db_session

            db = _db_session()
        except Exception:
            db = None

    if args.check == "site":
        payload = check_site_health(api_base=args.api_base)
    elif args.check == "code":
        payload = check_code_conventions()
    elif args.check == "conversion":
        payload = check_conversion_metrics(db)
    else:
        payload = build_diagnostics(api_base=args.api_base, db=db)

    if db is not None:
        db.close()

    if args.stdout:
        print(json.dumps(payload, indent=2, default=str))
    else:
        healthy = payload.get("healthy", True)
        alerts = payload.get("alerts") or []
        print(json.dumps(payload, indent=2, default=str)[:4000])
        if alerts:
            print(f"\nAlerts ({len(alerts)}):", *alerts, sep="\n- ")

    if args.fail_on_violations and args.check in ("all", "code"):
        violations = payload.get("violation_count") or len(payload.get("violations") or [])
        if violations:
            return 1
    if args.check == "site" and not payload.get("healthy", True):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
