# Localized Work Observation — acquisition primitive

**Status:** next experiment  
**Join algorithm:** **FROZEN** (100% precision when locality exists — do not tune further now)

---

## What we learned

1. When locality exists, the join works (Join Precision 100% on proposed joins).  
2. Bottleneck = acquiring **locality-bearing WHAT**, not join logic.  
3. ATS slug guessing is not a scalable primitive (53 requests → 1 useful join).

Do **not** overcommit to “JobPosting feeds” as the strategy.  
Jobs are **one** source of a more general unit.

---

## Primitive: Localized Work Observation (LWO)

```
Company: Burris Logistics
Locality: Orlando
Work: pick_cases
Evidence: job description / ops text
Function: distribution
Date: recent
Source: …
Confidence: …
```

Anything that produces this shape feeds the engine:

| Can generate an LWO |
|---------------------|
| Structured job record |
| Search-indexed job page |
| Facility page + task language |
| Hiring announcement at a site |
| Expansion / ops case study |
| Training / RFP / union class (later) |
| OSHA / regulatory text (later) |

Acquisition question:

> What is the cheapest, most repeatable way to acquire **company + physical work + locality**?

Not: “How do we scrape ATS systems?”

---

## Architecture: Observations → Claims → Robot Job

Do not require one document to be a Robot Job.

```
Observation A  Kenco operates Jeffersonville DC
Observation B  Kenco employs order pickers
Observation C  Jeffersonville hiring warehouse associates
Observation D  each-pick workflow language
        ↓
Claim: case picking at Kenco Jeffersonville — 88% confidence
        ↓
Robot Job (assembled, existence confidence labeled)
```

Each observation:

- company  
- locality  
- work_unit  
- worksite_function (optional)  
- source  
- timestamp  
- confidence  

Aligns with existence confidence vs completeness.

Frozen join attaches observations / claims to Level 1–2 Worksites when keys exist.

---

## Metric: Localized Work Yield (LWY)

Primary for now (PWRR secondary until WHAT volume exists):

```
LWY = (# accepted Localized Work Observations) / (# companies examined)
```

Also report per 100 companies: `LWY × 100`.

Companion scores:

| Score | Meaning |
|-------|---------|
| Companies covered | Unique companies with ≥1 accepted LWO |
| Precision | Accepted / proposed LWOs (defensible) |
| Work units | Distinct physical work units |
| Cost / observation | Requests · time per accepted LWO |

**Do not** chase PWRR on n≈5 work units — it swings on noise.

---

## Localized Work Yield benchmark (Origin 18)

Four acquisition strategies — score LWOs only:

| Strategy | Goal |
|----------|------|
| **S1 Structured jobs** | company + job + locality (known boards only; no slug spam) |
| **S2 Search-indexed jobs** | company + physical role + city (few targeted queries) |
| **S3 Facility ↔ careers crossover** | known/site language + openings/tasks |
| **S4 Local operating evidence** | facility announcement + workforce/workflow language |

```bash
python3 scripts/localized_work_yield_benchmark.py
python3 scripts/localized_work_yield_benchmark.py --live
```

Decide **after** the scorecard which stream (or combination) to ingest — not before.

---

## Stopped

Company-directed LWY collector benchmarking (offline≈live).  
Result diagnosed **acquisition pipeline failure**, not scarcity of public localized work.

Continue via **Robot-Directed Discovery** — see [ROBOT_DIRECTED_DISCOVERY.md](./ROBOT_DIRECTED_DISCOVERY.md).
