# Outcome — Fourier N1 one-SKU jobs

**Mission:** `missions/2026-08-21-n1-one-sku-jobs`  
**Type:** build  
**Date:** 2026-08-21

## Cause

Picker confirm for one SKU (`Fourier N1`) still opened the profile checkpoint. The picker CTA already said Find jobs; Review asked again. Jobs then rendered in a scrolling pane with Activate below the fold, so step 03 disappeared.

## What shipped

- One selected SKU: `fetchRobotJobSearch` then `openJobsFromAnalyses` — no `enterReview`.
- Type-first when the picker already knows the class; heading stays `Jobs for Fourier N1`.
- Jobs stage pins **Activate job list →** (`rfr-jobs-activate-bar`).
- Process nav 03 is a link once jobs are on screen; picker stage does not Activate an empty list.

## Tests

- Vitest: 28 passed (`jobsWorkflow.test.ts` + `jobsQualify.test.ts`).
- Production API smoke: `POST /api/robot-job-search` `{url: fftai.com/en, product: Fourier N1, asserted_class: humanoid, lookup_grain: robot_type}` → 38 jobs, ~1.2s. API `robot_name` is `Humanoid`; client stamps `Fourier N1`.
- Manual: `https://www.fftai.com/en` → pick N1 → one Find jobs click → **Jobs for Fourier N1** with pinned **Activate job list →**. No second Find jobs / review screen.
