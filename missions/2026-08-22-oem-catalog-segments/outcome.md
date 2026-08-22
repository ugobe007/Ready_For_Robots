# Outcome — Segment large OEM catalogs by class and family

**Date:** 2026-08-22  
**Mission:** `missions/2026-08-22-oem-catalog-segments`  
**Type:** build

## Diff

- `readyforrobots-new/client/src/lib/jobsWorkflow.ts` — `lineupSegments` groups by robot class, then SKU stem (`LD-250` → LD). `usesLineupSegments` turns on when the lineup is bigger than the search cap, spans types, or has a family plus leftovers. Search names still slice to 3/5.
- `readyforrobots-new/client/src/components/RobotJobsWorkspace.tsx` — picker shows family cards (`Start jobs for LD AMRs`) plus optional SKU picks. Family confirm still uses `lineupJobLookups` (one type-first search). Flat picker stays for a small same-class lineup.
- `app/services/robot_understanding_v1/resolve.py` — list up to 24 discovered names so families can form. Jobs still searches 3/5; we do not crawl each SKU page.

## Metrics

Not a pipeline-cache mission. Live `https://www.fftai.com/en`: picker **5 robots in 2 groups** (GR humanoids + Fourier N1). Family click searched 3 of 4 GR SKUs (free cap), type-first — not a 5-SKU crawl.

## Follow-ups

Paid pages of 5 inside a family. SQL `RobotFamily` catalog. Crawling every OEM SKU page remains out of scope.
