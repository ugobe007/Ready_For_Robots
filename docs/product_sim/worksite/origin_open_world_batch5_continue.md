# Batch 5 — Continue results (queries 59–78)

**Gate:** unchanged  
**Split:** 10 EXPLOIT / 10 EXPLORE  
**Bias:** healthcare supply · manufacturing/kits · returns empty totes · apparel/ecommerce · office products · pet · biotech — not grocery selectors  

---

## Headline

**Stop rule passed. Finish 79–100 on the same protocol.**

| Metric | Batch 4 | Batch 5 |
|--------|--------:|--------:|
| Promotion Precision | ~86% | **~85%** (11/13) |
| Robot Jobs promoted | 14 | **13** |
| Investigate=yes | 12 | **11** |
| **Job Density** (yes / 10 q) | 6.0 | **5.5** |
| New DIRECT/E1 per 10 q | ~4.0 | **~4.0** |
| Outside pallet-dock (of yes-jobs) | ~75% | **~100%** |

Density held above the ≥5 floor. Pattern breadth did **not** collapse to grocery dock/pallet. Continue to 100 without redesign.

---

## Cumulative metrics (q59 onward — first reading)

| Metric | Batch 5 | Reading |
|--------|--------:|----------|
| **Pattern Novelty Rate** | **~46%** (6/13) | Still inventing families, not only cloning |
| **Pattern Saturation (top-3)** | **~54%** (7/13) | Healthy — not yet exhausted |
| **Claim Maturation Rate** | **~80%** (4 matured / 5 revisited) | Watching layer still converts |

### Pattern Novelty (new families this batch)

| New family | Example |
|------------|---------|
| Hospital / clinical **par-cart delivery** | Beth Israel Lahey · Burlington, MA |
| Med-device **supermarket / POU** + packing carts/kits | Intuitive Surgical |
| Apparel **pack-mod tote induction** (slot → pack) | SanMar · Avondale |
| Apparel ecommerce **tote → conveyor** | Fashion Nova · Santa Fe Springs |
| Biotech / cell-therapy **kit replenishment** | RayzeBio |
| Clothing DC **empty-tote swap at conveyor** | Prologistix Groveport |

### Existing families (instances, not novel)

| Family | Example |
|--------|---------|
| Empty tote recirculation | Tasus · Bloomington, IN |
| Move completed totes pick→pack | Staples Bulk Selector |
| Pick-to-tote retail DC | Petco · Cranbury |
| Mfg kit stage → production | Multiquip · Cypress |
| Auto-parts cart transport | NAPA · Jacksonville (weak) |

### Top-3 saturation (this batch’s promoted jobs)

1. Apparel / ecommerce tote–cart handoff — SanMar · Fashion Nova · Prologistix  
2. Hospital / clinical cart routes — BILH · Ochsner  
3. Kit / POU / biotech replen — Intuitive · RayzeBio · Multiquip  

Top-3 ≈ **7/13 ≈ 54%**. Not exhausting; still room for new families in 79–100.

---

## Promoted Robot Jobs (investigate=yes)

| # | Company · site | Task | Load | Class | Pattern |
|---|----------------|------|------|-------|---------|
| 1 | Beth Israel Lahey · Burlington, MA | Stock/deliver **par carts**; Pyxis refill; unit delivery | cart | DIRECT E1 | Hospital par-cart |
| 2 | Ochsner · Meridian, MS | Organize **delivery carts** by location; deliver supplies | cart | DIRECT E1 | Hospital par-cart |
| 3 | Tasus · Bloomington, IN | Empty return **totes**; clean; stack; supply packaging | tote | DIRECT E1 | Empty-tote recirculation |
| 4 | Staples · Greencastle, PA | Pull/pack **totes**; move full totes onto conveyor | tote | DIRECT E1 | Tote pick→pack |
| 5 | Intuitive Surgical | Putaway **totes**; pack system **carts**/FRUs/**kits**; POU replen | tote/cart/kit | DIRECT E1 | Med-device SMKT/POU |
| 6 | SanMar · Avondale | Pick cart **or** totes; take ready-to-pack totes from slot | cart/tote | DIRECT E1 | Apparel pack-mod |
| 7 | Fashion Nova · Santa Fe Springs | Maneuver pick cart/tote; release full totes to conveyor | cart/tote | DIRECT E1 | Apparel ecommerce tote |
| 8 | Petco · Cranbury | **Pick-to-tote** merchandise for stores/DCs | tote | DERIVED E2 | Pick-to-tote retail |
| 9 | RayzeBio | Material replenishment **to Kitting Department** | kit | DERIVED E2 | Biotech kit replen |
| 10 | Prologistix · Groveport, OH | Product in totes → conveyor; replace with empty tote | tote | DIRECT E1 | Apparel tote swap |
| 11 | Multiquip · Cypress, CA | Pull/kit components; **stage** for production | kit | DERIVED E2 | Mfg kit stage |

### Weak (promoted, investigate=weak)

| Company · site | Why weak |
|----------------|----------|
| NAPA · Jacksonville | Cart named, but picker+PIT blend; known company/pattern |
| Press MH · Liberty, MO | Deliver to presses; pallet jack / paper rolls — Origin payload gate |
| Thermo Fisher · Swedesboro | Bins/totes language; regulated GDP — fit cautious |

### Held as Work Claims (not jobs)

Foxconn/Foxconn-style kitting-primary · Arrow Electronics (AS/RS) · ATD tire rolling · Wayfair heavy furniture MHE · Amazon FC · foodservice selectors without transport verb · 48forty-style tote *sorting* · Allina (cart soft) · Boston Scientific (load interface soft)

---

## Claim maturation (Batch 5)

| Prior watching | Revisited | Outcome |
|----------------|-----------|---------|
| Healthcare supply / Laborie-adjacent | BILH + Ochsner cart language | **→ Robot Jobs** (hospital par-cart family) |
| Empty-tote / Inmar family | Tasus manufacturing return totes | **→ Robot Job** (new industry instance) |
| Apparel Royal Apparel stage | SanMar pack-mod + Fashion Nova tote→conveyor | **→ Robot Jobs** (stronger named-load) |
| NAPA Norcross tote consolidate | NAPA Jacksonville carts | **→ weak Robot Job** (site maturation) |
| Baxter / Johnstone kitting | Multiquip kit stage | Multiquip promoted; Baxter-class remain mixed |

**Claim Maturation Rate:** 4 / 5 ≈ **80%** of revisited claims with stronger evidence promoted.

---

## Three value types (this batch)

| Type | Examples |
|------|----------|
| **New account** | BILH · Ochsner · Tasus · Staples · Intuitive · SanMar · Fashion Nova · Petco · RayzeBio · Multiquip |
| **New site** | NAPA Jacksonville (known brand) |
| **New work** | Hospital par-cart · Intuitive SMKT/POU · SanMar pack-mod induction — robot-compatible task types not just new logos |

New work discovery remains the strongest signal.

---

## Arm split

| | EXPLOIT | EXPLORE |
|--|--------:|--------:|
| Robot Jobs | 7 | 6 |
| Investigate=yes | 6 | 5 |
| Precision | ~86% | ~83% |
| Role | Hospital carts · empty totes · Staples totes · Intuitive | Apparel breadth · Petco · RayzeBio · Multiquip |

---

## Stop decision

| Criterion | Result |
|-----------|--------|
| Job Density ≥ 5 / 10 q | **5.5** ✓ |
| ≥30% outside pallet-dock | **~100%** ✓ |

→ **Finish queries 79–100.** No vocabulary redesign. Gate unchanged. Then whole-run scoreboard.
