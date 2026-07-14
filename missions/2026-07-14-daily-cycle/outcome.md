# Outcome — Daily orchestrator cycle (2026-07-14)

**Agent:** Orchestrator (ProductSurface work)
**Status:** done
**Type:** build — signup activation / value-first
**Commit:** see `git log` (frontend-only; Vercel auto-deploy on push to `main`)

## Mission chosen (priority #1: value proof → signup → first save)

**Ship:** Pause the anonymous `/pipeline` lead auto-rotation the moment a visitor clicks a
lead, so the outreach-draft value-proof view is never yanked away mid-read.

### Why this, from the snapshot

The 21-item conversion challenge board is fully built (`docs/conversion_agent_challenges.md`),
so the leverage is in the funnel leaks the snapshot exposes:

| Funnel (7d) | Value |
|-------------|-------|
| signup_start | 17 |
| signup_complete | 2 (88% abandon the signup page) |
| **first_save** | **0** (activation broken) |
| signups_total / 7d | 11 / 1 |
| paid_tier_users / active_subs | 1 / 1 |

Value-first acceptance test #1 is: *"Anonymous user can read a full outreach draft for a
selected lead without signing up."* But the anonymous pipeline auto-rotated the selected lead
every **7 seconds** (`PIPELINE_LEAD_READ_MS`), and the panel-sync effect reset
`selectedId → filtered[0]` on **every** rotation tick (it only bailed for `?lead=` deep links,
not for a manual click). So an anonymous visitor who clicked a HOT lead to read its
subject + ~680-char Cal draft + robot chips got bounced to a different lead after 7s —
directly defeating the value-proof moment that drives signup intent. A subject + full draft
does not read in 7 seconds.

This is a genuine value-first violation on the highest-priority rung, and a plausible
contributor to the anonymous → signup_start and signup → first_save drop-offs.

## Change

`readyforrobots-new/client/src/pages/Pipeline.tsx` (+28 / −5):

1. New `rotationPaused` state.
2. New `selectLead(id)` handler — a manual lead-card click now pins the selection **and**
   pauses rotation (engagement = intent to read). Wired to both lead lists.
3. Rotation interval effect + panel-sync effect now bail when `rotationPaused`, so neither
   the visible list window nor the selected lead is shuffled while the visitor reads.
4. Minimal, self-contained resume affordance for anonymous users: a one-line
   "Rotation paused — read the full draft, then save it free · **Resume live ↻**" strip
   (only rendered when `panelPlan === "anonymous" && rotationPaused`). Keeps the "live"
   feel available on demand without new layout risk.

Passive visitors still see the live 7s rotation on landing (unchanged); rotation only
freezes once the visitor actively engages. Signed-in users are unaffected (rotation is
already off behind `showKanban`).

## Verification (gates from harness/gates.yaml — all green)

| Gate | Result |
|------|--------|
| `vite build` (real prod build) | ✅ built in 5.8s, 2377 modules |
| `code_conventions` (`--check code --fail-on-violations`) | ✅ healthy, 0 violations |
| `site_health_smoke` (`--check site`) | ✅ healthy |
| `lead_quality_smoke` (pytest) | ✅ 215 passed |
| `harness_diagnostics_unit` (pytest) | ✅ 8 passed |

Note: `pnpm run check` (`tsc --noEmit`) reports pre-existing errors across many unrelated
files (humanoidPilotTier, getApiBase, PageHeroDarkProps, downlevelIteration, etc.) — none
touch the edited lines and the production `vite build` (esbuild) passes clean. Not introduced
by this mission.

## Metrics delta

- Snapshot: pipeline `built_at` 2026-07-14T14:18, `cache_pending: null`, fresh (<26h) —
  **no cache refresh needed** (acceptance criterion satisfied by no-op).
- junk_rate 4.8% (19/400), all vendor/OEM — no lead-quality blocker on trust.
- No backend/data change, so `intelligence` counts are unchanged this cycle.
- Funnel metrics above are the pre-change baseline; post-change effect (anonymous draft-read
  dwell → signup_start, first_save) to be read from `signup_funnel_metrics` next cycle.

## Follow-ups

1. **Measure:** next daily cycle, compare `signup_funnel_7d.first_save` and signup_start vs
   this baseline (start 17 / complete 2 / first_save 0). If first_save still 0 with traffic,
   escalate the in-pipeline first-save nudge, not the read experience.
2. **Signup-page abandonment (88%)** is the next-biggest single leak — candidate: reconsider
   GitHub OAuth prominence for a sales/OEM ICP (GitHub signals "dev tool"), A/B Google-only.
3. Consider auto-resume after N seconds of inactivity if analytics show visitors pausing then
   leaving without saving.
4. Backend-side: the `crm_accounts_7d = 86` vs `first_save = 0` gap confirms CRM accounts are
   agent/system-generated (proof-batch), not user saves — keep first_save as the true
   activation signal.
