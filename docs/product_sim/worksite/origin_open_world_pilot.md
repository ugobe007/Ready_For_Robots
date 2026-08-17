# Origin Open-World Pilot (v2)

**Date:** 2026-08-16  
**Input:** Origin-compatible work vocabulary **only** — no company list  
**Queries:** 3 (open-world)  
**Documents inspected (approx.):** ~12 SERP hits reviewed in synthesis  

Universe for Novelty: Origin 18 + prior scorecard companies  
(Sysco, Kenco, Dollar General, Lineage, Radial, HelloFresh, Amazon, Walmart, Home Depot, FedEx, DHL, Medline, PFG, Burris, …)

---

## Funnel (this pilot)

| Stage | Count |
|-------|------:|
| Queries | 3 |
| Candidate documents (SERP) | ~15 |
| Inspected / used | ~12 |
| Proposed LWO signals | ~18 |
| **Accepted LWOs** | **11** |
| Claims (assembled, rough) | **8** |
| Robot Job candidates | **8** |
| Strong Origin fit (manual) | **7** |
| **Novel companies** (∉ prior universe) | **6** |

| Metric | Value |
|--------|------:|
| Query Yield (LWO/query) | 11/3 ≈ **3.7** |
| Document Yield (LWO/inspected) | 11/12 ≈ **0.9** |
| Acceptance Precision (rough) | high on role+DC postings |
| Unique Company Yield | 8/3 ≈ **2.7** |
| Novelty Rate among job candidates | 6/8 = **75%** |

---

## Net-new discoveries (re-scored: transport tasks, not “Origin picks”)

| Company | Locality | Observed workflow | Robot-compatible task | Transf. conf. | Novel? | Automation |
|---------|----------|-------------------|----------------------|:-------------:|:------:|------------|
| **Kroger** | Delaware, OH | Manual case / order selection | Move accumulated picks / containers through selection → stage | M–H | **yes** | unknown |
| **Kroger** | Keller, TX | DC selection / logistics | Order / material transport in selection flow | M | **yes** | unknown |
| **Whole Foods Market** | Austin, TX | Perishable DC order selection | Carry picks / reduce travel in selection | M | **yes** | unknown |
| **SpartanNash** | (confirm city) | Freezer case selection | Transport through freezer selection (payload gate) | M | **yes** | unknown |
| **NAPA / Genuine Parts** | New Kingstown, PA | Pick + replenish + load | Tote/carton transport; replenishment transport | M | **yes** | unknown |
| **Grainger** | Easton, PA | Pick / pack / replenish | Pick→pack movement; replenishment transport | M | **yes** | unknown |
| **RF Fager** | Dillsburg, PA | Pick / replenish / stage | Cart / order movement; staging transport | M | **yes** | unknown |
| Sysco | Houston, TX | Order selection | Same class — known account | M | no | unknown |

**Reject as Origin Job:** “Pick cases at Kroger Delaware.”  
**Accept:** “Transport picked goods through order-selection, reducing picker travel.”

Tote/GTP open query → mostly vendor pages (no COMPANY+LOCALITY).

---

## Automation Interpretation (Kroger example)

**Work claim:** Order-selection work exists at Kroger Delaware.  

**Decomposition:** human picks from slot · travels with order · stages completed pick  

**Origin owns:** travel + container transport + staging movement  

**Robot Job:** Carry order containers through the picking workflow / move completed picks to next process.  

**Origin fit:** High (subject to payload / aisle / container). Novelty: net-new.

---

## Reading

1. Open world finds **companies we did not name**.  
2. Product is **workflow decomposition**, not job-posting count.  
3. Scoring sheet + top-25 audit locked in Open-World 100 protocol — **run unlocked**.

See [ORIGIN_OPEN_WORLD_100.md](./ORIGIN_OPEN_WORLD_100.md) · [locus_origin_work_translation.md](../envelopes/locus_origin_work_translation.md)
