# Source Yield Benchmark — Origin 18

**Status:** next experiment (after Acceptance Gate)  
**Not:** another resolver · ontology polish · SIGNAL extraction theater

---

## Finding that got us here

ReadyForRobots has **company intelligence**.  
It does **not** have an **operating-world model** of companies.

Robots work at **places**, not at companies.

A resolver cannot resolve information we do not possess.  
**This is a data acquisition problem**, not an ontology problem.

Infrastructure to build (eventually): **Company Operating Footprint** — not a feature, a foundational dataset.

---

## Question

> Can we economically reconstruct where companies perform physical work and what work happens there from publicly observable evidence?

If yes: *Find Jobs for Robots* becomes a data product.  
If no: we learn which sources fail, cheaply.

---

## Laboratory set

The **18** Origin companies with failure class `no_worksite_known` (auto v0.1 + gate).

Benchmark targets — do **not** manually fix them. Use them as a fixed yield panel.

Also keep the 3 `multiple_worksites` + 1 `signal_not_site_specific` for secondary notes, but primary scorecard = 18.

---

## Source families (test all, prefer none)

| Family | Examples | Hypothesis |
|--------|----------|------------|
| **A. Company-owned** | /locations, facilities, network, 10-K, sustainability | High precision, uneven coverage |
| **B. Job postings** | Careers selectors, warehouse/selector roles | WHERE + WORK + EVIDENCE in one artifact |
| **C. News / facility PR** | Expansion, groundbreaking, DC opening | WHERE + type + WHY NOW; sparse names |
| **D. Public / industry registries** | EPA FRS, FDA, hospital lists, aviation | Structured; function strong; work evidence weak |

Maps/listings are a later family (often high recall, weak function) — optional V0.2.

---

## Metrics (per source family)

| Metric | Definition |
|--------|------------|
| **Companies resolved** | /18 with ≥1 gate-accepted Worksite |
| **Worksites** | Count of accepted Worksites |
| **Function yield** | % accepted with known site type |
| **Work yield** | Physical work units extracted (expected or evidenced) |
| **Evidence yield** | % work units that are EVIDENCED |
| **Origin match yield** | Plausible Origin-relevant work units |
| **Precision (audit)** | Manual sample of accepted Worksites — WPR |
| **Acquisition cost** | HTTP requests + wall time per accepted Worksite |

Excitement bar: e.g. job postings resolve **≥10/18** with strong evidence yield and high WPR — without company-specific rules.

---

## Thesis probe (job postings)

Human job postings may be one of the best sources for **jobs for robots**:

```
Human Job → Physical Tasks → Worksite → Robotability → Compatible Robots
```

Not “replace every worker.”  
Job descriptions are structured evidence of **physical work demand** at **places**.

Old SIGNAL: “hiring increased.”  
New engine: **read the job itself**.

---

## How to run

```bash
python3 scripts/source_yield_benchmark.py
python3 scripts/source_yield_benchmark.py --family jobs
python3 scripts/source_yield_benchmark.py --no-network   # scorecard from cache only
```

Outputs:

- `docs/product_sim/worksite/source_yield_scorecard.json`
- `docs/product_sim/worksite/source_yield_scorecard.md`

---

## V0 scorecard (ran)

See [source_yield_scorecard.md](./source_yield_scorecard.md).

**Inconclusive winner.** Probe limitations (JS careers, ATS slug miss, EPA mismatch) mean we measured **channel readiness**, not source ceiling.

Partial signal: job/careers text can yield **WORK evidence without WHERE** (e.g. Kenco pick/load language).

Next probe: structured job feeds + facility sitemaps/10-K — same 18 panel.
