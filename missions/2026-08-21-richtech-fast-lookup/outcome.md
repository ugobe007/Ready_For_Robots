# Outcome — Fast Richtech URL lookup

**Mission:** `missions/2026-08-21-richtech-fast-lookup`  
**Type:** build  
**Date:** 2026-08-21

## Cause

`www.richtechrobotics.com` returns HTTP 429 (`x-vercel-mitigated: challenge`). Jobs then tried Wayback copies of guessed product hubs (`/adam`, `/products`, sitemap, …) until the client waited ~90s, then showed Profile C: identity confirmed, specs unconfirmed. Richtech is commercial, so it was not in the `/robots` humanoid index.

## What shipped

- Commercial seed `app/data/vendor_robots_commercial_seed.json` (Richtech: ADAM, Matradee family, Lucki, Medbot, Dust-E MX, Aidy, Scorpion, Titan).
- Vendor lookup merges that seed with the humanoid index.
- Catalog hit skips Wayback on the homepage fetch.
- Empty challenged homepages do not fan out source fetches.
- Catalog facts (service-robot class, environment, mobile base) fill the selected SKU when live pages are blocked.
- Cache namespace `robot_profile_v8`; catalog-first skip of live hub fan-out for every indexed vendor.
- Commercial seed also covers Bear, Pudu, Locus, and Boston Dynamics Spot/Stretch (merged with Atlas from `/robots`).
- Index specs map onto checklist predicates (`carrying_capacity`, `battery_runtime`).
- Unknown OEMs still get a typed live pack; guessed hubs never use Wayback.

## Tests

Targeted pytest on lookup + pipeline + fetch challenge tests.

## Follow-ups

- Fly deploy so Jobs API serves the vendor index + commercial seed.
- Industrial seed file (`vendor_robots_industrial_seed.json`) when that list is ready.
- More commercial OEMs: add JSON rows (do not reopen extractors).
