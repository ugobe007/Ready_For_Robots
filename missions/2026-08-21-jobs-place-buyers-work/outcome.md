# Outcome: Make Jobs Place a working buyer step

**Date:** 2026-08-21
**Type:** build
**Status:** done

## What changed

Place listed buyer names then sent the robot OEM URL as `/pipeline?url=…&src=place`. Pipeline treated that as a buyer-company scan.

- Place buyers are selectable; the open row shows pitch + outreach on `/`
- `jobsPlaceHref` passes `src=place` + selected `lead=` — never the OEM as `url=`
- Pipeline `src=place` ignores `url=` and does not recover a stored scan URL

## Tests

`npx vitest run client/src/lib/jobsWorkflow.test.ts client/src/lib/jobsQualify.test.ts` — 23 passed
`npx tsc --noEmit` — clean

Vercel preview EngineAI T800: Next → Place → Genesis Healthcare draft → Open this buyer → `/pipeline?src=place&lead=8089&submission=10` (no OEM `url=`).
