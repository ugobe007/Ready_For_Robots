# ReadyForRobots V1 Build Pack

**Version:** 1.0  
**Companion:** [Engineering Blueprint](../engineering_blueprint.md) + frozen contracts in `docs/v1/`  
**Status:** Execution authority for engineering and coding copilots

Build the smallest production-capable system that proves:

```text
Robot URL → Capability Profile → Work Envelope → Labor Signals →
Facility + Work Units → Work Match → Call Priority → Seller
Qualification → Outcome → Learning
```

Optimize for **prediction quality and learning**, not feature count.

The first defensible asset is:

```text
ROBOT ↔ CAPABILITY ↔ WORK ↔ FACILITY ↔ EVIDENCE ↔ PREDICTION ↔ OUTCOME
```

---

## Documents in this pack

| File | Contents |
| --- | --- |
| [README.md](README.md) | This file — mission, rules, epics, DoD, pilot gate, deferred scope |
| [00_copilot_guardrails.md](00_copilot_guardrails.md) | Pasteable agent instructions |
| [01_epics.md](01_epics.md) | E01–E15 |
| [02_acceptance_stories.md](02_acceptance_stories.md) | Core acceptance stories by epic |
| [03_sprints_rfr_tickets.md](03_sprints_rfr_tickets.md) | Sprint 0–8 + RFR ticket IDs |
| [04_migration_order.md](04_migration_order.md) | Logical 001–028 + repo mapping |
| [05_api_order.md](05_api_order.md) | Implementation order + OpenAPI path mapping |
| [06_golden_calibration.md](06_golden_calibration.md) | Dataset composition, golden record, hard gates |
| [07_definition_of_done.md](07_definition_of_done.md) | AI / scoring / screen DoD |
| [08_preflight_sprint_0_1.md](08_preflight_sprint_0_1.md) | Repo structure, migration plan, deps, open questions |

---

## Non-negotiable product rules

1. **Facility** is the commercial entity; never collapse facilities into headquarters.
2. **Jobs** are signals, not leads.
3. **Work Units** are the fundamental physical-work object.
4. **Robotability** and **Work Match** are different.
5. Known **hard blockers** override aggregate scores.
6. **Unknown** is not incompatible.
7. **Inference** is never presented as observed fact.
8. Every important claim preserves **source, timestamp, confidence, and truth state**.
9. **Prediction snapshots** are immutable.
10. The product must be capable of saying **WRONG ROBOT**.
11. The seller sees **decisions**, not unexplained AI scores.
12. Do **not** build CRM or automated outreach in V1.

### Truth-state vocabulary (API casing)

Product language may use `OBSERVED` etc. **HTTP/DB canonical values are lowercase** per `openapi-v1.yaml`:

`observed` | `inferred` | `oem_verified` | `customer_confirmed` | `site_verified` | `deployment_verified` | `unknown`

### Call Priority (API casing)

`call_now` | `qualify` | `watch` | `wrong_robot` | `insufficient_evidence` | `do_not_surface` (internal)

### Opportunity truth stages vs dispositions

Monotonic stages: `discovered → matched → prioritized → contacted → engaged → qualified → site_review → pilot → deployed`  
(`expanding` is **not** a separate V1 truth stage in frozen OpenAPI — capture expansion as outcome/event facts.)

Dispositions (do not erase truth): `active` | `watch` | `paused` | `lost`

---

## Epic map (E01–E15)

| Epic | Name | Outcome |
| --- | --- | --- |
| E01 | Platform Foundation | Canonical data model and tenant-safe app |
| E02 | Robot Intelligence | URL → verified Robot Capability Profile |
| E03 | Work Ontology | Shared language for capabilities and physical work |
| E04 | Labor Intelligence | Jobs → facility-level labor signals |
| E05 | Work Extraction | Job descriptions → Tasks → Work Units |
| E06 | Facility Work Graph | Physical work organized into facility flows |
| E07 | Robotability & Matching | Work Unit ↔ Robot compatibility |
| E08 | Opportunity Intelligence | Commercial prioritization |
| E09 | Opportunity Radar | Seller discovery experience |
| E10 | Opportunity Detail | Evidence-backed account intelligence |
| E11 | Qualification Engine | Unknowns → next-best questions |
| E12 | Truth Engine | Prediction → feedback → outcome history |
| E13 | Activity / Signal Change | Opportunity heartbeat |
| E14 | Golden Dataset & Evaluation | Regression protection |
| E15 | Admin / QA | Human review and debugging |

---

## Immediate build order

1. Create / use repository (this repo — do not greenfield unless approved).
2. Create canonical enums.
3. Seed ontology v1.
4. Build golden-dataset format.
5. Label calibration cases.
6. Build evaluation harness.
7. Create database migrations (mapped to existing Alembic).
8. Create provenance/truth utilities.
9. Implement core entities (facilities/sources/primitives gaps).
10. Add tenant isolation tests.

**Do not begin with the homepage.**

---

## First instruction to the coding copilot

Read the Engineering Blueprint and this Build Pack completely before writing code. Implement **Sprint 0 and Sprint 1 only**. Do not add later-sprint functionality. Do not reinterpret UNKNOWN, scoring thresholds, state enums, ontology IDs, or product scope.

**Before implementation, return:**

1. Proposed repository structure  
2. Migration plan  
3. Sprint 0/1 ticket dependency order  
4. Unresolved implementation questions  

After approval, implement against acceptance criteria and Definition of Done.

→ Preflight answers live in [08_preflight_sprint_0_1.md](08_preflight_sprint_0_1.md).

---

## Pilot success gate

| Metric | Gate |
| --- | ---: |
| Commercially credible Top 10 | ≥ 8/10 |
| Seller would pursue | ≥ 5/10 |
| Previously unknown | ≥ 3/10 |
| Materially wrong Work Graph | ≤ 2/10 |
| Known hard blockers missed | 0 |
| Hallucinated factual claims | 0 |

Strongest qualitative signal: **"Show me the next ten."**

## Explicitly deferred after V1 validation

Buyer-person expansion, CRM integrations, outbound sequencing, automated account monitoring, full ROI modeling, site-survey workflows, deployment management, telemetry, robot performance benchmarks, customer-side robot sourcing, marketplace.
