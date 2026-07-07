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

## Outcome (2026-07-07)

### Root cause (via `scripts/name_gate_probe.py`)
`is_junk("Locus Robotics")` → `allow=True, vendor=True, is_junk=False`: the brand
allowlist short-circuited `is_junk` before the vendor gate, and `"locus robotics"`
+ a prefix-allow were on the allowlist — so the vendor and its headline fragments
passed as buyers. Daifuku/Keenon weren't blocklisted; generic descriptors passed
every gate.

### Shipped
1. **Allowlist no longer overrides the vendor gate** — `is_junk` skips the
   allowlist short-circuit for known vendors (buyer mode). Removed
   `"locus robotics"`/`"bito lagertechnik"` from the buyer allowlist + prefix-allow.
2. **Added missing OEMs** to `KNOWN_ROBOTICS_VENDOR_NAMES`: Daifuku, Dematic,
   Vanderlande, Knapp, SSI Schäfer, Murata, TGW, Intelligrated, Addverb, Hikrobot,
   Exotec, Keenon, Richtech, Orionstar, Pudu, Grenzebach, Bastian, Kardex, Interroll.
3. **Conservative name rules** (`_generic_descriptor_or_list_fragment`): year-prefix
   fragments ("2021 Women"), lowercase generic descriptors ("Miami logistics
   company"), and "AI-Powered" headlines. Case-sensitive so Title-Case real buyers
   pass.

### Verified
- Probe: all target junk → `is_junk=True`; Radisson Hotel Group stays clean.
- **Pool audit: top-400 HOT/WARM went from ~5 junk leaks (Locus ×3, Dynamic
  Warehouse AI-Powered AMRs, media-domain) to 100% clean (400/400).**
- `tests/test_lead_filter_junk.py`: 209 pass, incl. new vendor/descriptor blocks +
  5 real-buyer survivors + oem_prospect-mode vendor pass-through. Pre-existing
  unrelated failures only (wikidata network probe, humanoid-catalog astribot data).

### Follow-ups
- Cal cycle window (`_hot_warm_companies(limit=max(draft_limit,100))`) is still
  burned by bounce-era sends — now safe to widen since the pool is clean.
- Add `ZERO_BOUNCE_API_KEY` to catch stale Hunter mailboxes pre-send.
- Consider applying the same vendor-precedence hardening to the supply pipeline.

### Diagnostics added
`scripts/name_gate_probe.py`, `scripts/cal_pool_contamination.py` (reuses `is_junk`
as a regression guard).
