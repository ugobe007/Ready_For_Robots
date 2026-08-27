# Outcome — agriculture / marine / avionics / construction classes

**Date:** 2026-08-27
**Branch:** `cursor/ag-robot-classes-009b`
**Status:** done

## What shipped

FIND class picker now has **10 tiles**: the original six form-factor classes plus **Agriculture, Marine, Avionics, Construction**. Ontology infers Carbon Robotics **LaserWeeder** as an agricultural weeding robot (`agricultural_robot` + `claims_agriculture` → `agriculture_task`). FIND matches weeding / crop / field jobs and skips the picker when that evidence is present.

## LaserWeeder classification

| Input | Result |
|-------|--------|
| Host `carbonrobotics.com` / SKU LaserWeeder | `product_class=agricultural_robot`, `claims_agriculture` |
| Operator tile **Agriculture** | `product_class=agriculture` (aliases include `agricultural_robot`) |
| Derived capabilities | `agriculture_task` + `mobile`. Payload/reach stay UNKNOWN |
| Job match | `tape_family=agriculture` only (weeding, harvest, spray, orchard). Not pallet/gripper/humanoid warehouse |

Avionics means hangar / airside aircraft work — not a consumer-drone class. Marine is hull / port / underwater. Construction is jobsite earthwork / layout / finishing. None of these are SIGNAL industry tags.

## Job-match change

`product_class` in {agriculture, marine, avionics, construction} (or the `*_robot` aliases) is a **named derivation** onto the matching task capability. Jobs still require that capability. This is COMPANY → PRODUCT → HARDWARE/claims → CAPABILITIES → TASK MODELS → WORKFLOWS → MATCH — not company → category → jobs.

Production smoke **before** this branch (`POST /api/robot-job-match` `https://carbonrobotics.com/`): `state=matches`, `robot_class=unknown`, capabilities=`[mobile]`, jobs were warehouse tote/cart transport. Local compose after the change: agriculture jobs only, `needs_class_choice=false`.

## Tests

- `pytest` `test_ag_robot_classes.py` + class qualify + ontology + tier families + task models — **pass**
- `vitest` `robotClassOptions` + `jobsWorkflow` + `knownOemLineups` — **43 passed**
- KEEP 0 / `Yes, keep them` assertions unchanged

## Follow-ups

- Deploy Fly so production carbonrobotics.com stops dumping warehouse transport.
- Parent opens the PR if ManagePullRequest is unavailable.
