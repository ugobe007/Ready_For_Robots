# Robot-Directed Discovery — Thin Universal Core (persist)

**Status:** **SCHEMA FROZEN** (2026-08-15). Do not churn. **Do not apply Fly migration yet** — conversion test runs on UI fixtures.  
**Rule:** Universal schema = claim + reasoning. Robot-family extensions = physics.

---

## Object semantics (locked)

| Object | Role |
|--------|------|
| `work_claim` | Physical work appears to occur here (first-class uncertainty) |
| `robot_job` | Work is sufficiently defined and robot-compatible to investigate — **solution-neutral** |
| `robot_job_match` | This particular robot appears capable of doing it |
| `discovery_profile_id` | Provenance: which profile’s search caused us to find the job |
| `job_evidence` | Observation backing a claim and/or job (≥1 parent required) |
| `automation_interpretation` | How a profile would own part of a claimed workflow |
| `robot_capability_profile` | What a robot can do (envelope-derived) |

```
work_claim  →  “work probably here”
robot_job   →  “defined enough to investigate”   (not owned by a robot)
robot_job_match → “this robot can do it”
discovery_profile_id → “this robot’s search found it”
```

**Never** encode an “Origin Job.” Encode a Robot Job *discovered while searching through Origin’s capabilities*.

---

## Design rule

```
robot_job.core          → identity, place, action, confidence, evidence, status
robot_job.requirements  → JSONB extension (physics) — shape varies by discovery lens
robot_job.discovery_*   → provenance only
robot_job_match         → compatibility (many robots ↔ one job)
```

**Never** universal columns for: `load_interface` · `floor_surface` · `grasp_type` · `sensor_modality`

| Discovery lens | Example `requirements` payload |
|----------------|--------------------------------|
| transport_amr (Origin) | `{load_interface, path, payload}` |
| floor_scrub (Neo) | `{floor_surface, spatial_unit, condition}` |
| inspection_mobile (Spot) | `{inspection_target, sensor_modality, route, observation_frequency, hazard_environment}` |

`discovered_via_capability_family` is optional provenance (which lens found it).  
A job must **not** require a single exclusive `capability_family` — kit delivery may fit AMR, humanoid, and mobile manipulator.

---

## Funnel

```
Robot Capability Profile
  → Work Translation
  → Robot-Directed Search
  → Localized Work Observations
  → Work Claims
  → Automation Interpretation
  → Robot Jobs          (+ discovery_profile_id provenance)
  → Robot Job Match     (compatibility)
```

---

## Evidence

`job_evidence` check: `work_claim_id IS NOT NULL OR robot_job_id IS NOT NULL`  
Same row may support both claim and promoted job.

---

## `source_run` (string today)

Opaque experiment id string. Future first-class `discovery_run` is expected — leave room; do not invent semantics that block that upgrade.

---

## Seeds (keep separate)

| Artifact | Role |
|----------|------|
| `docs/product_sim/rdd_demo_jobs.json` | **UI fixture only** (`kind: ui_fixture`) |
| `scripts/seed_rdd_demo.py` | Loads fixture → profiles + jobs + matches (no claim chain) |
| `scripts/seed_rdd_experiment.py` | Placeholder for real ledger import (Evidence→…→Match) |

---

## Tables

`app/models/robot_directed_discovery.py` · migration `rdd0a1b2c3d4_add_robot_directed_discovery_core`
