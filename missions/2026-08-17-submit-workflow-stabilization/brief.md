# Mission: Submit Workflow Stabilization

**Date:** 2026-08-17  
**Type:** build  
**Agents:** ProductSurface + Deploy  
**Status:** in progress

## Goal

The Jobs submit path must feel like one coherent transaction. Research privately. Reveal deliberately. Never expose the internal pipeline as unstable UI.

## Principle

> Never stream half-baked jobs. The server may work progressively. The UI reveals atomically.

## Acceptance

- [ ] One explicit UI state machine: `IDLE → RESEARCHING → PRODUCT_SELECTION? → COMPOSING_RESULTS → RESULTS`
- [ ] Zero partial-job rendering (no profile → empty jobs → partial jobs → reordered jobs)
- [ ] Atomic `SEARCHING → RESULTS READY` reveal of profile + first jobs together
- [ ] Stable panel dimensions (same outer geometry on submit → research → results)
- [ ] Public job tape keeps scrolling during research; it is not the personalized board yet
- [ ] Multi-product URLs resolve to a picker before deep research
- [ ] Cached Robot Profiles skip a full rebuild
- [ ] Instrument `resolve_ms`, `profile_ms`, `match_ms`, `total_ms`
- [ ] Target: <8s uncached first useful result, <2–3s cached
- [ ] No matcher ranking changes in this mission

## Non-goals

- Digit ranking / MATCH TRUTH retune (return after this)
- Understanding extractor / Blind 20 changes
- Auth continuity / telemetry (next after MATCH TRUTH ranking ships)
- Traffic / C04

## Out of scope after this

Matcher ranking evaluation resumes only after submit no longer jitters.
