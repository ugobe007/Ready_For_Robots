# Outcome — seed verified OEM catalog

**Date:** 2026-08-27
**Branch:** `cursor/seed-verified-oem-catalog-009b`
**Status:** done (verified HTTP 200 named SKUs only; leftovers recorded)

## Ontology law

MATCH is `COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → JOB REQUIREMENTS`. ChatGPT’s `robotType` / industry bucket tree was **not** adopted. FIND tiles remain unions; named SKUs ground work-kind claims.

**R30** (new): `claims_weeding` → `agriculture_weed` (LaserWeeder ≠ combine). Combine / spray / tractor / 3D-print / block-lay / layout are separate primitives. Wisk/EHang autonomy is a `autonomy_mode=autonomous` configuration fact, not an airplane-IFR dump. Elroy Chaparral is `autonomous_aircraft` → `autonomous_flight`, not LAWA eVTOL and not `drone_task`.

## Verified ingest (HTTP 200 named SKU pages only)

Vertical catalog after this pass: **47 companies / 53 named SKUs** (was 23 / 28). Merged OEM seed: **108 vendors / 241 robots**.

| Vertical | Companies | Named SKUs | Newly added this pass |
|----------|-----------|------------|------------------------|
| Agriculture | 11 | 16 | Naïo **Orio**; FarmDroid FD20; AgXeed AgBot; Agrobot E-Series; Verdant Sharp Shooter |
| Construction | 7 | 7 | Construction Robotics **MULE** (SAM URL 404); Hilti Jaibot |
| Avionics eVTOL | 12 | 12 | Volocopter VoloCity; EHang EH216-S; SkyDrive SD-05; AIR ONE; Doroni H1-X |
| Avionics autonomous aircraft | 1 | 1 | Elroy Chaparral (cargo VTOL — not passenger LAWA, not drone) |
| Avionics drone | 14 | 14 | Flyability Elios 3; DJI Matrice 350 RTK; Parrot ANAFI USA; WingtraOne GEN II; Autel EVO Max Series; AgEagle eBee X; Voliro T |
| Aerospace | 4 | 5 | (unchanged) |
| AMR / warehouse | 5 | 5 | Robotnik RB-ROBOUT; Neobotix MP-400; ForwardX Max Series; Exotec Skypod; SESTO Magnus |
| **Total vertical** | **47** | **53** | Empty specs = UNKNOWN |

Already in, not duplicated: Carbon LaserWeeder, Deere, Monarch, Naïo Oz/Ted/Jo, Ecorobotix ARA, Burro, CLAAS, Dusty FieldPrinter, ICON Vulcan, COBOD BOD2, FBR Hadrian X, ACR TyBOT, Skydio X10, Joby, Archer Midnight, BETA ALIA, Wisk Gen 6, Zipline, Shield AI V-BAT, GreyOrange, Locus, MiR, OTTO, Seegrid, Stretch.

## Skipped (HTTP reason)

| Name | Reason |
|------|--------|
| Built Robotics | homepage 403 (retry) |
| Canvas | SSL handshake failure (retry) |
| Honeybee Robotics | 429 (retry) |
| Advanced Farm Technologies | connection error / timeout (retry) |
| Eve Air Mobility | 403 |
| Lilium | SSL certificate expired |
| Overair | SSL handshake failure |
| Small Robot Company | 403 |
| Quantum-Systems Trinity | 403 |
| PeK Agroline | connection error |
| Urban Aeronautics | 404 |
| HP SitePrint | 404 |
| ABB Flexley Tug P603 | timeout |
| KUKA KMP | 404 |
| Clearpath | timeout |
| Zebra/Fetch AMR | 406 |
| OMRON LD | 404 |
| DroneDeploy | software-only — not a manufacturer |
| AMRA | alliance — does not manufacture a named robot |

## ChatGPT names with no official SKU page (homepage 200, not invented)

Bluewhite Pathfinder (SKU URL 404). MightyFly Cento (404). Monumental Pisa/Petra/Panama (no official product URL — do not invent). Construction Robotics SAM (404; ingested MULE instead). Vertical Aerospace VX4 (404). Percepto Sparrow (404; AIM is software). Wing (no named aircraft SKU). American Robotics Scout (404). Exyn A3 (404). Geekplus / Addverb / BALYO / Mujin / Toggle / Apis Cor / CyBe / August Robotics / Origin Robotics / DaFang / Industrial Automata / AutoFlight / Supernal / LahakX / AeroVironment / Near Earth / Tevel / FFRobotics / Fieldwork / Aigen Element / FarmWise Titan (product URLs 404) / Saga Thorvald / Rover Robotics (UGV platforms, not ag SKUs) / Tortuga (redirect timeout on second pass).

## MATCH

Configuration-based. Joby/Archer still one LAWA eVTOL card, no CNC, no ramp-walk. Skydio drone_task only. Carbon LaserWeeder weeding family, not combine. ICON Vulcan 3D-print home, not block-lay. Elroy Chaparral autonomous_flight only. DJI/Elios drone, not eVTOL. Robotnik AMR warehouse, not weeding. FIND-tile agriculture remains the work-kind **union**.

## Tests

- pytest seed catalog + vertical + eVTOL pad/ramp + ag classes + ontology + OEM catalog — **63 passed**
- extra: tier families + vendor lookup + job search passed; `test_healthcare_eldercare_delivery_matches_transport_robots` still fails on Origin AMR (amr class grounds `transport` — pre-existing, not this ingest)
- `python3 scripts/agent_verify.py ci` — doctor + FIND/chrome/about/CRM **ok**, skip_green false

## Leftover resume

```bash
PYTHONPATH=. python3 scripts/build_vertical_oem_catalog.py
# After a leftover official product URL returns 200, add the named SKU to the builder.
```

Priority leftovers: Built Robotics Exosystem, Canvas drywall, Monumental named bricklayer SKU page, MightyFly Cento, Vertical VX4, Eve, ABB P603, KUKA KMP, Bluewhite Pathfinder, FarmWise Titan, Saga Thorvald.
