# Database Migration Order

## Logical order (product)

Do not create scoring structures before underlying truth objects.

```text
001 organizations          → map to teams
002 users                  → map to user_profiles
003 companies              → exists
004 facilities             → NEW
005 sources                → NEW or claim-level only
006 primitives             → seed JSON ± table
007 robots                 → exists
008 robot_specs            → profile JSONB / robot_capabilities
009 robot_capabilities     → exists (Slice 1)
010 work_envelopes         → JSONB on robot_profile_versions
011 labor_signals          → NEW
012 jobs                   → job_observations
013 tasks                  → task_observations
014 work_units             → NEW
015 work_unit_primitives   → NEW or JSONB
016 work_graph_nodes       → JSONB refs OK per data_model
017 work_graph_edges       → NEW
018 work_matches           → NEW
019 opportunities          → extend sales_opportunities
020 opportunity_evidence   → evidence_claims
021 opportunity_unknowns   → NEW / JSONB on prediction
022 qualification_questions
023 qualification_responses → qualification_answers
024 prediction_snapshots   → opportunity_predictions
025 state_transitions      → sales_experience_events
026 outcomes               → deployment_outcomes
027 activity_events        → NEW or experience events
028 model_runs             → NEW
```

## Already applied in this repo

- `u5v6w7x8y9z0` — opportunity disposition
- `v6w7x8y9z0a1` — evidence_claims, robot_analyses, robot_profile_versions, robot_capabilities

## Sprint 0/1 concrete migrations

| Step | Action |
| --- | --- |
| S0 | No destructive schema — enums/ontology as versioned JSON under `packages/ontology` or `docs/ontology` |
| S1-a | `facilities` |
| S1-b | `sources` **if** approved; else document claim-level provenance as sufficient |
| S1-c | `primitives` table **or** load-only JSON with immutable IDs |
| S1-d | Provenance utility module (no table) |
| S1-e | Tenant isolation tests against teams |

Scoring tables (018+) wait until Sprint 4–5.
