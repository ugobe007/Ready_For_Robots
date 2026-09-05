# Robot-Directed Discovery v2 — Open World

**Status:** Open-World 100 unlocked (scoring refined)  
**v1 result:** capability→search works; evidence exists  
**v2 question:** Can the robot discover work we did **not** preselect?

**Origin gate:** [locus_origin_work_translation.md](../envelopes/locus_origin_work_translation.md)

---

## Funnel

```
Queries
  → candidate documents
  → inspected documents
  → accepted LWOs
  → Work Claims
  → Automation Interpretation   ← required
  → Robot Jobs
  → Fit / ranked
```

| Metric | Definition |
|--------|------------|
| **Query Yield** | accepted LWOs / queries |
| **Document Yield** | accepted LWOs / documents inspected |
| **Acceptance Precision** | accepted / proposed LWOs |
| **Unique Company Yield** | new companies / queries |
| **Unique Worksite Yield** | new localities·ops / queries |
| **Robot Job Yield** | assembled **transport-task** jobs / queries |
| **Novelty Rate** | jobs whose company∉input universe / job candidates |
| **Transformation Yield** | jobs with Medium+ transformation confidence / claims |
| Later | $ / accepted LWO · $ / Robot Job |

**Robot Job** = Origin-compatible **task**, not the human role name.

---

## Decomposition model (product asset)

```
Human Job → Physical Tasks → Robot-Compatible Tasks
```

Not: Human Job → Robot Job.

Applies to every robot category (AMR, Spot, scrubber, cobot).

**Observed Workflow → Friction/Transport → Robot Action → Fit**

---

## Open world (no company list)

Input only:

- Robot: Locus Origin  
- Capability: collaborative AMR — people pick, robots move  
- Work vocabulary: **A** direct transport actions + **B** enabled workflows for search  
- Reject **C**: grasping / forklift / autonomous shelf pick  

**No** Sysco · Kenco · Origin 18 · preselected universe.

---

## Vocabulary lenses

| Lens | Examples |
|------|----------|
| Human-role (B) | order selector, case picker, replenisher |
| Direct task (A) | tote transport, cart movement, pick→pack move |
| Problem | reduce walking, travel time, labor shortage |
| Workflow | reserve→pick, pick→pack, replenishment putaway |

---

## Automation state (separate from existence)

| State | Meaning |
|-------|---------|
| `manual` | No known robots on this work |
| `partially_automated` | Some automation adjacent |
| `incumbent_robot` | Robots already on related work |
| `unknown` | Default |

---

## Experiment: Origin Open-World 100

Protocol + scoring: [`ORIGIN_OPEN_WORLD_100.md`](./ORIGIN_OPEN_WORLD_100.md)

**Success criterion:**

> X companies · Y locations · Z **specific transport tasks** Origin could perform  
> — not N job postings or M order-selector employers.

---

## Tiny product (when v2 works)

```
Enter your robot
  → understand capabilities
  → search physical economy
  → decompose workflows
  → We found N transport jobs for your robot
```

---

## Pilot (pre-refinement)

[`origin_open_world_pilot.md`](./origin_open_world_pilot.md) — net-new companies found; jobs must be re-scored under transport decomposition (not `pick_cases` as Origin action).
