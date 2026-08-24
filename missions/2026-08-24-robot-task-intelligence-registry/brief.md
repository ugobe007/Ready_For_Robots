# Foundation model + trained-task registry

**Date:** 2026-08-24  
**Type:** build  
**Agents:** Ontology + ProductSurface

## Goal

Catalog **trained robot tasks** (not just model names) from LeRobot, Open X-Embodiment, OpenVLA, Octo, LIBERO, RoboCasa, RoboTwin, Behavior-1K, π₀ / π₀.₅, and GR00T. Connect those learned skills to Robot Jobs so matching can separate:

- **Hardware Fit** — can this embodiment physically do the work?
- **Intelligence Fit** — does an existing policy know how to do the work?
- **Environment Fit** — does trained-task environment overlap the workplace?
- **Deployment Readiness** = Hardware Fit × Intelligence Fit × Environment Fit

Chain:

```
JOB → work units → required physical skills → available learned policies
  → compatible embodiments → compatible robots → vendors
```

## Honesty

- Do **not** invent that a candidate SKU “has OpenVLA / π₀ / GR00T.” Presence stays unknown.
- Chat LLMs are not warehouse or hospital policies.
- Trajectory counts and licenses only when publicly stated; otherwise null / unknown.
- Categorical verdict (`POSSIBLE_MATCH` / `NOT_A_MATCH`) stays. Fit scores are a **second layer**, not a generic `score`.

## Acceptance

1. Seed registry of 100–300 canonical trained tasks with ontology fields (task, skills, model, embodiment, data, verification, license).
2. Job match payload includes `fit` (hardware / intelligence / environment / deployment_readiness) plus ranked model matches and task-family coverage.
3. Job Card QUALIFY shows the second score without claiming the robot already carries those weights.
4. Tests: warehouse mixed-case work has HIGH pick-place coverage and LOW mixed-case-depallet coverage; intelligence fit is independent of SKU presence; no generic `score` field.

## Out of scope

SIGNAL / Cal. Model marketplace. Fake per-SKU checkpoints.
