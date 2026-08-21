# Fourier lineup: find jobs, not an empty portfolio

**Date:** 2026-08-21  
**Type:** build  
**Agents:** ProductSurface  
**ICP:** OEM submits company URL with several SKUs (Fourier `fftai.com/en`)

## Goal

`https://www.fftai.com/en` lists the 5 Fourier robots, then shows **jobs + Activate job list** for a SKU. Listing all must not land on a portfolio of "0 matching jobs" with no Next.

## Acceptance

1. Several / all → per-SKU `robot-job-search` (no copied job list).
2. Land on jobs for the first SKU (Activate visible). Remaining SKUs fill in the background.
3. Unresearched shells do not display "0 matching jobs".
4. Default CTA is "Find jobs for all N robots →".
5. Vitest for jobsWorkflow green.

## Out of scope

- Matcher retune / SIGNAL / Qualify
- Seeding extra Fourier SKUs
