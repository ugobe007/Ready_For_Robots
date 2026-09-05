# Outcome — vertical robot catalog (avionics vs aerospace)

**Date:** 2026-08-27
**Branch:** `cursor/vertical-robot-catalog-009b`
**Status:** done (partial catalog — verified SKUs only)

## Taxonomy

| Class | Definition shipped |
|-------|-------------------|
| **Avionics** | Drones, eVTOL (“flying cars”), autonomous airplane-like robots. Hangar/airside inspect is *work a drone can do*, not the class. |
| **Aerospace** | Satellites, rockets, space-exploration/development robots. Hot work: a robot attached to a satellite that captures **orbital debris**. |

Tractor / combine **implements** are `configuration_kind=implement_on_host` + `host_platform=tractor|combine`. Not a FIND tile and not a company class. Docs: `ontology/ROBOT_AVIONICS_AEROSPACE.md`, `ontology/ROBOT_TRACTOR_IMPLEMENT.md`.

## FIND picker

11 tiles. Avionics hint rewritten to drones / eVTOL / autonomous aircraft. Aerospace is the 11th tile. Agriculture hint names combines/tractors/implements. Construction hint names homes and buildings.

## Company / SKU counts (verified official HTTP 200 only)

| Vertical | Companies | Named SKUs | Examples |
|----------|-----------|------------|----------|
| Agriculture | 7 | 11 | Carbon LaserWeeder; Deere X Series Combine, Autonomous Tractor, See & Spray Ultimate; Monarch MK-V; Naio Oz/Ted/Jo; Ecorobotix ARA; Burro; CLAAS LEXION 8000-7000 |
| Construction | 5 | 5 | Dusty FieldPrinter; ICON Vulcan; COBOD BOD2; FBR Hadrian X; ACR TyBOT |
| Avionics | 7 | 7 | Skydio X10; Joby eVTOL; Archer Midnight; Beta ALIA; Wisk Generation 6; Zipline Platform 2; Shield AI V-BAT |
| Aerospace | 4 | 5 | Astroscale ELSA-d, ADRAS-J; ClearSpace-1; Starfish Otter; GITAI S2 |
| **Total** | **23** | **28** | Empty specs = UNKNOWN |

Skipped unverified: Built Robotics (403), Canvas (SSL), Honeybee Robotics (429), Advanced.farm (timeout).

## Jobs / task models added

Corpus work families (named employers we can defend; NASA / ESA / LAWA for space and eVTOL; no space-Walmart):

- Agriculture: combine harvest, tractor plant, tractor harvest, implement-on-tractor (weeding kept)
- Construction: home framing, 3D-print home, commercial building block-lay
- Avionics: drone inspect, drone delivery, eVTOL, autonomous flight (hangar jobs kept as aircraft inspect)
- Aerospace: satellite servicing, orbital debris capture, launch/pad ground support

Task-model slots: `combine_harvest_policy`, `tractor_plant_harvest_policy`, `tractor_implement_policy`, `residential_construction_policy`, `building_construction_policy`, `drone_inspection_policy`, `drone_delivery_policy`, `evtol_flight_policy`, `autonomous_flight_policy`, `satellite_servicing_policy`, `orbital_debris_policy`, `launch_ground_support_policy`.

## Tests

- `pytest` vertical catalog + LaserWeeder/Carbon + class qualify + ontology + tier families + vendor lookup + task models — **pass**
- `vitest` robotClassOptions + jobsWorkflow + knownOemLineups — **43 passed**
- LaserWeeder still agriculture. Carbon no regress.

## Leftover resume

Do not fake completeness. Next increment after live `fetch_page`:

```bash
# Verify a leftover official product URL, then add the named SKU to
# ontology/vertical_oem_sku_catalog.v1.json (or this builder) and merge:
PYTHONPATH=. python3 scripts/build_vertical_oem_catalog.py
# Optional discover on a verified OEM host:
PYTHONPATH=. python3 scripts/ingest_oem_sku_catalog.py --lookup-urls --discover-skus --oem john-deere
```

Priority leftovers: Built Robotics Exosystem, Canvas drywall, FarmWise Vulcan (product URL 404), CNH/AGCO named tractor SKUs, Diamond Age / Mighty Buildings / Monumental (homepage 200, no named SKU page), Reliable Robotics, Northrop MEV, D-Orbit, Motiv, Honeybee, DJI enterprise (not fetched).
