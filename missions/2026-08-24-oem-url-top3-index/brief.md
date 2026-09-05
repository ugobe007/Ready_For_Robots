# FIND: OEM URL → top 3 named robots

**Date:** 2026-08-24
**Type:** build
**Agents:** ProductSurface, Deploy

## Goal

Build a large OEM URL index for Jobs FIND: company website → at most three product names in results. Parse names first, then a short description, then specs only when they already exist. Do not crawl every SKU page.

## Why

Indexed humanoid/commercial catalogs miss hundreds of AMR, cobot, and industrial OEMs. Pasting those homepages still waited on live fetch. The calibration seed already has company URL + `primary_robots` — enough to list three named robots without a product crawl.

## Acceptance

1. Additional OEM websites resolve from the jobs seed without live fetch.
2. Picker / profile lists ≤3 robots per URL.
3. Listing order is name → description → specs-if-present. Empty specs stay empty.
4. Generic lines (`AGV/AMR`) and retailer/research mega-sites are not invented product lists.
5. Targeted pytest (+ jobsWorkflow vitest cap) green.

## Out of scope

Inventing SKUs or payload numbers. Live crawl of 300 OEM catalogs. Fly deploy (PR first). SIGNAL.
