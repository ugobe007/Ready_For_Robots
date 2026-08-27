# Seed verified OEM catalog (ChatGPT 100-company list)

**Date:** 2026-08-27
**Type:** build
**Agents:** ProductSurface + ontology (LeadQuality)
**Status:** in progress
**Branch:** `cursor/seed-verified-oem-catalog-009b`

## Goal

Ingest **named SKUs** from the operator's agriculture / construction / eVTOL / drone / AMR list into the canonical ontology. Verify official URLs with HTTP 200. Deduplicate against existing OEM and vertical catalogs. MATCH via capabilities and task models — never `company → category → jobs`.

Canonical path:

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → WORKFLOWS → JOB REQUIREMENTS → MATCH
```

ChatGPT's `robotType` / `applicationDomain` / `mobilityType` tree is seed metadata at most. Do not add a parallel taxonomy that makes LaserWeeder interchangeable with a combine, or Joby a drone.

## Definitions (do not collapse)

| Class | Means | Does not mean |
|-------|--------|----------------|
| **eVTOL** | Passenger/cargo air-taxi flying cars (Joby Midnight, Archer) | Ramp-walk, CNC, drone delivery |
| **drone / UAV** | Inspect / delivery / hangar / airside flight (Skydio) | Passenger eVTOL |
| **autonomous aircraft** | Airplane-like / cargo VTOL autonomy as a **configuration fact** | Dump onto drone_task or evtol_flight |
| **aerospace** | Satellites / rockets / orbital debris (11th FIND tile) | This list |
| **implement** | Tractor/combine attachment (`configuration_kind=implement_on_host`) | A FIND tile |

## Acceptance

1. Deduplicate: Carbon, Joby, Archer, Skydio, ICON, Deere, Naïo Oz/Ted/Jo, Wisk, BETA, Zipline, Dusty, COBOD, FBR, ACR, GreyOrange, Locus, MiR, OTTO, Seegrid, Stretch already in — do not duplicate rows.
2. Official URLs HTTP 200 only. Retry Built Robotics (403), Canvas (SSL), Honeybee (429), Advanced.farm (timeout). Still skip non-200. Skip software-only (DroneDeploy). Skip AMRA-as-alliance.
3. Named SKUs as PRODUCT + CONFIGURATION. `primary_class` matches hardware. Empty specs UNKNOWN. No invented employers, rental dollars, or fake SKU names. Company homepage 200 with no named SKU page → company + UNKNOWN product, do not invent Oz/Ted/Orio without an official product URL.
4. MATCH is configuration-based: eVTOL → `evtol_flight` only (one LAWA card). Drones → `drone_task`. Autonomous aircraft / cargo VTOL → `autonomous_flight` when the class is that configuration. Ag SKUs with distinctive work (LaserWeeder weeding) must not dump onto combine harvest. Construction: Vulcan → 3D-print home; block-lay → block; not CNC/warehouse. AMR → warehouse/material-handling only.
5. FIND host lookup hits new verified hosts.
6. Tests: new OEMs classify correctly; Joby/Archer still one LAWA card no CNC; Skydio no eVTOL route; Carbon still ag weeding family; no company→category regression.
7. Mission `outcome.md` lists verified company/SKU counts, skipped with HTTP reason, leftovers.

## Out of scope

Hermes. SIGNAL hop. Invented 500 products. ChatGPT match graph. Aerospace satellites (already catalogued).
