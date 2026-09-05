# Mission: Fundability priorities — P0 site, P1 checkout, P2 #20 funnel

Type: build
Agent: ProductSurface / PipelineHealth

## Goal

Work the daily fundability priority list: (P0) Robots/Pipeline API timeouts, (P1) Pro checkout, (P2) conversion board #20 signup funnel instrumentation.

## Outcome

### P0 — Site API timeouts: FALSE ALARM, probe hardened
- Live checks: `/api/robot-companies` 0.26s, `/api/leads/pipeline` 0.16s, `/api/humanoid/robots` 0.27–0.60s — all 200 OK.
- `fly.toml` already has `auto_stop_machines = false` + `min_machines_running = 1`, so no cold start. The daily "read operation timed out" was transient saturation of the single shared-CPU web machine during the 14:00 UTC heavy-job window (secondary pass + cache rebuild), hit by the 15s probe.
- Fix: `_fetch_probe` now retries once (2s backoff) on timeout/5xx before declaring failure, so a one-off blip no longer raises a P0 fundability alert. Split into `_fetch_probe` (retry wrapper) + `_fetch_probe_once`.

### P1 — Pro checkout: WORKING, no bug
- `/api/billing/config` → `enabled:true, pro_available:true, premium_available:true`, prices set. `/api/billing/checkout` correctly 401s without auth.
- Frontend flow verified: `beginCheckout` → `startCheckout` → Stripe redirect; post-auth resume via `?upgrade=` effect on `/pricing`; `navigateAfterAuth` preserves the query via full-page `window.location.replace`.
- The "P1: fix Pro checkout" line is a **heuristic** (`active_subscriptions == 0 AND signups_total > 5`), not a detected defect. The real problem is conversion (signups don't upgrade) — which #20 now measures.

### P2 #20 — Signup funnel instrumentation: SHIPPED
- Events: `signup_start` (/signup view), `signup_complete` (auth callback, once per browser via localStorage guard), `first_save` (first saved lead, once per browser).
- Backend: `POST /api/track/funnel` with stage validation; `signup_funnel_metrics()` (counts + step rates: start→complete, complete→save, start→save); exposed in `/api/analytics` and the daily report exec summary.
- Frontend: `trackSignupStart/Complete/FirstSave` in `siteAnalytics.ts`; wired into `Signup.tsx`, `AuthCallback.tsx`, `Pipeline.tsx handleSaveLead`.
- Tests: aggregation + zero-safe rates (`tests/test_site_analytics.py`). Deployed + verified in prod (valid stage tracked, invalid → 400, funnel slice live in `/api/analytics`).

## Follow-ups
1. After a few days of traffic, read the funnel in the daily report: if start→complete is the drop, attack signup friction; if complete→first_save drops, attack activation (first-save guide, pipeline onboarding).
2. Add a funnel widget to the admin `SiteMetricsPanel` for at-a-glance monitoring.
3. Revenue: since checkout works, the lever for paid conversion is activation depth + upgrade prompts at the saved-leads limit, not the checkout mechanics.
