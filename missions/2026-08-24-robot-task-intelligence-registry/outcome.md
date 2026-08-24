# Outcome — Foundation-model + trained-task registry

**Date:** 2026-08-24  
**Mission:** `missions/2026-08-24-robot-task-intelligence-registry`  
**Type:** build

## Diff

- Seeded **189 trained robot tasks** (LIBERO, RoboCasa, OXE, LeRobot, RoboTwin, BEHAVIOR-1K, sparse industrial) with models OpenVLA, Octo, π₀/π₀.₅, GR00T, SmolVLA, ACT, Diffusion Policy.
- Catalog: `app/services/robot_task_registry_catalog.py` → `ontology/robot_task_registry.v1.json`.
- Scorer: `app/services/robot_intelligence_fit.py`. Matcher payload `fit` adds Hardware Fit, Intelligence Fit, Environment Fit, and Deployment readiness (product). No generic `score`.
- Job Card QUALIFY shows the second layer. Does **not** claim a SKU has OpenVLA/π₀/GR00T. Task-model presence stays unknown.
- Mixed-case depalletize: pick-place HIGH, mixed-case depalletize LOW.

## Tests

- `PYTHONPATH=/workspace ./venv/bin/pytest tests/test_robot_intelligence_fit.py tests/test_m2_requirement_match.py tests/test_robot_task_models.py tests/test_robot_ontology.py -q`
  - New intelligence tests pass.
  - `test_no_percentage_and_unknowns_stay_unknown` pass (model coverage field is `coverage`, not `score`).
  - `test_healthcare_eldercare_delivery_matches_transport_robots` still fails on `origin/main` (Origin matching clinical_delivery). Untouched.
- `npx vitest run client/src/lib/robotJobCard.test.ts` — 5 passed.

## Follow-ups

- Ingest live Hugging Face LeRobot dataset cards instead of a static seed.
- Embodiment transfer: WidowX-trained OpenVLA ↛ arbitrary industrial arm without a fine-tune note.
- Site-qualified checkpoints (presence: present) when OEM evidence exists.
