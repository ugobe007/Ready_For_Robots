# VinMotion review

**Date:** 2026-08-31
**Branch:** `cursor/vinmotion-oem-009b`
**Score:** corpus 20/20 PASS. VinMotion n=2 named robots. Fixtures 8/8 PASS.

This is the review. `report.md` in this folder has the product table.

## What the site actually names

https://vinmotion.net/ is a Next.js shell. The homepage Product menu names two robots and links them:

| Product | Evidence URL | Class | Why |
|---------|--------------|-------|-----|
| Motion 1 | https://vinmotion.net/product/motion-1 | humanoid | Homepage: "See our VinMotion Motion 1 humanoid robot in action." |
| Motion 2 | https://vinmotion.net/product/motion-2 | unclassified | Homepage: "Watch now - Motion 2 launching." Product page is a launch video. No hardware or work copy on that page. |

Chrome stays out: Product, Home, News, Careers, Contact Us, Humanoid Challenge 2025. Those are nav and campaign titles, not SKUs.

There is no third named robot on the page. I did not add VinMotion Humanoid.

## Class

Motion 1 is a humanoid because that product is called a humanoid robot on the homepage. Motion 2 does not inherit that class. The launching page has no biped / arm / work language, so it stays unclassified. Same rule as SRC-880 and PUDUA1.

Range is humanoid, not mixed. This OEM is not Pudu.

Capabilities (this product, no invented specs):

- Motion 1: mobile, manipulate
- Motion 2: none

## Extract

Listing hints: `/`, `/product/motion-1`, `/product/motion-2`. Homepage HTML already has those links, so href extract works. App Router `self.__next_f` ProductMenuItem titles are a second path for the thin product pages.

Catalog cache is `ontology/mixed_oem_sku_catalog.v1.json`. Live extract still wins.

## What stayed green

The other 19 corpus URLs still PASS. Tennant n=5. SEER n=7. Empty known OEM is still a break. No Fly deploy on this branch.
