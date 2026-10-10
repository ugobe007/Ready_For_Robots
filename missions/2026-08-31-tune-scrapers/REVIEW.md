# Tune scrapers to the new parameters

**Date:** 2026-08-31  
**Branch:** `cursor/tune-scrapers-new-params-009b`  
**Base:** `origin/main` @ `a80efed9` (#201)

This is the review. `report.md` in this folder has the field map and test list.

## What was wrong

Job-board extract stored title, pay, specs, and a named employer. That is not enough for FIND or CRM.

A banquet server could sit next to a cleaner SKU class because nothing on the job named the work. A window-wash drone posting could look like floor scrub. Chrome (`Impact`, Farmers, Product) could pass as an employer. Class dumps (`Seer Humanoid`, `AMR scrubbers`) and invented SKUs (`Galbot G2`, `TWA Reach`) could look like jobs.

Task models were a CRM-only question on draft #202. Scrapers had no slot for named source vs self-train vs unknown, so Apply could not fill it later.

## What we changed

Extract now classifies the **posting**, not the OEM.

| Field | Rule |
| --- | --- |
| `product_class` | Work language, then job function. Serving stays serving. Pudu is not one class. |
| `required_capabilities` | Grounded in that class. Serving is `serving_task`. Drone-cleaning is `surface_clean` + `drone_task`, not `hard_floor_scrub`. Floor janitor still gets floor scrub. |
| `task_model_ids` | Ontology slots (`dining_floor_service_policy`). Not a SKU name. |
| `work_task_model_kind` / `source` | Same names as CRM. Default `unknown`. `source` only if the posting names GR00T / OpenVLA / LeRobot / NVIDIA Isaac. `self_train` only if the posting says they will train. Never invent Galbot G2 as a model. |

Persist writes those onto `robot_jobs.requirements` JSONB. No `user_kept_jobs` migration. Draft #202 can copy the fields when it lands. Contacts stay page-only (`mailto`, JSON-LD). No Apollo. No SIGNAL.

Live overlay maps serving to `serve` (not `floor_scrub`) and drone-cleaning to `aerial_clean` (empty families, not scrub).

OEM discover treats `Impact` as chrome and rejects the invented SKU list.

Venue URLs stay hotels / restaurants / casinos / airports / offices / malls / data centers. We added one facade/drone query inside the 18-URL hospitality cap. We did not go back to hotel-only.

## Tests

100 passed locally (4 scheduler tests skipped because this venv has no `reportlab` for `app.main`). pstack `--local` ok. FIND drive skipped on purpose. No Fly deploy.

## Do not

Merge #195 or leftover #197. Merge CRM-first #202. Fly-deploy. Invent model names from listings.
