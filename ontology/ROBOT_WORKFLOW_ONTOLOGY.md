# Robot Workflow Ontology

**Purpose:** the real jobs-of-work a robot performs — the bridge between
capabilities and job requirements. A workflow is satisfied by **capabilities**,
which are grounded in **hardware**. A workflow is never selected by robot
category.

Code: work-physics templates + families in
`app/services/robot_requirement_match.py`; corpus in
`app/data/robot_job_match_corpus.json`; WORK primitives in
[`primitives.v1.json`](primitives.v1.json).

## Workflow families (implemented) ✅

Each corpus job has a `tape_family` (its work-physics). Each family requires a
**specific** capability — this is what keeps boards differentiated and prevents
category leakage.

| Workflow family | Required capability | Example work |
|-----------------|---------------------|--------------|
| `pallet` | `manipulate` (+ payload/grasp/throughput unknowns) | Case palletizing, stack finished cases |
| `gripper` | `manipulate` | Machine tending, load parts into CNC |
| `transport` | `tote_transport` \| `transport` (or mobile+manip → LIKELY) | Point-to-point tote transport, line replenishment |
| `cart` | `tote_transport` \| `transport` | Deliver medication carts, cart movement |
| `scrub` | `hard_floor_scrub` | Overnight hard-floor scrub routes |
| `inspect` | `inspect_route` | Facility inspection routes, gauge reads |
| `serve` | `transport` (item delivery) | Run food/drinks to tables, room-service delivery |
| `food_prep` | `food_prep` | Operate fry station, assemble bowls, grill line |
| `beverage` | `beverage_prep` | Espresso bar, cocktail bar |
| `shelf_scan` | `shelf_scan` | Retail inventory scanning — out-of-stocks, pricing, planogram (Simbe Tally) |
| `pallet_move` | `pallet_move` | Pallet putaway, dock→storage, line feed (autonomous forklift — Fox, Third Wave) |
| `trailer_unload` | `trailer_unload` | Unload cases from trailers/containers (Stretch, Pickle) |
| `pick_pack` | `pick_pack` | Piece/each picking into orders (Ambi, Plus One, RightHand) |
| `sortation` | `sortation` | Parcel sortation to destinations (put-to-wall) |
| `disinfection` | `disinfect` | UV/surface disinfection of rooms (Xenex, UVD) |
| `asrs` | `goods_to_person` | Store/retrieve goods to a picker (Exotec, AutoStore, Hai) |
| `agriculture` | `agriculture_task` | Weeding/harvest/spray (Carbon Robotics LaserWeeder, FarmWise) |
| `construction` | `construction_task` | Layout/drywall/rebar/earthmoving (Dusty, Built) |
| `marine` | `marine_task` | Hull inspect/clean, quay and underwater work |
| `avionics` | `avionics_task` | Drone inspection/delivery, eVTOL, autonomous flight |
| `aerospace` | `aerospace_task` | Satellite servicing, orbital debris capture, launch ground support |
| `mining` | `mining_task` | Haulage/drilling/loading |
| `clinical_delivery` | `healthcare_task` | Deliver meds pharmacy→units, specimens→lab, supply/meal/linen delivery |
| `resident_services` | `healthcare_task` | Eldercare meals/linens/amenities to resident rooms |
| `restroom` | `surface_clean` | Clean restrooms (toilets, urinals, floors) |

> Healthcare (`clinical_delivery`) and eldercare (`resident_services`) require
> the `healthcare_task` work primitive — **not** warehouse `tote_transport` and
> **not** a humanoid torso class — so a hospital/clinical assistant (Moxi, Aethon,
> Relay with hospital evidence) matches them while a warehouse tote-AMR (Origin)
> does not. The `healthcare`/`eldercare` vertical
> ([`ROBOT_VERTICAL_ONTOLOGY.md`](ROBOT_VERTICAL_ONTOLOGY.md)) labels *where*;
> these families are the *work*. FIND class **Healthcare** (aliases:
> medical / clinical / hospital) stamps `product_class=healthcare`.

> Broader target workflows — trailer unloading, kitting, pick/pack (robot-side),
> line replenishment as a distinct family, hospital delivery as a distinct family
> — are ⬜ planned; today hospital/hotel delivery flows through `cart`/`serve`.

## Requirement templates

Each family expands to a set of **requirements** (`_*_REQS` in the matcher). A
requirement is evaluated to `MATCHED` / `LIKELY` / `UNKNOWN` / `UNMET`. Example —
`serve`:

```
serve_food_drink   (required)  → MATCHED if transport present
indoor_navigation  (required)  → MATCHED/LIKELY if mobile
mobility           (required)  → MATCHED if mobile
payload_vs_object  (required)  → UNKNOWN (tray/load weight not established)
```

Unknowns are **preserved**, not guessed. A family whose required capability is
absent yields `UNMET` → `NOT_A_MATCH` (truthful rejection).

## Mapping to WORK primitives

Workflow families decompose into the frozen WORK primitives
([`primitives.v1.json`](primitives.v1.json)), e.g. `cart` ⊇
`eng.acquire_cart_or_tote` + `tr.point_to_point` + `plc.staging_place` +
`per.detect_human`. Primitive IDs are frozen (never renamed; only added).

## Rules
- A workflow is satisfied only by the **specific** capability it requires.
- Generic mobility is a **gate**, not a differentiator (`GENERIC_CAPABILITIES`).
- Ranking prefers **distinctive-capability utilization**, never a category quota
  (`DISTINCTIVE_CAPABILITIES`, `distinctive_utilization`).

See [`ROBOT_JOB_ONTOLOGY.md`](ROBOT_JOB_ONTOLOGY.md) for the full job object and
[`ROBOT_INFERENCE_RULES.md`](ROBOT_INFERENCE_RULES.md) for match verdicts.
