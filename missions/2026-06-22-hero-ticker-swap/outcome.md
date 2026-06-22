# Outcome: Hero ticker swap

**Result:** success (code complete; deploy pending human approval)
**Commit:** (see git log)

## Changes

- Added `HeroLeadTicker` — compact wrapper for home hero (8 rows, 6s)
- `ExperimentLeadTicker` accepts props for max rows, tick interval, pipeline link
- `Home.tsx` replaces `HeroSpotlightLeads` with `HeroLeadTicker`; visible on all breakpoints

## Metrics (before → after)

Run after deploy:

```bash
python3 scripts/harness_snapshot.py
```

- pipeline leads / built_at: TBD post-deploy

## Follow-ups

- Deploy with `fly deploy -a ready-2-robot --wait-timeout 600`
- Optional: remove or archive `HeroSpotlightLeads` after 7-day soak
