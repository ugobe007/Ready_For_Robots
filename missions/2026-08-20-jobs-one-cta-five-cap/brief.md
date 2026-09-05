# Mission: One CTA on Jobs, 5 example jobs, digest owned in-repo

**Date:** 2026-08-20
**Type:** build
**Agents:** ProductSurface + Deploy
**Status:** done

## Goal

Jobs step 2/3 must not mix competing CTAs or show 12 jobs while promising 5. Anonymous path is 5 example jobs → 5 buyer leads. More than 5 exists only on `/pipeline`. Fly/GitHub own the daily digest so Hermes cannot 402 it.

## Why

Signup dies when the Jobs terminal asks the same question twice, shows 12 jobs next to “5 buyer leads”, then jumps into SIGNAL chrome on pipeline.

## Acceptance

- [x] Jobs list capped at 5 example jobs (signed-in included)
- [x] One primary CTA on the Jobs step (sidebar is quiet nav)
- [x] No “See all matches” vs “See 5 buyer leads” double ask
- [x] Job cards are evidence only — no second buyer CTA
- [x] Pipeline/Results from Jobs keep Jobs terminal chrome
- [x] Digest send is Fly + GitHub Action; Hermes skill retired
- [x] Targeted tests pass
