# V1 Implementation Plan

> **Execution authority moved to [`docs/v1/build-pack/`](build-pack/README.md).**  
> This file retains slice history. New work follows Sprint 0–8 tickets. Do not invent requirements outside the build pack + OpenAPI + data model.

## Delivery Strategy

Build one evidence-complete vertical path for autonomous forklifts before broad ingestion or category support:

`robot URL → verified profile → ten facility opportunities → one qualification answer → one structured outcome`

Each slice must produce a user-visible decision and preserve provenance. Do not build all tables first and defer the experience.

**Before expanding scoring:** complete Sprint 0 golden calibration (`build-pack/07_golden_calibration_spec.md`).

## Slice 0: Contract Alignment

**Goal:** prevent legacy CRM/outreach semantics from leaking into V1.

**Status (2026-08-10):** landed in code.

Build:

- [x] establish `/api/v1` router and shared error envelope (`app/api/v1/`);
- [x] change conversion service vocabulary to V1 states: `site_review` replaces `site_verified` / `solution_fit` / `economic_fit` / `expanding`;
- [x] add separate opportunity `disposition` (`active`/`watch`/`paused`/`lost`) + migration `u5v6w7x8y9z0`;
- [x] use seven V1 dimensions; remove standalone Deployment Readiness;
- [x] retain permanent opportunity ID and append-only events;
- [x] add feature flag `V1_ROBOT_INTELLIGENCE` for new routes (`GET /api/v1/meta` probe).

Acceptance:

- [x] save/contact cannot imply qualified;
- [x] WATCH/PAUSED do not move truth state backward;
- [x] prediction cannot be updated or deleted;
- [x] old routes continue to run behind compatibility adapters (CRM deployment-transition still works; lost/watch map to disposition).

Enable locally: `V1_ROBOT_INTELLIGENCE=true`.

## Slice 1: Robot Input And Verified Profile

**Goal:** user submits one supported robot and approves a source-grounded capability profile.

**Status (2026-08-10):** landed in code.

Backend:

- [x] create analysis-job storage (`robot_analyses`);
- [x] add robot profile version, capability, and evidence-claim models/migration (`v6w7x8y9z0a1`);
- [x] build URL safety/normalization and crawl adapter;
- [x] extract V1 category, Work Envelope, payload, lift, speed, runtime, navigation, environment, and human-interaction claims;
- [x] expose create/status/confirm endpoints under `/api/v1/robot-analyses`.

Frontend:

- [x] Home primary action switches when `V1_ROBOT_INTELLIGENCE` is on;
- [x] Robot Analysis route `/robots/analysis/:analysisId`;
- [x] Confirmed profile shell `/robots/:robotId/review` with OEM payload correction.

Tests:

- [x] SSRF/private-network rejection;
- [x] source excerpt required for observed claims;
- [x] unknown differs from false;
- [x] correction creates a new immutable profile version;
- [ ] anonymous analysis resumes across auth (deferred — token in sessionStorage for Slice 1).

Exit gate: one autonomous-forklift product URL yields a reviewable profile with no invented field values.

Enable: `V1_ROBOT_INTELLIGENCE=true` (and run migration `v6w7x8y9z0a1`).

## Slice 2: Facility And Historical Labor Evidence

**Goal:** resolve job evidence to durable physical facilities and preserve time series.

Backend:

- add Facility, Labor Signal, Job Observation, Task Observation, and Evidence Claim tables;
- adapt existing jobs/careers ingestion only;
- implement source fingerprinting, first/last seen, and active/historical state;
- resolve company then facility with explicit location precision;
- create merge review for ambiguous facilities.

Frontend:

- internal evidence inspection page or admin view;
- show facility precision and source history in opportunity detail scaffolding.

Tests:

- repeated posting updates one labor-signal time series;
- disappeared posting becomes inactive, not deleted;
- same company can own multiple facilities;
- anonymous staffing post remains low resolvability and does not fabricate a facility.

Exit gate: calibration sources produce ten distinct, source-backed facility candidates.

## Slice 3: Job To Work Graph

**Goal:** transform source language into bounded Work Units with lineage.

Backend:

- add Work Unit, task-to-work evidence, Work Graph, and edge models;
- extract action, object, origin, destination, sequence, shift, and unknowns;
- preserve task excerpts and extraction version;
- construct simple structural flow.

Frontend:

- build `WorkGraphSimple` with text alternative;
- add Known/Inferred/Unknown evidence triad.

Tests:

- every task and Work Unit has evidence refs;
- omitted payload remains unknown;
- graph branches preserve warehouse/trailer alternatives;
- no numeric work volume is invented.

Exit gate: at least eight of ten forklift calibration facilities have commercially credible Work Graphs, with no more than two material errors in customer review.

## Slice 4: Robotability And Hard Blockers

**Goal:** compare Work Units against the verified robot profile without hiding incompatibility in an average.

Backend:

- add Work Match model and deterministic V1 rules;
- evaluate task capability, payload, mobility, manipulation, environment, human interaction, throughput, and exceptions;
- output matched, unknown, and incompatible constraints;
- calculate internal score and customer label;
- hard blocker forces wrong-robot policy.

Frontend:

- show Work Match label, confidence, unknowns, and blocker banner;
- link each comparison to robot/work evidence.

Tests:

- known 1,800 kg payload vs. 1,500 kg max is a blocker;
- unknown aisle width is not incompatibility;
- blocker prevents CALL NOW regardless of average score;
- customer sees labels, not false engineering precision.

Exit gate: positive and negative controls in the autonomous-forklift calibration report classify correctly.

## Slice 5: Opportunity Radar And Immutable Prediction

**Goal:** rank ten facility decisions by seller effort.

Backend:

- add prediction table and opportunity facility/profile columns;
- implement seven independent dimension policies;
- implement Call Priority decision tree;
- create DISCOVERED, MATCHED, and PRIORITIZED events;
- expose search progress, radar list, and detail endpoints.

Frontend:

- build Opportunity Radar filters/cards/counts;
- build Opportunity Detail header, dimensions, evidence triad, graph, and timeline;
- support anonymous preview of ten results before registration where cost permits.

Tests:

- one posting alone cannot claim labor shortage;
- unresolved facility cannot become CALL NOW;
- prediction includes all evidence available at T0 and remains immutable;
- wrong-robot and insufficient-evidence negative controls remain visible but out of default pursuit queue.

Exit gate: one robot produces ten ranked facility decisions with at least eight commercially credible and five seller-accepted.

## Slice 6: Dynamic Qualification

**Goal:** reduce decision uncertainty with the fewest questions.

Backend:

- add question library and append-only answers;
- implement transparent Information Value ordering;
- recalculate current dimensions and qualification gap after answers;
- enforce CONTACTED, ENGAGED, QUALIFIED, and SITE REVIEW gates;
- preserve prediction/current comparison.

Frontend:

- build Qualification screen, one question at a time;
- add source/truth-state selection;
- show before/after recalculation and next action;
- add Mark Contacted and structured contact-result control without sending email.

Tests:

- maximum payload question outranks lower-impact economics when it could block fit;
- answered reliable facts are suppressed;
- unknown answer does not inflate qualification;
- customer-confirmed answer appends claim and answer, never edits source inference;
- seller can complete a common answer in under one minute.

Exit gate: qualification removes measurable uncertainty and produces the correct next decision for calibration cases.

## Slice 7: Queue, Outcome, And Learning

**Goal:** close the loop without building a CRM.

Backend:

- expose minimal team opportunity queue;
- implement watch/pause/resume dispositions;
- add V1 loss ontology and deployment outcome storage;
- append structured outcomes and derive stage-specific labels;
- add metrics queries for Discovery Alpha, Seller Acceptance, Precision@10, engagement/qualification conversion, Work Graph accuracy, wrong-robot accuracy, and Qualification Gain.

Frontend:

- build My Opportunities table/list;
- build thirty-second Outcome flow;
- surface `ReadyForRobots prediction was wrong` prominently;
- add four notification types.

Tests:

- loss requires controlled reason;
- prediction-wrong is queryable independently;
- optional win metrics never block save;
- CRM notes cannot substitute for structured outcome;
- outcome changes labels without mutating T0.

Exit gate: a seller can report pursued/not pursued, engagement, loss, pilot, or deployment and the cohort report reflects it.

## Slice 8: First Customer Calibration

**Goal:** prove intelligence value, not automation volume.

Run one robot/company cohort and measure:

- ten opportunities per robot;
- eight or more commercially credible;
- five or more seller would pursue;
- three or more previously unknown;
- no more than two materially incorrect Work Graphs;
- at least one engagement attributable to the intelligence.

Do not expand robot categories until this gate passes for autonomous forklifts/material movement.

## Legacy Capability Policy

Existing automated outreach, sequences, AI SDR, calling, calendar, proposal, CRM, and HubSpot code may remain operational for existing users. During V1 development:

- do not invoke it from `/api/v1`;
- do not show it in V1 navigation;
- do not delete it as part of V1 slices;
- do not use outreach volume as V1 success evidence;
- do not allow legacy CRM stages to establish physical truth.

After intelligence-value validation, automated execution can be tested as a separate product layer.

## Test Matrix

| Layer | Required checks |
| --- | --- |
| Schema | constraints, FK indexes, append-only prediction/answers/claims, tenant isolation |
| Ingestion | source retention, dedupe, history, URL safety, failure recovery |
| Extraction | excerpts, unknown preservation, versioning, no fabricated measurements |
| Matching | hard blockers, units, labels, negative controls |
| Ranking | independent dimensions, decision tree, resolvability gates |
| API | OpenAPI validation, idempotency, auth/token scope, transition errors |
| UI | desktop/mobile, keyboard, loading/empty/error, no overlap, source access |
| Learning | point-in-time features, maturity windows, stage-specific labels, no T0 mutation |

## Initial Engineering Tickets

1. `V1-001` Add `/api/v1` router, error envelope, and feature flag.
2. `V1-002` Add Robot Profile Version, Capability, Evidence Claim models and migration.
3. `V1-003` Implement safe robot-analysis job and URL ingestion.
4. `V1-004` Build Robot Input and Robot Analysis screens.
5. `V1-005` Add Facility and historical Labor Signal models/migration.
6. `V1-006` Build facility resolver with precision and merge tests.
7. `V1-007` Add Job/Task/Work Unit/Work Graph models and extraction.
8. `V1-008` Implement forklift Work Match and hard-blocker policy.
9. `V1-009` Add immutable Prediction Record and seven-dimension policy.
10. `V1-010` Build Opportunity Radar and Detail.
11. `V1-011` Add qualification question/answer engine and transition gates.
12. `V1-012` Build Qualification screen.
13. `V1-013` Add minimal opportunity queue, outcomes, and notifications.
14. `V1-014` Build My Opportunities and Outcome screens.
15. `V1-015` Run first customer calibration and publish metric deltas.

## First Coding Slice

Start with `V1-001` and `V1-002`, then immediately build a thin Robot Input → Robot Analysis path using a fixture-backed extractor. This establishes the new API, provenance model, and frontend route with a runnable result before connecting the crawler.
