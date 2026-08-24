# Outcome — Job task models

**Date:** 2026-08-24  
**Mission:** `missions/2026-08-24-job-task-models`  
**Type:** build

## Diff

- Ontology: `ontology/task_model_ontology.v1.json` + `ROBOT_TASK_MODEL_ONTOLOGY.md`. Product term is **task model**. Internal nickname “certificate” is never used in UI/API.
- Resolver `app/services/robot_task_models.py` maps job tape/industry/title → required slots. Presence always starts `unknown`. Lookups are search destinations (OEM store, Isaac, Hugging Face robotics), not fake “this robot has GR00T.”
- Matcher attaches `required_task_models` on every Job Card. Hardware-capable + model unknown stays **conditional**. Open question: which policy covers this work, and where is it published?
- Jobs UI: **Task models** section on the expanded card. Copy names the distributor hole (resell chassis vs buy/train the policy).
- Spine now: `HARDWARE → CAPABILITIES → TASK MODELS → WORKFLOWS → JOB REQUIREMENTS → MATCH`.

## Tests

- `./venv/bin/python -m pytest tests/test_robot_task_models.py tests/test_robot_ontology.py -q` pass.
- `npx vitest run client/src/lib/robotJobCard.test.ts client/src/lib/jobsWorkflow.test.ts` 32 passed.
- `tests/test_m2_requirement_match.py::test_healthcare_eldercare_delivery_matches_transport_robots` fails on `origin/main` already (Origin matching clinical_delivery). Untouched.

## Follow-ups

Evidence that a candidate *carries* a named task model. Do not build a model storefront. Do not hop this onto SIGNAL/Cal.
