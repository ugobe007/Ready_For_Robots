# Worksite V0 — Fix WHERE before more scoring

**Status:** experimental branch · primary build objective  
**Metrics:** WRR + **WPR** + WCR + WorkRR + ERR + JRR (expected/strict) + AJY  
**Not yet:** robot URL frontend · 10×25 audit · persist `robot_job`

Prefer **WRR 45% / WPR 96%** over high recall with garbage places.

See [OPERATING_FOOTPRINT.md](./OPERATING_FOOTPRINT.md) · [ORIGIN_DIAGNOSTIC.md](./ORIGIN_DIAGNOSTIC.md)

---

## Product gap (from Origin V0)

Current data can identify **interesting companies**.  
It cannot yet reliably identify **work at places**.

Without WHERE, a Robot Job collapses to:

> Sysco looks interesting.

Instead of:

> At this Sysco operation, this work likely occurs.

---

## Chain

```
CAPABILITY → WORK → WHERE → WHY NOW → PURSUE
```

| Link | State |
|------|--------|
| Capability | Reasonable (robot envelopes) |
| Work | Modelable (patterns + units) |
| **WHERE** | **Weak — bottleneck** |
| Why now | Lots of company-level signals |
| Pursue | Premature without WHERE |

---

## Object: Worksite

**Worksite** = a real-world operating location where **physical work** occurs.

Avoid calling everything a “facility” (adversarial: HQ, showroom, vendor booth, campus lobby ≠ work site).

Examples:

| Worksite | Site type |
|----------|-----------|
| Sysco distribution center — Las Vegas | food_distribution_center |
| Mitsubishi Chemical plant — Shiga | chemical_plant |
| Harry Reid Airport — Terminal 3 | airport_terminal |
| MGM Grand — casino/hotel property | hospitality_campus |
| Solar farm — project site | energy_project_site |
| Hospital — campus | hospital_campus |
| Farm — growing operation | agricultural_operation |
| Construction project — temporary site | construction_site |

### Hierarchy

```
Company → Worksites → Work → Robot Jobs
```

Stronger than:

```
Company → Signals → Opportunities
```

### Relationship to DB `facilities`

`app.models.facility.Facility` is the eventual persistence shape.  
**Worksite** is the product/experiment term: truth-gated operating location, not every address row.

`Facility.truth_state` / `facility_type` map later. Do not rename the table in this branch.

---

## Work status (evidence classes)

| Class | Meaning |
|-------|---------|
| **EXPECTED** | Inferred from site type via Work Pattern Library |
| **EVIDENCED** | Supported by public evidence (jobs, ops materials, articles naming the work) |
| **CONFIRMED** | Directly stated at this worksite |
| **UNKNOWN** | Insufficient evidence |
| **CONTRADICTED** | Evidence indicates otherwise |

Shortcut: we do **not** need every workflow at every site.  
Infer **likely work from site type**, then upgrade with evidence.

---

## Three builds (this branch)

### 1. Worksite Resolver

**In:** company (+ optional signals)  
**Out:** operating locations + site types + confidence

### 2. Work Pattern Library

**In:** site type (e.g. `food_distribution_center`)  
**Out:** ordered physical work units (not robots)

### 3. Work Evidence Layer

For each predicted work unit at a worksite, classify EXPECTED → … → CONTRADICTED.

---

## Success experiment

Rerun Origin against the **same universe**.

**Fail (today):** Sysco — HOT — automation expansion  

**Pass (target):**

> Sysco — Riverside DC  
> Case movement: reserve → pick area  
> Work: EVIDENCED  
> Origin fit: HIGH

---

## Job Resolution Rate

```
JRR = (# results with Worksite resolved AND Work resolved) / (# search results)
```

Illustrative Origin V0:

| | Count |
|--|------:|
| Results | 22 |
| Worksite resolved | 7/22 |
| Work resolved | 9/22 |
| Worksite + Work | 5/22 |
| **JRR** | **~23%** |

**Immediate objective:** JRR **> 70%** before 10×25 or robot-URL UI.

See `job_resolution_rate.md` and `reports` from `scripts/worksite_origin_baseline.py`.
