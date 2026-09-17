# Outcome — Daily orchestrator cycle

**Date:** 2026-09-17
**Agent:** Orchestrator
**Status:** diagnosis complete — **no code shipped** (root cause is a Supabase dashboard/SMTP setting, not application code)
**Type:** build → converted to diagnosis

## Headline

**Email sign-in has been a black hole since 2026-08-28. 57 real people asked for a sign-in link and not one of them ever got in.**

Google OAuth still works. The magic-link path — the only email option on `/signup` — creates the account then silently fails to deliver. The harness has been reporting "Zero new signups in 7 days" for weeks and recommending conversion/copy missions; the alert was right, the recommendation was aimed at the wrong layer.

## Ground truth (from `auth.users`, not the event table)

| Provider | Confirmed | Count |
|----------|-----------|-------|
| email | **no** | **57** |
| google | yes | 12 |
| email | yes | 9 |

- All 57 stranded rows have `confirmation_sent_at` **set** and `email_confirmed_at` / `last_sign_in_at` **NULL** — Supabase accepted and attempted the send; nobody ever clicked through.
- Last successful email confirmation ever: **2026-08-28**. Six email signups confirmed fine Aug 18–28, then it stops dead.
- Stranded by month: **43 in August, 14 in September.**
- `user_profiles` last row: **2026-08-19**. A month of zero activated accounts.

## The redirect chain is NOT the problem (ruled out)

I suspected the Aug 28 "Port Kare Macintosh landing onto `/`" commit broke the callback, since PKCE exchange only runs on `/signup` and `/auth/callback`, and `authNext.ts` documents Supabase dumping users on Site URL `/`. Tested it against live Supabase instead of assuming:

```
# ours — preserved, so it IS allowlisted
location: https://readyforrobots.com/auth/callback?next=%2Fpipeline#error=access_denied&error_code=otp_expired...
# control, deliberately non-allowlisted — falls back to Site URL
location: https://readyforrobots.com#error=access_denied&error_code=otp_expired...
```

The allowlist honors `/auth/callback?next=…`, that route returns 200 in prod, and `AuthCallback.tsx` does the exchange. Routing is healthy. **The failure is email delivery.**

Corroborating: `mailer_autoconfirm: false` (confirmation click required), and the most recent commit on `main` is `019c2239 docs(env): add RESEND_API_KEY template variable` — someone was already walking toward this and stopped at the template.

## Operator action required (I cannot do this from the harness)

Configuring Supabase Auth SMTP needs dashboard / service-role access that this environment does not have. In priority order:

1. **Wire custom SMTP** in Supabase → Auth → Emails (Resend key already templated in `.env.example`). Supabase's built-in email sender is rate-limited to a few messages/hour and in current versions restricts delivery to project team members — which matches a clean break with zero successes.
2. **Recover the 57.** They are real inbound intent with addresses on file, sitting in `auth.users` unconfirmed. Once SMTP is live, re-invite them; do not let them expire silently.
3. **Add a delivery canary** so this cannot regress unnoticed for a month: assert in `harness_diagnostics.py` that `count(auth.users where email_confirmed_at is null and created_at > now() - 7d)` is not the *entire* recent cohort, and alert on a zero-confirmation streak.

## Why I shipped no code

The mission pre-approves autonomous commits/deploys "when gates pass," and the brief asked for one conversion build. I deliberately did not ship one: every candidate change (reordering Google above email, honest copy on the email path) would have been cosmetic decoration over a broken pipe, and would have muddied the diagnosis. The single highest-value output of this cycle is the named, dated root cause plus 57 recoverable leads. Fixing signups here means turning on SMTP, not editing `Signup.tsx`.

Gate run: `code_conventions` **pass** (0 violations, all sub-gates ok). Remaining gates not run — no diff to verify. Working tree clean apart from this mission directory.

## Correction to a standing assumption

`docs/conversion_agent_challenges.md` lists all 21 conversion challenges as ✅ Done, and prior cycles (`2026-07-17`, `2026-07-14`) attributed the flat funnel to `signup_start` denominator inflation. That inflation is real — `signup_start` fires on `/signup` mount and on route-guard bounces (observed payloads with `next: /admin`, `next: /intelligence`), while `signup_complete` is latched **once per browser forever** in `localStorage`, so the two counters cannot be divided. But it is **not** the explanation this time. `auth.users` shows the funnel genuinely floored at the email step. The instrumentation noise masked a hard outage for ~3 weeks.

## Metrics

| Metric | Value |
|--------|-------|
| `signups_7d` | 0 |
| `signup_funnel_7d` | start 82 · complete 1 · first_save 0 (counters not divisible — see above) |
| Stranded unconfirmed email accounts | **57** |
| Last confirmed signup (any provider) | 2026-08-28 |
| junk_rate | 6.5% (26/400), 100% vendor/OEM |
| Pipeline | `built_at` 14:02 today, 5 leads — fresh, no refresh needed |
| Site health | healthy; all pages 200; billing live |

## Follow-ups

1. **P0 (operator):** Supabase custom SMTP via Resend → re-invite the 57.
2. **P0 (harness):** zero-confirmation-streak alert so this regresses loudly, not silently.
3. **P1:** give `signup_start`/`signup_complete` a shared `session_id` and drop the lifetime `localStorage` latch on the numerator, so the funnel becomes readable at all.
4. **P1:** exclude route-guard bounces (`next=/admin`, `/intelligence`) from `signup_start`.
5. **P2:** `/signup` shows "Microsoft sign in coming soon" twice (one a dead disabled button) while `/login` offers Microsoft and would error — tidy once signups flow.
6. **P2:** `pipeline_surface` has only 5 leads; thin proof surface for anonymous visitors.
