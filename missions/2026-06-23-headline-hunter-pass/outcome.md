# Mission: Headline junk quarantine + Hunter contact upgrade

**Date:** 2026-06-23  
**Status:** Done

## [1] Headline junk quarantine (HOT/WARM)

New heuristics in `app/services/headline_hot_quarantine.py` + `scripts/quarantine_headline_hot_leaks.py`.

Targets RSS headline stubs leaking into HOT/WARM (`News …`, `New Costco`, colon event titles, sentence verbs).

**Run (2026-06-23):** 33 candidates → **33 quarantined** (11 HOT, 22 WARM)

## [2] Hunter credit pass

`app/services/hunter_contact_upgrade.py` + `scripts/run_hunter_contact_upgrade.py`

Upgrades role-inbox / inferred contacts when CRM has named decision makers.

**Run (2026-06-23):** 6 candidates → **2 upgraded**
- FedEx Ground → `john.dietrich@fedex.com` (CFO)
- Accor Hotels → `david.liu@accor.com`

## Ops

```bash
python3 scripts/quarantine_headline_hot_leaks.py --limit 3500 --apply
python3 scripts/run_hunter_contact_upgrade.py --limit 25
python3 scripts/refresh_pipeline_cache.py --remote
```
