# V1 Pre-Traffic Test Pass

**Date:** 2026-08-17  
**Environment:** Production — `https://readyforrobots.com` (Vercel) + API `https://ready-2-robot.fly.dev` (Fly)  
**Operator:** Automated agent pass (curl + Playwright/Chrome)  
**Evidence (uncommitted):** `reports/v1_pretraffic_20260817/` · P0-A spine `reports/v1_p0a_spine_20260817/`  
**Content publishing:** **PAUSED** until remaining gates clear  

---

## Gate verdict

# **GO — all pre-traffic gates GREEN (2026-08-19)**

All technical pre-traffic gates are green (MATCH TRUTH, auth continuity, telemetry,
final pre-traffic smoke; production health OK). Opening external traffic / publishing
C04 is the operator's business decision.

Do **not** blur matcher-in-isolation with the production MATCH TRUTH gate.

| Release line | Status |
|--------------|--------|
| **MATCH TRUTH** | **PRODUCTION PASS** |
| **SUBMIT WORKFLOW** | **merged** (#13) / **production smoke PASS** (visual 2026-08-17) |
| **AUTH CONTINUITY** | **PASS** (2026-08-18) |
| **TELEMETRY** | **PASS** (2026-08-19) |
| **FINAL PRE-TRAFFIC SMOKE** | **PASS** (2026-08-19) |
| **TRAFFIC** | **operator GO/NO-GO** (gates clear) |

Architecture is unchanged: grounded profile first, then capability → workflow → requirements matching; unknowns stay unknown rather than inferred away.

Pre-traffic gates (simplified 2026-08-17 post–P0-A):

| # | Gate | Status |
|---|------|--------|
| 1 | **PROFILE PATH** — production uses `/api/robot-profile` + multi-product selection | **PASS** (P0-A 2026-08-17) |
| 2 | **MATCH TRUTH** — different robots, explainable requirement-level reasons | **PRODUCTION PASS** (2026-08-17) — #15 merged and live on Fly. Four-board verify: Vega manipulation/palletize + Novolex #8; Digit machine-load first, tote remains at rank 17; Origin transport/tote only; Neo scrub only. Every positive match has Why; unknowns kept; Origin/Neo Novolex name the unmet manipulation blocker. **M2 frozen.** |
| 2a | **SUBMIT WORKFLOW** — atomic reveal, stable layout, `/api/robot-job-search` | **merged** / **production smoke PASS** — Vercel bundle calls `/api/robot-job-search`; uncached Stretch ~14s researching UI then one reveal; picker keeps public market tape (not a personal board); bad URL recovers with zero matched jobs. |
| 3 | **FUNNEL** — See All → signup → same jobs; Qualify | **PASS** (2026-08-18) — See All → signup PASS; **auth continuity now verified** with a service-role-provisioned account. Single-product (Relay): research → JOBS → "See All" signup CTA → `/signup?next=/…` → return to `/` restores the exact same jobs workspace; a real session shows the signed-in state on that same workspace. Multi-product (Boston Dynamics → Stretch): SELECT persists and the Stretch workspace (42 jobs) restores across a full reload while signed in. Auth infra verified live (2026-08-17): providers **email + Google + GitHub**, `/signup` `/login` `/auth/callback` `/pipeline` all SPA 200, return-path plumbing unit-tested (10/10). **Caveat:** the third-party OAuth *consent* hop + PKCE `?code=` exchange is provider-side and was substituted by a service-role-established session (admin links can't complete a browser PKCE flow); the account + token issuance are verified server-side. A fully-live provider consent can be run via the Desktop pane if desired. |
| 4 | **TELEMETRY** — events + src/persona + shadow | **PASS** — verified 2026-08-17: `rdd_capabilities_viewed` emits (RobotJobsExperiment:627) → `/api/track/visit` ingests + stores; `persona` (via `funnelBase()`) survives ingest and is queryable; signup funnel `signup_start→complete→first_save` aggregates with rates; unknown funnel stage rejected 400. Note: `marketing_conversion_snapshot` uses Postgres `->>` (runs live via `/api/analytics`); SQLite can't round-trip that JSON operator (same limit as `pipeline_cache_store`). **Re-confirmed 2026-08-19 for the new workspace:** persona still travels on `/jobs/:slug` (legacy surface); the new `/` workspace has no slug → persona null (correct). Fixed one duplicate — `RobotJobsWorkspace.restore()` re-fired `rdd_capabilities_viewed` on reload/auth-return (single-product review state); now silent (PR #30). Verified live: research fires each funnel step once; reload fires only `experiment_view`, no repeat `capabilities_viewed`. |
| 5 | **FINAL PRE-TRAFFIC SMOKE** — prod health + core journey + deployed intelligence | **PASS** (2026-08-19) — frontend + backend `/health` 200; pipeline cache fresh (built_at current, 90 leads); deployed ontology live via real `/api/robot-job-search`: Carbon Robotics → `mobile`+`agriculture_task` + agriculture jobs (Tier-3), Relay → 34 transport jobs, Boston Dynamics → Stretch 42 jobs. Prod UI journey (single click after normal typing): FIND → research → PROFILE (evidence) → 34 JOBS → expanded job Why/Unknown → **QUALIFY** → QUALIFIED 0→1. No console errors. Note: automated type-then-instant-click can appear to need two clicks (controlled input + `disabled`-until-value button); a normal human cadence is single-click. |

**Release sequence (gate, not a suggestion):** #13 smoke (done) → re-land ranking (#15 merged) → four-board production verify (**PRODUCTION PASS**) → **M2 frozen** → auth continuity (**PASS** 2026-08-18) → telemetry (**PASS** 2026-08-19) → final pre-traffic smoke (**PASS** 2026-08-19) → **pre-traffic gate GREEN**. Publishing C04 / inviting external traffic is now the operator's GO/NO-GO call.

---

## P0-A — Profile path into production (2026-08-17)

### Root cause

Local Jobs UI (`RobotJobsExperiment` + `robotProfile.ts` + `RobotProfileCard`) already implemented:

```
URL → POST /api/robot-profile → product selection if needed → profile → job match
```

Production Vercel bundle (`index-FsiIAaXX.js`) still called **only** `/api/robot-job-match`. Cause: research-first client files were **local/uncommitted** (`robotProfile.ts`, `RobotProfileCard.tsx`, large `RobotJobsExperiment` diff) and never uploaded in the prior `vercel --prod` from `readyforrobots-new/`.

Host: **`readyforrobots.com` → Vercel project `ready-for-robots`** (API proxied to Fly). Not Fly-static for `/`.

### Deploy

| Item | Value |
|------|--------|
| Host | Vercel production alias `https://readyforrobots.com` |
| Deploy | `vercel --prod --yes` from `readyforrobots-new/` |
| Deployment | `ready-for-robots-d1cd8owlj-ugobe07-gmailcoms-projects.vercel.app` |
| Bundle | `/assets/index-C3RjlZqF.js` — `robot-profile` ×2, `needs_product_choice` ×1 |
| Title | `ReadyForRobots — Find Jobs for Your Robot` (was SIGNAL) |

### Spine retest (PROFILE PATH only — not matcher quality)

| Case | Outcome | Evidence |
|------|---------|----------|
| **Agility homepage** | **PASS** | Network: `POST …/api/robot-profile` then job-match; UI shows Digit / “Jobs for Digit” |
| **Boston Dynamics** | **PASS** | Network: `robot-profile` only (no premature job-match); UI “Select a Robot” / Spot · Stretch · Atlas (`needs_product_choice`) |
| **Bad/thin URL** (`example.com`) | **PASS** | Network: `robot-profile`; UI C-tier / “Still not enough evidence…” — no invented A-tier confidence |

Evidence: `reports/v1_p0a_spine_20260817/spine_results.json` + screenshots.

### P0-A gate

| Clause | Status |
|--------|--------|
| Live path is URL → robot-profile → (product choice) → profile → jobs | **PASS** |
| Prod bundle references `robot-profile` | **PASS** |
| Multi-product OEM asks which robot | **PASS** (BD) |
| Thin URL honest | **PASS** |
| Matcher differentiation / MATCH TRUTH | **not in scope** — still OPEN |

---

## Executive summary (full matrix — prior pass + P0-A delta)

Smoke works. **PROFILE PATH is live.** **MATCH TRUTH is PRODUCTION PASS** — four live boards are physically different and explainable. **AUTH CONTINUITY is PASS** (2026-08-18, service-role account: single + multi-product land-back). **TELEMETRY is PASS** (2026-08-19: persona intact; restore no longer re-fires `capabilities_viewed`, PR #30). **FINAL PRE-TRAFFIC SMOKE is PASS** (2026-08-19: prod health OK; deployed ontology live incl. Tier-3; core journey + Qualify works). **M2 is frozen.** Understanding extractors stay frozen. **All pre-traffic gates are GREEN — opening traffic / publishing C04 is the operator's GO/NO-GO call.**

---

## Method

| Layer | How |
|-------|-----|
| A Smoke | Playwright/Chrome against `readyforrobots.com`; GET route checks |
| B Logic | `POST /api/robot-profile` + `POST /api/robot-job-match` on Fly; UI screenshots/network |
| C Funnel | Network capture of `rdd_*` + `signup_start` (`src=v1_pretraffic` / `src=p0a_spine`) |
| Shadow fail-open | Code review + unit tests; prod Jobs now hits profile → shadow can accrue |

**Done (2026-08-18):** auth continuity — signup → return-to-same-jobs (single-product Relay) + multi-product restore (Boston Dynamics → Stretch) verified with a service-role-provisioned account. MATCH TRUTH production verify is done; M2 frozen.

---

## Six workflows (required matrix)

| Workflow | Must happen | Outcome | Notes |
|----------|-------------|---------|-------|
| **Agility homepage** | Resolve Agility → Digit → grounded profile → jobs | **PASS** | Profile path + MATCH TRUTH: machine-load/palletize dominate; legitimate tote work remains (first tote rank 17). |
| **Dexmate homepage** | Resolve Vega → manipulation-weighted jobs | **PASS** | CNC/palletize board; Novolex-class work at rank 8. Historical FAIL was pre-M2. |
| **Locus** | Origin → transport jobs, no bleed | **PASS** | Transport/tote/cart only; Novolex rejected with named manipulation blocker. Historical MISLEADING was pre-M2. |
| **Avidbots** | Neo → cleaning jobs | **PASS** | Scrub-only board; transport/manipulation rejected. Historical MISLEADING was pre-M2. |
| **Multi-product OEM** | Discover products → ask which robot | **PASS** (P0-A UI) | BD: Spot/Stretch/Atlas picker |
| **Bad/thin URL** | Honest B/C or unable-to-verify | **PASS** | example.com recover / C-tier |

---

## Full test matrix

Outcomes: **PASS** · **FAIL** · **MISLEADING** · **BLOCKED**

### A. Smoke

| ID | Case | Outcome | Evidence |
|----|------|---------|----------|
| A1 | New visitor lands on `/` | **PASS** | Desktop screenshots; CTA Find Jobs |
| A2 | Job ticker / live board visible | **PASS** | Prior + P0-A home |
| A3 | Submit URL → research → jobs | **PASS** | Profile path in network |
| A4 | Open job / Qualify This Job | **PASS** | Prior pass |
| A5 | See All → signup | **PASS** (to signup page) | Prior |
| A6 | Signup → return to same robot/jobs | **PASS** (2026-08-18) | Single-product (Relay): anon research → JOBS → "See All 34 matches" signup CTA → `/signup?next=/…` → return to `/` restored the exact same Relay Robotics jobs workspace (34 jobs). With a real session established, "SIGN IN" is gone on that same workspace. |
| A7 | Returning user continuity | **PASS** (2026-08-18) | Multi-product (Boston Dynamics → SELECT Stretch → 42 jobs): full page reload restored the exact Stretch workspace (42 jobs), still signed in — same restoration mechanism as post-auth landing. |
| A8 | `/jobs` index | **PASS** | Prior |
| A9 | Legacy `/experiment` | **PASS** | Prior |
| A10 | Bad URL | **PASS** | P0-A spine |
| A11 | Unreachable host | **PASS** (API) | Prior |
| A12 | Slow site tolerance | **PASS** | Prior |
| A13 | Desktop viewport | **PASS** | Prior |
| A14 | Mobile viewport | **PASS** | Prior |
| A15 | Document title / SEO claim | **PASS** (P0-A) | Title is Jobs, not SIGNAL |
| A16 | Loading silence | **PASS** | Prior |

### B. Logic

| ID | Case | Outcome | Evidence |
|----|------|---------|----------|
| B1 | Agility → Digit grounded | **PASS** (UI+API) | P0-A profile card / Digit |
| B2 | Agility jobs plausible for Digit | **PASS** | Production 2026-08-17: gripper/pallet top-12; tote available at rank 17 |
| B3 | Dexmate → Vega + manipulation jobs | **PASS** | Production 2026-08-17: gripper 7 + pallet 5; Novolex #8 |
| B4–B6 | Locus / Avidbots / bleed / boards | **PASS** | Origin transport/cart only; Neo scrub only; Novolex blocked for both |
| B6 | Multi-product ask-which-robot | **PASS** | P0-A BD UI |
| B7 | Thin URL honest uncertainty | **PASS** | P0-A |
| B12 | Job boards materially different | **PASS** | Four-board production verify 2026-08-17 |
| B13 | Prod UI uses Understanding profile | **PASS** | Bundle + network `robot-profile` |

### C. Funnel / instrumentation

| ID | Event / check | Outcome | Evidence |
|----|---------------|---------|----------|
| C1–C3, C6–C8, C10 | Core funnel + src | **PASS** | Prior |
| C4 | `rdd_capabilities_viewed` | **PASS** | Emit wired (RobotJobsExperiment:627 → `trackMarketingEvent` → `/api/track/visit`); ingest + storage verified (event stored as `visit`, `payload.path=/event/rdd_capabilities_viewed`) |
| C9 | `persona` survival | **PASS** | `funnelBase()` attaches `persona` on `/jobs/:slug`; verified persisted + queryable in event payload (`integrator`, `oem`) across visit + funnel events |
| C11 | Shadow logging fail-open | **PASS** (code) | Jobs UI now calls profile → can feed shadow |
| C12 | Qualify copy | **PASS** | Prior |

#### Telemetry — ingest verification (2026-08-17)

Verified end-to-end against the local API (no writes to production analytics):

| Check | Result |
|-------|--------|
| `POST /api/track/visit` `path=/event/rdd_capabilities_viewed` | **PASS** — `{status: tracked}`, row stored as `visit` |
| `persona` in payload survives ingest | **PASS** — queryable: `integrator`, `oem` |
| `POST /api/track/funnel` `signup_start` / `signup_complete` / `first_save` | **PASS** — each stored; `signup_funnel_metrics` aggregates with rates |
| Unknown funnel stage | **PASS** — rejected `400 Unknown funnel stage` |
| Emit wiring | **PASS** — `capabilities_viewed` (RobotJobsExperiment:627) + `funnelBase()` persona (line 387) |

Reproduce: `POST /api/track/visit {"path":"/event/rdd_capabilities_viewed","persona":"oem","step":"capabilities_viewed"}` then read `site_analytics_events`. `marketing_conversion_snapshot` (Postgres `->>`) is exercised live via `GET /api/analytics`.

### Auth / qualify

| Workflow | Outcome |
|----------|---------|
| Auth return after signup | **PASS** (2026-08-18; service-role account) — single + multi-product land-back verified; provider consent hop substituted by service-role session |
| Qualify request confirmation | **PASS** |

#### Auth continuity — infra verification (2026-08-17)

Everything except the live authenticated round trip is verified. Reproduce:

```bash
SB=https://lmoyydlhlgdyqbxkmkuz.supabase.co
ANON=<VITE_PUBLIC_SUPABASE_ANON_KEY from fly.toml>
curl -sS "$SB/auth/v1/health" -H "apikey: $ANON"          # GoTrue v2.195.0
curl -sS "$SB/auth/v1/settings" -H "apikey: $ANON"        # email+google+github true; disable_signup false
for p in /signup /login /auth/callback /pipeline; do
  curl -s -o /dev/null -w "$p %{http_code}\n" "https://readyforrobots.com$p"   # 200
done
```

| Check | Result |
|-------|--------|
| GoTrue reachable | **PASS** — `v2.195.0` |
| Providers enabled | **PASS** — `email`, `google`, `github` (signup enabled) |
| `mailer_autoconfirm` | **off** — email path needs a real inbox to click the link |
| SPA auth routes serve app | **PASS** — `/signup` `/login` `/auth/callback` `/pipeline` = 200 |
| Post-auth return-path resolver | **PASS** — `signupWorkflowPath` + `authNext` + `resume=save` unit-tested (10/10 vitest) |
| Live A6/A7 round trip | **PASS** (2026-08-18) — service-role account: admin-created a confirmed user, minted a session, verified single-product land-back (Relay, 34 jobs) + multi-product restore (Boston Dynamics → Stretch, 42 jobs) across reload, signed-in. Provider *consent* hop is provider-side (substituted by service-role session; run live via Desktop if a 100% end-to-end provider trace is required). |

**Fastest agent-driven unblock:** add `SUPABASE_SERVICE_ROLE_KEY` — then `POST /auth/v1/admin/users` (`email_confirm: true`) + `POST /auth/v1/admin/generate_link`, drive `/auth/callback?next=/pipeline?lead=…&resume=save`, and assert save completes and a re-visit lands on the same workspace/robot. Alternative: complete a Google/magic-link login in the Desktop pane.

---

## Punch list (remaining)

### P0 — still blocking traffic

1. ~~Deploy Jobs frontend that calls `/api/robot-profile`~~ **DONE (P0-A)**  
2. ~~**MATCH TRUTH / M2**~~ **PRODUCTION PASS** — #15 live; four boards verified; **M2 frozen**. No fifth robot, no ranking tweaks, no new scoring ideas.
2a. ~~**Submit workflow**~~ **merged / production smoke PASS** — atomic reveal, stable layout, profile cache. Public market tape during research/picker is intended; personal boards reveal once.  
3. ~~Multi-product OEM ask on live UI~~ **DONE (P0-A)**  
4. ~~Dexmate → Vega~~ **PASS** (production MATCH TRUTH)

### P1

5–8. ~~Class / bleed / product_name alignment~~ **PASS** on the four production boards (M2 frozen)
9. ~~Replace SIGNAL document title~~ **DONE**  
10. ~~Prove auth return with controlled account~~ **PASS** (2026-08-18) — service-role account: single-product (Relay) land-back + multi-product (Boston Dynamics → Stretch) restore verified signed-in (see Auth continuity — infra verification)  

### P2

11–15. Health probe; ~~capabilities_viewed verification~~ **DONE**; ~~persona~~ **DONE**; shadow accrual confirm (needs traffic); keep Playwright script  

---

## Traffic policy

| Action | Status |
|--------|--------|
| Content / LinkedIn publishing (incl. C04) | **STOP** |
| Invite external traffic | **NO** |
| Understanding Phase 4 extractors / Blind retune | **DO NOT OPEN** |
| **M2 matcher** | **FROZEN** after **MATCH TRUTH — PRODUCTION PASS** |
| Next step | ~~Auth continuity~~ **PASS** → ~~telemetry~~ **PASS** → ~~final pre-traffic smoke~~ **PASS** → **operator GO/NO-GO to open traffic / publish C04** |

---

## Reproduce

```bash
# Confirm prod bundle has profile path
curl -sS https://readyforrobots.com/ | rg -o '/assets/index-[^"]+\.js|<title>[^<]+</title>'
# count robot-profile in that asset (expect ≥1 after P0-A)

curl -sS -X POST https://ready-2-robot.fly.dev/api/robot-profile \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://agilityrobotics.com"}'

curl -sS -X POST https://ready-2-robot.fly.dev/api/robot-profile \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://bostondynamics.com"}'
```

Evidence: `reports/v1_p0a_spine_20260817/` (do not commit `reports/`).
