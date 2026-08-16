# Reverse-five experiment — Channel Graph × Robot Job Graph

**Question:** Can one distributor reasonably receive a feed of multiple Robot Jobs matched to robots they actually sell?

**Not collecting OEMs 11–50.** Reconstructing partner portfolios first.

Artifacts: [`reverse_five_portfolios.json`](./reverse_five_portfolios.json)

---

## Two distributor kinds (lock)

| Kind | Pattern | RFR need |
|------|---------|----------|
| **Catalog distributor / VAD** | Many SKUs, broad geo, lighter app engineering | *Find demand across my portfolio* |
| **Solution distributor / integrator** | Fewer OEMs, deep integrate/deploy/service | *Find automation work my team can solve* |

For solution partners, discovery can start from the **combined capability envelope** (Capability-Directed Discovery) without changing the RDD engine.

---

## Matrices (unknown stays unknown)

### RobotShop — catalog VAD

| OEM | Sell | Integrate | Deploy | Service | Train |
|-----|------|-----------|--------|---------|-------|
| AGIBOT | ✓ | ✓ | ✓ | ✓ | ✓ |

**Breadth:** 1 deep OEM (plus broader catalog C4 not scored here)  
**Families:** humanoid · quadruped/inspection · cleaning  
**Depth:** deep on AGIBOT VAD

### Cross Company — solution integrator

| OEM | Sell | Integrate | Deploy | Service | Train |
|-----|------|-----------|--------|---------|-------|
| Doosan | ✓ | ✓ | ✓ | ✓ | ✓ |
| Universal Robots | ? | ✓ | ✓ | ✓ | ✓ |
| FANUC | ? | ✓ | ✓ | ✓ | ✓ |

**Breadth:** 3 robot platforms  
**Families:** cobot · industrial manip · palletizing · machine tending  
**Depth:** deep solution (SE territory)

### RG Group — solution integrator (AMR)

| OEM | Sell | Integrate | Deploy | Service | Train |
|-----|------|-----------|--------|---------|-------|
| MiR | ✓ | ✓ | ✓ | ✓ | ? |
| Seegrid | ✓ | ✓ | ✓ | ? | ? |
| VisionNav | ✓ | ✓ | ? | ? | ? |
| ROEQ (modules) | ✓ | ✓ | ✓ | ? | ? |

**Breadth:** 3 AMR OEMs + payload modules  
**Families:** transport_amr (tote/cart/pallet workflows)  
**Depth:** deep AMR solution

### Accu Tech USA — catalog / VAR

| OEM | Sell | Integrate | Deploy | Service | Train |
|-----|------|-----------|--------|---------|-------|
| Techman | ✓ | ? | ? | ? | ? |

(+ EOAT: Robotiq, SCHUNK, ATI — components, not robot OEMs)

**Breadth:** 1 robot OEM  
**Families:** cobot / vision cobot  
**Depth:** sell-centric + components

### XCube — catalog VAD (single OEM, multi-product)

| OEM | Sell | Integrate | Deploy | Service | Train |
|-----|------|-----------|--------|---------|-------|
| Pudu | ✓ | ? | ✓ | ✓ | ✓ |

**Breadth:** 1 OEM, many products  
**Families:** floor_scrub · sweep · service delivery · hospitality delivery  
**Depth:** distribution + lifecycle claims

---

## Cross against existing Robot Job corpus

Corpus available now:

| Source | Jobs (approx) | Family |
|--------|----------------|--------|
| Origin Open-World 100 | ~67 | transport_amr |
| Neo Transfer 25 | ~16 | floor_scrub |
| Spot Extension 15 | ~13 | inspection_mobile |
| **Manipulation Open-World 25** | **~19** | palletizing · machine_tending |

### Routeability (theoretical)

| Partner | Compatible families | Jobs in corpus | Inside territory (rough) | Supported by their lines |
|---------|---------------------|----------------|--------------------------|---------------------------|
| **RG Group** | transport_amr | ~67 Origin | subset Mid-Atlantic + national warehouse jobs they bid | **Yes — MiR/Seegrid + ROEQ tote/cart** |
| **XCube** | floor_scrub (+ delivery) | ~16 Neo | nationwide claim → ~16 | **Yes — Pudu cleaning** |
| **RobotShop** | floor_scrub (+ inspection via D1) | ~16 Neo + ~13 Spot | US+CA → most | **Yes — AGIBOT C5 / D1** |
| **Cross** | cobot / palletizing / tending | **~19** (Manipulation 25) | ~9–11 SE | **Fed** — Doosan / UR / FANUC |
| **Accu Tech** | cobot | ~0 in current corpus | select states | Corpus gap |

### Verdict on the experiment question

**Yes — for the right partner.**

- **RG Group** can already be shown a multi-job AMR feed from Origin discovery (robots they sell / integrate).  
- **XCube** can already be shown a multi-job cleaning feed from Neo (Pudu).  
- **RobotShop** can already be shown cleaning + inspection feeds tied to AGIBOT lines.  
- **Cross** is now fed by **Manipulation Open-World 25** (~11 palletizing · ~8 machine tending) — **0 → ~19** jobs their team can solve. Accu Tech remains a cobot corpus gap.

One distributor **can** receive a feed containing multiple Robot Jobs matched to multiple robots/products they sell — demonstrated most cleanly by **RG Group** (multi-AMR OEM), **XCube** (multi-product cleaning/delivery under one OEM), and now **Cross** (multi-platform integrator × manipulation corpus).

---

## Distributor demo (build next — fixture only)

Lead with the partner who already intersects our graphs:

### Demo A — RG Group (solution / AMR)

> We found **37+** jobs for robots you sell.  
> *(subset of Origin corpus filterable to transport_amr + US)*  

Organized:

- Material movement / tote & cart transport — majority  
- Matched lines: MiR · Seegrid · VisionNav (+ ROEQ modules)

CTA: See jobs your company can solve.

### Demo B — XCube (catalog VAD / cleaning)

> We found **16** jobs for robots you sell.  

- Hard-floor scrubbing — 16  
- Matched line: Pudu cleaning portfolio

### Demo C — RobotShop (portfolio VAD)

> We found jobs for robots you sell.  

- Cleaning (AGIBOT C5) — from Neo family  
- Inspection routes (AGIBOT D1 / Spot-class) — from Spot family  

### Demo D — Cross Company (solution integrator) — **Manipulation 25**

> We found **~19** automation jobs your company can solve.  

- Palletizing — ~11  
- Machine tending — ~8  
- Matched lines: Doosan · Universal Robots · FANUC  
- ~9–11 inside SE footprint (capability + territory; Channel Match not scored yet)

Honesty: RG’s “37” remains an illustrative subset of ~67 Origin jobs and is **not** territory-filtered. Same discipline for Cross SE candidates vs full 19.

---

## Product distinction unlocked

```
Multiple robots → Distributor → Multiple jobs
```

Aggregation point on **both** sides. Marketplace position:

```
Robot Job → Compatible robots A/B/C → Partner who sells+supports A and C → Pursuit
```

OEM model weakness (customer doesn’t care which OEM we discovered first) is solved by routing through the channel.

---

## Stopped (2026-08-15)

Channel research complete for now. Question answered. Fixtures kept.

| Do | Don’t |
|----|--------|
| Keep fixtures · return to mixed-audience traffic | OEM 11–50 · more distributors · Channel Match scoring · distributor UI |
| Track See All CTR by `persona` | Expand channel graph before traffic evidence |

---

## Answer

> Can the Channel Graph + Robot Job Graph combine to create a new product for distributors?

**Yes.** Demonstrated product modes from the same engine:

1. **Find jobs for the robots you sell** — RG Group / XCube / RobotShop against existing corpora  
2. **Find automation jobs your company can solve** — Cross after Manipulation 25 (0 → ~19)

Portfolio breadth multiplies value when the work corpus covers the partner’s families. Cross needed a **manipulation** corpus — not another distributor.
