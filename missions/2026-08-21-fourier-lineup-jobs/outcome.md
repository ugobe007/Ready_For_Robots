# Outcome — Fourier lineup jobs (type first)

**Mission:** `missions/2026-08-21-fourier-lineup-jobs`  
**Type:** build  
**Date:** 2026-08-21

## Cause

`fftai.com/en` correctly listed 5 Fourier SKUs. Confirming all correlated the workflow to **one robot** (or to five sequential SKU searches). The lineup is a **group**. MagicLab overcorrection (do not copy G1 jobs onto X1) skipped match entirely, then per-SKU fan-out was the wrong grain: slow, and still SKU-shaped.

## What shipped

- Several / all: one job search per **robot type** (`lookup_grain=robot_type` + `asserted_class`). Thin class profile, no SKU scrape.
- Same-class SKUs share type-level jobs. Mixed classes look up separately.
- Land on **jobs** (Activate visible). Heading: `Jobs for {company}` when several robots.
- One SKU: unchanged — profile checkpoint, then product-level jobs.
- **Process nav always:** 01 Show us your robot → 02 Here are its jobs → 03 Activate the job list. 02/03 are links, not dead labels. Activate never no-ops.
- CTA: `Find jobs for all N robots →`.

## Tests

See this cycle's pytest / vitest run in the PR.
