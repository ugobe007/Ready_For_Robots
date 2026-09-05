# Mission: Unknown-industry residual sweep

**Date:** 2026-06-23
**Agent:** LeadQuality
**Status:** done
**Type:** build

## Goal

Clear the remaining **56** active Unknown-industry rows with signals left after `industry-rescue-ontology` (153→52).

## Acceptance criteria

- [x] Extend `unknown_industry_rescue.py` — market-report noise, vendor/OEM PR, residual headline stubs
- [x] Expand `KNOWN_COMPANY_INDUSTRY` for real buyers (TraceGains, Crewline, Schaeffler, etc.)
- [x] Tests in `tests/test_unknown_industry_rescue.py`
- [x] Dry-run → `--apply` → cache refresh
- [x] Active Unknown w/ signals → **0**
