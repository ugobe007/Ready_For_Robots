# Origin Open-World 100 — results

**Started:** 2026-08-16 · **Completed:** 2026-08-15 (local)  
**Capability gate:** [locus_origin_work_translation.md](../envelopes/locus_origin_work_translation.md)  
**Budget:** 100 queries · ≤5 docs inspected / query  
**Queries completed:** **100** · status: `origin_100_complete`

**Final scoreboard:** [`ORIGIN_OPEN_WORLD_100_SCOREBOARD.md`](./ORIGIN_OPEN_WORLD_100_SCOREBOARD.md)

| Batch | Queries | Key result |
|-------|---------|------------|
| Audit | 1–18 | 24→11 worth investigating (46%) · [`origin_open_world_18_audit.md`](./origin_open_world_18_audit.md) |
| B3 Gate | 19–38 | Precision ~88% · density 7.5 · [`origin_open_world_batch3_gate_validation.md`](./origin_open_world_batch3_gate_validation.md) |
| B4 Durability | 39–58 | Precision ~86% · density 6.0 · new patterns · [`origin_open_world_batch4_durability.md`](./origin_open_world_batch4_durability.md) |
| B5 Continue | 59–78 | Density 5.5 · stop pass · pattern metrics · [`origin_open_world_batch5_continue.md`](./origin_open_world_batch5_continue.md) |
| B6 Finish | 79–100 | Same protocol · [`origin_open_world_batch6_finish.md`](./origin_open_world_batch6_finish.md) |

---

## Legacy section (q1–18 cards — historical)

The cards below document the early permissive-gate surface. Post-audit keep-list and Batches 3–6 supersede ranking for product claims. See scoreboard for whole-run numbers.

**Batch 3:** precision ~88% · [`origin_open_world_batch3_gate_validation.md`](./origin_open_world_batch3_gate_validation.md)  
**Batch 4:** precision ~86% · Job Density 6.0 · new patterns (tote/cart/kit/mfg/ecommerce) · [`origin_open_world_batch4_durability.md`](./origin_open_world_batch4_durability.md)  

### Post-audit Robot Job surface (keep from q1–18)

Replacement Parts · NAPA · KeHE · Container Store · Advance Auto · Schneider · Kraft · Zenith/Kroger Indy · National DCP · CuraScript · Carter’s

### Demoted to Work Claim (not Robot Job)

McLane · LKQ · L&F · thin selector families (WFM, SpartanNash, CPFD, Vallarta, Sysco, Kroger Delaware as ranked job)

---

## Success frame (locked)

> Starting only with Locus Origin capabilities, discovered **X companies** and **Y locations** with physical workflows, and **Z specific transport tasks** Origin could perform.

Not: warehouse posting count · order-selector employer count.

---

## Funnel so far

| Stage | Count |
|-------|------:|
| Queries run | 18 |
| Candidate docs (SERP) | ~85 |
| Inspected / used | ~60 |
| Proposed LWO signals | ~40 |
| Accepted LWOs (company+locality+work) | **32** |
| Work Claims (assembled) | **26** |
| Passed Automation Interpretation | **24** |
| Robot Jobs (transport tasks) | **24** |
| Rejected (grasping / forklift-primary / no locality / vendor essay) | ~12 |

---

## Ranked Robot Job cards (refined scoring)

### 1. Kroger · Delaware, OH — **High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Manual grocery DC order selection: obtain from slots, build pallets/orders, submit to shipping |
| Robot-compatible task | `move_completed_picks` / `cart_movement` — carry accumulated order containers through selection → staging |
| Transformation confidence | **High** (select + stage + move language in localized posting) |
| Evidence | krogerdc.com · eQuest Kroger Supply Chain Order Selector, Delaware OH |
| Automation state | unknown |
| Origin fit | High (payload / aisle / container unknowns) |
| Novel | Yes |
| Unknowns | Order container vs pallet jack workflow; load; route design; current automation |

**Not claimed:** Origin picks cases.

---

### 2. Replacement Parts / Crow Burlingame · Little Rock, AR — **High fit** (direct A)

| Field | Value |
|-------|--------|
| Observed workflow | Collect, organize, distribute shipping totes across warehouse zones |
| Robot-compatible task | `transport_totes` — point-to-point tote distribution |
| Transformation confidence | **High** (role *is* tote transport) |
| Evidence | Auto Parts Warehouse Tote Distribution posting |
| Automation state | unknown |
| Origin fit | High |
| Novel | Yes |
| Unknowns | Tote weight/stack; aisle; incumbent carts |

---

### 3. NAPA Auto Parts · Duncansville, PA — **High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Receive, replenish, pick, load; push/pull carts & pallet jacks over distances |
| Robot-compatible task | `cart_movement` + `move_orders_pick_to_pack` + `replenishment_transport` |
| Transformation confidence | **High** (explicit cart push/pull + transport orders to shipping) |
| Evidence | jobs.genpt.com DC Associate Duncansville |
| Automation state | unknown |
| Origin fit | High (forklift tasks elsewhere → split human/PIT) |
| Novel | Yes |

---

### 4. Albertsons / Tom Thumb · Roanoke, TX — **Medium–High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Voice-directed full-case selection on ride-on EPJ; palletize for stores |
| Robot-compatible task | Absorb **travel** component of selection route / stage completed pallets — *if* collaborative AMR config fits case-on-pallet flow |
| Transformation confidence | **Medium** (travel explicit via EPJ; container = pallet → Origin payload gate) |
| Evidence | Albertsons Tom Thumb DC, Henrietta Creek Rd, Roanoke TX |
| Automation state | unknown (EPJ today ≠ robot fleet) |
| Origin fit | Medium–High |
| Novel | Yes |
| Unknowns | Pallet vs tote Origin config; heavy case lift remains human |

Same pattern @ Albertsons: Portland OR · Tolleson AZ · Meridian ID · Irvine CA · Melrose Park IL (multi-site claim family).

---

### 5. Whole Foods Market · Richmond, CA / Vernon, CA / Austin area — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Perishable DC order selection (floral/meat/produce; freezer→chill) |
| Robot-compatible task | Transport picks / reduce travel in selection; chill/freezer mods |
| Transformation confidence | Medium |
| Evidence | careers.wholefoods.com Order Selector DC postings |
| Automation state | unknown |
| Origin fit | Medium (cold + payload) |
| Novel | Yes (multi-site) |

---

### 6. KeHE Distributors · Dallas, TX — **High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Dry selector builds pallets; **transports completed orders via EPJ to staging** |
| Robot-compatible task | `move_completed_picks` / `order_consolidation_movement` |
| Transformation confidence | **High** (transport-to-staging explicit) |
| Evidence | KeHE Dry Selector C1/C2 Dallas |
| Automation state | unknown |
| Origin fit | High |
| Novel | Yes |

---

### 7. Coastal Pacific Food Distributors · Ontario, CA — **Medium–High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Voice pick dry/chill order selection; ground + flow rack |
| Robot-compatible task | Carry order through selection / to consolidation |
| Transformation confidence | Medium–High |
| Evidence | CPFD Order Selector Ontario CA |
| Automation state | unknown |
| Origin fit | Medium–High |
| Novel | Yes |

---

### 8. The Container Store · Aberdeen, MD / Coppell, TX — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Relocate inventory receiving → reserve / active pick; pallet jack putaway in pick modules |
| Robot-compatible task | `putaway_transport` / `replenishment_transport` |
| Transformation confidence | High for movement; Medium for Origin vs automated DC |
| Evidence | Container Store Replenishment & Putaway specialist postings |
| Automation state | **partially_automated** (Aberdeen described as automated DC) |
| Origin fit | Medium (incumbent automation adjacency) |
| Novel | Yes |

---

### 9. SpartanNash · Midland, GA — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Select from racks; assemble/palletize/wrap for customers |
| Robot-compatible task | Move accumulated picks / staging movement |
| Transformation confidence | Medium |
| Evidence | careers.spartannash.com Midland GA |
| Automation state | unknown |
| Origin fit | Medium–High |
| Novel | Yes |

---

### 10. McLane · Forest Park, GA — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Select/load; move product dock↔warehouse; reach truck + pallet jack |
| Robot-compatible task | Internal transport subset (not reach-truck high bay) |
| Transformation confidence | Medium |
| Evidence | McLane Warehouse Order Selector Forest Park |
| Automation state | unknown |
| Origin fit | Medium |
| Novel | Yes |
| Gate | Reach truck / forklift portions = reject for Origin |

---

### 11. Advance Auto Parts · Kutztown, PA — **Medium–High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Pick, pack, stage parts; move boxes; RF / voice |
| Robot-compatible task | Carton/box movement + pick→stage transport |
| Transformation confidence | Medium–High |
| Evidence | DC Associate Kutztown |
| Automation state | unknown |
| Origin fit | Medium–High |
| Novel | Yes |

---

### 12. LKQ / Keystone Automotive · Exeter, PA — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Pull, package, stage auto parts for shipment |
| Robot-compatible task | Stage / move completed picks |
| Transformation confidence | Medium |
| Novel | Yes |

---

### 13. L&F Distributors · El Paso, TX — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Beverage: pick account orders + replenish + wrap/stage pallets |
| Robot-compatible task | Replenishment transport + order movement (non-forklift subset) |
| Transformation confidence | Medium |
| Novel | Yes |
| Gate | Forklift-heavy beverage DCs often → Medium |

---

### 14. Schneider Electric · West Chester, OH — **Medium fit** (direct A, manufacturing)

| Field | Value |
|-------|--------|
| Observed workflow | Waterspider: deliver kits/parts, replenish POU, remove empty containers |
| Robot-compatible task | `point_to_point_transport` / `transport_totes` / empty-container return |
| Transformation confidence | **High** (role = material movement) |
| Automation state | unknown |
| Origin fit | Medium (plant floor vs classic DC; still Origin-class mobility) |
| Novel | Yes |

---

### 15. Kraft Heinz · Cedar Rapids, IA — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Water spider: stage materials, remove empty totes, return ingredients |
| Robot-compatible task | `transport_totes` / empty tote return / staging movement |
| Transformation confidence | High |
| Novel | Yes |

---

### 16. Vallarta / Roxford Produce · Sylmar, CA — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Overnight order select + audit; stage for shipment; EPJ |
| Robot-compatible task | Move/stage completed selections |
| Transformation confidence | Medium |
| Novel | Yes |

---

### 17. Zenith Logistics (Kroger DC) · Indianapolis, IN — **High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Voice/order select cases onto pallet; wrap completed store orders; **deliver to shipping dock** |
| Robot-compatible task | `move_completed_picks` / `move_orders_pick_to_pack` |
| Transformation confidence | **High** (dock delivery of completed orders explicit) |
| Evidence | Zenith Logistics Order Selector — 3PL at Kroger Indianapolis DC |
| Automation state | unknown |
| Origin fit | High |
| Novel | Yes (operator + site; Kroger network expansion beyond Delaware) |

---

### 18. SpartanNash · Bloomington, IN / Byron Center, MI / Fargo, ND — **Medium–High fit**

| Field | Value |
|-------|--------|
| Observed workflow | Select from racks; assemble/palletize/wrap; freezer variant @ Fargo |
| Robot-compatible task | Selection-route container movement / staging (freezer mods @ Fargo) |
| Transformation confidence | Medium |
| Novel | Yes (multi-site; Fargo freezer confirms earlier SpartanNash signal) |

---

### 19. National DCP (Dunkin’) · Greensboro, NC — **High fit**

| Field | Value |
|-------|--------|
| Observed workflow | EPJ/voice select dry/cooler/freezer; build custom orders; **stage pallets at outbound dock** |
| Robot-compatible task | `move_completed_picks` / staging movement |
| Transformation confidence | **High** |
| Novel | Yes |

---

### 20. C&S Wholesale Grocers · Brattleboro, VT — **Medium fit**

| Field | Value |
|-------|--------|
| Observed workflow | Freezer selector: pick via headset; double walkie / EPJ; wrap for bay doors |
| Robot-compatible task | Travel + completed-order movement (freezer gate) |
| Transformation confidence | Medium–High |
| Novel | Yes |

---

### 21. CuraScript SD (Cigna) · Grove City, OH / Newark, DE — **High fit** (direct A)

| Field | Value |
|-------|--------|
| Observed workflow | Pharma pick/pack/ship; **return totes and carts** to proper areas; restock pack stations |
| Robot-compatible task | `transport_totes` / `cart_movement` / pick→pack adjacency |
| Transformation confidence | **High** (tote/cart return explicit) |
| Novel | Yes |
| Gate | Cherry picker / high-bay tasks = reject for Origin |

---

### 22. Carter’s · Stockbridge, GA — **High fit**

| Field | Value |
|-------|--------|
| Observed workflow | OB shipper: RF close pallets; **EPJ move product to assigned drop zones** |
| Robot-compatible task | `order_consolidation_movement` / staging→drop-zone transport |
| Transformation confidence | **High** |
| Novel | Yes |

---

### 23–24. Whole Foods · Lacey, WA · Sysco Canton, MI / Indianapolis — **Medium** (network expansion)

Same decomposition as prior grocery/foodservice selection: human picks cases; robot candidate owns travel/container movement. Sysco = known-universe (novelty no for company; locality may still be new).

---

## Rejected / downgraded (gate working)

| Hit | Why |
|-----|-----|
| Imperial Trading Elmwood LA replenisher | Reach-lift / PIT primary — forklift class |
| United Distributors Savannah | Forklift pallet replenisher |
| Wild Fork reachtruck | Forklift / high reach |
| 48forty tote sorter Lakeland | Tote *sorting/stacking* manipulation, not AMR transport |
| Amazon delivery station | Package sortation / last-mile — weak Origin core |
| Capstone / FHI traveling selector | Labor contractor; no fixed worksite |
| Blue Origin “material movement” | Wrong industry / brand collision |
| Problem-lens essays (GTP vendor, travel-time blogs) | No COMPANY+LOCALITY — not LWOs |
| American Freight store warehouse | Retail floor movement, not Origin DC workflow |

---

## Scoreboard so far (toward success criterion)

| Metric | Value |
|--------|------:|
| Companies with transport tasks | **~22** |
| Distinct operating locations | **~30+** |
| Specific Origin transport tasks identified | **24** Robot Jobs |
| Novelty (vs Origin-18 / prior lab) | High |
| High transformation confidence | **9** |
| Cards labeled “Origin picks cases” | **0** |

---

## Next

**Paused.** Resume queries 19–100 only after Automation Interpretation uses the promotion gate in [`ORIGIN_OPEN_WORLD_100.md`](./ORIGIN_OPEN_WORLD_100.md) and [`origin_open_world_18_audit.md`](./origin_open_world_18_audit.md). Prefer DIRECT-language search lenses (tote return, dock staging, drop zones, cart movement, waterspider).
