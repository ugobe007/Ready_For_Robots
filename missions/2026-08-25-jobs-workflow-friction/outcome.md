# Outcome — Jobs workflow friction smoke (post PR #128)

**Date:** 2026-08-25  
**Type:** research  
**Status:** observe complete. Next act recommended, not shipped.

## Production truth

- Vercel `https://readyforrobots.com` → `/assets/index-FvmGmueR.js` (2.2 MB). Canaries: `Jobs for`, `openvla.github.io`, `π0.5`, `gr00t-n1_5`, Supabase host.
- Fly `/health` 200. GHA deploy-frontend for #128: 47s, not a skip-green lie.
- Compiled memory `next_mission`: `jobs-workflow-smoke` — this cycle.

## What still works

| Step | Result |
|------|--------|
| Header `/` | JOBS / ABOUT / SIGN IN. No Pipeline. |
| Catalog FIND | Fourier, Boston Dynamics, Richtech, Dexmate listings in <3s. Lineup pages 3 SKUs. |
| Fourier N1 | 5 Conditional Job Cards. Task model Unknown. Links OpenVLA, π0.5, GR00T N1.5. |
| Next | `/signup?next=/crm?src=jobs_activate&submission=…&src=jobs_activate`. Signup restates 3 N1 jobs. Google/GitHub look live. |
| Value-first | Anonymous user sees employer / workplace / work before signup. |

`POST /api/robot-job-search` with `{url, product}` (not `product_name`): N1 / Stretch / Vega return `requirement_v1` jobs with task-model lookups in ~4–6s.

## Ranked weak points

### P0 — Hospitality SKU never reaches Job Cards

Richtech **ADAM** is catalogued as `service_robot` (“autonomous bar and F&B robot”). Search returns `state=qualify_robot`, 0 jobs, `needs_class_choice=true`. UI asks “What kind of robot is ADAM?” with humanoid / AMR / cobot / quadruped / scrubber — **no service class**. Copy says the page was not enough to name the class, which is false: listing already says SERVICE ROBOT.

The corpus already has the work: `serve` (3), `food_prep` (3), `beverage` (2) including “Mix and serve cocktails at the bar.” ADAM has facts (`product_class`, payload, runtime) but zero *work* capabilities (`food_prep` / `beverage_prep`), so `classify_zero_state` returns `insufficient_profile_evidence` and we open the class picker.

**Needed improvement:** Ground catalog `service_robot` (and ADAM-like SKUs) to existing serve/beverage/food_prep tapes. Do not invent new jobs. Do not ask the operator to call a bartender a humanoid.

### P1 — Every manipulator/humanoid opens on the same CNC job

Fourier N1, Boston Dynamics Stretch, and Dexmate Vega all list **Fulcrum Technologies CNC laser load/unload** as job 00001. Stretch is a warehouse case/pallet robot. Five N1 cards are all machine-tending. Qualification is Conditional (honest) but the *work* is not robot-specific enough to believe.

Matcher retune is frozen this cycle. Treat as the next QUALIFY-integrity mission after hospitality grounding — still requirement match, not SIGNAL rank.

### P2 — Copy: 5 selected vs 3 free

Job list: “5 selected. Next opens CRM with your checked jobs — 3 opportunities on free.” Signup correctly shows 3. The 5-vs-3 jump is unexplained on step 02.

### P3 — FIND chrome before a robot URL

Anonymous `/` already shows **0141 JOBS FOUND** (corpus feed, ~12 rows). That is not the 3-SKU lineup cap. It proves work exists, but it is not qualified for *this* robot. Three Start jobs CTAs. Sidebar copy reads like operator notes (“run each SKU by itself”).

### P4 — Observability hole

This environment has no `DATABASE_URL`, so conversion telemetry is unavailable. Pipeline cache probe: 5 leads, ~7s — SIGNAL path, not Jobs core.

## Recommended next build

**Slug:** `jobs-path-followup`  
**One act:** ADAM / `service_robot` → existing serve/beverage jobs, or an honest corpus-gap (not a humanoid class quiz).

## Verify

- Harness diagnostics `--check all`: site+code healthy; conversion skipped (no DB).
- Vercel production smoke: custom domain matches new bundle.
- Browser: production Fourier N1 card + signup; Richtech 3-at-a-time picker; ADAM class picker after search.

## Out of scope kept

No matcher ranking tweaks. No invented hospitality SKUs. No SIGNAL hop.
