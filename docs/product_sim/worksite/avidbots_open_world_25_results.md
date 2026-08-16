# Avidbots Neo — Open-World Transfer 25 — Results

**Input:** Neo envelope only · **No** known Avidbots customers · **No** seeded airport/hospital/retailer account lists  
**Architecture:** identical funnel to Origin 100  
**Queries:** 25 · ≤5 docs / query  
**Gate:** DIRECT | DERIVED≥E2 · named `floor_surface` **or** `spatial_unit` · commercial_availability set  

---

## One sentence

> Starting only with Avidbots Neo’s capabilities, ReadyForRobots searched the open economy and found **~16** defensible floor-scrub Robot Jobs across **~15** companies and **~16** locations; **~14** were worth investigating.

---

## Transfer verdict: **PASS**

| Criterion | Result |
|-----------|--------|
| Promotion precision ≥70% | **~88%** (14/16) ✓ |
| ≥3 operating-context types | **≥8** ✓ |
| Density ≥4 yes-jobs / 10 q | **~5.6** ✓ |
| Zero known-customer seeding | **Yes** ✓ |
| Gate works without Origin `load_interface` | **Yes** ✓ |

**Robot-directed discovery transfers.** Origin 100 was not an AMR search hack.

---

## What transferred

Same loop:

```
Robot → capability → work vocabulary → open search
  → observations → claims → automation interpretation → Robot Jobs
```

Different physics, different vocabulary, different requirement fields — same core objects.

| Origin needed | Neo needed |
|---------------|------------|
| `load_interface` (tote/cart/kit…) | `floor_surface` + `spatial_unit` |
| move / deliver / return / stage | scrub / floor-care / overnight route |
| warehouse / pack / dock | hospital / airport / mall / aisle / lobby |

Shared and stable: **Work Claim · Evidence · Automation Interpretation · Robot Job · investigate**.

That is the persistence signal — not Origin’s tote fields.

---

## Funnel (25 queries)

| Stage | Count |
|-------|------:|
| Queries | 25 |
| Docs inspected (approx) | ~90 |
| Accepted LWOs | ~28 |
| Work Claims | ~22 |
| Robot Jobs | **16** |
| Investigate=yes | **14** |
| Investigate=weak | 2 |
| Hard rejects | carpet-primary · restroom-only · outdoor-primary · generic cleaner E4 |

---

## Promoted Robot Jobs (investigate=yes)

| # | Company · locality | Observed | Robot-compatible task | Surface / unit | Context | Class |
|---|--------------------|----------|----------------------|----------------|---------|-------|
| 1 | Surge Staffing site · Joliet, IL | Ride-on/walk-behind sweeper-scrubber on warehouse/production floors | Recurring hard-floor scrub route | hard_floor / aisle | warehouse | DIRECT E1 |
| 2 | Crothall @ MUSC · Charleston, SC | Floor tech · industrial equipment · automated large-area floor cleaning | Large-area hard-floor scrub | hard_floor / ward_floor | hospital | DIRECT E1 |
| 3 | Compass @ Delta CLT · Charlotte, NC | Overnight floor tech · hard-surface + automated large-area equipment | Overnight terminal floor scrub | hard_floor / concourse | airport | DIRECT E1 |
| 4 | Lemontree @ North Shore Medical · FL | Overnight floor tech · auto-scrubbers · hallways · tile/vinyl/terrazzo | Overnight corridor scrub | hard_floor / hallway | hospital | DIRECT E1 |
| 5 | Harris Health LBJ · Houston, TX | EVS Floor Tech II nights · riding + walk-behind scrubbers | Night hospital floor scrub routes | hard_floor / corridor | hospital | DIRECT E1 |
| 6 | Unifi · ATL, Atlanta, GA | Airport floor tech overnight · low/high-speed scrubbers | Overnight terminal scrub | hard_floor / concourse | airport | DIRECT E1 |
| 7 | FCS · Sioux Falls Regional Airport, SD | 3rd-shift floor tech · scrubbers on hard floors | Overnight airport floor scrub | hard_floor / terminal | airport | DIRECT E1 |
| 8 | Southeast Airport Services · MCO, Orlando, FL | 3rd-shift floor tech · walk-behind scrubbers · terminal/public | Overnight terminal scrub | hard_floor / concourse | airport | DIRECT E1 |
| 9 | Mall of America · Bloomington, MN | 3rd-shift · ride-on + walk-behind auto scrubbers · common areas/food court | Overnight mall hard-floor scrub | hard_floor / concourse | mall | DIRECT E1 |
| 10 | Johns Hopkins SOM · Baltimore, MD | Custodian Floor Tech · auto-scrubbers **primary ≥3 days/week** | Recurring campus hard-floor scrub | hard_floor / corridor | university | DIRECT E1 |
| 11 | Multimatic · Fort Wayne, IN | Floor scrubber operator · scrub throughout plant | Recurring production-floor scrub | concrete / production_floor | manufacturing | DIRECT E1 |
| 12 | Office Pride · Riverside area, CA | Warehouse cleaning tech · ride-on/walk-behind auto scrubber | Warehouse aisle/floor scrub | hard_floor / aisle | warehouse | DIRECT E1 |
| 13 | Compass @ ExxonMobil HQ · Spring, TX | Floor tech · scrubber experience required · large-area automated | Evening campus hard-floor scrub | hard_floor / lobby | office | DIRECT E1 |
| 14 | Compass @ Illumina HQ · San Diego, CA | Floor tech · 6pm–2:30am · large-area automated equipment | Overnight campus hard-floor scrub | hard_floor / corridor | office | DIRECT E1 |

### Weak (promoted)

| Company · locality | Note |
|--------------------|------|
| Publix Fresh Kitchen · Lakeland, FL | Floor scrubbers stated; food-plant sanitation mix — Neo fit cautious |
| AbbVie · North Chicago, IL | Ride-on/walk-behind floor equipment in GMP — compliance/gowning gate |

### Incumbent signal (claim / competitive, not greenfield job)

McKinney ISD + Nilfisk robotic scrubbers (gym/cafeteria/corridor overnight) — `commercial_availability = incumbent_competitor`. Same class of finding as Capacity+Locus in Origin run: open search surfaces **where the work already attracts robots**.

### Held as Work Claims

Generic EVS without machine language · strip/wax/carpet-primary overnight techs · hotel carpet/terrazzo restoration · event-only convention custodial · BART (ride-on knowledge + heavy outdoor mix)

### Rejected

Carpet extractors as primary · restroom-only · outdoor lot/pressure-wash primary · “janitor” E4 with no floor machine · fogging-only

---

## Operating-context diversity (the transfer proof)

| Context | Yes-jobs |
|---------|--------:|
| Hospital / medical | 3 |
| Airport / aviation | 4 |
| Warehouse / DC | 2 |
| Mall / retail concourse | 1 |
| University / campus | 1 |
| Manufacturing plant | 1 |
| Corporate campus / office | 2 |

**Not one vertical.** Grammar generalized the way Origin’s did — without tote/cart physics.

---

## Grammar observation (do not persist yet)

The run naturally produced:

```
ACTION × TARGET × OPERATING CONTEXT × SPATIAL UNIT × CONDITION
scrub × hard_floor × airport × concourse × overnight
```

OBJECT-as-transported-load was **not** required. That falsifies “Origin schema = product schema.”

Universal core stays thin:

1. Understand the robot  
2. Translate capability → work  
3. Search the economy  
4. Interpret the workflow  
5. Preserve uncertainty (claims)  
6. Promote strong evidence (jobs)  
7. Rank investigate  

Family-specific requirements attach underneath Robot Job.

---

## Comparison to Origin 100

| | Origin 100 | Neo 25 |
|--|----------:|-------:|
| Physics | AMR transport | Floor scrub |
| Precision (post-gate) | ~85% | **~88%** |
| Density (yes/10q) | ~5.5–7.5 | **~5.6** |
| Context breadth | High (after B4) | **High immediately** |
| Known-customer seed | None | **None** |
| Schema pressure | load_interface | floor_surface / spatial_unit |

Same machine. Different world. Same behavior.

---

## What this green-lights / still blocks

### Green-light (now justified)

Persist **core** objects only:

- `work_claim`  
- `robot_job`  
- `job_evidence`  
- `automation_interpretation`  
- `robot_job_match` (later)

With **robot-family requirement extensions** (Origin: load/path; Neo: surface/spatial/condition; future manipulator: grasp/reach…).

Tiny product experience becomes honest:

> Enter your robot. We found jobs it can do.

### Still blocked

- Encoding Origin tote/cart as universal columns  
- Homepage redesign as the next move  
- Cal / CRM return  
- Another Origin 100  

---

## Recommended next

1. Sketch persistence schema: core tables + extension JSON/columns per robot family.  
2. Optional third envelope (inspection or manipulator) — **15 queries** — to stress-test extensions again.  
3. Only then: first tiny “enter robot → jobs” surface.

Artifacts: [`AVIDBOTS_OPEN_WORLD_25.md`](./AVIDBOTS_OPEN_WORLD_25.md) · envelopes [`avidbots_neo.md`](../envelopes/avidbots_neo.md) · [`avidbots_neo_work_translation.md`](../envelopes/avidbots_neo_work_translation.md)
