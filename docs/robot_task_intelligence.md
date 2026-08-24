# Trained-task registry and Intelligence Fit

**Status:** Seed v1 (2026-08-24)  
**Surface:** Robot Job Card QUALIFY. Not SIGNAL. Not a model store.

ReadyForRobots already stores **task-model slots** (which policy a job needs; presence starts unknown). This layer catalogs **trained tasks** — what public VLAs and robot policies were actually trained on — and scores **Intelligence Fit** separately from **Hardware Fit**.

```
JOB
  → work units
    → required physical skills
      → available learned policies
        → compatible embodiments
          → compatible robots
            → vendors
```

Ontology insert:

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES
  → EMBODIMENT → MODEL → LEARNED SKILL → WORKFLOW → JOB REQUIREMENTS → MATCH
```

## Two scores (plus environment)

| Score | Question |
|-------|----------|
| **Hardware Fit** | Can this embodiment physically do the job? (requirement MATCHED / LIKELY / UNKNOWN / UNMET) |
| **Intelligence Fit** | Do public trained tasks/policies cover this job's skills? |
| **Environment Fit** | Do those trained tasks overlap this workplace (warehouse vs kitchen vs hospital)? |
| **Deployment readiness** | Hardware × Intelligence × Environment |

A robot with 95% hardware fit and 20% intelligence fit is not deployment-ready. π₀ may know pick-and-place well and still fail if reach, payload, or sensing are missing.

There is **no** generic match `score`. Categorical verdict (`POSSIBLE_MATCH` / `NOT_A_MATCH`) stays the gate. Fit is a second layer.

## Honesty

- Cataloging OpenVLA / Octo / π₀ / GR00T / LeRobot is **not** claiming a candidate SKU has those weights.
- Task-model `presence` stays `unknown` until evidence names a checkpoint on that robot.
- Chat LLMs are not warehouse, hospital, or CNC policies.
- Trajectory counts and licenses are filled only when the source states them.

## Seed sources

LeRobot, Open X-Embodiment, OpenVLA (incl. LIBERO fine-tunes), Octo, LIBERO, RoboCasa, RoboTwin, BEHAVIOR-1K, Physical Intelligence π₀ / π₀.₅, NVIDIA GR00T.

Machine-readable: `ontology/robot_task_registry.v1.json`  
Builder: `app/services/robot_task_registry_catalog.py`  
Scorer: `app/services/robot_intelligence_fit.py`

Example: mixed-case depalletizing decomposes to detect carton → estimate pose/grasp → reach/grasp/lift/orient/place. Pick-place coverage is HIGH; mixed-case depalletize coverage is LOW. Those are not the same job.
