# Batch 3 — Gate Validation (queries 19–38)

**Status:** running → stop for comparison  
**Prerequisite:** [`origin_open_world_18_audit.md`](./origin_open_world_18_audit.md)

## Design

| Arm | n | Intent |
|-----|--:|--------|
| **EXPLOIT** | 10 | Language close to Origin action (tote/cart/stage/dock/drop/waterspider) → high precision Robot Jobs |
| **EXPLORE** | 10 | Broader workflows (selector/replenish/pick-pack) → discovery; promote **only** if gate passes |

Search may be speculative. **Product surface may not.**

```
EXPLORE hit → Work Claim (default)
  + observation of move × object × place → Robot Job
```

### Promotion gate (locked)

Robot Job iff: `(DIRECT | DERIVED≥E2)` AND `load_interface ≠ unknown`  
Else: Work Claim / watching.

### Target

| Metric | Target |
|--------|--------|
| **Promotion Precision** (investigate=yes / Robot Jobs) | **≥70%** |
| Baseline (old gate) | 11/24 ≈ 46% |

Also track: Claim-to-Job Conversion (Jobs / Claims) — low can be healthy.

---

## Query plan

### EXPLOIT (19–28)

| Q# | Query |
|----|-------|
| 19 | warehouse return totes carts pack station hiring |
| 20 | DC associate move carts between pick zones |
| 21 | stage completed orders shipping dock warehouse job |
| 22 | warehouse associate deliver materials drop zone EPJ |
| 23 | water spider tote delivery warehouse manufacturing hiring |
| 24 | putaway transport pallet jack distribution center job |
| 25 | move completed orders staging distribution center |
| 26 | order consolidation staging dock warehouse associate |
| 27 | replenishment transport carts totes pick face hiring |
| 28 | 3PL warehouse move totes between zones associate |

### EXPLORE (29–38)

| Q# | Query |
|----|-------|
| 29 | order selector distribution center job posting |
| 30 | case picker grocery warehouse DC hiring |
| 31 | batch picker distribution center hiring |
| 32 | pick pack replenish DC associate |
| 33 | warehouse associate material handler distribution center |
| 34 | discrete order picker warehouse job |
| 35 | wholesale distributor order selector hiring |
| 36 | produce order selector warehouse distribution |
| 37 | e-commerce fulfillment picker travel hiring |
| 38 | night shift grocery DC selector hiring |

---

## Metrics (per arm)

- LWOs · Work Claims · Robot Jobs promoted  
- DIRECT / DERIVED mix · E1 / E2 mix · named-load rate  
- worth-investigating rate · novel-company rate  
- **Promotion Precision** · Claim-to-Job Conversion  

Results: [`origin_open_world_batch3_gate_validation.md`](./origin_open_world_batch3_gate_validation.md)
