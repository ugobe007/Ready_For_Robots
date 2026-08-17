# Understanding v1.0 calibration freeze

**Date:** 2026-08-17  
**Decision:** Phase 1–3 frozen as **v1.0 calibration**. Blind 20 gate **FAIL** left open. Understanding extractors **CLOSED**. **M2 matcher prototyping allowed** against frozen profiles (see milestones).

## Checksums

| Item | Value |
|------|--------|
| Git tip (at Blind 20 freeze window) | `dffbc1a133d7c32a3554b280d7bec447cab3f66f` |
| Understanding tree (`*.py` under `app/services/robot_understanding_v1/`) | `TREE d528e9249bb7f58bd05ce08b9bbcf46e2af66ee066c7f5bb32c9dd5b967eac46` (8 files) |
| Gate run | `runs/run_20260817T040820Z` |

## Summary

- Critical recall **78%** (below ≥80%) — **do not chase 80%** on Blind 20.
- Identity / disentanglement / grounding / numeric scope held — system is **credible but incomplete**.
- Remaining critical gaps are multi-mechanism (OTTO, Geek+, Sanctuary, ABB, library pages).
- No extractor / source / resolve / Blind 20 bar retune.
- Next: **production shadow** as a **finite M1 Understanding decision instrument** (first **20 real reviewed** profiles) — see [`../understanding_shadow_v1.md`](../understanding_shadow_v1.md) and product spine [`../../readyforrobots_v1_milestones.md`](../../readyforrobots_v1_milestones.md). Not open-ended Understanding research.
- **M2 matcher prototyping is allowed** against frozen A/B/C profiles (propagate unknowns). The 20-shadow gate does **not** block M2 — circular dependency: credible match needs M2; organic shadows need traffic; traffic needs credible match.
- Optional fresh Blind 20 only after a **narrow** reopen justified by **repeated production failures**, not cohort polishing.

## Reopen rule

Any change under `app/services/robot_understanding_v1/` after this freeze must cite which **repeated production shadow failure** (from the first ~20 reviewed labels + themes) justified a **narrow** reopen. Individual cases before 20 reviewed are observations only.

If shadow shows scattered failures and most profiles are professionally useful: **accept B/C unknowns** — do not keep polishing Understanding. **M2 may proceed regardless** of whether the 20-review checkpoint has fired. Blind 20 retune stays closed unless the narrow reopen bar is met and documented.

Full decision: [`outcome.md`](./outcome.md) § v1.0 freeze. Prior Blind 20 window rules: [`FREEZE.md`](./FREEZE.md).
