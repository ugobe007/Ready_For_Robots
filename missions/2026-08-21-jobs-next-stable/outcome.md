# Outcome — Next / Start jobs, stable FIND

**Mission:** `missions/2026-08-21-jobs-next-stable`  
**Type:** build  
**Date:** 2026-08-21

## What shipped

- FIND: **Start jobs →** in the process bar, above the live tape, and on the URL form.
- Jobs list: **Next →** in the process bar, at the top of the list, and at the bottom.
- Wordmark hard-loads `/` (does not bounce `/?new=1` → `/`).
- Live tape seeds once (no remount re-seed). Auth skips duplicate `INITIAL_SESSION`.

## Tests

- Vitest: `jobsWorkflow` + `jobsQualify`.
- Manual: FIND shows Start jobs without a remount flash. Fourier N1 jobs list shows Next in chrome and above the cards.
