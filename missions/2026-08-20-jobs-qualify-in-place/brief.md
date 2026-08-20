# Mission: Kill the post-login Jobs dead-end

**Date:** 2026-08-20
**Type:** build
**Agents:** ProductSurface
**Status:** in progress

## Goal

After login, users must not land on a second "Jobs for ______ robot" list with no action. FIND and QUALIFY stay on `/`. Clicking a job is the next step.

## Why

Login currently dumps people on `/pipeline?src=jobs_*`, which replaces the CRM with `JobsHandoffBoard`: expand-only cards and **no CTA** when signed in. The Jobs footer ("Next step: Jobs for your robot") is tautological — they are already looking at jobs for that robot. The hop kills FIND → QUALIFY.

## Acceptance

- [ ] Job cards on `/` are selectable and expose **Qualify this job**
- [ ] Page-level "Jobs for your robot →" footer is gone
- [ ] Signed-in Jobs links never render a second job list on `/pipeline` or `/results`
- [ ] Leftover `/pipeline?src=jobs_*` and `/results?src=jobs_*` bounce to `/?restore=1`
- [ ] Header Pipeline is the CRM (`/pipeline`), not a Jobs replay
- [ ] Targeted tests pass
