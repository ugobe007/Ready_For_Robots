# Operating Footprint — demand-intelligence primitive

**Status:** experimental · Origin laboratory  
**Not:** torturing SIGNAL into geography

---

## Why this exists

SIGNAL was collected to answer: **which company looks interesting?**  
The new product asks: **where does interesting physical work occur?**

Those are different collection problems. Pipeline prose often has network counts (“334 DCs”) and zero named places — that is an **architecture** signal, not just an NLP bug.

---

## Object

```
Company
  → Operating Footprint
      → Worksites (accepted)
          → Expected / Evidenced Work
```

Company-level signals propagate carefully across the footprint without pretending they belong to a specific site until evidence says so.

HQ / conference / supplier locations may appear as **rejected candidates**, not Worksites.

---

## Four intelligence systems

| System | Chain |
|--------|-------|
| **PHYSICAL WORLD** | Company → Operating Footprint → Worksites (**WHERE**) |
| **WORK** | Human jobs → Physical Tasks → Work Units (**WHAT**) |
| **TIMING** | SIGNAL → WHY NOW |
| **SUPPLY** | Robot → Capabilities → Compatible Work |

Join via entity resolution (company + locality + function) — not whole-document discovery.

Progressive Worksite identity: Levels 0–4 (`app/services/worksite_identity.py`).  
Composition experiment: [SOURCE_COMPOSITION_YIELD.md](./SOURCE_COMPOSITION_YIELD.md).

**SIGNAL wasn’t wrong — it was asked to do too much.**

User-facing chain stays:

```
CAPABILITY → WORK → WHERE → WHY NOW → PURSUE
```

Internally: WHERE from footprint, WHAT from jobs/evidence, WHY NOW from SIGNAL, matched to robot capability.

---

## Worksite Acceptance Gate

Before a candidate enters the graph:

| Axis | Question |
|------|----------|
| ENTITY | Real physical place? |
| OWNERSHIP | Does this company operate here? |
| FUNCTION | What happens there? (may be UNKNOWN) |

Prefer **WRR 45% / WPR 96%** over **WRR 80% / WPR 61%**.

Code: `app/services/worksite_acceptance_gate.py`  
Resolver: `app/services/operating_footprint_resolver.py`

---

## Metrics

| Metric | Meaning |
|--------|---------|
| WRR | Companies with ≥1 **accepted** Worksite |
| **WPR** | Of accepted Worksites, share that are legitimate (gold / audit) |
| WCR | Accepted worksites with known function |
| WorkRR / ERR / JRR | As before (expected vs strict) |
| AJY | Jobs / 100 companies without manual research |

---

## Sprint constraint

Origin 22 laboratory only.  
Zero company-specific rules/seeds on the auto path.  
Empty footprint > garbage footprint.
