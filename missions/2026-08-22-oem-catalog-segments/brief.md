# Segment large OEM catalogs by class and SKU family

**Date:** 2026-08-22  
**Type:** build  
**Agents:** ProductSurface

## Goal

Makers with many robots (Omron AMRs, Fourier GR vs N1) cannot be a flat 10-card picker plus a 3-SKU crawl. Group the lineup by robot class and SKU family. One family click = one type-first job search, not N product-page fetches.

## Acceptance

1. Picker groups by class (AMR / humanoid / …) and SKU stem (LD, HD, GR) when the lineup is larger than the search cap or spans types.
2. “Start jobs for LD AMRs” searches that family once (type-first), still capped at 3/5 SKU tags.
3. Individual SKU pick remains, capped at 3 free / 5 paid.
4. Do not fetch a job search per SKU in a family.
5. Vitest covers Omron-style LD/HD and Fourier GR vs N1.

## Out of scope

SQL robot catalog families, matcher (M2), SIGNAL, crawling every OEM SKU page.
