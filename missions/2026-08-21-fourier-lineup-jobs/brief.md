# Fourier lineup: jobs for the robot type, then the product

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface  
**ICP:** OEM submits company URL with several SKUs (Fourier `fftai.com/en`)

## Goal

`https://www.fftai.com/en` lists the 5 Fourier robots, then shows **jobs + Activate job list** for the **humanoid type** (the group). Listing all must not land on a portfolio of "0 matching jobs", and must not wait on five SKU scrapes.

The workflow broke because it correlated to **one specific robot**. A lineup is a group. Jobs for the robot type first; jobs for the product when the operator picks a SKU.

## Acceptance

1. Several / all → one `robot-job-search` per **robot type** (`lookup_grain=robot_type`), not per SKU.
2. Same-class SKUs share type-level jobs (Fourier GR-1/GR-2/GR-3). Mixed classes (Atlas / Spot / Stretch) do not share.
3. Land on jobs (Activate visible). Heading is type-level (`Jobs for humanoids`).
4. One SKU still goes to the profile checkpoint, then product-level jobs.
5. Type-first compose does not call `build_robot_profile` (no SKU scrape).
6. Vitest + targeted pytest green.

## Out of scope

- Matcher retune / SIGNAL / Qualify / family dump
- Seeding extra Fourier SKUs
