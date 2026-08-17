# Mission: M2 Match Truth

**Date:** 2026-08-17  
**Type:** build  
**Agents:** Orchestrator  
**Status:** in progress

## Goal

Prove the same Robot Job can produce materially different, explainable verdicts for different robots because of **requirement satisfaction** — not category scoring.

## Housekeeping (done / this mission)

1. Profile-first Jobs UI is on `origin/main` (`011aa4e`) so Vercel cannot silently restore matcher-only UI.
2. Canonical Understanding doc no longer says “Phase 4 remains CLOSED” in Blind 20 while the header allows M2.

## Truth test (this mission)

Start with **one job**, then four gold jobs, then the existing corpus using work-physics templates.

### Novolex Kinston — Case conveyor → outbound pallet

Same job against frozen Understanding profiles:

| Robot | Expected verdict |
|-------|------------------|
| Dexmate Vega | POSSIBLE MATCH — manipulation grounded; payload/grasp/cycle unknown |
| Agility Digit | POSSIBLE MATCH if manipulation primitives are grounded; own unknowns |
| Locus Origin | NOT A MATCH — essential manipulation unmet |
| Avidbots Neo | NOT A MATCH — case palletizing outside grounded profile |

Requirement states only: **MATCHED · UNMET · UNKNOWN · LIKELY** (LIKELY only with a named derivation). No match percentage.

### Four-job cross-physics

| Work | Expected discrimination |
|------|-------------------------|
| Novolex case palletizing | Vega/Digit vs Origin/Neo |
| CuraScript tote return | Origin/Digit vs Neo/fixed arm |
| Airport hard-floor scrub | Neo vs everyone else |
| Inspection route | Spot/ANYmal-class vs transport/manipulation |

## Non-goals

- Reopen Understanding extractors / Blind 20 retune
- Patch the old keyword/family matcher to fake differentiation
- Publish C04 / invite traffic (still paused until MATCH TRUTH + funnel)
- Auth continuity / telemetry (next, after this matcher)

## Acceptance

- [ ] Same job → different verdicts for physically different robots
- [ ] Every positive match explains matched requirements / grounded why
- [ ] Every hard rejection names the unmet requirement
- [ ] Unknowns remain unknown
- [ ] No robot-type → family → jobs shortcut
- [ ] Corpus boards differentiate Agility, Locus, Avidbots, and a manipulation robot
