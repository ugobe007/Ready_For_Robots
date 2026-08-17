# V1 Pre-Traffic Test Pass

**Date:** 2026-08-17  
**Environment:** Production — `https://readyforrobots.com` (Vercel) + API `https://ready-2-robot.fly.dev` (Fly)  
**Operator:** Automated agent pass (curl + Playwright/Chrome)  
**Evidence (uncommitted):** `reports/v1_pretraffic_20260817/` · P0-A spine `reports/v1_p0a_spine_20260817/`  
**Content publishing:** **PAUSED** until remaining gates clear  

---

## Gate verdict

# **NOT READY for traffic**

Pre-traffic gates (simplified 2026-08-17 post–P0-A):

| # | Gate | Status |
|---|------|--------|
| 1 | **PROFILE PATH** — production uses `/api/robot-profile` + multi-product selection | **PASS** (P0-A 2026-08-17) |
| 2 | **MATCH TRUTH** — different robots, explainable requirement-level reasons | **PROTOTYPED** locally (M2 2026-08-17) — not production-cleared until Fly+Vercel ship `requirement_v1` and a human reviewer agrees ~8/10 |
| 3 | **FUNNEL** — See All → signup → same jobs; Qualify | **PARTIAL** — See All → signup PASS; auth return still BLOCKED |
| 4 | **TELEMETRY** — events + src/persona + shadow | **PARTIAL** — src/events mostly PASS; profile-path events newly available; persona BLOCKED |

**Until MATCH TRUTH clears (and auth return is proven): keep traffic paused. Do not publish C04 / invite external traffic.**

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

Smoke works. **PROFILE PATH is now live** (was the critical UI/API split). **MATCH TRUTH remains open:** heuristic job boards can still look alike across robots — do not invite traffic on profile wiring alone. Auth return still needs a controlled account. M2 (requirements matching, e.g. Novolex) is the **next mission**, unlocked for prototyping against grounded Tier A/B/C profiles — Understanding extractors stay frozen.

---

## Method

| Layer | How |
|-------|-----|
| A Smoke | Playwright/Chrome against `readyforrobots.com`; GET route checks |
| B Logic | `POST /api/robot-profile` + `POST /api/robot-job-match` on Fly; UI screenshots/network |
| C Funnel | Network capture of `rdd_*` + `signup_start` (`src=v1_pretraffic` / `src=p0a_spine`) |
| Shadow fail-open | Code review + unit tests; prod Jobs now hits profile → shadow can accrue |

**Not done:** full email signup / return-to-jobs (BLOCKED — no operator-controlled inbox). MATCH TRUTH / Phase 4 matcher rebuild (deferred to M2 mission).

---

## Six workflows (required matrix)

| Workflow | Must happen | Outcome | Notes |
|----------|-------------|---------|-------|
| **Agility homepage** | Resolve Agility → Digit → grounded profile → jobs | **PASS** (spine) / MATCH TRUTH open | P0-A: profile path + Digit UI. Job quality still heuristic. |
| **Dexmate homepage** | Resolve Vega → manipulation-weighted jobs | **FAIL** (prior) | Not re-run in P0-A spine; Understanding frozen — M2/honest recover |
| **Locus** | Origin → transport jobs, no bleed | **MISLEADING** (prior match) | Profile path now available; matcher still open |
| **Avidbots** | Neo → cleaning jobs | **MISLEADING** (prior match) | Profile API was strong; UI now can show it |
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
| A6 | Signup → return to same robot/jobs | **BLOCKED** | Needs controlled email/OAuth |
| A7 | Returning user continuity | **BLOCKED** | Same as A6 |
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
| B2 | Agility jobs plausible for Digit | **OPEN** (MATCH TRUTH) | Not claimed by P0-A |
| B3 | Dexmate → Vega + manipulation jobs | **FAIL** | Prior; frozen Understanding |
| B4–B6 | Locus / Avidbots / bleed / boards | **OPEN** / prior MISLEADING | Matcher mission |
| B6 | Multi-product ask-which-robot | **PASS** | P0-A BD UI |
| B7 | Thin URL honest uncertainty | **PASS** | P0-A |
| B12 | Job boards materially different | **FAIL** / OPEN | MATCH TRUTH — M2 |
| B13 | Prod UI uses Understanding profile | **PASS** | Bundle + network `robot-profile` |

### C. Funnel / instrumentation

| ID | Event / check | Outcome | Evidence |
|----|---------------|---------|----------|
| C1–C3, C6–C8, C10 | Core funnel + src | **PASS** | Prior |
| C4 | `rdd_capabilities_viewed` | **READY TO VERIFY** | Profile path live; re-check on next funnel pass |
| C9 | `persona` survival | **BLOCKED** | Needs persona slug session |
| C11 | Shadow logging fail-open | **PASS** (code) | Jobs UI now calls profile → can feed shadow |
| C12 | Qualify copy | **PASS** | Prior |

### Auth / qualify

| Workflow | Outcome |
|----------|---------|
| Auth return after signup | **BLOCKED** (still needs controlled account before traffic) |
| Qualify request confirmation | **PASS** |

---

## Punch list (remaining)

### P0 — still blocking traffic

1. ~~Deploy Jobs frontend that calls `/api/robot-profile`~~ **DONE (P0-A)**  
2. **MATCH TRUTH / M2** — differentiated, explainable jobs (requirements matching; Novolex-shaped example). **Next mission — do not patch old heuristic to fake differentiation.**  
3. ~~Multi-product OEM ask on live UI~~ **DONE (P0-A)**  
4. Dexmate → Vega (may stay honest recover until Understanding reopen rule trips)

### P1

5–8. Class / bleed / product_name alignment — largely M2  
9. ~~Replace SIGNAL document title~~ **DONE**  
10. Prove auth return with controlled account  

### P2

11–15. Health probe, capabilities_viewed verification, persona, shadow accrual confirm, keep Playwright script  

---

## Traffic policy

| Action | Status |
|--------|--------|
| Content / LinkedIn publishing (incl. C04) | **STOP** |
| Invite external traffic | **NO** |
| Understanding Phase 4 extractors / Blind retune | **DO NOT OPEN** |
| **M2 matcher prototyping** | **ALLOWED** against grounded A/B/C profiles (propagate unknowns) — see milestones |
| Next step | M2 MATCH TRUTH mission → re-run gates → then consider traffic |

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
