# Outcome: Hero pipeline panel — on-brand redesign

**Date:** 2026-06-23
**Status:** done

## Changes

- `ExperimentLeadTicker.tsx` — restored dark editorial glass panel; purple label, teal Live badge, compact 4-row ticker
- `HeroLeadTicker.tsx` — `maxVisible={4}`, removed hero variant props
- `Home.tsx` — hero grid back to `lg:grid-cols-[1fr_360px]`

## Verification

- `pnpm run build` passes in `readyforrobots-new/`

## Notes

Supersedes the Supabase-style treatment from `hero-live-pipeline-panel` per user feedback (wrong color, too large, off-theme).
