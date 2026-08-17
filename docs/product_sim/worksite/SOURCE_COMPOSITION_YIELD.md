# Source Composition Yield — join WHERE and WHAT

**Status:** next experiment (supersedes “which source wins”)  
**Panel:** Origin 18 `no_worksite_known`

---

## What the single-source benchmark taught us

We assumed one magical source would contain **Worksites + Work**.

Measured reality:

| Stream | Stronger at |
|--------|-------------|
| Company / footprint sources | **WHERE** |
| Job / employment sources | **WHAT** |

Kenco: careers → `pick_cases`, `load_outbound` evidenced · Worksite unresolved.

Under JRR that looks like failure.  
As an engine state it is a **partial Robot Job**:

```
Kenco
  pick_cases — EVIDENCED
  load_outbound — EVIDENCED
  Worksite — UNRESOLVED
```

Retain orphans. Attach later when footprint supplies WHERE.

---

## Graph construction (entity resolution, not whole-document discovery)

```
Company → Operating Footprint → Worksite          (WHERE)
Company → Human Jobs → Physical Tasks → Work      (WHAT)
                 ↓
         Human Job → Worksite  (join)
                 ↓
         Worksite → Evidenced Work
```

Narrower problem than “find a webpage that is already a Robot Job.”

Join keys (progressive): company + locality (+ site type).  
Street address is **not** required for Level 1–2 reasoning.

---

## Worksite identity levels

| Level | Identity | Status |
|------:|----------|--------|
| 0 | Company only | Not resolved |
| 1 | Company + metro/locality | **Candidate** Worksite |
| 2 | Company + locality + operating function | **Resolved** Worksite |
| 3 | Named / addressed physical site | **Verified** Worksite |
| 4 | Site + evidenced workflow | **Deeply** resolved |

Honesty preserved: always label the level. Scalability improves because Jeffersonville, IN + fulfillment is enough to associate an Order Picker job.

---

## Four intelligence systems

| System | Chain |
|--------|-------|
| **PHYSICAL WORLD** | Company → Operating Footprint → Worksites |
| **WORK** | Human jobs + ops evidence → Tasks → Work Units |
| **TIMING** | SIGNAL → WHY NOW |
| **SUPPLY** | Robot → Capabilities → Compatible Work |

Join:

```
JOB DISCOVERY     = Worksite + Work + Robot Capability + Evidence
COMMERCIAL RANK   = + WHY NOW
PURSUIT           = + people / economics / qualification
```

**SIGNAL wasn’t wrong — it was asked to do too much.**  
It times pursuit; it does not discover WHERE or WHAT.

---

## Composition arms (same 18)

| Arm | Sources | Question |
|-----|---------|----------|
| **A** | Company only | How much WHERE? |
| **B** | Structured jobs only | How much WHAT? |
| **C** | Company + jobs | How much WHERE↔WHAT can we **join**? |
| **D** | Company + jobs + news | How much WHERE↔WHAT↔WHY NOW? |

Primary product metric is **C**, not A or B alone.

---

## Physical Work Reconstruction Rate (PWRR)

Forget robots temporarily.

```
PWRR = (# evidenced work units attached to Level≥1 Worksite)
     / (# evidenced work units detected)
```

Example (illustrative): 15 detected · 3 attached → **PWRR = 20%**.

Engineering job: **increase the % of WORK that acquires WHERE.**  
Robot matching sits on top.

---

## Structured jobs priority

Stop brute-forcing careers HTML shells.

Find where structured JobPosting lives: ATS APIs/feeds, JSON-LD, Greenhouse, Lever, Workday, iCIMS, SmartRecruiters, SuccessFactors, sitemaps.

Not to become a jobs aggregator — each posting is a **sensor** for physical work inside a company.

---

## How to run

```bash
# Offline: uses source_yield_cache from prior probes
python3 scripts/source_composition_yield.py

# Optional refresh of company/jobs caches first:
python3 scripts/source_yield_benchmark.py --family company,jobs
python3 scripts/source_composition_yield.py
```

Outputs: `source_composition_scorecard.json` / `.md`

---

## Excitement bar

Not: one source resolves 14/18 alone.

Yes: Company + jobs moves from “6 Worksites + 15 orphaned work units” toward **many Level≥1 Worksites with attached physical-work units** on the same 18 — cheaply, with labeled identity levels and rising **PWRR**.
