# Outcome: Make Jobs Place a working buyer step

**Date:** 2026-08-21
**Type:** build
**Status:** in progress

## What changed

Place listed buyer names then sent the robot OEM URL as `/pipeline?url=…&src=place`. Pipeline treated that as a buyer-company scan.

- Place buyers are selectable; the open row shows pitch + outreach on `/`
- `jobsPlaceHref` passes `src=place` + selected `lead=` — never the OEM as `url=`
- Pipeline `src=place` ignores `url=` and does not recover a stored scan URL
