# WORK Unit Reconstruction

Reconstruct physical **WORK** from job / labor signal text onto the shared `primitives.v1` spine.

**Spine:** [`ontology/primitives.v1.json`](../ontology/primitives.v1.json)  
**Architecture:** [`docs/rfr_intelligence_architecture.md`](rfr_intelligence_architecture.md)

```
JOB TEXT ──► WORK UNIT (task, object, origin, destination, action_chain)
                │
                ▼
         required primitives.v1 codes
                │
                ├── Robot→Job: which facilities have matching WORK?
                └── Job→Robot: which robots SUPPORT these primitives?
```

## Modules

| Module | Role |
|--------|------|
| `app/services/work_unit_reconstruct.py` | Job/signal text → WORK unit + evidence |
| `app/services/robot_primitives.py` | Robot categories → supported primitives |
| `app/services/primitive_match.py` | Coverage score + hard blockers (wrong machine) |
| `app/services/market_graph_loop.py` | OBSERVE→UNDERSTAND→MATCH via spine |
| `POST /api/v1/market-graph/reconstruct` | Dry-run Job→Robot for a posting |
| `GET /api/v1/market-graph/work-units` | Latest reconstructed units from snapshot |

## Truth states

Reconstruction is **Knowledge / SIGNAL_INFERRED**. Customer confirmation and site surveys later write Truth edges (`CUSTOMER_CONFIRMED`, `SITE_VERIFIED`, `DISPROVED`).

## Hard blockers

| Code | Meaning |
|------|---------|
| `WRONG_MACHINE_TUGGER` | Work needs tow/hitch; robot is forklift-class without tow |
| `WRONG_MACHINE_FORKLIFT` | Work needs pallet fork/lift; robot is tugger-only |
| `PARTIAL_ONLY_MANIPULATION` | Mixed case handling vs forklift-only |

## Example

```bash
curl -s -X POST "$API/api/v1/market-graph/reconstruct" \
  -H 'content-type: application/json' \
  -d '{
    "job_title": "Line Replenishment Associate - Tugger Route",
    "text": "Pull cart trains on timed milk-runs…",
    "robot_categories": ["autonomous_forklift"]
  }'
```

Expect low match + `WRONG_MACHINE_TUGGER`.

## Persistence

Tables: `work_units`, `work_matches` (migration `z0a1b2c3d4e5`).  
Written by `persist_market_graph_work` during the market-graph loop; Pipeline feed attaches overlays via `best_work_overlays_for_companies`.

## Next

- Crosswalk `physical.*` (robotability calibration) ↔ `primitives.v1`
- Robot product-page claims → primitive cards (beyond category defaults)
- Results page Work Match (Pipeline done)
- Link Deployment Evidence into Work Match scoring numerically
