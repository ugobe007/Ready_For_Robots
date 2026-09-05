# V1 API And Processing Pipeline

## Principles

- API prefix: `/api/v1`.
- Long-running crawl/extraction/matching uses durable analysis jobs; never hold an HTTP request open for the whole pipeline.
- POST endpoints accept `Idempotency-Key` where retries could duplicate records.
- Public analysis uses an opaque analysis token scoped to one job. Team data requires Bearer authentication.
- Every response includes `schema_version`.
- Every material fact returned to the UI includes `value`, `truth_state`, `confidence`, and `evidence_refs`.
- State transitions are commands with evidence gates, not arbitrary field patches.

## End-To-End Pipeline

```mermaid
sequenceDiagram
    actor Seller
    participant UI
    participant API
    participant Crawl as Robot Analyzer
    participant Labor as Labor Engine
    participant Match as Robotability Engine
    participant Rank as Opportunity Engine
    participant Truth as Truth Engine

    Seller->>UI: Submit robot URL
    UI->>API: POST /robot-analyses
    API-->>UI: 202 analysis_id + token
    API->>Crawl: Crawl and extract claims
    Crawl->>Truth: Store profile version + evidence
    UI->>API: GET /robot-analyses/{id}
    API-->>UI: needs_review + Robot Capability Profile
    Seller->>API: POST /robot-analyses/{id}/confirm
    API->>Truth: Append OEM corrections; create version
    API->>Labor: Start opportunity search
    Labor->>Truth: Facilities, historical signals, Work Units, Work Graphs
    Labor->>Match: Work Units + robot profile
    Match->>Truth: Work Matches and blockers
    Match->>Rank: Match + commercial dimensions
    Rank->>Truth: Opportunity + immutable prediction
    UI->>API: GET /robots/{id}/opportunities
    API-->>UI: Ranked radar
    Seller->>API: POST /opportunities/{id}/transitions
    Seller->>API: POST /opportunities/{id}/answers
    Seller->>API: POST /opportunities/{id}/outcomes
```

## Analysis Job States

`queued → crawling → extracting → needs_review → confirmed → finding_work → resolving_facilities → matching → ranking → complete`

Terminal states: `failed`, `unsupported_robot`, `insufficient_product_evidence`.

The response exposes stage, percentage, current message, retryability, warnings, and timestamps. Percentage is progress, not model confidence.

## Endpoint Inventory

### 1. Enter Robot

#### `POST /api/v1/robot-analyses`

Public when rate limits permit.

Request:

```json
{
  "source_url": "https://robotcompany.com/product",
  "description": null
}
```

Rules:

- require one of `source_url` or `description`;
- normalize and validate URL;
- reject unsupported schemes and private-network targets;
- deduplicate active analyses by normalized URL and requester scope;
- return `202 Accepted`.

Response:

```json
{
  "schema_version": "v1",
  "analysis_id": "uuid",
  "analysis_token": "opaque-public-token",
  "status": "queued",
  "status_url": "/api/v1/robot-analyses/uuid"
}
```

#### `GET /api/v1/robot-analyses/{analysis_id}`

Returns job state. At `needs_review`, includes the draft Robot Capability Profile and field-level claims.

### 2. Understand Robot

#### `POST /api/v1/robot-analyses/{analysis_id}/confirm`

Creates an immutable Robot Profile Version. Anonymous confirmation may continue the preview job; team ownership is attached after authentication.

Request:

```json
{
  "profile_etag": "sha256",
  "corrections": [
    {
      "field_path": "physical_capabilities.payload.max_kg",
      "value": 1500,
      "truth_state": "oem_verified",
      "note": "Current production specification"
    }
  ]
}
```

Reject stale `profile_etag` with `409 profile_changed`.

Response: profile version, summarized work envelope, unresolved critical fields, and `opportunity_search_id`.

#### `GET /api/v1/robots/{robot_id}/profiles/{version_id}`

Returns profile and all visible claims grouped as Known, Inferred, and Unknown.

### 3-5. Find Work, Resolve Facilities, Rank

#### `POST /api/v1/robots/{robot_id}/opportunity-searches`

Starts or reuses a search for a profile version. Optional filters: country, state/region, industry, and maximum facilities. V1 maximum is bounded operationally.

#### `GET /api/v1/opportunity-searches/{search_id}`

Returns pipeline stage and counts:

```json
{
  "status": "matching",
  "counts": {
    "labor_signals": 486,
    "facilities_resolved": 126,
    "work_units": 219,
    "matched": 82,
    "prioritized": 39
  },
  "warnings": []
}
```

#### `GET /api/v1/robots/{robot_id}/opportunities`

Query parameters:

- `profile_version_id`
- `priority[]`
- `country`, `state_region`
- `industry`, `work_type`, `automation_thesis`, `shift`
- `minimum_evidence`
- `cursor`, `limit` with maximum 50

Default order is decision class then internal rank. Internal score is not returned as a prominent customer field.

Card response includes opportunity ID, facility summary and precision, Work Unit summary, Work Match label, Why Now reasons, Automation Thesis, Evidence label, unknown count, blocker summary, and Call Priority.

`wrong_robot` opportunities are available through their filter but do not appear in the default pursuit queue.

### Opportunity Detail

#### `GET /api/v1/opportunities/{opportunity_id}`

Returns:

- permanent opportunity identity and current truth state/disposition;
- account and facility;
- robot profile version;
- immutable prediction;
- Work Units and simple Work Graph;
- seven dimension labels and confidence;
- Why This Opportunity Exists;
- Known, Inferred, Unknown, and Blockers;
- automation theses;
- qualification gap and next questions;
- buyer-function recommendation;
- append-only timeline;
- allowed commands based on current state and evidence.

The API computes allowed commands. The frontend does not recreate transition policy.

### 6. Qualify

#### `GET /api/v1/opportunities/{opportunity_id}/qualification`

Returns current qualification percentage, blocking unknowns, and a maximum of five questions ordered by Information Value. Each question includes input type, unit/options, impact, affected dimensions, and blocker warning.

Qualification percentage is coverage of decision-critical facts, not probability of closing.

#### `POST /api/v1/opportunities/{opportunity_id}/answers`

Request:

```json
{
  "question_id": "uuid",
  "answer": {"value": 180, "unit": "moves_shift"},
  "answer_state": "known",
  "truth_state": "customer_confirmed",
  "source": {"type": "customer_call", "occurred_at": "2026-08-10T18:00:00Z"}
}
```

Response includes the appended answer, recalculation diff, qualification gap, new blockers, next question, next recommended action, and permitted transitions.

Recalculation appends an `opportunity_recalculated` event. It does not change the original Prediction Record.

#### `POST /api/v1/opportunities/{opportunity_id}/transitions`

Request:

```json
{
  "command": "mark_engaged",
  "contact_result": "interested",
  "evidence_refs": ["evidence-uuid"],
  "occurred_at": "2026-08-10T18:00:00Z"
}
```

Commands:

- `mark_contacted`
- `mark_engaged`
- `mark_qualified`
- `request_site_review`
- `start_pilot`
- `mark_deployed`
- `watch`
- `pause`
- `resume`
- `mark_lost`

The service maps commands to truth-state/disposition changes and validates evidence gates.

`mark_lost` requires `loss_reason`. `pause` may include `resume_at`. `watch` requires a monitoring reason. V1 does not permit dragging arbitrary columns.

### 7. Report Outcome

#### `POST /api/v1/opportunities/{opportunity_id}/outcomes`

Request supports:

```json
{
  "outcome_type": "lost",
  "loss_reason": "payload",
  "prediction_wrong": true,
  "robot_profile_version_id": "uuid",
  "work_unit_ids": ["uuid"],
  "units_deployed": null,
  "deployment_scope": null,
  "metrics": {},
  "occurred_at": "2026-08-10T18:00:00Z"
}
```

For pilot/deployment outcomes, optional fields include units, dates, expected/actual volume and uptime, labor before/after, throughput before/after, human intervention, costs, payback, and expanded scope.

The endpoint must complete with only outcome type and the required controlled reason or deployment basics. Optional detail is progressively disclosed and takes under thirty seconds for the common path.

### My Opportunities

#### `GET /api/v1/opportunities`

Authenticated team queue. Filters by truth state, disposition, priority, robot, facility, next action, and qualification band. Default columns match the V1 table: Opportunity, Work, Priority, State, Qualification, Next Action.

### Notifications

#### `GET /api/v1/notifications`

Only V1 event types:

- `new_call_now_opportunity`
- `opportunity_heating_up`
- `new_evidence`
- `work_match_changed`

No messaging sequence notifications appear in the V1 shell.

## Transition Gates

| Command | Required current truth | Required evidence/result | New truth/disposition |
| --- | --- | --- | --- |
| system discover | none | resolved account or facility signal | discovered/active |
| system match | discovered | compatible Work Unit and robot profile | matched/active |
| system prioritize | matched | complete seven-dimension prediction | prioritized/active |
| mark contacted | prioritized+ | seller-confirmed contact attempt | contacted/active |
| mark engaged | contacted+ | structured customer response | engaged/active |
| mark qualified | engaged+ | critical workflow facts customer-confirmed | qualified/active |
| request site review | qualified+ | remote qualification supports assessment | site_review/active |
| start pilot | site_review+ | deployment conditions validated | pilot/active |
| mark deployed | pilot+ | production deployment confirmed | deployed/active |
| watch | any non-lost | monitoring reason | truth unchanged/watch |
| pause | any non-lost | pause reason | truth unchanged/paused |
| mark lost | discovered+ | controlled loss reason | truth unchanged/lost |

## Loss Reason Contract

Customer codes:

- Work: `wrong_workflow`, `low_volume`, `too_variable`, `insufficient_robotable_share`
- Robot: `payload`, `reach`, `speed`, `navigation`, `manipulation`, `environment`
- Economics: `roi`, `low_labor_cost`, `integration_cost`, `no_budget`
- Customer: `no_interest`, `no_champion`, `procurement`, `it_security`
- Timing: `too_early`, `project_delayed`, `project_already_awarded`
- Competition: `incumbent`, `competitor_selected`, `already_automated`
- Data: `rfr_prediction_wrong`

Store explanatory notes separately. `rfr_prediction_wrong` is never hidden inside `other`.

## Error Envelope

```json
{
  "schema_version": "v1",
  "error": {
    "code": "evidence_gate_failed",
    "message": "QUALIFIED requires customer-confirmed workflow facts.",
    "field_errors": [],
    "required_facts": ["moves_per_shift", "maximum_payload", "buyer_function"],
    "retryable": false
  }
}
```

Canonical codes: `invalid_url`, `unsupported_robot`, `analysis_failed`, `analysis_not_ready`, `profile_changed`, `not_found`, `forbidden`, `invalid_transition`, `evidence_gate_failed`, `hard_blocker_present`, `loss_reason_required`, `idempotency_conflict`, `rate_limited`.

## Background Job Reliability

- Persist job state before queueing work.
- Each stage is idempotent by `(analysis_id, stage, input_version)`.
- Retry network and parser failures with bounded backoff.
- Store source timestamp and extraction version.
- Do not mark the whole analysis failed when one source fails; return warnings and evidence coverage.
- Never delete historical labor signals when a source disappears.
- Re-ranking uses a new rules-version event; it never modifies the T0 prediction.

## Existing API Disposition

| Existing surface | V1 use |
| --- | --- |
| `/api/scout/scan-for-results` | Adapter during rollout; replaced by robot-analysis job |
| `/api/leads/pipeline` | Legacy company feed; not the V1 facility radar |
| `/api/crm/accounts` | Optional compatibility save; V1 writes opportunities directly |
| `/api/crm/accounts/{id}/send-outreach` | Not exposed in V1 UI |
| `/api/scout/activations` | Not used by V1; no automated outreach |
| `/api/crm/accounts/{id}/deployment-transition` | Internal compatibility adapter to V1 transition service |
