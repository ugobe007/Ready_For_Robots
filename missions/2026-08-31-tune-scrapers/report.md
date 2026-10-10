# Scraper parameter tune report

**Date:** 2026-08-31  
**Branch:** `cursor/tune-scrapers-new-params-009b`  
**SHA base:** `a80efed9` (#201 mixed OEM page class)

## Files

| Path | Role |
| --- | --- |
| `app/services/robot_job_scrape_params.py` | New. Chrome / invented SKU / class-dump filters. Product class, capabilities, task-model kind. |
| `app/services/robot_job_extract.py` | Extract schema. `product_class`, `required_capabilities`, `task_model_ids`, `work_task_model_kind`, `work_task_model_source`, `persistable`. Facade-cleaning function. Chrome employers rejected. |
| `app/services/robot_job_lifecycle.py` | Persist the new fields on `robot_jobs.requirements`. Skip non-persistable rows. |
| `app/services/robot_job_live_corpus.py` | FIND overlay. Serving ≠ floor_scrub. Drone-cleaning → `aerial_clean`. Pass through task-model fields. |
| `app/scrapers/job_board_scraper_enhanced.py` | Skip class-dump titles and chrome employers. Window-wash stems. Industry follows product class for serving / food_prep / drone. |
| `app/scrapers/scrape_targets.py` | Ontology field list. Facade/drone URL in the hospitality rotation (inside the 18-URL cap). Venue list unchanged. |
| `app/services/oem_sku_discover.py` | `Impact` chrome. Invented SKU names fail `is_junk_sku_name`. |
| `docs/robot_job_scraper.md` | Extract table. |
| `scripts/pstack_release.py` | Scrape-only file list includes the new extract/persist modules. |
| `tests/test_robot_job_scrape_params.py` | Serving ≠ cleaner. Drone ≠ floor-scrub-only. Chrome / invented SKU reject. Task-model unknown unless named. |
| `tests/test_job_board_scraper_pipeline.py` | Same cases through parse/upsert. Venue + facade URLs. |

## Encoding

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → JOB REQUIREMENTS → MATCH
```

Never company → category → jobs.

**Product range.** Mixed OEM hubs are not a job class. BellaBot work is serving. CC1 work is cleaning. A casino banquet-server posting is `product_class=serving` even if the scrape URL is a hotel.

**Named products.** Evidence SKUs only. Rejected as jobs or SKUs: `Seer Humanoid`, `AMR scrubbers`, `Galbot G2`, `TWA Reach`, empty names, chrome (`Impact`, Farmers, Product).

**Capabilities.** From the posting's class, not the OEM default. Serving → `serving_task`. Floor janitor → `surface_clean` + `hard_floor_scrub`. Cleaning drone → `surface_clean` + `drone_task` (no `hard_floor_scrub`).

**Task models.** Ontology slot IDs on the job. CRM field names on the same object:

- `work_task_model_kind`: `unknown` | `source` | `self_train`
- `work_task_model_source`: set only for `source`, and only when the posting names a known policy family

No Alembic on this branch. JSONB is enough. `jtm0a1b2c3d4` stays on `user_kept_jobs` in draft #202.

**Venues.** Food prep, serving, cleaning across hotels, restaurants, casinos, airports, offices, malls, data centers. Plus facade/drone. Not QSR-only.

**Contacts.** `mailto` and JSON-LD only.

## Tests

```
100 passed, 4 deselected
```

Deselected tests import `app.main` (needs `reportlab`). They were not changed.

pstack `--local`: `ok: true`. FIND drive skipped.

## Out of scope

Fly deploy. Merge #195 / leftover #197 / CRM-first #202.
