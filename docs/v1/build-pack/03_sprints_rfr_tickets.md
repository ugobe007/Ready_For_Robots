# Sprint Plan & RFR Tickets

## Sprint 0 — Calibration & Contracts

| ID | Work |
| --- | --- |
| RFR-001 | Freeze truth-state enum |
| RFR-002 | Freeze opportunity-state enum |
| RFR-003 | Freeze Call Priority enum |
| RFR-004 | Seed primitive ontology v1 |
| RFR-005 | Define loss ontology v1 |
| RFR-006 | Build golden-dataset format |
| RFR-007 | Select first 10 robots |
| RFR-008 | Select first 50 jobs |
| RFR-009 | Label first ~100 calibration pairs |
| RFR-010 | Create automated evaluation harness |

**Exit:** Golden harness runs before scoring development.

## Sprint 1 — Foundation

| ID | Work | Repo note |
| --- | --- | --- |
| RFR-101 | Create monorepo | **Use existing repo** unless approved otherwise |
| RFR-102 | Configure PostgreSQL | Existing `DATABASE_URL` / Alembic |
| RFR-103 | Configure migrations | Continue Alembic chain |
| RFR-104 | Implement organizations/users | **Reuse** teams / user_profiles |
| RFR-105 | Implement companies | **Reuse** `companies` |
| RFR-106 | Implement facilities | **New** |
| RFR-107 | Implement sources | New table **or** claim-level source_* (decide in preflight) |
| RFR-108 | Implement robots | **Reuse** catalog + profile versions |
| RFR-109 | Implement primitives | Seed package + optional table |
| RFR-110 | Implement event log | **Reuse** `sales_experience_events` |
| RFR-111 | Add tenant-isolation tests | Teams scope |
| RFR-112 | Add provenance/truth utility | Shared claim helpers |

**Exit:** Core entities work safely.

## Sprint 2 — Robot Intelligence

Robot URL UI/API; fetch product pages; identity/spec extraction; unit normalization; primitive mapping; Work Envelope; Robot Profile; OEM correction; rematch trigger; golden extraction tests.

*(Core URL→profile path already landed — finish gaps only.)*

## Sprint 3 — Labor Intelligence

Source ingestion; job normalization; company/facility resolution; labor-signal parser/history; task extraction; physical-work classification; Work Unit extraction; primitive mapping; golden extraction tests; Admin QA v1.

## Sprint 4 — Matching

Robotability; Work Match; constraint comparison; hard-blocker engine; unknown detector; rationale; Wrong-Robot classifier; persistence/API; golden pair evaluation.

## Sprint 5 — Opportunity Intelligence

Labor Pressure; Signal Density; Operational Exposure; Buyability v0.1; Account Resolvability; Automation Thesis; Call Priority; opportunity creation; initial Prediction Snapshot; list API; regression tests.

## Sprint 6 — Seller Experience

Opportunity Radar; filters; cards; Opportunity Detail; Work Graph; Known/Infer/Unknown panel; evidence drilldown; qualification percentage; My Opportunities.

## Sprint 7 — Qualification + Truth

Unknown registry; decision-impact ranking; question generator/UI; customer-confirmed answers; recalculation; snapshots; state transitions; Outcome UI; structured loss reasons; Prediction Wrong; history API.

## Sprint 8 — Pilot Readiness

Activity feed; priority-change events; Top-10 report export; buyer-function inference; analytics; error/model telemetry; performance/security review; golden CI gate; pilot account setup and feedback dashboard.
