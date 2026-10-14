# Outcome — Daily orchestrator cycle

**Date:** 2026-10-14
**Agent:** Orchestrator → ProductSurface
**Status:** shipped (signup decision-point fix + email-delivery canary)
**Type:** build

## Headline

**Nobody has created an account in over three weeks.** `auth.users` has no new rows of any kind (Google, GitHub or email) since the week of 2026-09-21. Over the same 7 days, 82 `signup_start` events fired. The biggest source is `jobs_activate` (23): people who had just seen Job Cards, which is our peak-intent moment. They reach `/signup` and leave without trying.

## Diagnosis (live probes, not assumptions)

| Check | Result |
|-------|--------|
| Prod bundle has Supabase URL + anon key | ✅ `lmoyydlhlgdyqbxkmkuz.supabase.co` baked in |
| `/auth/v1/settings` | google ✅ github ✅ email ✅ · `mailer_autoconfirm: false` · azure ❌ |
| `/auth/v1/authorize?provider=google` / `github` | 302 to Google / GitHub ✅ |
| Email confirmations since 2026-08-28 | **1** (2026-09-19). Still broken: SMTP not wired (the P0 from the 2026-09-17 cycle is still open) |
| Unconfirmed email accounts (stranded) | **59** (was 57) |

`signup_start` by source (7d): `jobs_activate` 23 · `header_hero_boost` 18 · `mobile_hero_boost` 10 · `/pipeline?lead=…` deep links ~20 · misc.

The signup card was asking visitors to choose among five options. Three of them were dead or unreliable: a "Microsoft sign in coming soon" banner, a second disabled "Microsoft sign in coming soon" button, and an email link that doesn't arrive. The one path that does work (Google) was styled the same as everything else.

## What shipped

1. **`readyforrobots-new/client/src/pages/Signup.tsx`**
   - **Google is now the single filled primary button** (emerald fill). GitHub stays as the secondary.
   - **Removed both dead "Microsoft sign in coming soon" elements** (follow-up #5 from 2026-09-17).
   - Added an honest line under the email form: *"Link slow to arrive? Google signs you in instantly — same account, nothing lost."*
   - **"Check your email" state now has a "Skip the wait — continue with Google" button.** This is exactly where the 59 stranded email users got stuck.
   - The Jobs (`jobs_activate`) path keeps its kept-jobs list and its "Keep these jobs" heading. Value-first order is unchanged.
2. **`scripts/harness_diagnostics.py`**: adds an **email delivery check** (follow-up #2 from 2026-09-17). Conversion diagnostics now report `auth_email_14d {created_14d, confirmed_14d, unconfirmed_total}` from `auth.users`. If 3 or more email signups in 14 days produce 0 confirmations, it raises a named P0 alert ("Email sign-in delivery broken…") instead of the generic "zero signups" message. Tested against live data: 0 created / 0 confirmed / 59 unconfirmed. It is quiet right now only because nobody has even tried email in 14 days.

## Gates

| Gate | Result |
|------|--------|
| lead_quality_smoke + harness_diagnostics_unit | ✅ 235 passed |
| site_health_smoke | ✅ healthy |
| code_conventions (`--fail-on-violations`) | ✅ 0 violations |
| agent_verify ci | ✅ exit 0 (`find-stay: false` is a live-prod probe from before this change) |
| pstack_release | ✅ exit 0 |
| `tsc --noEmit` (Signup.tsx) | ✅ no errors |

Pipeline cache: `built_at` 2026-10-14T14:03Z, 5 leads, so no refresh was needed.

## Metrics (before; after measurable next cycle)

| Metric | 2026-09-17 | 2026-10-14 |
|--------|-----------|-----------|
| `signups_7d` (user_profiles) | 0 | 0 |
| auth.users created, last 14d (all providers) | — | **0** |
| signup_funnel_7d start / complete / first_save | 82 / 1 / 0 | 82 / 1 / 1 |
| Stranded unconfirmed email accounts | 57 | 59 |
| junk_rate (400 sample) | 6.5% | **11.0%** (44/400, 98% vendor/OEM) |
| buyer_intent no_intent_rate | — | 21.9% |
| Unknown industry w/ signals | — | 954 |
| Pipeline surface | 5 HOT | 5 HOT |
| Site health / billing | healthy / live | healthy / live |

**Watch next cycle:** auth.users Google rows created after this deploy, and signups by `src=jobs_activate`.

## Follow-ups

1. **P0 (operator, still open since 2026-09-17):** Supabase Auth → custom SMTP (Resend), then re-invite the **59** unconfirmed email users. No code change can fix this.
2. **P1:** junk_rate has nearly doubled (6.5% → 11%) and is almost all vendor/OEM. Run the LeadQuality vendor-OEM live-flow sweep before it reaches the 5-lead proof surface.
3. **P1:** `signup_start` and `signup_complete` share no session_id, and the lifetime localStorage latch makes the funnel ratio unreadable. Use auth.users (now in diagnostics) as ground truth until this is fixed.
4. **P2:** `header_hero_boost` / `mobile_hero_boost` send 28 low-intent clicks a week straight to `/signup` from `/`, which skips Job Cards. Consider routing them to the Jobs URL box first (value-first).
