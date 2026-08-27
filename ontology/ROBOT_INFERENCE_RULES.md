# Robot Inference Rules

**The most important file for the copilot.** These are the rules — not vibes —
that turn hardware/facts into capabilities and matches. Every rule cites its
confidence output and its status in code.

## The core traversal (never violate)

```
COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → WORKFLOWS → JOB REQUIREMENTS → MATCH
```

**Forbidden:** `company name → robot category → jobs`. `primary_class` is a
descriptor; it never selects a job family.

## Confidence vocabulary (closed set, flows end-to-end)

| Label | Meaning | Code |
|-------|---------|------|
| `EXPLICIT` | Directly stated by the manufacturer | `epistemic="explicit"` |
| `DERIVED` | Logically inferred from grounded hardware/facts | `epistemic="strongly_inferred"` |
| `LIKELY` | Strongly suggested but incomplete (named derivation only) | matcher requirement state `LIKELY` |
| `UNKNOWN` | Not enough evidence | `epistemic="unknown"` |
| `CONFLICTED` | Contradictory evidence | `epistemic="contradicted"` |

`EXPLICIT` + `DERIVED` are **GROUNDED** (matcher-visible). `UNKNOWN`/`CONFLICTED`
never assert a capability. `LIKELY` is only reachable through a **named
derivation** (see below) and can only produce a `LIKELY` match — never `MATCHED`.

## Capability inference rules

### Manipulation
- **R1 ✅** If `arm_count >= 1` **and** an `end_effector` is grounded → infer
  `manipulate` = supported (`DERIVED`; `EXPLICIT` when the arm/effector fact is
  explicit).
- **R2 ✅** If `arm_count = 2` **and** hand/effector evidence → infer
  `dual_arm` manipulation.
- **R3 ✅** `has_dexterous_hands` (or `hand_dof`) alone → `manipulate` +
  dexterous manipulation.
- **R4 ✅** `product_class` ∈ {`humanoid`, `mobile_manipulator`, `cobot`,
  `manipulator`, `arm`} is manipulation-morphology evidence — but only grounds
  `manipulate` when no stronger hardware fact already did, and never overrides a
  sibling-SKU/off-subject gate.
- **R5 ✅** **Food prep** (`claims_food_prep`) → `food_prep`; **beverage prep**
  (`claims_beverage_prep`) → `beverage_prep`. These are **distinct** from generic
  `manipulate` so a fry/barista robot maps to food/beverage work and does **not**
  match industrial CNC/case jobs.

### Mobility & transport
- **R6 ✅** `has_mobile_base` \| `autonomous_navigation` \| `mobility_architecture`
  \| mobile class → `mobile`.
- **R7 ✅** **Do not infer `transport` simply from mobility.** `transport`
  (point-to-point item delivery, incl. serving/luggage) requires
  `claims_item_delivery`; `tote_transport` requires warehouse tote/cart evidence.
- **R8 ✅** Human-in-the-loop picking (person-to-goods / "workers pick") →
  `transport`/`tote_transport` only, **never** `manipulate`.

### Structural (forward-chained) — `robot_inference_engine.py`
- **R9 ✅** `product_class=humanoid` → `mobility_architecture=bipedal` +
  `has_mobile_base`; if hand/effector present → `arm_count=2`.
- **R10 ✅** `product_class=mobile_manipulator` → `has_mobile_base` +
  manipulation (`end_effector`). By definition mobile **and** manipulates.
- **R11 ✅** `autonomous_navigation` or `mobility_architecture` → `has_mobile_base`.
- **R12 ✅** `product_class=autonomous_scrubber` → `hard_floor_scrub`.
- **R22 ✅** `product_class` ∈ {`agriculture`, `agricultural_robot`} **or**
  `claims_agriculture` **or** LaserWeeder / carbonrobotics.com weeding evidence →
  `agriculture_task` + `mobile`. Empty specs stay `UNKNOWN`.
- **R23 ✅** `product_class` ∈ {`marine`, `marine_robot`} **or** `claims_marine` →
  `marine_task` + `mobile` (hull / port / underwater — not a category dump).
- **R24 ✅** `product_class` ∈ {`avionics`, `aviation_robot`, `drone`, `evtol`}
  **or** `claims_avionics` → `avionics_task` + `mobile` (drones, eVTOL,
  autonomous aircraft — not satellites). Hangar/airside inspection of an
  airframe is avionics *work*, not the class definition.
- **R28 ✅** Avionics **configuration** splits work. `product_class=evtol` →
  `evtol_flight` (air-taxi / flying-car routes). `drone`/`uav` → `drone_task`
  (aerial inspect or delivery). `autonomous_aircraft` → `autonomous_flight`.
  Hangar/airside *walking* jobs require `inspect_route` (quadruped) **or**
  `drone_task` — never `evtol_flight`. An eVTOL is the aircraft on the ramp,
  not the inspect robot walking around it. Generic `avionics` FIND-tile class
  (or `claims_avionics` with no subclass) is the flying-work union, not a
  dump of ramp-walk jobs onto every SKU.
- **R25 ✅** `product_class` ∈ {`construction`, `construction_robot`} **or**
  `claims_construction` → `construction_task` + `mobile` (homes, buildings,
  plus jobsite earthwork / layout / finishing).
- **R26 ✅** `product_class` ∈ {`aerospace`, `aerospace_robot`} **or**
  `claims_aerospace` → `aerospace_task` + `mobile` (satellites, rockets,
  orbital debris / space-exploration robots — not drones).
- **R27 ✅** `configuration_kind=implement_on_host` **and**
  `host_platform` ∈ {`tractor`, `combine`} → `agriculture_task` (`DERIVED`).
  An attachment is hardware on a tractor or combine, **not** a FIND class
  and not a company category. Empty specs stay `UNKNOWN`.
- **R13 (humanoid nuance) ✅/🟡** `2 arms + 2 hands + vision + mobile body`
  ⇒ **likely mobile-manipulation platform** — grounds `manipulate` + `mobile`,
  but `payload`, `reach`, and `autonomy` still each require their own evidence
  (do not fabricate them).

### AMR configuration nuance
- **R14 ✅** "AMR" does **not** mean "cannot manipulate." An AMR grounds
  `manipulate`/`tote_transport` **only** from its own configuration evidence:
  ```
  AMR
  ├─ mobility only                → mobile
  ├─ transport interface          → tote_transport
  ├─ lift module                  → (planned) lift
  ├─ conveyor module              → (planned) transport interface
  ├─ arm module                   → manipulate (if grounded on this config)
  └─ mobile manipulator config    → mobile + manipulate
  ```
- **R15 ✅** Likewise "humanoid" does **not** automatically grant `palletize`;
  palletizing requires manipulation + payload/throughput evidence (mostly
  `UNKNOWN` until established).

## Subject-scoping rules (anti-leak)
- **R16 ✅** Facts from **sibling products** may not flow into the selected
  product (`_evidence_names_sibling_sku`).
- **R17 ✅** Do **not** infer a capability from **company-level copy** when the
  selected product has no supporting hardware/evidence
  (`page_supports_subject` + subject-near gates).
- **R18 🟡** **Optional modules must be represented as configurations**, not
  universal product capabilities. Schema supports it (`RobotConfiguration`); live
  per-configuration resolution on multi-product homepages is in progress.

## Truth guards (reject false positives) ✅
- Word-boundary matching: "handles" ≠ "hand"; "2X productivity" ≠ `arm_count=2`.
- Claim-appropriate evidence: an `arm_count` needs an actual "arm"; a payload
  number must be whole-robot scope (reject per-tray/per-shelf/accessory).
- Off-subject pages contribute nothing.

## Match rules
- **R19 ✅** A job requirement is `MATCHED` only if the **specific** required
  capability is grounded (`EXPLICIT`/`DERIVED`). Generic `mobile` is a gate.
- **R20 ✅** `LIKELY` requires a named derivation (`LIKELY_DERIVATIONS`), e.g.
  `amr_indoor_nav`, `scrubber_indoor_nav`, `mobile_manip_tote_carry`,
  `inspect_from_quadruped`, `reach_documented`.
- **R21 ✅** Any required `UNMET` → `NOT_A_MATCH`. Unknowns are preserved, never
  guessed. No match percentage.
- **R29 ✅** If a configuration grounds a domain work primitive (`evtol_flight`,
  `drone_task`, `autonomous_flight`, `agriculture_task`, `construction_task`,
  `marine_task`, `mining_task`, `aerospace_task`), a job is eligible **only**
  when it exercises at least one of those primitives. Do not pad leftover
  slots from the cobot/CNC/pack/warehouse corpus. A short honest list (one
  LAWA eVTOL card) is correct. Never invent employers.

## Worked examples

| Robot | Grounded facts | Capabilities | Matches |
|-------|----------------|--------------|---------|
| 1X NEO (humanoid) | humanoid, hands 22×2, arms 7×2, nav, payload | manipulate, dual_arm, mobile | pallet/gripper (manip) |
| Locus Origin (P2G AMR) | amr, nav, totes, workers pick | mobile, tote_transport | transport/cart (no manip) |
| Brightpick (robotic-pick AMR) | mobile manipulators pick | mobile, manipulate, tote_transport | manip + transport |
| Relay (delivery) | service_robot, nav, delivers items | mobile, transport | transport/cart/serve |
| Miso Flippy (fry) | fry station / cooking | food_prep | food_prep only |
| Somatic (restroom) | bathroom cleaning, self-navigates | mobile, surface_clean | restroom only |
| Avidbots Neo (scrubber) | autonomous scrubber | hard_floor_scrub, mobile | scrub only |
| Carbon Robotics LaserWeeder | agricultural weeding robot, laser weeding | agriculture_task, mobile | weeding / crop / field only |
| John Deere X Series Combine | autonomous combine harvest | agriculture_task, mobile | combine / harvest only |
| Skydio X10 | drone / UAV | avionics_task, drone_task, mobile | drone inspect / delivery / hangar inspect |
| Archer Midnight | eVTOL flying car | avionics_task, evtol_flight, mobile | eVTOL vertiport routes only — not ramp walking |
| Astroscale ELSA-d | on-orbit servicing / debris | aerospace_task, mobile | satellite servicing / debris only |

## Regression coverage
`tests/test_robot_inference_engine.py`, `tests/test_facts_item_delivery.py`,
`tests/test_m2_requirement_match.py` (incl.
`test_frozen_robots_do_not_leak_into_hospitality_families`).
