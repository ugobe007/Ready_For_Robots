# Robot-Directed Discovery

**Status:** active experiment  
**Stopped:** company-directed LWY collector benchmarks (offline≈live = pipeline failure, not evidence scarcity)

---

## Diagnosis

Amazon, Walmart, Home Depot, Dollar General, FedEx, DHL, Medline, PFG returning **zero** LWOs from our collectors is implausible as market emptiness.

It diagnoses the **acquisition machinery**, not the physical economy.

Do not run another Python collector pass until the discovery *path* is validated.

---

## Reversal

| Old (company-directed) | New (robot-directed) |
|------------------------|----------------------|
| Company → footprint → work → match robot | **Robot → capability → compatible work → search world** |
| Map America, then find jobs | Find jobs, build map as byproduct |
| LWY / 100 companies | **Robot Job Discovery Yield / 100 retrievals** |

User ask: *Find jobs for my robot* — not *Map America’s DCs*.

---

## Path

```
Robot (e.g. Origin)
  → Capabilities
  → Compatible work units
  → Work vocabulary / evidence patterns
  → SEARCH for WORK + COMPANY + LOCALITY
  → Localized Work Observations
  → Robot Job candidates
```

Operating Footprint = **verification / enrichment**, not always prerequisite infrastructure.

---

## Origin vocabulary (example)

| Work unit | Hunt patterns |
|-----------|----------------|
| `pick_cases` | order selector, case picker, order filler, pick slot |
| `replenish` | replenish pick areas, slotting, replenishment WIP |
| `move_totes` / tote transport | tote, cart, goods-to-person, AMR tote |

Each robot family has its own eyes: scrub · inspect · palletize · carry …

---

## Metric: Robot Job Discovery Yield (RJDY)

```
RJDY = accepted LWOs per 100 retrieval operations
```

Optional funnel:

```
retrievals → LWOs → accepted LWOs → Robot Job candidates → strong Origin matches
```

Compare honestly to: **53 ATS requests → 1 observation**.

---

## Manual web-search lab (this experiment)

Take Origin + three work units.  
Genuine public search (not RFR caches / ATS slug spam).  
Record WORK + COMPANY + LOCALITY + evidence.

Scorecard: [`robot_directed_discovery_scorecard.md`](./robot_directed_discovery_scorecard.md)

---

## Excitement bar

If robot-directed search yields **~15–30** accepted LWOs where company-directed collectors found **~1**, then:

> ReadyForRobots should look for jobs and build the map as it finds them — not map companies and then look for jobs.
