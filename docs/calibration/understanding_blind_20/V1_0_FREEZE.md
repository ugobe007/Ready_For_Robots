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

---

## Narrow reopen — 2026-08-18 (Robot Inference Engine)

**Authorized by:** Bob (operator).

**Reopen reason (generalized production failure):**

> Manufacturer capability narrative + structured product data present → material robot capabilities absent.

**Triggering case:** `https://www.1x.tech/` (1X NEO). The page publishes explicit,
abundant capability evidence (humanoid, bipedal, autonomous navigation, dexterous
22–25 DoF hands, 7-DoF arms, 55 lb carry) yet v1's regex/table extractors produced
`product_class/mobility/autonomy = UNKNOWN` and `capabilities = []` → 0 jobs. This is
not an unknowable robot; it is an **architectural extraction failure** (narrow regex
cannot convert capability narrative into a robot model), so it meets the narrow-reopen
bar — not a single-cohort polish and not a per-vendor rule.

**Change (this reopen):** add a **deterministic Robot Inference Engine** —
`app/services/robot_inference_engine.py` — over the SAME fetched evidence pack. Source
of truth is **evidence → inference → capability**, NOT `prompt → profile`. It is a
forward-chaining engine (the in-repo Pythh pattern, cf. `inference_engine.py`):

- **Phase 1** detects explicit facts from evidence signals (word-boundary matching so
  "handles" ≠ "hand", "2X" ≠ arm_count).
- **Phase 2/3** forward-chain structural + capability inference; each conclusion cites
  its **basis**, **confidence**, and **source**.
- **Phase 4** derives candidate workflows from grounded capabilities (display only).

Facts are emitted in the **existing** RobotFact predicate schema (`explicit` for
detected, `strongly_inferred` for rule-chained — both GROUNDED), so `derive_capabilities`
and the M2 matcher are unchanged. **No LLM is required** (an LLM may later be one
optional reasoning mechanism *inside* the engine, but the architecture and source of
truth are inference, not generation).

**Scope guardrails (still frozen):** no per-vendor branches (`if 1x` / `if humanoid`),
no Blind 20 retune, no corpus expansion, no matcher change. Gated by
`ROBOT_INFERENCE_ENGINE=1`; fails conservatively to the deterministic v1 profile.

**Subject scoping (capabilities belong to the product/configuration, not the company
or morphology):** Phase-1 detection is bound to the SELECTED product — off-subject
pages contribute no capability facts, and any signal whose sentence-level evidence
window names a different SKU/module is dropped (`page_supports_subject` +
sibling-SKU gate). This is the correct model for the real world where a company sells
multiple robots and AMR / mobile-manipulator / cobot / accessory-module boundaries
overlap: e.g. an AMR page that also mentions a separate pick/pack arm will not
attribute that arm to the AMR. `derive_capabilities` consumes only facts bound to the
selected robot.

**Manipulation is a capability, not a category (domain correction, Bob):**
Manipulation is grounded from *evidence*, never excluded by a category label.
Humanoids inherently manipulate (hands/end-effectors → `product_class=humanoid`);
AMRs manipulate when equipped (telescoping grab-off-shelf, mounted arms, mobile
manipulators — grounded from the robot's own grab/pick/retrieve actions); **food
prep is dexterous manipulation** (chop/slice/dice, prepare/assemble meals). What is
NOT manipulation: human-in-the-loop picking (person-to-goods / "workers pick" — the
worker manipulates, the robot transports), distribution verticals ("foodservice
warehouse" moves totes of food, it does not prepare it), and marketing metrics
("2X productivity"). These distinctions are evidence/sentence-level, not label-level.

**Validated (deterministic, repeatable):** NEO / Atlas (humanoids) → `manipulate`;
an AMR that grabs items off shelves → `manipulate`; a food-prep robot → `manipulate`;
Locus Origin (person-to-goods page) → transport/tote only (no false manipulation);
Avidbots Neo (scrubber) → scrub only. See `tests/test_robot_inference_engine.py`.

**Blind competitor set (2026-08-18, Bob-supplied):** this is a big, overlapping
space — the engine was re-validated against two more real manufacturer sites:

- **Brightpick** (`brightpick.ai`) — same job class as Locus, but the *robot* picks:
  "mobile robotic picking", "mobile manipulators pick directly inside the storage
  area". Grounds `manipulate` + `mobile` + `tote_transport`. The robot-attributed
  picking signal (`robotic picking` / `manipulators pick`) is what separates it from
  a person-to-goods AMR — the distinction is the *actor*, not the category.
- **Nimo** (`nimotechs.com`) — mobile-base humanoid-like food-prep robot whose entire
  pitch is "highly dexterous bimanual manipulation" / "two-handed tasks". There is no
  noun "hands", so v1 grounded nothing. `bimanual` / `dexterous manipulation` /
  `two-handed manipulation` now ground `manipulate` + `dexterous_manipulation` +
  `dual_arm` (word-bounded so "handles" ≠ "hands"/"handed").

Detector additions (still category-agnostic, evidence-first, no per-vendor branch):
plural "mobile manipulators"; `mobile_manipulator` class → mobile + manipulation;
robot-attributed picking (`robotic picking`, `manipulators pick`); and bimanual /
two-handed / dexterous-manipulation dexterity language.
