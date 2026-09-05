# Outcome — Daily orchestrator cycle (2026-07-15)

**Agent:** Orchestrator (ProductSurface build)
**Status:** shipped
**Type:** build — signup → activation

## Mission selected

**Auto-resume the first save through the signup wall** (activation, funnel rung 2).

## Diagnostics (from `harness_snapshot.py`, generated 2026-07-15T14:32Z)

Snapshot was fresh (pipeline `built_at` 13:58Z, `cache_pending: null`) → **no cache refresh needed**
(acceptance gate not triggered; `built_at` well within 26h).

Site health: **healthy** (fly + vercel proxy + pipeline + billing all OK).
Code review: **0 violations**, all conversion gates green.

### Conversion funnel (7d) — the decision driver

| Stage | Count | Read |
|-------|-------|------|
| signup_start | 18 | healthy top of funnel |
| signup_complete | 2 | 89% drop (magic-link/OAuth infra — already well-optimized on `/signup`) |
| **first_save** | **0** | **activation is fully broken** |
| crm_accounts_7d | 82 | saves DO happen via other paths → the funnel-tracked user save is the leak |

**Intelligence:** junk_rate 0.102 (100% vendor/OEM, no name/event junk), Unknown-industry
with signals = **1** (essentially solved), buyer-intent no_intent_rate 0.047. North-star
layers (names/events, scores, industry) are clean — so the correct lever is **activation UX**,
not lead quality.

## Root cause

An anonymous visitor who clicks **"Sign up free — save & copy"** on a specific lead is routed
to `/signup?next=/pipeline?lead=X&co=Y`. After auth they land back on `/pipeline?lead=X` with the
lead **selected but not saved** — they must re-discover and re-click "Save to workspace". New users
routinely skip that second click → `first_save = 0` despite clear expressed intent.

## Change shipped (frontend-only → Vercel)

1. **`lib/signupHref.ts`** — `signupHrefForLead()` now embeds `resume=save` in the `next` path
   (`/pipeline?lead=X&resume=save`). Flows through existing `storePendingNext` / `navigateAfterAuth`
   machinery untouched.
2. **`pages/Pipeline.tsx`** — new resume-save effect: when authenticated **and** `resume=save` is
   present **and** the intended deep-linked lead is loaded **and** the workspace has 0 saves, it
   auto-calls `handleSaveLead(target)` once (ref-guarded, param stripped via `replaceState`).
   - Fires `trackFirstSave` → converts the expressed intent into a real activation event.
   - Guards: only the exact intended lead; never double-saves; no-op if already activated.

Honors value-first ("Show → Believe → Act"): the user already *asked* to save pre-signup; we
complete the act instead of asking again.

## Verification (gates — ProductSurface set, all green)

| Gate | Result |
|------|--------|
| `code_conventions` (`--fail-on-violations`) | ✅ 0 violations |
| `site_health_smoke` | ✅ healthy |
| `harness_diagnostics_unit` | ✅ 8 passed |
| `lead_quality_smoke` | ✅ 215 passed |

Frontend `tsc`/`vite build` could not run locally (sandbox `node_modules` missing dev plugins +
`@types/node`; pre-existing tsconfig `baseUrl` error unrelated to this change). Edits use only
existing in-scope symbols and standard DOM APIs; Vercel's pinned toolchain builds on push.

## Metrics delta (expected — to confirm next cycle)

| Metric | Before (7d) | Target |
|--------|-------------|--------|
| signup_complete → first_save | 0 / 2 | ≥1 first_save per completed signup that came from a lead CTA |
| Activated workspaces | flat | ↑ (first save = activation) |

## Follow-ups

- **Next cycle:** confirm `first_save > 0` in the conversion slice; if still 0, instrument whether
  `resume=save` reaches `/pipeline` post-auth (magic-link redirect param stripping risk).
- Consider a short "Saved ✓" confirmation toast tuned for the resume path (currently reuses the
  standard save toast) and auto-advancing to the outreach-draft copy step.
- `signup_start → signup_complete` (89% drop) remains the larger raw leak but is infra-bound
  (email deliverability / OAuth); revisit only if a code lever appears.
