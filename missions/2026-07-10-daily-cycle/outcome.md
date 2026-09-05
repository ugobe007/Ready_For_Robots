# Outcome — Daily orchestrator cycle (2026-07-10)

**Agent:** Orchestrator → ProductSurface
**Status:** complete
**Type:** build (conversion / value-first funnel)

## Mission selection

Snapshot was fresh (`generated_at` 2026-07-10T14:53Z; pipeline `built_at` same, `cache_pending: null`, 5 visible HOT leads) — **no cache refresh needed**.

Diagnostics were **unhealthy** on one axis only:

> `Zero new signups in 7 days — prioritize conversion missions`

Funnel (7d): `signup_start: 2 → signup_complete: 1 → first_save: 0`. Site health, code review, billing, and lead-quality gates all green. Conversion challenge board (`docs/conversion_agent_challenges.md`) is complete through #21, so the recommended items (#20 instrumentation, signup friction) were already shipped.

Chose **Priority 1 (signup/activation)**: fix an upstream **value-first funnel leak** rather than re-touch the already-polished signup page.

## Change shipped

**Home hero "Live pipeline" widget rows are now clickable deep links to each lead's value proof.**

`client/src/components/marketing/MarketingHeroPipeline.tsx`

- The hero widget is the strongest value-proof element on the site: a real HOT company + `pipeline_action` + `robot_types_needed` + SIGNAL score, rotating live from `/api/leads/homepage`.
- **Before:** the rows were inert `<div>`s. The only navigation was a generic "View all" → `/pipeline` (no lead selected). An engaged anonymous visitor who saw a specific hot buyer had **no path** to that buyer's pitch + outreach draft — a dead end at the exact browse → proof step of the funnel.
- **After:** each **real, live** lead row (`live && id > 0`) is a `<Link href="/pipeline?lead=<id>">`. `/pipeline` already deep-links `?lead=` — it auto-selects the lead, fetches it by id, and opens the `PipelineOutreachValuePanel` (pitch action + full Cal outreach draft) with no account required. From there, save/copy gate signup via `signupHrefForLead` (`?next=/pipeline?lead=<id>&co=<company>`), preserving context through the wall.
- Added a hover affordance ("See the pitch + outreach draft →") and `aria-label` for accessibility. Fallback/demo rows (negative ids or preview mode) stay non-clickable so we never route a visitor to a lead the pipeline can't load.

This routes the most-convinced visitors straight to the intent peak (value proof → save → `?next=` signup), the shortest path from anonymous browse to a tracked `signup_start`.

## Verification gates (harness/gates.yaml — ProductSurface)

| Gate | Result |
|------|--------|
| `site_health_smoke` (`--check site`) | ✅ healthy |
| `code_conventions` (`--check code --fail-on-violations`) | ✅ 0 violations |
| `lead_quality_smoke` + `partnership_rule` + `harness_diagnostics_unit` | ✅ 223 passed |
| esbuild TSX compile of edited file | ✅ clean (full `tsc`/`vite build` blocked by partial node_modules — env, not this change) |

Reused the exact `Link` + `className` pattern already used in `Home.tsx`, so wouter prop-forwarding is proven.

## Metrics delta

| Metric | Before | After (target) |
|--------|--------|----------------|
| Signups 7d | 0 | ↑ (drive anonymous → `signup_start`) |
| Funnel 7d | start 2 / complete 1 / first_save 0 | ↑ start rate from home hero engagement |
| Hero live-lead → value proof path | **dead end** | **1 click to pitch + draft** |
| junk_rate (sample 400) | 0.092 (100% vendor/OEM) | unchanged (not this mission) |
| Pipeline surface | 5 HOT leads, cache fresh | unchanged |

Signup counts are the true delta and can only be read on the next daily snapshot; instrumentation (#20) is already live to measure it.

## Follow-ups

1. **Measure:** next daily cycle — did `signup_start` (funnel denominator) rise after hero rows became clickable? Compare 7d funnel.
2. **Instrument hero-lead clicks** (optional): add a `home_hero_lead_click` track event so we can attribute `signup_start` to the hero path vs URL scan vs "Browse the pipeline free".
3. **`first_save = 0`** remains the deepest drop. `FirstSaveGuideModal`/`FirstSaveNudge` exist — next candidate mission is to verify they fire for the single completed signup and strengthen the first-save moment.
4. **Vendor/OEM leak** — junk sample is still 100% vendor/OEM (26 + 11 of 37). LeadQuality mission when it starts blocking trust; not blocking signup today.
