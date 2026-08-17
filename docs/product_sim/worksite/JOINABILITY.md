# Joinability — the WHERE ↔ WHAT bridge

**Join algorithm:** **FROZEN** — do not tune. Next bottleneck is Localized Work Observation acquisition.

See [LOCALIZED_WORK_OBSERVATION.md](./LOCALIZED_WORK_OBSERVATION.md) · LWY benchmark over JobPosting-only thesis.

---

## Bottleneck

C failed because we lack the **linking key**:

> We can detect work, and we can sometimes detect places, but we do not yet connect a specific piece of work to a specific operating context.

Next focus: **joinability** — the smallest reliable bridge between WHERE and WHAT.

---

## Bridge keys (progressive)

Enough for a defensible Level 1–2 association:

- company
- city / metro
- job location (structured)
- facility function (compatible)
- optional: requisition / ATS location metadata

**Not required yet:** street address (Level 3).

Example (honest):

```
Worksite: Kenco Jeffersonville distribution operation
Work: case picking
Evidence: Kenco job posting
Association: company + locality + facility function
Join confidence: 87%
Identity level: 2
```

---

## Product shape

| Stream | Role |
|--------|------|
| WHERE | Physical operations exist |
| WHAT | Humans performing physical tasks |
| WHY NOW | Commercial pressure (SIGNAL) |
| WHO | Robots that can plausibly do the work |

**The join is where “Find Jobs for Robots” starts.**

---

## Metrics (pair forever)

| Metric | Meaning |
|--------|---------|
| **Location-bearing job rate** | % of physical job records with usable city/metro/site id |
| **Join Precision** | % of proposed work→worksite joins that are defensible |
| **PWRR uplift** | Orphaned evidenced work → attached |
| **Cost / successful join** | Requests · compute · time |

**Do not** optimize PWRR alone — a sloppy matcher attaches to the wrong facility.  
**PWRR ∩ Join Precision** is the bar.

---

## Excitement bar

| | Target |
|--|--------|
| PWRR | 0% → **≥40%** |
| Join Precision | **≥90%** |
| Manual company rules | **0** |

If structured JobPosting feeds hit this on the Origin 18 → real acquisition primitive.  
If not → problem is broader entity resolution, not “better HTML.”

---

## Run

```bash
python3 scripts/joinability_benchmark.py           # uses cache + optional live ATS
python3 scripts/joinability_benchmark.py --live-ats  # refresh structured locality from Greenhouse/Lever
```

Outputs: `joinability_scorecard.json` / `.md`
