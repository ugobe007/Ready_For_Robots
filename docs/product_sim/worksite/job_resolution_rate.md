# Resolution funnel + Actionable Job Yield

**Principle:** JRR >70% is not the goal if it requires expensive per-company research.  
Measure whether **repeatable sources + inference** move the funnel.

```bash
python3 scripts/worksite_origin_baseline.py
```

Outputs: `origin_resolution_funnel.json`, `origin_jrr_baseline.json`, `pipeline_origin_snapshot.json`.

---

## Metrics

| Metric | Meaning |
|--------|---------|
| **WRR** | Companies with ≥1 **accepted** Worksite |
| **WPR** | Of accepted Worksites, share that are legitimate (gold/audit) |
| WCR | Function known on accepted Worksite |
| WorkRR | Plausible physical work (pattern OK for EXPECTED) |
| ERR | ≥1 EVIDENCED work unit |
| JRR expected / strict | Worksite+work (+ evidence for strict) |
| AJY | Jobs per 100 companies without manual research |

Prefer high **WPR** over high **WRR**. False Worksites poison everything downstream.

### Two JRR definitions

| Metric | Meaning |
|--------|---------|
| **JRR expected** | Worksite + type + pattern work. Probabilistic discovery. Show as EXPECTED WORK. |
| **JRR strict** | Also ≥1 EVIDENCED/CONFIRMED work unit. Higher prominence. |

EXPECTED is useful discovery. Do not require courtroom evidence for every first-result row — but label it honestly.

---

## Failure classes (diagnostic on unresolved)

| Failure | Meaning | Generalized fix |
|---------|---------|-----------------|
| `no_worksite_known` | Ops locations absent | Location discovery |
| `worksite_buried_in_source` | Place exists in article/posting | Extraction |
| `multiple_worksites` | Network count / many sites, none picked | Ranking / disambiguation |
| `hq_contamination` | Only corporate location available | Location classification |
| `site_type_unknown` | Place found, function unclear | Worksite classification |
| `work_unknown` | Site known, workflow uncertain | Pattern library |
| `evidence_weak` | Pattern only | Evidence retrieval |
| `signal_not_site_specific` | WHY NOW is company-level | Propagate carefully; don't fake WHERE |

Treat unresolved Origin rows as a **diagnostic dataset**, not a research queue.

---

## Actionable Job Yield (AJY)

Business-shaped metric:

```
AJY_expected  = expected Robot Jobs / 100 candidate companies
AJY_evidenced = evidenced Robot Jobs / 100 candidate companies
```

On the Origin 22-set the script reports both. Later: cost/time per resolved job, novel jobs per 100, pursued/surfaced, deployments/pursued.

---

## Product loop

```
Observe → classify failures → build ONE generalized resolver → rerun same 22 → measure
```

No hand-curated company additions between runs.
