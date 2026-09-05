# ReadyForRobots V1 Engineering Blueprint

**Version:** 1.0 (consolidated paste)  
**Saved:** 2026-08-10  
**Purpose:** Preserve the full narrative blueprint shared for implementation.  
**Build authority on conflict:** the split package in this folder (`README.md`, `information_architecture.md`, `data_model.md`, `api_pipeline.md`, `openapi-v1.yaml`, `implementation_plan.md`).

---

## Deltas vs frozen `docs/v1/` (docs win for code)

| Topic | This blueprint | Frozen `docs/v1` (authoritative) |
| --- | --- | --- |
| Navigation | Discover / Opportunities / Robots / Activity / Settings tree | Focused routes: `/`, `/robots/:id/review`, `/robots/:id/opportunities`, `/opportunities`, `/opportunities/:id`, qualify, outcome |
| Truth casing | `OBSERVED`, `INFERRED`, … | lowercase: `observed`, `inferred`, … |
| Call priority | includes `DO_NOT_SURFACE`; checklist sometimes `UNRESOLVABLE` | OpenAPI: `do_not_surface` (no `unresolvable`) |
| Opportunity states | includes `EXPANDING`, `WATCH`, `PAUSED`, `LOST` in one list | Truth states end at `deployed`; `watch`/`paused`/`lost` are **dispositions** |
| Site stage | `SITE_REVIEW` in state machine section; elsewhere varies | Single truth stage `site_review` replaces `site_verified` / `solution_fit` / `economic_fit` / `expanding` |
| Schema shape | Normalized `sources`, `primitives`, `robot_specs`, `work_graph_nodes` | Prefer `evidence_claims`, profile JSONB, JSONB graph node refs (see `data_model.md`) |
| Opportunities table | new `opportunities` | Reuse `sales_opportunities` + new columns |
| Predictions / outcomes / answers | `prediction_snapshots`, `outcomes`, `qualification_responses` | `opportunity_predictions`, `deployment_outcomes`, `qualification_answers` |
| API paths | `/robots/analyze`, `/discover`, `/action`, `/questions` | OpenAPI: `/robot-analyses`, `/opportunity-searches`, `/transitions`, `/qualification`, `/answers` |
| Repo layout | Suggested `/apps` `/packages` `/services` monorepo | Evolve existing FastAPI `app/` + `readyforrobots-new` + `worker/` |
| Build plan | Eight sprints | Vertical slices 0–N, forklift-first path (`implementation_plan.md`) |
| Legacy | Implicit greenfield | Explicit reuse + compatibility adapters |

**Gap analysis:** [gap_analysis.md](gap_analysis.md)

---

## Full blueprint text


# 1. Product Definition

ReadyForRobots answers: **Where should this robot company's next hour of sales effort go?**

User provides a robot or product URL. System: understand capabilities → Work Envelope → labor signals → facilities → Work Units / Work Graphs → score dimensions → Call Priority → evidence / unknowns / questions / buyer functions → capture feedback/outcomes → improve predictions.

V1 wedge: material movement robots (AMRs, autonomous forklifts, autonomous tuggers).

# 2. V1 Information Architecture

Primary journey (canonical routes in `information_architecture.md`):

1. Enter Robot → 2. Understand Robot → 3. Find Work → 4. Find Facilities → 5. Rank Opportunities → 6. Qualify → 7. Report Outcome

Screen inventory: Robot Input, Robot Analysis, Opportunity Radar, Opportunity Detail, Qualification, My Opportunities, Outcome/Feedback, Robot Detail, Activity Feed, Minimal Settings. No full CRM in V1.

# 3. Core Domain Model

```text
COMPANY → FACILITY → LABOR_SIGNAL → JOB → TASK → WORK_UNIT
FACILITY → WORK_GRAPH
ROBOT → ROBOT_CAPABILITY + WORK_ENVELOPE
WORK_UNIT ↔ ROBOT → WORK_MATCH → OPPORTUNITY
  → PREDICTION_SNAPSHOT + QUALIFICATION_* + STATE/DISPOSITION + OUTCOME
```

# 4. Canonical Truth Model

Every important field:

```json
{
  "value": "...",
  "truth_state": "observed",
  "confidence": 0.91,
  "source_id": "src_123",
  "observed_at": "2026-08-10T12:00:00Z"
}
```

Allowed truth states (lowercase in API): `observed`, `inferred`, `oem_verified`, `customer_confirmed`, `site_verified`, `deployment_verified`, `unknown`.

**Rule:** Never overwrite an earlier prediction or observation. New truth creates a new record/version.

# 5. Database Recommendation

PostgreSQL + pgvector later; Redis/SQS queues; S3-compatible object storage; append-only events; ORM already SQLAlchemy/Alembic in this repo. No graph DB in V1.

# 6. Database Schema

See [data_model.md](data_model.md) for the authoritative table list and migration order. Blueprint SQL for `companies`, `facilities`, `sources`, `labor_signals`, `jobs`, `tasks`, `work_units`, `primitives`, graph tables, `robots`, capabilities, specs, envelopes, `work_matches`, `opportunities`, evidence/unknowns, qualification, snapshots, transitions, and outcomes remains the conceptual model; naming and normalization follow `data_model.md` when they diverge (section Deltas above).

Facility is the primary commercial unit.

# 7. Scoring Inputs

Seven V1 dimensions (no standalone Deployment Readiness):

1. Work Match  
2. Labor Pressure  
3. Operational Exposure (`LOW`/`MODERATE`/`HIGH`/`CRITICAL`)  
4. Buyability (`LOW`/`MEDIUM`/`HIGH`/`UNKNOWN`)  
5. Deployability  
6. Evidence Confidence  
7. Account Resolvability  

Plus Qualification Percent and Call Priority output.

Robotability (internal 0–100) and Labor Pressure weights as in the original blueprint §7; hard blockers override aggregates.

# 8. Opportunity Decision Logic

Experimental thresholds; must be versioned. Conceptual order:

1. Known hard blocker → `wrong_robot`  
2. Low evidence → `insufficient_evidence`  
3. High match + labor + resolvability → `call_now`  
4. Good match + critical unknowns → `qualify`  
5. Moderate match + lower labor → `watch`  
6. Else → `do_not_surface`

# 9–14. API Architecture

Browser → Web App API → application services (Robot, Labor, Work Extraction, Matching, Opportunity, Qualification, Truth) → PostgreSQL. Async workers for crawl/extract/score.

Authoritative HTTP contract: [openapi-v1.yaml](openapi-v1.yaml) and [api_pipeline.md](api_pipeline.md).

# 15. Internal Pipelines

Robot → Labor → Match → Opportunity → Truth (see `api_pipeline.md`). All jobs idempotent.

# 16. Job / Worker Queue

Families: `robot.*`, `labor.*`, `match.*`, `opportunity.*`, `truth.*`, `activity.notify`.

# 17. Screen Wireframes

ASCII wireframes for Input, Profile, Radar, Detail, Qualify, My Opportunities, Outcome — see [information_architecture.md](information_architecture.md).

# 18. State Machine

Monotonic truth: `discovered → matched → prioritized → contacted → engaged → qualified → site_review → pilot → deployed`.

Dispositions (do not erase truth): `active`, `watch`, `paused`, `lost`.

# 19. Backend Services

Keep scoring separate from extraction. Service list as in blueprint §19; map onto `app/services/` + new V1 modules under `app/api/v1/`.

# 20. Repository Structure

Suggested monorepo layout is aspirational. **This repository** continues with:

```text
app/                 # FastAPI API + services + models
worker/              # Celery tasks
readyforrobots-new/  # primary web client
docs/v1/             # frozen V1 contracts
migrations/          # Alembic
```

# 21. Ontology Package

Version ontology separately (`primitives`, job families, automation/replacement modes, facility nodes, loss reasons). Every prediction stores ontology/model version.

# 22. V1 Build Sequence

Use [implementation_plan.md](implementation_plan.md) slices (0–N), not the eight-sprint list, for scheduling. Forklift-first vertical path is mandatory.

# 23. Explicitly Out of Scope for V1

Full CRM, automated outreach, AI SDR, calling agent, calendar, proposals, marketplace, RaaS, deployment PM, telemetry, digital twins, CAD, facility simulation, full ROI calculator, customer marketplace, automated site surveys, global labor coverage, every robot category, mobile app.

# 24–25. Acceptance Criteria & Metrics

As in blueprint §24–25 and `docs/v1/README.md` Definition of Done (10 opportunities / robot pilot targets).

# 26. Core Product Loop

Give us your robot → understand its work → find humans doing that work → resolve the facility → determine why it matters → tell the seller who to call → qualify → capture what happened → find the next one better.

# 27. Engineering North Star

> Never confuse inference with truth.

Proprietary chain: SIGNAL → PREDICTION → SELLER ACTION → QUALIFICATION → DEPLOYMENT → OUTCOME.
