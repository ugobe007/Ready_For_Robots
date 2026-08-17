# Avidbots Neo — Capability → Work translation

**Gate:** Observed human work ≠ robot action.

```
Observed Workflow
  → Friction / floor-care requirement
  → Robot-compatible task (Neo)
  → Robot Job
  → Fit
```

Neo model: **humans still own detail work; robot owns recurring hard-floor scrubbing routes.**

This file is **robot-family specific**. It must not rewrite shared Origin concepts. Core funnel objects stay:

Work Claim · Evidence · Automation Interpretation · Robot Job · (later) Robot Match

Neo defines its own **requirement fields** underneath Robot Job — not Origin’s `load_interface`.

---

## Vocabulary groups

### A. Direct Neo work (robot action)

| ID | Description |
|----|-------------|
| `scrub_hard_floors` | Machine-scrub hard flooring on a route |
| `recurring_floor_route` | Repeatable area coverage (nightly / shift) |
| `large_area_floor_care` | Contiguous high-sqft indoor floors |
| `overnight_floor_program` | Off-peak / overnight floor machine work |
| `aisle_or_concourse_scrub` | Long path floors (warehouse aisle, concourse, corridor) |

These are what Neo **owns**.

### B. Neo-enabled workflows (search terms, not robot actions)

| Term | Why search |
|------|------------|
| EVS / environmental services | Hospitals & campuses with floor programs |
| Custodian / janitor floor care | Buildings with machine floor routes |
| Floor technician / floor tech | Explicit floor-machine roles |
| Ride-on scrubber / auto-scrubber operator | Closest human analogue to Neo physics |
| Night porter / overnight cleaning | Schedule window matching autonomous runs |
| Hard-floor maintenance | Surface type Neo needs |

Use to **find** places. Then decompose before declaring a Robot Job.

### C. Reject / different robot

| Reject | Why |
|--------|-----|
| Carpet shampoo / extractor-primary | Different machine |
| Restroom / fixture detail cleaning only | Not floor-route scrubber |
| Window / exterior facade | Different robot |
| Disinfectant fogging as sole claim | Not Neo core |
| Outdoor lot sweeping | Outdoor class |
| “Clean warehouse” with zero floor-machine evidence | Too weak — claim only |
| Origin-style tote/cart transport | Different robot (already tested) |

---

## Promotion gate (Robot Job vs Work Claim)

After Automation Interpretation, classify:

| Label | Meaning |
|-------|---------|
| **DIRECT** | Role text explicitly contains Neo-assumable floor-machine / scrub work |
| **DERIVED** | Floor-care workflow implies recurring hard-floor scrub route |
| **SPECULATIVE** | Plausible only — insufficient evidence |

Evidence: **E1** floor machine / scrub / ride-on stated · **E2** floor care stated, area/surface ambiguous · **E3** custodial role implies floors · **E4** generic cleaner.

### Neo requirement fields (not Origin load_interface)

| Field | Allowed values (named required for Robot Job) |
|-------|-----------------------------------------------|
| `floor_surface` | hard_floor · VCT · concrete · tile · terrazzo · mixed_hard · unknown |
| `spatial_unit` | corridor · hallway · lobby · concourse · aisle · ward_floor · classroom · production_floor · unknown |
| `operating_context` | hospital · airport · mall · warehouse · school · manufacturing · hotel · office · other · unknown |
| `condition` | overnight · scheduled_recurring · shift_floor_care · unknown |

**Robot Job** only if:

1. `action_class` is DIRECT, or DERIVED with evidence ≥ **E2**  
2. `floor_surface` **or** `spatial_unit` is named (not both unknown)  
3. `commercial_availability` is set (may be `unknown`)  

Else stay **Work Claim**.

**Commercial availability:** greenfield_likely · partially_automated_expansion · incumbent_competitor · unknown.

Do **not** require Origin `load_interface`. Absence of tote/cart is expected and correct.

---

## Decomposition pattern

**Human job:** EVS Floor Technician  

| Physical tasks | Neo-compatible? |
|----------------|-----------------|
| Detail clean restrooms | No |
| Empty trash | No |
| Spot mop spills | Weak / human |
| Operate auto-scrubber on corridors | **Yes** |
| Cover large public flooring overnight | **Yes** |
| Recurring nightly floor program | **Yes** |

**Robot Job (correct):**

> Autonomously scrub recurring hard-floor routes (corridors / public flooring) during the overnight cleaning window.

**Robot Job (incorrect):**

> Clean the hospital.  
> Replace the entire EVS department.

---

## Transformation confidence

| Band | Meaning |
|------|---------|
| High | Text mentions scrubber, auto-scrubber, ride-on, hard floors, corridor/concourse machine routes |
| Medium | EVS / custodian with floor-care duties; machine implied but not named |
| Low | “Janitor” / “cleaner” with no floor language |

Medium is allowed for discovery; label it.

---

## Automation interpretation stage

After Work Claim, before Robot Job:

1. What floor work is observed?  
2. What portion is recurring hard-floor scrubbing Neo could own?  
3. What remains human (detail, restrooms, carpet, trash)?  
4. Is surface / spatial unit named enough to promote?

---

## Search grammar (capability-derived — not account lists)

```
ACTION × TARGET × OPERATING CONTEXT × SPATIAL UNIT × CONDITION
scrub|clean|sweep|wash|floor-care
  × floor|hard floor|VCT|concrete
  × hospital|airport|mall|warehouse|school|plant|hotel   ← types, not named accounts
  × corridor|concourse|aisle|lobby|hallway
  × overnight|recurring|ride-on|auto-scrubber
```

This grammar is a **hypothesis**. The 25-query transfer test may falsify or reshape it. Do not persist schema from this file until transfer succeeds.
