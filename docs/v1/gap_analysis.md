# ReadyForRobots V1 Gap Analysis

**Date:** 2026-08-10  
**Compared:** Engineering Blueprint + `docs/v1/*` vs live `app/`, `worker/`, `readyforrobots-new/`  
**Visual:** Cursor canvas `v1-gap-analysis.canvas.tsx`

## Executive summary

V1 product definition is frozen in `docs/v1/`. Almost none of the V1 domain schema or `/api/v1` HTTP surface exists in code. Reusable foundations are lead/CRM era objects (`companies`, `robots`, `signals`, `sales_opportunities`, `sales_experience_events`) plus a conversion vocabulary module that must be aligned in Slice 0.

| Layer | Full V1 | Partial | Missing |
| --- | ---: | ---: | ---: |
| Blueprint tables (24) | 0 | 3 | 21 |
| Checklist `/api/v1` endpoints | 0 | ~6 legacy cousins | rest |
| Canonical frontend routes | 0 | Home + Pipeline patterns | all V1 paths |
| Feature flag `V1_ROBOT_INTELLIGENCE` | — | documented only | not in code (until Slice 0) |

## Schema

| Blueprint table | Status | Live mapping / gap |
| --- | --- | --- |
| companies | PARTIAL | `app/models/company.py` — no facility separation |
| facilities | MISSING | location still on company |
| sources | MISSING | `signals.source_url` / JSON provenance only |
| labor_signals | MISSING | `signals` is company intent, not facility labor series |
| jobs / tasks | MISSING | V1 doc: `job_observations` / `task_observations`; ≠ `crm_tasks` |
| work_units | MISSING | — |
| primitives / work_unit_primitives | MISSING | ontology JSON in docs only |
| work_graph_nodes / edges | MISSING | V1 doc uses JSONB node refs on edges |
| robots | PARTIAL | flat catalog; no immutable profile versions |
| robot_capabilities / robot_specs | MISSING | `robots.features` JSON |
| work_envelopes | MISSING | planned on `robot_profile_versions` |
| work_matches | MISSING | legacy `scores` robotics fit |
| opportunities | PARTIAL | `sales_opportunities` — missing facility, disposition, V1 stage vocab |
| opportunity_evidence / unknowns | MISSING | planned `evidence_claims` + prediction arrays |
| qualification_questions / responses | MISSING | V1: `qualification_answers` |
| prediction_snapshots | PARTIAL | JSON on experience events at PRIORITIZED only |
| state_transitions | PARTIAL | `sales_experience_events` + agent action stage fields |
| outcomes | MISSING | planned `deployment_outcomes` |

**Truth/provenance:** no `truth_state` / `observed_at` columns on domain models. Confidence appears sparsely (experience events, contacts). Slice 0+ must introduce claim-level provenance per `data_model.md`.

## API

- **`/api/v1` namespace:** missing (config already defines `API_PREFIX=/api/v1` but routers are not mounted there).
- Blueprint paths (`/robots/analyze`, `/discover`, …) differ from OpenAPI (`/robot-analyses`, `/opportunity-searches`, `/transitions`, `/qualification`). **OpenAPI + `api_pipeline.md` win for build.**
- Closest legacy: `/api/robots`, `/api/sales/opportunities`, `/api/crm/.../deployment-transition`, `/api/leads/.../feedback`, scout/analyze URL scanners.

## Pipelines & workers

| Pipeline | Status | Notes |
| --- | --- | --- |
| Robot (crawl → profile) | MISSING | catalog only |
| Labor | PARTIAL | scrapers + signals; no facility/work-unit chain |
| Match | PARTIAL | offline calibration scripts |
| Opportunity / Call Priority | PARTIAL | `deployment_conversion.py` validates snapshots |
| Truth | MISSING | no evidence-claim store |
| Named jobs `robot.fetch`, `labor.*`, `match.*`, … | MISSING | Celery scrapers/rescoring/outreach only |

## Frontend

Canonical routes from `docs/v1/README.md` are **not** in `readyforrobots-new/client/src/App.tsx`.

| Screen | Status | Notes |
| --- | --- | --- |
| Robot Input `/` | PARTIAL | Home/Hero URL → company `/results` |
| Robot Analysis | MISSING | — |
| Opportunity Radar | MISSING | Pipeline is company HOT/WARM |
| Opportunity Detail | MISSING | CRM ≠ Work Graph / Evidence Triad |
| Qualification | MISSING | — |
| My Opportunities | MISSING | Pipeline / SalesConsole patterns only |
| Outcome | MISSING | — |
| Activity / Settings | PARTIAL | outreach feed; heavy CRM settings |

**Reuse:** Home URL normalize/submit; Pipeline card density. **Do not** map humanoid `/robots` or SalesConsole IDs to V1 robot/opportunity IDs.

## Compatibility adapters (keep alive)

CRM teams/accounts/engagements, outreach sequences, scout chat, marketplace RFQs, newsletter/waitlist, humanoid benchmarks, legacy SIGNAL scoring (`automation_score`, `labor_pain_score`, …).

## Naming deltas (blueprint vs frozen docs)

Prefer `docs/v1` names when implementing:

| Blueprint | docs/v1 |
| --- | --- |
| `jobs` / `tasks` | `job_observations` / `task_observations` |
| `prediction_snapshots` | `opportunity_predictions` |
| `qualification_responses` | `qualification_answers` |
| `outcomes` | `deployment_outcomes` |
| `OBSERVED` casing | lowercase `observed` |
| `DO_NOT_SURFACE` | OpenAPI: `do_not_surface` |
| Greenfield monorepo | Evolve FastAPI + `readyforrobots-new` |

## Next

1. Slice 0 — `/api/v1` router, error envelope, `V1_ROBOT_INTELLIGENCE`, conversion vocabulary + disposition.
2. Slice 1 — robot URL → provenanced profile.
3. Continue vertical path per `implementation_plan.md`.
