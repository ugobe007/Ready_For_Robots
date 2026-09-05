# Vertical robot catalog — avionics vs aerospace + ag/construction depth

**Date:** 2026-08-27
**Type:** build
**Agents:** ProductSurface + LeadQuality (ontology)
**Status:** done

## Goal

Define **avionics** vs **aerospace**, deepen agriculture (combines, tractors, tractor implements as configurations) and construction (homes and buildings), catalogue verified named SKUs, and teach FIND + the ontology to classify them. Never `company → category → jobs`.

## Definitions

| Class | Means | Does not mean |
|-------|--------|----------------|
| **Avionics** | Drones, eVTOL (“flying cars”), autonomous airplane-like robots | Hangar/airside-only; not satellites |
| **Aerospace** | Satellites, rockets, robots for space exploration/development; robots attached to a satellite that clear **orbital debris** | Drones / eVTOL |
| **Agriculture** | Autonomous combines, autonomous tractors (planting/harvest), weeding; **attachments to tractors** are a *configuration* (hardware on a tractor), not a fake company class | SIGNAL industry tag |
| **Construction** | Homes and buildings — residential framing / finishing and commercial building work — plus existing jobsite earthwork/layout | SIGNAL industry tag |

## Acceptance

1. Taxonomy docs + JSON split avionics vs aerospace. Tractor-implement is a configuration.
2. FIND picker: 11 tiles; avionics hint is drones/eVTOL/autonomous aircraft; aerospace is the 11th tile. Agriculture/construction tiles stay and deepen.
3. Verified official-site named SKUs in `ontology/oem_sku_catalog` + vendor seed. Unverified URLs skipped (Stretch-on-Spot rule). Empty specs = UNKNOWN.
4. Task models + job-match corpus work families: weeding (keep), combine harvest, tractor plant/harvest, implement-on-tractor, residential construction, building construction, drone inspection/delivery, eVTOL, autonomous flight, satellite servicing, orbital debris, launch ground support as appropriate. Named employers we can defend; no invented space-Walmart; no invented rental $.
5. Tests: LaserWeeder still agriculture; Carbon Robotics no regress. At least one combine/tractor OEM, one construction homebuilder robot OEM, one drone/eVTOL, one debris/sat-servicing or aerospace OEM classify correctly. Vitest picker has aerospace + 4 domain tiles.
6. If full catalogs are too large: ship taxonomy + verified named SKUs we can defend, plus a resume command. Do not fake completeness.

## Out of scope

Hermes. Cal sales. SIGNAL hop. Matcher deletion. Invented employer emails. Invented economics.
