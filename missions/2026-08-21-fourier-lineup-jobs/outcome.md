# Outcome — Fourier lineup jobs

**Mission:** `missions/2026-08-21-fourier-lineup-jobs`  
**Type:** build  
**Date:** 2026-08-21

## Cause

`fftai.com/en` correctly listed 5 Fourier SKUs. Confirming all called `identityAnalysis` only — a portfolio of unresearched shells showing "0 matching jobs" and no Activate (Next). Production `POST /api/robot-job-search` for Fourier GR-1 already returns jobs (~8s, 12 in payload).

## What shipped

- Several / all: match the first SKU, land on **jobs** (Activate visible), fill remaining SKUs in the background without copying jobs.
- Hide "0 matching jobs" on unresearched shells.
- CTA: `Find jobs for all N robots →`.

## Tests

`npx vitest run client/src/lib/jobsWorkflow.test.ts client/src/lib/jobsQualify.test.ts` — 27 passed.
