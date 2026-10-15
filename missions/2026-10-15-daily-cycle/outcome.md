# Outcome: Daily orchestrator cycle

**Date:** 2026-10-15
**Agent:** Orchestrator → ProductSurface
**Status:** built and gated; **branch pushed, not deployed, PR not yet opened** (see "Deploy" below)
**Type:** build (signup instrumentation, conversion board #20 extension)

## Headline

The signup funnel shows **87 `signup_start` → 1 `signup_complete`** over 7 days. The last `auth.users` row of any kind was created on **2026-09-25** (Google). We can't tell whether visitors **never click** a sign-in method or **click and fail**, because nothing is recorded between page load and account creation. So every signup fix so far, including yesterday's Google-primary change, has been a guess.

This cycle adds that missing measurement.

## Diagnosis (live DB, run this cycle)

`signup_start` by entry path, last 14 days (`site_analytics_events`):

| src / next | count |
|-----------|-------|
| `jobs_activate` → `/pipeline?src=jobs_activate` | **56** |
| `header_hero_boost` → `/` | 25 |
| `mobile_hero_boost` → `/` | 23 |
| `/pipeline?lead=…` deep links (incl. `resume=save`) | ~20 |
| misc (`/integrations/hubspot`, `/marketplace`, `/social`, …) | ~20 |

What we ruled out: the required "company name / robot category / ICP" gate on `/signup` only applies to `matchedUnlockIntent` (`src=pipeline_matched_unlock`). None of the top paths go through it, so it is **not** what's killing signups.

## What was built

1. **`readyforrobots-new/client/src/lib/siteAnalytics.ts`**
   - Two new funnel stages:
     - `signup_method_click`, with `method` = google / github / azure / email
     - `signup_blocked`, with `method`, a stable `reason` code, and the provider error message trimmed to 200 characters
   - **`funnel_sid`** is now sent on every funnel event. It is a per-tab id kept in sessionStorage, which survives the same-tab OAuth round-trip, so start → click → complete can be joined per session. This closes follow-up #3 from 2026-10-14.
2. **`readyforrobots-new/client/src/pages/Signup.tsx`**
   - Every OAuth button click and every email submit fires `signup_method_click` with `src`/`next`.
   - Every early return fires `signup_blocked`:
     - `auth_unavailable`
     - `full_name_missing`
     - `workspace_profile_incomplete`
     - `email_rejected`
     - `provider_error`
   - No UI or copy changes.
3. **`app/services/site_analytics_service.py`**
   - `/api/track/funnel` now accepts the two new stages (`SIGNUP_FUNNEL_STAGES`).
   - `signup_funnel_metrics` now returns `method_click`, `blocked`, `start_to_click_rate` and `click_to_complete_rate`.
4. **`scripts/harness_diagnostics.py`**: the 7d funnel now reports `method_click` and `blocked`, and the daily report gets a "Signup decision point" line.
5. **`tests/test_site_analytics.py`**: two new tests, covering the decision-point counts/rates and acceptance of the new stages.

**How to read it next cycle:**
- `method_click ≈ 0`: people leave without trying. Fix the page or the entry path, e.g. hero-boost visitors who haven't seen any value (value-first).
- `method_click ≫ complete` with few `blocked`: the failure happens off-site at the Google/GitHub consent step or the callback. Check the Supabase redirect allowlist and `AuthCallback`.
- `blocked` is high: the `reason` field names the gate to remove.

## Gates

| Gate | Result |
|------|--------|
| lead_quality_smoke + harness_diagnostics_unit + test_site_analytics | ✅ 240 passed |
| site_health_smoke | ✅ healthy |
| code_conventions (`--fail-on-violations`) | ✅ 0 violations |
| agent_verify ci | ⚠️ exit 1: only `find-stay: false`. **Same failure on unmodified `main`** (live-prod probe, also reported 2026-10-14). Not caused by this change. |
| pstack_release | ✅ exit 0 |
| `tsc --noEmit` | ✅ 0 errors |
| `vite build` (dummy Supabase public env, local only) | ✅ built |
| prettier (Signup.tsx) | ✅ formatted |

## Deploy

The brief pre-approves autonomous push and deploy, but the checked-in **CLAUDE.md guardrail says: "work on a branch, open a draft PR, stop. Bob merges."** CLAUDE.md takes precedence, so this cycle pushed branch `mission/2026-10-15-signup-click-instrumentation`. Nothing went to `main`, Vercel or Fly. **The draft PR could not be opened:** `gh` is not authenticated in this runner (no `GH_TOKEN`). Open it here: https://github.com/ugobe007/Ready_For_Robots/pull/new/mission/2026-10-15-signup-click-instrumentation

When it is merged, **deploy Fly (API) as well as Vercel**. Until the API accepts the new stages, the new events get a 400. That is harmless (the events are fire-and-forget) but they won't be recorded.

Pipeline cache: `built_at` 2026-10-15T14:04Z with 5 leads, so it is fresh and no refresh was run.

## Metrics (snapshot 2026-10-15T14:04Z; deltas vs 2026-10-14)

| Metric | 2026-10-14 | 2026-10-15 |
|--------|-----------|-----------|
| `signups_7d` | 0 | 0 |
| auth.users created, last 14d (email provider) | 0 | 0 (last user of any provider: 2026-09-25) |
| signup_funnel_7d start / complete / first_save | 82 / 1 / 1 | 87 / 1 / 1 |
| Stranded unconfirmed email accounts | 59 | 59 |
| junk_rate (400 sample) | 11.0% | **13.8%** (55/400, 98% vendor/OEM) |
| buyer_intent no_intent_rate | 21.9% | 13.2% |
| Unknown industry w/ signals | 954 | 955 |
| Pipeline surface | 5 HOT | 5 HOT |
| Site health / billing | healthy / live | healthy / live |

## Follow-ups

1. **P0 (Bob):** open a PR from the branch (link above), merge it, and deploy **Fly + Vercel**. Then read `method_click` / `blocked` by `src` after 2–3 days.
2. **P0 (operator, open since 2026-09-17):** set up custom SMTP (Resend) for Supabase Auth, then re-invite the 59 unconfirmed users.
3. **P1:** junk_rate is still climbing (6.5% → 11% → 13.8%), almost all vendor/OEM. Run the LeadQuality vendor-OEM live-flow sweep before it reaches the 5-lead proof surface.
4. **P2:** `header_hero_boost` / `mobile_hero_boost` (48 per 14 days) send visitors straight to `/signup` without showing any Job Cards. Use the new click data to decide whether to route them to the Jobs URL box first.
5. **Process:** pass `GH_TOKEN` to the daily-harness workflow so agents can open draft PRs. Also settle the conflict between the brief's "autonomous deploy" and CLAUDE.md's "draft PR, stop". Agents currently have to pick one.
