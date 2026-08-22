# Outcome — tag jobs per robot

**Mission:** `missions/2026-08-21-jobs-per-robot-tag`  
**Type:** build  
**Date:** 2026-08-21

## What shipped

- One robot: five jobs, each labeled `Job ##### is for {SKU}`.
- Several robots: one distinct sample job per SKU, tagged, plus **Run one robot for 5 jobs →**.
- Pipeline list keeps the robot tag and prompts **Save this job list to CRM**.
- Email-on-change watch loop documented as next, not built.

## Tests

- Vitest: `jobsWorkflow` + `jobsQualify`.
