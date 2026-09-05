# Origin Open-World — pause audit (18 queries / 24 Robot Jobs)

**Date:** 2026-08-16  
**Purpose:** Break the pool before spending queries 19–100.  
**Question:** Are these real product value, or plausible-looking cards?

---

## Audit dimensions (locked for this pass)

| Dimension | Labels |
|-----------|--------|
| **Action class** | DIRECT · DERIVED · SPECULATIVE |
| **Evidence** | E1 direct movement stated · E2 movement stated, interface ambiguous · E3 workflow implies · E4 generic role |
| **Load interface** | tote · carton · cart · pallet · rack/bin · unknown |
| **Commercial availability** | greenfield_likely · partially_automated_expansion · incumbent_competitor · unknown |
| **Investigate?** | yes · weak · no *(Would I spend 20 minutes?)* |

**DIRECT** = human role text *explicitly contains* work Origin can assume.  
**DERIVED** = workflow implies a transport task Origin could own.  
**SPECULATIVE** = plausible transformation; insufficient evidence.

Product ranking should favor **DIRECT + strong DERIVED (E1/E2)** — not High/Medium fit alone.

---

## Card-by-card

| # | Site | Action | Ev | Load | Commercial | Investigate? | Notes |
|---|------|--------|----|------|------------|--------------|-------|
| 1 | Kroger · Delaware, OH | DERIVED | E3 | pallet / unknown | unknown | **weak** | Correct framing (not “picks cases”); movement to shipping only weakly stated. Classic selector→travel inference. |
| 2 | Replacement Parts · Little Rock, AR | **DIRECT** | **E1** | **tote** | unknown | **yes** | Role *is* tote distribution. Gold standard. |
| 3 | NAPA · Duncansville, PA | **DIRECT** | E2 | **cart** (+ jack) | unknown | **yes** | Push/pull carts over distance explicit. Origin object = cart (or cart substitute). Forklift duties must stay human. |
| 4 | Albertsons · Roanoke, TX | DERIVED | E2 | **pallet** | unknown | **weak** | Travel via EPJ real; Origin↔pallet payload gate open. Interesting, not product-primary. |
| 5 | Whole Foods · Richmond/Vernon/Austin | SPECULATIVE | E4 | unknown | unknown | **weak** | Order selector + cold; little movement language. |
| 6 | KeHE · Dallas, TX | **DIRECT** | **E1** | pallet | unknown | **yes** | “Transport completed orders … to staging” — duty is Origin-class. |
| 7 | Coastal Pacific · Ontario, CA | SPECULATIVE | E3 | unknown | unknown | **weak** | Voice selection; no explicit post-pick movement. |
| 8 | Container Store · Aberdeen/Coppell | **DIRECT** | E2 | pallet | **partially_automated_expansion** | **yes** | Putaway relocate is movement; Aberdeen automation = commercial question, not existence fail. |
| 9 | SpartanNash · Midland, GA | SPECULATIVE | E3 | pallet | unknown | **weak** | Assemble/palletize; transport inferred. |
| 10 | McLane · Forest Park, GA | SPECULATIVE | E3 | unknown | unknown | **no** | Reach truck / forklift-heavy; Origin subset too thin. **Should not have passed as Robot Job.** |
| 11 | Advance Auto · Kutztown, PA | DERIVED | E2 | **carton** | unknown | **yes** | “Move boxes” + pick/pack/stage — interface namable. |
| 12 | LKQ / Keystone · Exeter, PA | SPECULATIVE | E4 | unknown | unknown | **no** | Pull/package/stage — no movement object. **Should not have passed.** |
| 13 | L&F Distributors · El Paso, TX | SPECULATIVE | E3 | pallet | unknown | **no** | Beverage + likely forklift; Origin slice unclear. **Should not have passed (or hold as lead only).** |
| 14 | Schneider Electric · West Chester, OH | **DIRECT** | **E1** | tote / kit / empty container | unknown | **yes** | Waterspider = material movement. Plant-floor vs DC = sales context, not action fail. |
| 15 | Kraft Heinz · Cedar Rapids, IA | **DIRECT** | **E1** | **tote** | unknown | **yes** | Empty tote return / stage materials. |
| 16 | Vallarta / Roxford · Sylmar, CA | SPECULATIVE | E3 | pallet | unknown | **weak** | Select + stage; EPJ implied; thin. |
| 17 | Zenith (Kroger) · Indianapolis, IN | **DIRECT** | **E1** | pallet | unknown | **yes** | Wrap completed orders → **deliver to shipping dock**. |
| 18 | SpartanNash · Bloomington/Byron/Fargo | SPECULATIVE | E3 | pallet | unknown | **weak** | Multi-site existence OK; same thin interpretation as #9. Count as one weak family. |
| 19 | National DCP · Greensboro, NC | **DIRECT** | **E1** | pallet | unknown | **yes** | Stage completed pallets at outbound dock. |
| 20 | C&S · Brattleboro, VT | DERIVED | E2 | pallet | unknown | **weak** | EPJ/walkie movement real; freezer + pallet gates. Worth a glance, not top tier. |
| 21 | CuraScript SD · Grove City OH / Newark DE | **DIRECT** | **E1** | **tote + cart** | unknown | **yes** | Return totes/carts explicit. Cherry-picker duties excluded. |
| 22 | Carter’s · Stockbridge, GA | **DIRECT** | **E1** | pallet | unknown | **yes** | EPJ move product to **assigned drop zones** — pure staging transport. |
| 23 | Whole Foods · Lacey, WA | SPECULATIVE | E4 | unknown | unknown | **weak** | Duplicate pattern of #5; should fold into WFM claim, not new Robot Job. |
| 24 | Sysco · Canton MI / Indianapolis | SPECULATIVE | E3 | pallet | unknown | **weak** | Known-universe company; thin interpretation. Novelty fail for account discovery. |

---

## Aggregate (the number that matters)

### Action class

| Class | Count | IDs |
|-------|------:|-----|
| **DIRECT** | **10** | 2, 3, 6, 8, 14, 15, 17, 19, 21, 22 |
| **DERIVED (strong, E1/E2)** | **2** | 4 Albertsons, 11 Advance |
| **SPECULATIVE / weak derived** | **12** | 1, 5, 7, 9, 10, 12, 13, 16, 18, 20, 23, 24 |

*(C&S #20 kept in speculative/weak despite E2 — freezer+pallet + investigate=weak.)*

### Investigate?

| Bucket | Count | Share |
|--------|------:|------:|
| **Worth investigating (yes)** | **12** | 50% |
| Interesting but weak | **8** | 33% |
| **Should not have passed / no** | **4** | 17% |

| Bucket | Count | Share |
|--------|------:|------:|
| yes | **11** | 46% |
| weak | **9** | 38% |
| no (hard demote) | **4** | 17% |

**Yes (11):** Replacement Parts · NAPA · KeHE · Container Store · Advance Auto · Schneider · Kraft · Zenith/Kroger Indy · National DCP · CuraScript · Carter’s  

**Hard demote (4):** McLane · LKQ · L&F · Sysco-as-Robot-Job (known + E3).  
WFM Lacey folds into WFM claim — not a separate job.

### Evidence mix (among all 24)

| Band | Count |
|------|------:|
| E1 | **8** |
| E2 | **5** |
| E3 | **8** |
| E4 | **3** |

### Load interface named?

| Status | Count |
|--------|------:|
| Named (tote/cart/carton/pallet) | **16** |
| unknown | **8** |

Among **investigate=yes**, load named on **11/11**.

---

## Verdict

**24 surfaced → 11 genuinely worth investigating (~46%).**  
**10 DIRECT · 2 strong DERIVED · 12 speculative.**

Not catastrophic — and not good enough to spend 82 more queries at the same gate.

The engine **is** producing real product value at the top (Replacement Parts, KeHE, Zenith, National DCP, CuraScript, Carter’s, NAPA, Kraft, Schneider).  
It is also **over-producing** from “order selector exists → Origin carries picks” (E3/E4), which inflated Robot Job count from ~12 to 24.

**High fit ≠ product-good.** Several High-fit cards (Kroger Delaware, early SpartanNash) are correctly framed but **weak evidence**. Ranking must prefer **DIRECT + E1/E2 + named load**, not Origin-fit alone.

Rejection gate already works (forklift, tote sortation, Amazon sortation, contractors, Blue Origin collision). Keep it. Add a **promotion gate** before something becomes a Robot Job.

---

## Tightened definition of a good Robot Job

A candidate becomes a **Robot Job** only if:

1. **Action class ≠ SPECULATIVE** — DIRECT or DERIVED with ≥ E2  
2. **Load interface named** (or explicitly unknown → demote to Work Claim, not Robot Job)  
3. **Commercial availability** recorded (even if `unknown`)  
4. **Investigate?** would be yes *or* weak-with-named-load — speculative E3/E4 selectors stay as **Work Claims / workflow existence**, not Robot Jobs  

### Surface order (product)

1. DIRECT + E1  
2. DIRECT + E2  
3. DERIVED + E2 with named load  
4. Everything else → claim layer only  

### Demote from current pool (keep as claims, not Robot Jobs)

McLane · LKQ · L&F · Whole Foods Lacey (fold) · Sysco thin hit · SpartanNash Midland/family · CPFD · Vallarta · WFM Richmond family (claim OK) · Kroger Delaware (claim + weak derived — keep visible as example of framing, demote from “job” rank)

### Keep as Robot Jobs (n≈11)

Replacement Parts · NAPA · KeHE · Container Store · Advance Auto · Schneider · Kraft · Zenith · National DCP · CuraScript · Carter’s  

*(Albertsons / C&S: hold as DERIVED watchlist with pallet gate — not top surface.)*

---

## Resume rule (queries 19–100)

Do **not** resume until Automation Interpretation applies:

```
Work Claim
  → name load interface (or mark unknown)
  → classify DIRECT / DERIVED / SPECULATIVE
  → evidence E1–E4
  → commercial availability
  → Robot Job ONLY if DIRECT|DERIVED≥E2 AND load ≠ unknown
  → investigate yes/weak/no
```

Prefer search lenses that yield **DIRECT** language: tote return, cart movement, stage to dock, drop zone, water spider, putaway relocate — not only “order selector + state.”

---

## Success criterion (refined)

After Open-World 100:

> Starting only with Origin capabilities, discovered **X companies / Y locations** with workflows, and **Z Robot Jobs** that are DIRECT or strong-DERIVED transport tasks with named load interfaces — of which **W are worth investigating**.

Not: 24 cards from 18 queries.  
Not: order-selector employer count.
