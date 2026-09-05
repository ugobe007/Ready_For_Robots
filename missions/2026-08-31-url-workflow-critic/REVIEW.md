# URL critic review

**Date:** 2026-08-31  
**Branch:** `cursor/url-workflow-critic-009b`  
**Score:** 19/19 PASS, Tennant n=5, SEER n=7. Empty is a break.

This is the review. `report.md` in this folder has the full scoreboard.

## The bug

Tennant and SEER both sell robots. The critic still passed them with 0 products.

That was treated as an honest empty picker. It was a bug. A robot OEM hub with nothing named is `empty_range_on_robot_oem`.

We also must not put back the class dumps that caused the first failure: `AMR scrubbers`, generic `Scrubber`, `Seer Humanoid`. Those are categories, not SKUs.

## Cause

Three things stacked.

The old Tennant listing path 404s. The live robotics hub is `/en_us/robotics.html`. Product pages use Hybris names like `product.x6-rovr.autonomous-floor-scrubber.…html`. The extractor treated that filename as a hub called `product`, so it never kept T7AMR / X6 ROVR.

SEER's homepage is a thin Next.js shell. Named AMRs live on `/amr/liftingrobot` and `/amr/autonomousforklifts`. The listing hint pointed at `/amr/others.html`, which has no products. Discovery also fetched generic `/products` first and often never reached the AMR pages.

Then the corpus said `allow_empty: true` for both OEMs. Zero products could not fail.

## Fix

Empty known robot OEM (`expects_named_robots: true`) now BREAKS. Fixtures cover an empty hub and a class-dump name (`Seer Humanoid` / `AMR scrubbers`).

Extract follows Tennant robotics pages and only keeps robotic SKUs (AMR / ROVR / autonomous / robotic in the product path). Manual T7 ride-on stays out. SEER listing hints go to lifting, forklifts, controllers. Next.js `__NEXT_DATA__` names are used when the HTML links are there.

Catalog cache (not invented):

| OEM | Named products | Evidence |
|-----|----------------|----------|
| Tennant | X6 ROVR, X16 SWEEP, T7AMR, T380AMR, T16AMR | robotics hub + those product pages |
| SEER | AMB-300JZ, AMB-300XS, SJV-SW600, SFL-CBD15, SFL-300L, SCB-1400, SRC-880 | lifting / forklift / controller pages |

Tennant class is cleaning floor AMR. SEER class is warehouse/logistics AMR. SRC-880 is a named controller with no class. Thin SKUs elsewhere still do not inherit a sibling class.

## What stayed green

The other 17 OEM URLs still PASS with the same ranges and named products as the last report. Kaercher is still KIRA only.

## What still needs a live Fly deploy

Production FIND still returns the old junk (`AMR scrubbers`, `Seer Humanoid`, generic `Scrubber`). This branch's catalog is local until Fly (and the frontend lineup cache) ship.

After deploy, paste Tennant or SEER on `/` and you should get named robots, not an empty class picker and not a humanoid dump.

Do not merge #195.

## Remaining gaps

- Fly is stale until deploy.
- SRC-880 and other thin SKUs stay unclassified. That is honest, not a sibling dump.
- X16 SWEEP is a sweeper that still grounds floor-scrub capabilities because FIND class is cleaning.
- SEER has more named forklift variants on the live listing than we cached. We kept a Kaercher-sized robotic set, not every mop-equivalent vehicle.
