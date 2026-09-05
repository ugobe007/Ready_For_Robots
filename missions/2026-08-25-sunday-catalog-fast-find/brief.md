# Mission: Catalog-first Sunday Memo + named Job Cards

**Date:** 2026-08-25
**Agent:** ProductSurface + LeadQuality (Jobs path)
**Status:** in_progress
**Type:** build

## Goal

Make FIND robot and FIND jobs fast for known URLs (index first, scrape only if new), and stop showing incomplete rows as Robot Jobs. Operator submitted `https://www.sunday.ai/` — Memo is a home kitchen helper, not an office humanoid. Jobs must be named employer + workplace kitchen work (home-like and corporate kitchens).

## Acceptance criteria

- [ ] `https://www.sunday.ai/` hits the vendor index (Memo) without a live OEM fetch
- [ ] Client `knownOemLineups` lists Memo so FIND robot does not wait on the API
- [ ] Job search for Memo returns named kitchen/hospitality jobs (espresso, dishes, corporate kitchen) — not CNC, not Employer/Workplace `[unknown]`
- [ ] Incomplete corpus rows (missing employer or workplace) are not returned as Job Cards
- [ ] Task-model presence stays `unknown` (honest QUALIFY) but kitchen jobs use a kitchen policy slot instead of opaque "Site-specific task policy"
- [ ] ADAM catalog claims include beverage prep so bar jobs are reachable without the class quiz
- [ ] Targeted pytest + vitest green

## Context

Operator quality bar: paste URL → useful result in seconds (Pythh-style). Architecture they asked for: URL list → compare to DB → scrape only if new. Do not invent SKUs. Do not catalog Memo as a bipedal humanoid.

## Out of scope

- New scrape stack / Pythh integration
- Matcher ranking retune
- SIGNAL / CRM / Cal
- Inventing household employers
