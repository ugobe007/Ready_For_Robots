# Fast Richtech URL lookup from commercial seed

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface + Understanding integrity  
**ICP:** Robot OEM submits `richtechrobotics.com` on Jobs FIND  

## Goal

`richtechrobotics.com` must not take ~90s and land on a hollow Profile C. Live host is a Vercel 429 challenge. Until URL lookup is rock-solid, pull stored commercial SKUs (ADAM, Matradee, …) from a vendor index instead of guessing via Wayback fan-out.

## Acceptance

1. `richtechrobotics.com` returns a picker of indexed SKUs without archive/source fan-out.
2. Selecting ADAM uses catalog class/environment facts; no 90s crawl.
3. Challenged empty homepages do not fetch `/adam`, sitemap, or Wayback copies of every hub.
4. Low-coverage challenged research profiles are not cached for 6 hours (picker payloads may cache).
5. Targeted pytest green.
