# ReadyForRobots V1 Build Package

**Status:** implementation source of truth for Robot Customer Acquisition Intelligence

This package converts the frozen product definition into buildable boundaries. It supersedes the broader workflow in `docs/mvp_product_specification_v1.md` wherever the two conflict.

## Product Boundary

ReadyForRobots V1 answers:

> Where should this robot company's next hour of sales effort go?

The seven-step journey is fixed:

1. Enter Robot
2. Understand Robot
3. Find Work
4. Find Facilities
5. Rank Opportunities
6. Qualify
7. Report Outcome

The initial supported robot categories are AMRs, autonomous forklifts, autonomous tuggers, and material-movement robots.

## Documents

| Artifact | Owner | Purpose |
| --- | --- | --- |
| **[build-pack/](build-pack/README.md)** | Eng + product | **Execution authority v1.0:** epics E01–E15, acceptance stories, RFR tickets, migrations, API order, golden dataset, DoD, copilot guardrails, Sprint 0/1 preflight |
| [information_architecture.md](information_architecture.md) | Product + frontend | Canonical routes, navigation, screen states, and wireframes |
| [data_model.md](data_model.md) | Backend + data | Tables, constraints, provenance, indexes, and migration order |
| [api_pipeline.md](api_pipeline.md) | Backend + frontend | Pipeline stages, endpoint behavior, jobs, errors, and event contracts |
| [openapi-v1.yaml](openapi-v1.yaml) | Backend + frontend | Machine-readable V1 HTTP contract |
| [implementation_plan.md](implementation_plan.md) | Engineering | Vertical slices, dependencies, acceptance gates, and legacy disposition |
| [engineering_blueprint.md](engineering_blueprint.md) | Product + eng | Consolidated blueprint paste + deltas vs this package |
| [gap_analysis.md](gap_analysis.md) | Engineering | Live codebase gap vs blueprint / docs (2026-08-10) |

**Next practical step:** Approve Sprint 0/1 preflight ([build-pack/08_preflight_sprint_0_1.md](build-pack/08_preflight_sprint_0_1.md)), then: *Implement Sprint 0 then Sprint 1 only. Do not invent requirements outside these specifications.*

## Architecture Decisions

1. **Facility is the central commercial object.** Company remains the parent legal/account identity.
2. **Every material fact is a claim with provenance.** The shared truth states are `observed`, `inferred`, `oem_verified`, `customer_confirmed`, `site_verified`, `deployment_verified`, and `unknown`.
3. **V1 has seven opportunity dimensions:** Work Match, Labor Pressure, Operational Exposure, Buyability, Deployability, Evidence Confidence, and Account Resolvability.
4. **Prediction freezes at PRIORITIZED.** Later facts append events and claims; they never mutate T0.
5. **Hard blockers override averages.** A known physical incompatibility cannot produce CALL NOW.
6. **WATCH, PAUSED, and LOST are dispositions.** The monotonic truth state remains separately queryable.
7. **V1 is seller-assisted intelligence.** No automated outreach, email sequencing, AI SDR, calling, calendar, proposal, or deployment-management surface appears in V1 navigation.
8. **Existing systems are reused where they fit.** `companies`, `signals`, `robots`, `sales_opportunities`, `sales_experience_events`, teams, and authentication remain canonical.

## Canonical Routes

| Route | Screen |
| --- | --- |
| `/` | Robot Input |
| `/robots/:robotId/review` | Robot Analysis and OEM correction |
| `/robots/:robotId/opportunities` | Opportunity Radar |
| `/opportunities/:opportunityId` | Opportunity Detail |
| `/opportunities/:opportunityId/qualify` | Dynamic Qualification |
| `/opportunities` | My Opportunities |
| `/opportunities/:opportunityId/outcome` | Outcome Capture |

`/results`, `/pipeline`, and `/crm` remain compatibility routes during migration. They are not the target V1 information architecture.

## Definition Of Done

A first customer can submit one supported robot URL and receive ten facility-level opportunities where:

- at least eight are commercially credible;
- at least five are worth pursuing;
- at least three were previously unknown;
- no more than two contain materially incorrect Work Graphs;
- every important value exposes source, timestamp, confidence, and truth state;
- the seller can qualify or reject an opportunity in under one minute;
- the original prediction remains unchanged after outcome reporting.
