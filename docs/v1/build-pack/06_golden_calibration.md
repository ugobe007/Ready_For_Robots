# Golden Calibration Dataset

Create **before** aggressively tuning prompts or scoring.

## Composition

### Robots (10)

| Count | Class |
| ---: | --- |
| 2 | Autonomous forklifts |
| 2 | AMRs |
| 2 | Autonomous tuggers |
| 1 | Pallet-moving AMR |
| 1 | Mobile manipulator |
| 1 | Warehouse humanoid |
| 1 | Intentionally poor-fit robot |

Seed file: `docs/robot_set_v0_1.json` (extend/align to this mix; mark verification status).

**Not a product limit.** Full OEM inventory lives in `robot_companies` / `robots`. See [catalog_vs_golden.md](../../calibration/catalog_vs_golden.md).

### Jobs (minimum 50)

| Count | Class |
| ---: | --- |
| 15 | Strong transport |
| 10 | Mixed material-handler |
| 10 | Tugger / line-replenishment |
| 5 | Superficially attractive wrong-fit |
| 5 | Low-information |
| 5 | Negative controls |

Collection frame: `docs/calibration/robotability_jobs_50_v0_1.json`.

### Pairs

Approximately **100** manually reviewed robot×job (or Work Unit×robot) calibration pairs emphasizing positives, ambiguity, wrong-robot, hard blockers, and low-evidence cases.

Expectations: `docs/calibration/golden_expectations_v1.json`.

## Golden record shape

```json
{
  "case_id": "GOLD-001",
  "robot_id": "robot_af_01",
  "job_id": "job_001",
  "expected": {
    "robotability": "HIGH",
    "work_match": "EXCELLENT",
    "call_priority": "CALL_NOW",
    "automation_thesis": ["REPLACE", "PROTECT"],
    "required_unknowns": ["moves_per_shift", "payload_max"],
    "must_not_claim": ["labor_shortage", "confirmed_robot_budget"]
  }
}
```

API runtime values remain lowercase; golden files may use uppercase product labels — harness normalizes.

## Evaluation classes

1. Extraction accuracy  
2. Robot Match  
3. Negative controls  
4. Hard blockers  
5. Evidence discipline  
6. Unknown detection  
7. Call Priority  

## Initial hard gates

| Gate | Threshold |
| --- | --- |
| Hallucinated factual claims on golden set | **0** |
| Known hard-blocker recall | **100%** |

Every AI-derived record stores **model, prompt, and ontology versions**. Prompt/model changes require golden regression evaluation.

## Mandatory control questions

1. Did Riviana-class forklift positives still rank highly for an autonomous forklift?  
2. Did the tugger workflow still reject the forklift?  
3. Did the mixed Material Handler remain partial automation rather than full replacement?  

Controls index: `docs/calibration/golden_controls_v1.md`.
