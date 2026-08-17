# Origin Open-World 100 — Final Scoreboard

**Capability start:** Locus Origin only ([locus_origin_work_translation.md](../envelopes/locus_origin_work_translation.md))  
**Method:** open-economy search · LWO → Work Claim → Automation Interpretation → Robot Job  
**Gate (locked q19–100):** DIRECT **or** DERIVED≥E2 · named load · commercial_availability recorded · investigate yes/weak/no  
**Queries:** 100 · Batches: pilot/audit (1–18) · gate validation (19–38) · durability (39–58) · continue (59–78) · finish (79–100)

---

## The one sentence

> Starting only with Locus Origin’s capabilities, ReadyForRobots searched the open economy and found **~67** defensible Robot Jobs across **~55** companies and **~75** operating locations; **~59** were worth investigating.

That sentence is **impressive enough** to treat as product-behavior evidence — not merely a positioning hypothesis. The engine repeatedly found named-load transport work outside the original grocery dock vein, preserved watching claims until evidence matured them, and held promotion precision near **85%** after the gate tightened.

---

## Verdict

**We have the beginnings of a repeatable discovery engine.**

| Question | Answer |
|----------|--------|
| Does capability → search → observe → promote work? | **Yes** |
| Does the gate keep junk out without killing EXPLORE? | **Yes** (~85% precision post-gate) |
| Does discovery generalize beyond grocery pallet-dock? | **Yes** (hospital, pharmacy, apparel, electronics, books, kits, returns, ecommerce carts…) |
| Is claim maturation real? | **Yes** (~75% of revisited claims with new evidence promote) |
| Ready to redesign mid-run? | **No** — finish analysis first; grammar expansion is a *next* experiment |

---

## Discovery

| Metric | Approx. |
|--------|--------:|
| Queries | **100** |
| Documents inspected (≤5/query) | **~380–420** |
| Accepted LWOs (company + locality + work) | **~160** |
| Work Claims (watching) | **~125** |
| Robot Jobs (post-gate) | **~67** |
| Worth investigating (investigate=yes) | **~59** |
| Unique companies (among jobs) | **~55** |
| Unique operating locations | **~75** |

*Notes:* q1–18 audit kept **11** of 24 old-gate jobs. Batches 3–6 add under the locked gate (~17+14+13+12). Counts are run-ledger estimates; exact card dumps are deliberately omitted — scoreboard > inventory.

### Funnel shape (what matters)

```
Queries 100
  → Docs ~400
    → LWOs ~160
      → Claims ~125
        → Robot Jobs ~67   (~40% of claims eventually promote or start as jobs)
          → Worth investigating ~59  (~88% of Robot Jobs)
```

Search stays broad. Product surface stays narrow. That split is the product architecture.

---

## Quality

| Metric | Result |
|--------|--------|
| **Promotion precision** (yes / Robot Jobs, post-gate) | **~85–88%** (B3≈88 · B4≈86 · B5≈85 · B6≈83) |
| **DIRECT / E1 share** of yes-jobs | **~55–60%** |
| **Named-load share** | **~100%** of Robot Jobs (gate requirement) |
| **Hard-demotion rate** (audit) | **3/24** old pool (McLane · LKQ · L&F) + ongoing rejects (Amazon AS/RS, tire primary, forklift-only, tote *sorting*) |

Precision did **not** collapse when leaving grocery density. That is the durability result.

---

## Novelty

| Metric | Result |
|--------|--------|
| **Novel account rate** (new company among yes-jobs) | **~80%+** across B3–B6 |
| **Novel site rate** (known company, new location) | Material — CuraScript Tempe→Newark · NAPA multi-site · Lineage CA · Ingram Chambersburg |
| **Pattern Novelty Rate** (q59–100) | **~40%** of promotions introduce a new family |
| **Top-3 pattern saturation** (q59–100) | **~58%** — rising slowly; not exhausted |

### Strongest recurring work-pattern families

1. **Move completed picks / orders → stage or pack** (tote · cart · pallet)  
2. **Return / recirculate empty totes & carts** to pack or process lines  
3. **Hospital / pharmacy cart & cassette delivery** (par carts · med carts)  
4. **Manufacturing waterspider / kit → line / POU replenishment**  
5. **Ecommerce / apparel pick-cart & tote → putwall or conveyor**  
6. **Zone consolidation via tote / pullwall** (auto parts, wholesale)

Pallet-dock grocery remains a **valid** family — it is no longer the **only** family.

### Three value types (all real)

| Type | Defensibility |
|------|----------------|
| New account — “didn’t know this company” | High volume |
| New site — “knew brand, not this operation” | High (CuraScript, NAPA, Lineage, Ingram) |
| **New work** — “knew account, not this robot-compatible task” | **Highest** long-term (hospital carts, pack-mod induction, kit→line, empty-tote recirculation) |

---

## Productivity

| Metric | Per 10 queries |
|--------|---------------:|
| Robot Jobs | **~6–7** (post-gate average) |
| Worth-investigating jobs | **~5.5–7.5** (B3 peak 7.5 · B4 6.0 · B5 5.5 · B6 ~4.5) |
| DIRECT/E1 jobs | **~3.5–4.0** |

Productivity dipped when deliberately diversifying industries — **quality and pattern novelty did not**. Correct trade for a discovery-engine test.

---

## Learning

| Metric | Result |
|--------|--------|
| **Claim Maturation Rate** (q59–100) | **~75%** of claims revisited with stronger evidence → Robot Job |
| **EXPLOIT vs EXPLORE** | EXPLOIT ≈ high-precision jobs; EXPLORE ≈ breadth + maturation feedstock; both needed |
| **Strongest vocabulary terms** | `tote` · `cart` · `kit` · `deliver` · `return` · `stage` · `replenish` · `waterspider` · `pack station` · `put to light` · `par cart` / `medication cart` |
| **Weak / reject vocabulary** | order selector alone · forklift-primary · AS/RS · tote *sorter* · tire rolling · grasping / case pick as Origin action |

### What the dual-arm design proved

- **EXPLOIT** without EXPLORE → saturates one family.  
- **EXPLORE** without gate → 46% precision (audit).  
- **Both + gate + claims** → ~85% precision **and** new pattern families.

### Grammar note (do not change yet)

```
ACTION × OBJECT × PLACE
```

is already carrying the run. A plausible *future* expansion:

```
ACTION × OBJECT × PATH/DESTINATION × OPERATING CONTEXT × FRICTION
```

e.g. `return × empty tote × pack→pick × fulfillment × repetitive travel`

**Do not reopen the experiment to fit that.** Origin 100 is complete. Grammar expansion is a separate trial.

---

## Batch trajectory (longitudinal)

| Phase | Queries | Job Density | Precision | Pattern signal |
|-------|---------|------------:|----------:|----------------|
| Audit | 1–18 | — | 46% old gate | Broke the pool |
| B3 Gate | 19–38 | **7.5** | **~88%** | Gate works |
| B4 Durability | 39–58 | **6.0** | **~86%** | New patterns outside grocery |
| B5 Continue | 59–78 | **5.5** | **~85%** | Hospital · apparel · kit · biotech |
| B6 Finish | 79–100 | **~4.5** | **~83%** | Pharmacy · aerospace · book cart · pharma return |

Gate held. Grammar generalized. Finish was correct.

---

## What this is / is not

| Is | Is not |
|----|--------|
| Evidence of **repeatable robot-directed discovery** | A CRM / SIGNAL lead list |
| Proof Origin-shaped work exists broadly in the open economy | A claim Origin should pick cases |
| A scoreboard for product behavior | A dump of 67 cards |
| Justification to productize the **funnel** (claims → jobs) | Permission to weaken the gate |

---

## Recommended next (after this scoreboard)

1. Persist **Work Claims** and **Robot Jobs** as first-class objects (with evidence grade + investigate).  
2. Instrument Pattern Novelty / Saturation / Claim Maturation in the run harness.  
3. Optional second envelope (different robot) — same protocol — to test method transfer.  
4. Defer ACTION×OBJECT×PATH×CONTEXT×FRICTION until a fresh controlled trial.

---

## Artifact index

| Doc | Role |
|-----|------|
| [ORIGIN_OPEN_WORLD_100.md](./ORIGIN_OPEN_WORLD_100.md) | Protocol |
| [origin_open_world_18_audit.md](./origin_open_world_18_audit.md) | Pause audit |
| [origin_open_world_batch3_gate_validation.md](./origin_open_world_batch3_gate_validation.md) | Gate works |
| [origin_open_world_batch4_durability.md](./origin_open_world_batch4_durability.md) | Patterns generalize |
| [origin_open_world_batch5_continue.md](./origin_open_world_batch5_continue.md) | Stop rule pass + cumulative metrics |
| [origin_open_world_batch6_finish.md](./origin_open_world_batch6_finish.md) | Queries 79–100 |
| **This file** | Whole-run scoreboard |

Ledger status: `origin_100_complete`
