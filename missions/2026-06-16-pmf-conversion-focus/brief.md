# Mission: PMF conversion focus

**Date:** 2026-06-16
**Agent:** Orchestrator → ProductSurface (primary)
**Status:** planned
**Type:** build

## Goal

Align the product surface and agent harness with PMF: **ReadyForRobots is the automated sales pipeline for robot companies** — sign up → automate funnel → native CRM or HubSpot.

This mission is a **directive mission**: update docs and pick the next highest-impact build that moves robot OEMs/integrators through signup and activation. Do not treat generic robotics content or lead-volume metrics as success.

## Acceptance criteria

- [ ] `docs/product_market_fit.md` exists and is linked from AGENTS.md, CLAUDE.md, market_thesis, conversion challenges
- [ ] `scripts/run_mission.py` injects PMF doc into every agent prompt
- [ ] Daily cycle template prioritizes conversion/activation over data-only work unless P0 junk blocks trust
- [ ] Execute **one** ProductSurface build ranked below (or document blocker in `outcome.md`)
- [ ] Write `outcome.md` with PMF metrics lens (pipeline views, signup path, activation signals)

## PMF build backlog (pick one)

| Rank | Slug | Hypothesis | Acceptance |
|------|------|------------|------------|
| 1 | `hubspot-connect-onboarding` | Robot sales teams on HubSpot need a visible connect path after signup | Signed-in user sees HubSpot CTA on `/crm` or `/profile` with honest tier gate |
| 2 | `signup-robot-company-copy` | Hero/subcopy should speak to OEMs/integrators automating sales, not generic “robotics” | Home + signup pages mention automate sales funnel + CRM choice |
| 3 | `pipeline-first-workspace` | Post-auth workspace should feel like a running sales machine | `/pipeline` default landing shows kanban + next actions + save CTA above settings |
| 4 | `crm-native-vs-hubspot-parity` | Both CRM paths visible in nav/onboarding | Clear “Use our CRM” vs “Connect HubSpot” fork without dead ends |

## Context

- Operator directive (2026-06-16): product/market fit is **automated sales pipeline for robot companies**
- Canonical frontend: `readyforrobots-new/client/`
- Hero headline already: “Automate Your Sales Pipeline.”
- Read `docs/product_market_fit.md` before choosing rank

## Out of scope

- Stripe billing implementation (unless copy-only)
- Lead quality sweeps unless snapshot shows live vendor/OEM leak blocking trust
- Legacy `frontend/nextjs/` work
- Committing `reports/`
