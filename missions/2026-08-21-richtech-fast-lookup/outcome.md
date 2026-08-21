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
- Cache namespace `robot_profile_v7`; do not pin 6-hour low-coverage misses.

## Tests

`pytest tests/test_richtech_vendor_lookup.py tests/test_fetch_challenge_archive.py tests/test_vendor_robot_lookup.py tests/test_product_href_discovery.py tests/test_robot_job_search.py` → 38 passed.

## Follow-ups

- Fly deploy so Jobs API serves the commercial seed.
- Industrial seed file (`vendor_robots_industrial_seed.json`) when that list is ready.
