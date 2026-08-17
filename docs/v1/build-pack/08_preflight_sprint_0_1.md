# Preflight — Sprint 0 & 1

**Status:** Decisions locked 2026-08-10 — implementation authorized for Sprint 0 then Sprint 1 only.

## Locked decisions

| # | Decision |
| --- | --- |
| Q1 | **First-class `sources` table** + claims reference `source_id` |
| Q2 | **DB-compliant primitives** — seed JSON + `primitives` table for S0/1 |
| Q3 | **`teams` = organization** — no parallel organizations table |
| Q4 | **`expanding` is not a truth stage** — see recommendation below |
| Q5 | **OpenAPI paths only** (`/robot-analyses`, …). Hunter.io / Anthropic are available in the stack but **out of Sprint 0/1** and out of V1 seller nav (email finding = deferred; no outreach) |
| Q6 | Robot URL→profile already shipped — Sprint 2 = gap-fill only |
| Q7 | Job mix = Build Pack 15/10/10/5/5/5 |
| Q8 | **Progressive V1** behind `V1_ROBOT_INTELLIGENCE` (locked); **no Home redesign in S0/1** |

### Q4 recommendation (adopted)

Keep monotonic stages ending at `deployed` (OpenAPI). Represent expansion as:

- `deployment_outcomes.outcome_type = expanded` (or equivalent), and/or
- experience-event facts `{ "expansion": true }`

Do **not** add `expanding` to `OpportunityState` unless OpenAPI is explicitly amended later.

### Q8 recommendation (locked 2026-08-10)

Surface V1 progressively behind `V1_ROBOT_INTELLIGENCE`:

1. **Home stays SIGNAL** — headline/CTA remain buyer-finding (`Find Companies That Need Your Robots` / **Find Buyers**). Do not hijack Home for robot-URL analysis.
2. **V1 analysis** lives on `/robots/analysis/:id` (and APIs) — not the primary Home action.
3. **Next (Sprint 6):** V1 shell nav — Robot · Radar · Opportunities · Activity (hide Pipeline/CRM/outreach)
4. **Optional:** per-team entitlement later 

Hunter email enrichment, if ever used, stays behind post-V1 or admin-only tools — never as V1 Call Priority UI.

### Catalog vs golden (locked with Q1 clarification)

- **Product catalog** = `manufacturers` → `robot_families` → `robot_models` → `robot_configurations` (+ legacy `robots` projection). See [robot_catalog_hierarchy.md](../robot_catalog_hierarchy.md).
- **`robot_companies`** = GTM/leads only — never capability storage.
- **Calibration** = Tier-1 (~30 OEMs / 50–75 models), not a 10-robot cap. Golden pairs bind to `robot_model` slugs.
- **V1 supported categories** = `autonomous_forklift`, `amr`, `autonomous_tugger`, `material_movement`, **`humanoid`**
- **V1 target industries**: Logistics, Manufacturing, Hospitality, Healthcare, Food Service, Casinos & Gaming, Retail, Defense — `app/domain/v1_coverage.py`
- **Commercial maturity**: `concept|prototype|pilot|commercial|production|discontinued|unknown`

---

## Repository structure

Continue existing monorepo (see prior §1). Ontology lives in `docs/ontology/` + DB tables.

## Migration plan (executing)

| Order | Change | Sprint |
| --- | --- | ---: |
| 1 | Enum/ontology JSON + Python module | 0 |
| 2 | Golden format + harness | 0 |
| 3 | `sources` | 1 |
| 4 | `facilities` | 1 |
| 5 | `primitives` (+ seed) | 1 |
| 6 | Provenance utility `app/services/truth.py` | 1 |
| 7 | Tenant isolation tests | 1 |

## Ticket order

RFR-001→005 → 006→010 (Sprint 0 exit) → RFR-106/107/109/112 → RFR-111 (Sprint 1 exit).
