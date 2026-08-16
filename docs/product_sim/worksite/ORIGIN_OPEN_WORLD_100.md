# Origin Open-World 100 — protocol (refined)

**Input:** robot + vocabulary only. **No company list.**  
**Capability gate:** [locus_origin_work_translation.md](../envelopes/locus_origin_work_translation.md)

---

## Funnel

```
Queries
  → candidate documents
  → inspected documents
  → accepted LWOs
  → Work Claims
  → Automation Interpretation   ← NEW
  → Robot Jobs
  → Fit / ranked
```

**Automation Interpretation:** Given this observed workflow, what portion can Origin actually perform?

---

## Budget (declare before run)

- [x] **100 queries** (primary budget)  
- Cap documents inspected: **≤5 per query** (≤500)  
- Track both Query Yield and Document Yield  

---

## Vocabulary (search)

**Direct (A):** tote transport, carton transport, cart movement, putaway, replenishment transport, pick-to-pack movement  

**Enabled workflows (B — search only):** order selector, case picker, replenisher, discrete/batch picking, pick travel  

**Never as robot action (C):** autonomous picking/grasping, forklift, AS/RS replacement  

---

## Scoring sheet (per accepted candidate)

| Field | Required |
|-------|----------|
| company | |
| locality | |
| observed_workflow | What people do |
| work_claim | Existence claim |
| robot_compatible_task | Origin subset (transport…) |
| action_class | DIRECT / DERIVED / SPECULATIVE |
| evidence_strength | E1 / E2 / E3 / E4 |
| load_interface | tote · carton · cart · pallet · rack/bin · unknown |
| transformation_confidence | H/M/L |
| commercial_availability | greenfield_likely · partially_automated_expansion · incumbent_competitor · unknown |
| automation_state | manual / partial / incumbent_robot / unknown |
| origin_fit | H/M/L + gates |
| investigate | yes / weak / no |
| novel | yes/no vs prior lab universe |
| unknowns | container, load, route, WMS, current automation |

### Robot Job promotion gate (post–18-query audit)

Promote to **Robot Job** only if:

1. `action_class` is DIRECT, or DERIVED with evidence ≥ E2  
2. `load_interface` is named (not `unknown`)  
3. `commercial_availability` is set (may be `unknown`)  

Otherwise keep as **Work Claim** / workflow existence — do not count as Robot Job.

**Product surface order:** DIRECT+E1 → DIRECT+E2 → DERIVED+E2+named load.

### Reject if

- Robot Job stated as “pick cases / select orders” as **Origin’s action**  
- Only manipulation/grasping/forklift work  
- No defensible transport/travel component  
- SPECULATIVE / E3–E4 selector inference only (claim layer OK)  

---

## Pause audit (mandatory before queries 19–100)

See [`origin_open_world_18_audit.md`](./origin_open_world_18_audit.md).

**Result at 18 queries:** 24 surfaced → **11 worth investigating** · **10 DIRECT** · **3 hard demotions** (McLane, LKQ, L&F).  
Tighten gate before spending remaining budget.

---

## Top-25 manual audit

1. Does observed work exist?  
2. Workflow decomposition correct?  
3. Real Origin-compatible **task** inside it?  
4. Action class DIRECT/DERIVED (not SPECULATIVE)?  
5. Evidence ≥ E2? Load interface named?  
6. Origin technically plausible for that task?  
7. Commercial availability (unclaimed job)?  
8. Worth investigating?  
9. Novel?  
10. Automation state?  

---

## Success criterion (locked)

> Starting only with Locus Origin’s capabilities, ReadyForRobots independently discovered **X companies** and **Y operating locations** containing physical workflows, and identified **Z DIRECT or strong-DERIVED transport tasks** (named load) Origin could plausibly perform — of which **W are worth investigating**.

**Not:** “We found N warehouse job postings.”  
**Not:** “We found companies that hire order selectors.”  
**Not:** High-fit cards without E1/E2 + load interface.

---

## Card shape (good)

```
Kroger · Delaware, OH
Observed workflow: manual case selection / order filling
Robot-compatible task: move accumulated picks / order containers
  through selection route → consolidation/stage
Evidence: localized order-selector job description
Transformation confidence: Medium–High
Origin fit: High (subject to payload/aisle/container)
Automation state: unknown
Unknowns: order container type, load, route design, current automation
Novel: Yes
```

## Card shape (bad)

```
Kroger · Delaware, OH
Origin Job: Pick cases
```

---

## Run log

Results: [`origin_open_world_100_results.md`](./origin_open_world_100_results.md)  
Ledger: [`origin_open_world_100_ledger.json`](./origin_open_world_100_ledger.json)
