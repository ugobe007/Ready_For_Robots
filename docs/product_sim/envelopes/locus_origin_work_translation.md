# Origin — Capability → Work translation

**Gate:** Observed human work ≠ robot action.

```
Observed Workflow
  → Friction / transport requirement
  → Robot-compatible task (Origin)
  → Robot Job
  → Fit
```

Locus model: **people pick, robots move.** Origin supports picking *workflows*, transport, replenishment/putaway *movement*, tote/box handling **on the robot** — not autonomous grasping of cases off shelves.

---

## Vocabulary groups

### A. Direct Origin work (robot action)

| ID | Description |
|----|-------------|
| `transport_totes` | Move totes between locations |
| `transport_cartons` | Move cartons/boxes on robot |
| `point_to_point_transport` | Zone-to-zone material movement |
| `move_completed_picks` | Carry accumulated picks / order containers |
| `move_orders_pick_to_pack` | Pick → pack / consolidation transport |
| `putaway_transport` | Move product to putaway locations |
| `replenishment_transport` | Move replenishment loads to pick faces |
| `cart_movement` | Cart / mobile container movement |
| `order_consolidation_movement` | Stage / consolidate completed orders |

These are what Origin **owns**.

### B. Origin-enabled workflows (search terms, not robot actions)

| Term | Why search |
|------|------------|
| case picking / order selection | Environments with picker travel + container movement |
| replenishment / discrete / batch picking | Travel + putaway/replen movement |
| pick-assist / high travel | Friction Origin reduces |

Use to **find** places. Then decompose before declaring a Robot Job.

### C. Reject / different robot

| Reject | Why |
|--------|-----|
| Autonomous shelf picking / grasping | Manipulation, not Origin mobility |
| Autonomous case manipulation off rack | Not “people pick, robots move” |
| Forklift / heavy pallet racking | Different machine class |
| Pure sortation package handling | Weak Origin core (FedEx-style) |
| Lights-out AS/RS replacement | Different category |

---

## Promotion gate (Robot Job vs Work Claim)

After Automation Interpretation, classify:

| Label | Meaning |
|-------|---------|
| **DIRECT** | Role text explicitly contains Origin-assumable work |
| **DERIVED** | Workflow implies Origin transport task |
| **SPECULATIVE** | Plausible only — insufficient evidence |

Evidence: **E1** direct movement stated · **E2** movement stated, interface ambiguous · **E3** workflow implies · **E4** generic role.

**Load interface** (required): tote · carton · cart · pallet · rack/bin · unknown.

**Robot Job** only if: `(DIRECT | DERIVED≥E2)` AND `load_interface ≠ unknown`.  
Else stay **Work Claim**.

**Commercial availability** (not SIGNAL): greenfield_likely · partially_automated_expansion · incumbent_competitor · unknown.

See audit: [`../worksite/origin_open_world_18_audit.md`](../worksite/origin_open_world_18_audit.md).

---

## Decomposition pattern

**Human job:** Order Selector  

| Physical tasks | Origin-compatible? |
|----------------|-------------------|
| Locate SKU | No |
| Walk / travel between slots | **Absorbs friction** (robot carries load) |
| Grasp / pick product from slot | No (human) |
| Scan | No |
| Place item in container | No (human) |
| Transport container along route | **Yes** |
| Stage completed order | **Often yes** |

**Robot Job (correct):**

> Transport picked goods / order containers through the order-selection workflow, reducing non-value-added picker travel.

**Robot Job (incorrect):**

> Pick cases at {site}.

---

## Transformation confidence

How certain is it that the observed workflow **contains** a robot-compatible transport task?

| Band | Meaning |
|------|---------|
| High | Job text mentions carts, totes, pallet jack travel, staging, push orders, long walks |
| Medium | Order selector / replenisher role in DC — travel implied, container not explicit |
| Low | Only “warehouse associate” with no movement language |

Medium is allowed for discovery; label it. Do not upgrade to High without evidence of transport friction.

---

## Automation interpretation stage

After Work Claim, before Robot Job:

1. What workflow is observed?  
2. What friction is transport/travel related?  
3. What subset can Origin perform?  
4. Transformation confidence?  
5. Automation state (`manual` / `partial` / `incumbent_robot` / `unknown`)?
