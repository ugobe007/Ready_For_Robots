# Mission: Clean HOT/WARM buyer names (north-star #1)

**Date:** 2026-07-07
**Type:** build
**Agents:** LeadQuality
**North star:** names & events → scores → rank → specs. Fix names before ranking.

## Why

The contact-enrichment ramp surfaced junk in the surfaced HOT/WARM pool that
`classify_lead` lets through. Root causes (probed via `scripts/name_gate_probe.py`):

1. **Allowlist overrides the vendor gate.** `is_junk` checks
   `is_allowlisted_company_name` *before* the robot-vendor check, and the allowlist
   contains `"locus robotics"` + a prefix-allow — so the vendor **and its headline
   fragments** ("Locus Robotics Surpasses 5 Billion Pick Milestone") pass as buyers.
2. **Missing vendors.** Daifuku (AS/RS OEM), Keenon headline forms, and other
   material-handling OEMs are not in `KNOWN_ROBOTICS_VENDOR_NAMES`.
3. **Generic descriptors pass every gate.** "PA logistics company", "Miami logistics
   company", "2021 Women", "Dynamic Warehouse AI-Powered AMRs".

## Goal

Robot vendors and obvious scrape-descriptor/headline names never reach HOT/WARM,
**without** false-positiving real buyers (Radisson Hotel Group, Melia Hotel Group,
RJW Logistics Group, Rebel Hotel Company, PM Hotel Group).

## Acceptance criteria

1. Vendor gate takes precedence over the allowlist in `is_junk` (buyer mode); a known
   vendor is junk even if allowlisted. `"locus robotics"`/`"bito lagertechnik"`
   removed from the buyer allowlist.
2. Missing OEMs added to `KNOWN_ROBOTICS_VENDOR_NAMES` (Daifuku, Dematic, Vanderlande,
   Knapp, SSI Schäfer, Murata Machinery, TGW, Intelligrated, Addverb, Hikrobot,
   Keenon, Richtech, Exotec …).
3. Conservative name rules reject: 4-digit-year prefixes ("2021 Women"), lowercase
   generic descriptors ("<Geo> logistics company"), and "AI-Powered" product headlines.
4. Tests: vendors/fragments/descriptors blocked; the 5 real-buyer names above still pass.
5. Re-run `scripts/cal_pool_contamination.py` + `name_gate_probe.py`; deploy; confirm
   the flagged leads drop to COLD without collateral.

## Verify

Targeted pytest (`tests/test_lead_filter_junk.py`), probe + pool audit before/after,
deploy to `ready-2-robot`.

## Outcome

_Filled on completion._
