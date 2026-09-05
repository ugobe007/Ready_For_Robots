# Core Acceptance Stories

## E01 — Platform Foundation

- Authenticated users see only their organization's data.
- Sources preserve URL, type, capture time, content hash and provenance.
- Supported truth states: `observed`, `inferred`, `oem_verified`, `customer_confirmed`, `site_verified`, `deployment_verified`, `unknown`.
- API tests verify tenant isolation.

## E02 — Robot Intelligence

- User submits a public product URL.
- System extracts manufacturer, model, category and relevant specs.
- Units are normalized while original values remain preserved.
- Missing information remains UNKNOWN.
- Specs map to physical primitives and a Work Envelope.
- OEM corrections are retained historically as `oem_verified`.
- Material corrections trigger rematching (Sprint 4+; stub hook acceptable in Sprint 2).

## E03 — Work Ontology

- Seed and version primitives including mobility, load engagement, transport, placement, perception, interaction and exception handling.
- IDs never change after release.

## E04 — Labor Intelligence

- Capture employer, title, description, dates, employment type, wage, shift, differential, overtime and location.
- Resolve company and exact facility when evidence permits.
- Do not substitute headquarters for an unresolved facility.
- Preserve repeated and expired postings as history.

## E05 — Work Extraction

- Convert job descriptions into evidence-backed physical Tasks and Work Units.
- Classify work contribution as `PRIMARY`, `SIGNIFICANT`, `SECONDARY`, `INCIDENTAL`, or `UNKNOWN`.
- Work Units capture action, object, origin, destination, payload, distance, frequency, shift, environment, traffic, variability, human interaction and exceptions when known.

## E06 — Facility Work Graph

- Represent facility flows as nodes and edges with Work Units attached to edges.
- Multiple sources can corroborate the same flow.
- V1 visualization is intentionally simple.

## E07 — Robotability & Matching

- Calculate Robotability separately from robot-specific Work Match.
- Evaluate physical fit, mobility, load engagement, manipulation, environment, performance, human interaction and exception burden.
- Known hard blockers (payload, aisle width, lift height, environment, trailer incompatibility, …) prevent `call_now`.
- Engine must support `wrong_robot` and recommend a more appropriate automation mode when evidence supports it.

## E08 — Opportunity Intelligence

- Calculate Labor Pressure, Operational Exposure, Buyability, Evidence Confidence and Account Resolvability (plus Deployability per frozen seven-dimension set).
- One job posting cannot automatically imply a labor shortage.
- Customer-facing actions: `call_now`, `qualify`, `watch`, `wrong_robot`, `insufficient_evidence`; internal `do_not_surface`.

## E09 — Opportunity Radar

- Show matching facilities and counts by Call Priority.
- Filters: geography, industry, work type, shift, priority, automation thesis.
- Cards show facility, workflow, Work Match, Why Now, automation thesis, evidence strength.

## E10 — Opportunity Detail

- Concise Why This Opportunity Exists, Work Graph, decision panel.
- Three evidence sections: WHAT WE KNOW / WHAT WE INFER / WHAT WE DON'T KNOW.
- Inferences must never appear as known facts.

## E11 — Qualification Engine

- Register critical unknowns with decision impact and acquisition difficulty.
- Generate the minimum next-best questions.
- Customer answers create `customer_confirmed` truth, resolve unknowns, trigger rescoring, create a new immutable snapshot.

## E12 — Truth Engine

- State machine: `discovered → matched → prioritized → contacted → engaged → qualified → site_review → pilot → deployed`, with dispositions `watch`, `paused`, `lost`.
- Expansion facts attach to outcomes/events (not a required separate truth stage in OpenAPI).
- Loss reasons use structured categories: `WORK`, `ROBOT`, `ECONOMICS`, `CUSTOMER`, `TIMING`, `COMPETITION`, `DATA`.
- `RFR_PREDICTION_WRONG` is mandatory in the loss ontology.

## E13 — Activity

- Support: `NEW_CALL_NOW`, `LABOR_PRESSURE_INCREASED`, `NEW_SHIFT_DETECTED`, `NEW_RELATED_JOB`, `NEW_EVIDENCE`, `WORK_MATCH_CHANGED`, `PRIORITY_CHANGED`.
- V1 surface is an in-app feed.

## E14 — Golden Dataset

- See [06_golden_calibration.md](06_golden_calibration.md).

## E15 — Admin / QA

- Human review of extractions claims, facility merges, and match rationales.
- Inspectable model/prompt/ontology versions.
