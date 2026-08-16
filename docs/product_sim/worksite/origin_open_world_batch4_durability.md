# Batch 4 — Durability results (queries 39–58)

**Gate:** unchanged  
**Split:** 10 EXPLOIT / 10 EXPLORE  
**Baseline Job Density (B3):** ~7.5 worth-investigating / 10 queries  

---

## Headline

**Precision held. Discovery still producing new patterns — not only grocery dock/pallet clones. Continue toward 100.**

| Metric | Batch 3 | Batch 4 | Drift? |
|--------|--------:|--------:|--------|
| Promotion Precision | ~88% | **~86%** (12/14) | Stable |
| Robot Jobs promoted | 17 | **14** | Gate still tight |
| Investigate=yes | 15 | **12** | — |
| Work Claims | 45 | **~34** | Healthy watching pool |
| Claim→Job | ~38% | ~29% of new claims | Still cautious |
| **Job Density** (yes / 10 q) | **7.5** | **6.0** | Mild dip, still productive |
| New DIRECT/E1 per 10 q | — | **~4.0** | Strong |

Precision did **not** collapse. Density dipped slightly (diversified search finds fewer pure foodservice dock hits) but stayed productive. Novelty and pattern breadth are the better news.

---

## Decision question (after query 58)

> Is the engine continuing to find **new, direct robot work** — or merely repeating dock/staging/pallet across new companies?

**Answer: still finding new work patterns.** Continue 59–100 with same dual-arm mix + gate.

Evidence below. If Batch 5 collapses to pallet-dock only, then pause for vocabulary broaden — not yet.

---

## Object diversity (promoted jobs)

| Load | Count | Examples |
|------|------:|----------|
| **tote** | 5 | Inmar empty-tote supply · NAPA Norcross zone consolidate · Copeland kit totes · CuraScript Tempe · MSC pick-to-tote |
| **cart** | 3 | Ship Smarter put-to-light cart · Ingram pick carts · Rexel pack carts |
| **kit / container** | 2 | Dover waterspider · Copeland kits→pack |
| **carton** | 2 | DigiKey pick→pack · PRH Crawfordsville carton stock |
| **pallet** | 2 | Charlie's Seattle stage · Lineage Fullerton stage/deliver |

**Not collapsed to pallet.** Tote+cart+kit carry the batch. Pallet-dock remains a valid family but is no longer the only surface.

---

## Pattern families this batch

### New / diversified (what we wanted)

| Pattern | Example | Industry |
|---------|---------|----------|
| Supply empty totes to process line | Inmar · Libertyville, IL | Returns / reverse logistics |
| Zone→store **tote consolidation** | NAPA · Norcross, GA | Auto parts |
| Manufacturing waterspider / JIT route | Dover · South Chesterfield, VA | Industrial mfg |
| Stage **kits in totes** → packing | Copeland · Forney, TX | Manufacturing |
| Ecommerce **put-to-light cart** + totes | Ship Smarter · Indianapolis, IN | 3PL ecommerce |
| Electronics pick → pack transport | DigiKey · Thief River Falls, MN | Electronics dist. |
| Book carton / low-lift move | Penguin Random House · Crawfordsville, IN | Publishing FC |
| Apparel material move + stage | Royal Apparel · Hauppauge, NY | Apparel |
| Electrical wholesale cart/container pack | Rexel · Hayward, CA | Electrical dist. |
| Med-device deliver supplies to depts | Laborie · Mechanicsburg, PA | Med device |

### Repeat family (useful, saturating if exclusive)

| Pattern | Example |
|---------|---------|
| Completed order → stage/dock (pallet) | Lineage Fullerton/Riverside · Charlie's Seattle |
| Return totes/carts to pack area | CuraScript Tempe (new **site**, known pattern) |

Repeat family ≈ 3/14 jobs. Acceptable. Not dominant.

---

## DIRECT-action yield

**New DIRECT + E1 this batch:** 8 / 20 queries ≈ **4.0 per 10 queries**

| Site | Task | Why DIRECT/E1 |
|------|------|----------------|
| Inmar · Libertyville | Stock empty totes at scan lines; tote→pallet move | Role owns tote movement |
| NAPA · Norcross | Consolidate via **tote + pullwall** zone→store | Explicit tote process |
| Dover · S. Chesterfield | Waterspider material logistics routes | Role = material delivery |
| Copeland · Forney | Kits staged in totes → packing | Explicit tote/kit deliver |
| CuraScript · Tempe | Return totes and carts | Same E1 as prior sites |
| Ship Smarter · Indy | iPad cart + lighted totes | Cart/tote is the tool |
| DigiKey · TRF | Transport product pick→pack locations | Explicit internal transport |
| Lineage · Fullerton | Stage and deliver completed orders | Explicit deliver/stage |

---

## Novelty

| | Count |
|--|------:|
| Novel companies (among yes-jobs) | **10 / 12** |
| Known company, new site | CuraScript Tempe · Lineage CA sites · NAPA Norcross |
| Known-universe collapse? | **No** |

Novel set includes: Inmar, Dover, Copeland, Ship Smarter, DigiKey, MSC, Laborie, Penguin Random House, Ingram, Royal Apparel, Rexel, Charlie's (new), Schwan's (claim/weak job).

---

## Claim maturation (started tracking)

| Prior claim | This batch | Outcome |
|-------------|------------|---------|
| Charlie's Produce (locality soft) | Seattle + “wrapped and staged upon completion” | **→ Robot Job** (DERIVED E2, pallet) |
| Lineage selector (locality soft) | Fullerton / Riverside / Fontana + stage/deliver | **→ Robot Job** (DIRECT E1, pallet) |
| CuraScript family | Tempe AZ same tote/cart return language | **→ new site Robot Job** |
| NorCal / WFM thin selectors | — | Remain watching |
| Baxter / Johnstone kitting | Assembly-primary | Remain **claims** (not jobs) |

**Maturation works.** EXPLORE holdings are not dead ends — additional observations promote them. That validates:

> Search broadly → preserve claims → promote narrowly.

---

## Arm split (Batch 4)

### EXPLOIT

| Metric | Value |
|--------|------:|
| Robot Jobs | 7 |
| Investigate=yes | 6 |
| Precision | ~86% |
| Dominant objects | tote, kit, cart |

### EXPLORE

| Metric | Value |
|--------|------:|
| Work Claims | ~28 |
| Robot Jobs | 7 |
| Investigate=yes | 6 |
| Precision | ~86% |
| Value | Industry breadth + claim maturation |

Held as claims (not jobs): Hanna Andersson pick/pack, Stryker walk-pick, Revlon pick-to-light pack station, City Furniture (heavy / order-picker heights → Origin weak), building-materials forklift-primary, Delta Apparel E3, Cosmetics E3 station work.

Rejected: 48forty tote *sorting*, KeHE forklift putaway, Amazon FC.

---

## Job Density

Worth-investigating Robot Jobs / 10 queries:

| Batch | Density |
|-------|--------:|
| 3 | 7.5 |
| 4 | **6.0** |

Still strong. Dip expected when deliberately leaving the densest grocery-dock vein to test breadth.

---

## Product reading

1. **Architecture still correct** — broad search, narrow promotion, claims as watching layer.  
2. **Surface is broader than grocery AMR dock work** — apparel, books, electronics, auto parts totes, manufacturing waterspider/kits, returns tote supply, ecommerce cart totes.  
3. **Pallet-dock is a durable family, not the whole product** — object mix proves Origin-relevant work exists beyond EPJ grocery selection.  
4. **Claim maturation is real** — Charlie's, Lineage, CuraScript Tempe. Track this as a first-class metric going forward.  
5. **Search grammar asset confirmed:**

```
ACTION × OBJECT × PLACE
move|deliver|return|stage|supply|consolidate
  × tote|cart|carton|kit|order|pallet
  × dock|staging|pack|pick face|zone|station|department
```

---

## Next

**Continue queries 59–100** · keep 50/50 · same gate · re-check at ~78 (another 20) for pattern collapse.

If Batch 5 Job Density stays ≥5 **and** ≥30% of new jobs are non-pallet-dock patterns → finish 100.  
If Batch 5 is ≥70% pallet-dock grocery/foodservice → pause and broaden capability vocabulary (problem/workflow lenses, more manufacturing/returns/ecommerce cart language) — not company lists.

Ledger: `batch4_complete_continue_to_100`
