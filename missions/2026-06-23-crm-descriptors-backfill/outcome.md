# Outcome: CRM descriptors backfill

**Date:** 2026-06-23
**Status:** done

## Changes

- `app/services/crm_extractor.py` — `_infer_automation_requirements_fallback()` via `humanize_robot_types()` when regex finds no requirements
- `app/services/lead_secondary_pass.py` — `_crm_metadata_field_has_content()` so empty budget/timing dicts are not counted as fills

## Batch results

- `--require-gap crm_descriptors --limit 30`: **4** leads filled (`automation_requirements` from industry/signal robot-fit inference)
- Harness gap frequency: `crm_descriptors` **30 → 28** (snapshot `20260623_040355`)

## Residual

- Leads with unknown industry and no robot signal context (e.g. Orchestra PE) still skip — need inference pass or signal backfill first
- Apollo contact backfill on HOT/WARM blocked by free-plan API (`403` on `mixed_people/api_search`)
