# Batch 3 — Gate Validation results

**Queries:** 19–38 (20) · **10 EXPLOIT + 10 EXPLORE**  
**Gate:** Robot Job only if `(DIRECT | DERIVED≥E2)` AND named `load_interface`  
**Baseline:** old gate Promotion Precision ≈ **11/24 = 46%**  
**Target:** ≥ **70%** worth investigating among promoted Robot Jobs  

Search may be speculative. Product surface is not.

---

## Headline answer

**Yes — the tightened gate raised Robot Job precision substantially without destroying discovery.**

| | Old (q1–18) | Batch 3 (q19–38) |
|--|------------:|------------------:|
| Robot Jobs promoted | 24 (too loose) | **17** |
| Worth investigating (yes) | 11 | **15** |
| **Promotion Precision** | **46%** | **15/17 ≈ 88%** |
| Work Claims (watching) | conflated with jobs | **28** |
| Claim→Job conversion | n/a | **17/28 ≈ 61%** of claims that had enough evidence… wait — see below |

Correct Claim→Job framing:

| | EXPLOIT | EXPLORE | Combined |
|--|--------:|--------:|---------:|
| Work Claims created | 14 | **31** | **45** |
| Robot Jobs promoted | **9** | **8** | **17** |
| Claim→Job conversion | 9/14≈64% | **8/31≈26%** | **17/45≈38%** |

**38% Claim→Job is healthy.** EXPLORE especially: saw many workflows, promoted few. That is epistemic discipline — not failure.

---

## Arm comparison

### EXPLOIT (q19–28) — precision arm

| Metric | Value |
|--------|------:|
| Queries | 10 |
| LWOs accepted | ~16 |
| Work Claims | 14 |
| Robot Jobs | **9** |
| DIRECT / DERIVED | 7 / 2 |
| E1 / E2 | 6 / 3 |
| Named-load rate (jobs) | **9/9 = 100%** |
| Investigate=yes | **8** |
| Investigate=weak | 1 |
| **Promotion Precision** | **8/9 ≈ 89%** |
| Novel companies (among jobs) | **8/9** |

**Promoted Robot Jobs (EXPLOIT)**

| Site | Task | Class | Ev | Load | Invest. |
|------|------|-------|----|------|---------|
| Duluth Trading · Calhoun, GA | Pick into **tote on cart** → pack/conveyor | DIRECT | E1 | tote | yes |
| O'Reilly Auto Parts · Des Moines, IA | Keep pick zones supplied with **totes** | DIRECT | E1 | tote | yes |
| Performance Foodservice · Houma, LA | Completed orders → **shipping dock staging** | DIRECT | E1 | pallet | yes |
| Shepherd Electric · Sterling, VA | Pull/verify/**stage** outbound & will-call | DIRECT | E2 | carton | yes |
| UDT · Orlando, FL | Pull finished product → **stage freight dock** | DIRECT | E1 | carton/pallet | yes |
| C&S · Windsor Locks, CT | EPJ: staging area → **correct doors** (cross-dock) | DIRECT | E1 | pallet | yes |
| Quince · Carneys Point, NJ | Push **utility carts** / move items (returns+fulfill) | DERIVED | E2 | cart | yes |
| Weiman Products · Cartersville, GA | **Stage** outbound orders for ship | DERIVED | E2 | pallet | yes |
| Gopuff · Cherry Hill, NJ | Carts/jacks move product (generic DC) | DERIVED | E2 | carton | **weak** |

**Held as Work Claim / rejected (EXPLOIT)** — gate working:

| Hit | Disposition |
|-----|-------------|
| KeHE Stockton putaway forklift | reject (forklift-primary) |
| Publix / Williams-Sonoma putaway forklift | reject |
| Waterspider *definition* pages | no COMPANY+LOCALITY |
| 3PL tote-zone vendor essays | no LWO |
| Returns *inspect/repair* (Tustin, Mettler) | claim only — manipulation, not AMR transport |
| Carter's Stockbridge | duplicate prior job (not re-counted) |

EXPLOIT lesson: action vocabulary finds **DIRECT** jobs. Also finds forklift traps — rejection gate still needed.

---

### EXPLORE (q29–38) — discovery arm

| Metric | Value |
|--------|------:|
| Queries | 10 |
| LWOs accepted | ~35 |
| Work Claims | **31** |
| Robot Jobs | **8** |
| DIRECT / DERIVED (jobs) | 6 / 2 |
| E1 / E2 (jobs) | 6 / 2 |
| Named-load rate (jobs) | **8/8 = 100%** |
| Investigate=yes | **7** |
| Investigate=weak | 1 |
| **Promotion Precision** | **7/8 ≈ 88%** |
| Novel companies (among jobs) | **6/8** (Sysco/Lineage known-ish) |

**Promoted only when dock/stage/transport language appeared**

| Site | Why promoted (not “selector=job”) | Class | Ev | Load | Invest. |
|------|-----------------------------------|-------|----|------|---------|
| National DCP · Burleson, TX | Stage pallets at **outbound dock** | DIRECT | E1 | pallet | yes |
| Keurig Dr Pepper · Austin, TX | Move completed order → **loading dock** | DIRECT | E1 | pallet | yes |
| Keurig Dr Pepper · Cranberry Twp, PA | Same dock-move language | DIRECT | E1 | pallet | yes |
| US Foods · Sacramento, CA | Deliver products to **correct dock area** | DIRECT | E1 | pallet | yes |
| Performance Foodservice · Punta Gorda, FL | Completed order → **dock staging** | DIRECT | E1 | pallet | yes |
| UNFI · Stockton, CA | **Stages** pallets in bay | DERIVED | E2 | pallet | yes |
| UNFI · Harrisburg, PA | Stages pallets / move in warehouse | DERIVED | E2 | pallet | yes |
| Sysco · Fremont/Coraopolis pattern | Transport product to **dock staging** | DIRECT | E1 | pallet | **weak** (known account) |

**Work Claims kept watching (not Robot Jobs)** — this is the point of EXPLORE:

| Examples | Why claim-only |
|----------|----------------|
| WFM Richmond / Cheshire | Selector exists; no move×object×place |
| SpartanNash St Cloud / Menominee / Fargo produce | Assemble/palletize; transport inferred only (E3) |
| Publix Orlando selector | Wrap ready for truck — E3 |
| Ryder Tracy case picker | Palletize/hand stack — E3 |
| CPFD Ontario / Albertsons EPJ family | Already claimed; no new E1 |
| NorCal Produce West Sac | Stages mentioned → *could* promote; held weak E2 overlapping UNFI network — counted in claims if not double-promoting |
| Charlie's Produce | Strong language but locality soft in SERP → claim until city locked |
| Lineage order selector | Stage/deliver stated — locality soft → claim until pinned |
| Ecommerce Las Vegas picker/pack | No Origin transport interface |
| Capstone / FHI travel | No fixed worksite |

EXPLORE lesson: **broad search still finds companies and sites.** Promotion stays narrow. Vocabulary discovery: “stage at outbound dock” and “move completed order to loading dock” recur across foodservice/grocery — gold for future EXPLOIT seeds.

---

## Did we only prove “search transport → find transport”?

**No.**

- EXPLOIT: high precision Robot Jobs (expected).  
- EXPLORE: **31 Work Claims** from selector/replenish/pick-pack language — including net-new localities (Burleson NDCP, KDP Austin/PA, US Foods Sacramento, PFS Punta Gorda, UNFI Harrisburg/Stockton).  
- Of those, only **8** matured to Robot Jobs — and only because a second observation (dock/stage/transport verb) appeared in the same doc.

That is: **search broadly → reason cautiously → surface narrowly.**

UI shape validated:

> **17 Jobs Ready to Investigate**  
> **28 Work Patterns We're Watching** *(45 claims − 17 jobs; some claims are multi-LWO)*

---

## Promotion Precision (the number you asked for)

| Pool | Investigate=yes / Robot Jobs |
|------|-----------------------------:|
| Old gate (batches 1–2) | 11/24 = **46%** |
| Batch 3 combined | 15/17 = **88%** |
| EXPLOIT alone | 8/9 = **89%** |
| EXPLORE alone | 7/8 = **88%** |

**≥70% target: met.**

---

## Search grammar asset (reinforced)

Recurring Origin-shaped pattern:

**ACTION × OBJECT × PLACE**

| Action | Object | Place |
|--------|--------|-------|
| move / transport / deliver / stage / return / supply | tote · cart · carton · pallet · order | dock · staging · drop zone · pick face · pack station · door |

Not “AMR” / “warehouse automation.”

Generalizes later: Spot (`inspect × gauge × route`), Avidbots (`scrub × floor × concourse`), UR (`load × part × fixture`).

---

## Decision gate for queries 39–100

| Criterion | Result |
|-----------|--------|
| Precision ≥70%? | **Yes (~88%)** |
| Novel companies still appearing? | **Yes** (Duluth, O'Reilly Des Moines, Shepherd, UDT, Quince, KDP, PFS sites, …) |
| EXPLORE still producing useful claims? | **Yes** (31 claims, 26%→job) |
| Destroy discovery yield? | **No** — yield shifted from fake jobs → real claims + fewer true jobs |

**Recommendation: continue 39–100** with the same dual-arm mix (~50/50 EXPLOIT/EXPLORE) and the same promotion gate. Do **not** collapse to EXPLOIT-only.

Stop point before full remaining budget optional every ~20 queries to re-check precision drift.

---

## Files

- Protocol: [`ORIGIN_OPEN_WORLD_BATCH3.md`](./ORIGIN_OPEN_WORLD_BATCH3.md)  
- Prior audit: [`origin_open_world_18_audit.md`](./origin_open_world_18_audit.md)  
- Ledger status: paused → **batch3_complete_awaiting_continue**
