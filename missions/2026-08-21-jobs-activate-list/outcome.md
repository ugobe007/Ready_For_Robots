# Outcome: Activate the job list, not a buyer dump

**Date:** 2026-08-21
**Status:** complete

## Diff

- Wordmark / Jobs nav → `/?new=1` and clear workspace session so `/` returns to FIND.
- Jobs cards have checkboxes. Page CTA is **Activate job list →** (no Place buyers, no Next on the card, no 03 Place box).
- Activate writes a 15-job snapshot (checked first, then fill) and opens `/pipeline?src=jobs_activate` without the OEM as `url=`.
- Pipeline Jobs handoff board shows that list with left-rail instructions; no Upgrade to Pro banner on this landing.
- MagicLab locale product paths (`/en/x1`, `/en/app/g1`, `/en/human`, …) discover multiple SKUs. Cache namespace `robot_profile_v4`.

## Metrics

- Commercial event: `rdd_jobs_list_activated` (replaces Place opened on this path).
- Identity: MagicLab homepage must yield ≥3 products in picker, not G1-only.

## Follow-ups

- Live MagicLab HTML fetch on Fly (cookie / `/en` → `/en/en` 404) if picker is still thin after v4 cache bust.
- Signup CTA on the live list once the list itself is understandable.
