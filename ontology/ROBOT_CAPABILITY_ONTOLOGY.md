# Robot Capability Ontology

**Purpose:** the vocabulary of *actions* a robot can perform. A capability is
derived from grounded hardware/facts on the **selected configuration** and
carries a confidence state. Capabilities are consumed by the matcher; they are
**not** job families and **not** morphology labels.

Code: `app/services/robot_capability_derive.py` (`derive_capabilities`).

## Capability vocabulary

Full target vocabulary (from the WORK primitives in
[`primitives.v1.json`](primitives.v1.json) + the derived-capability layer):

`navigate · carry · lift · grasp · pick · place · push · pull · open · close ·
inspect · scrub · scan · load · unload · stack · sort · handoff · manipulate ·
tool_use`

### Derived capabilities implemented today ✅

| Capability key | Meaning | Derived from (grounded facts) |
|----------------|---------|-------------------------------|
| `mobile` | Autonomous mobility | `has_mobile_base` \| `autonomous_navigation` \| `mobility_architecture` \| mobile class |
| `manipulate` | General manipulation | `arm_count>=1` \| `has_dexterous_hands` \| `end_effector`∈grasp \| manip class |
| `dual_arm` | Two-arm manipulation | `arm_count>=2` |
| `transport` | Autonomous item delivery/transport (point-to-point) | `claims_item_delivery` |
| `tote_transport` | Warehouse tote/cart handling | `supports_tote_handling` \| `claims_warehouse_transport` |
| `load_unload` | Load/unload claim | `claims_load_unload` |
| `reach` | Documented working reach | `reach_or_workspace` |
| `payload` | Documented carry weight | `carrying_capacity` |
| `hard_floor_scrub` | Hard-floor scrubbing | `supports_hard_floor_scrubbing` \| scrubber class |
| `surface_clean` | Restroom/fixture/carpet cleaning | `claims_surface_cleaning` |
| `food_prep` | Food preparation / cooking | `claims_food_prep` |
| `beverage_prep` | Drink / beverage preparation | `claims_beverage_prep` |
| `inspect_route` | Mobile inspection route | quadruped class (named derivation) |

> Some target verbs (`push`, `pull`, `open`, `close`, `stack`, `sort`,
> `rotate`, `insert`, `handoff`, `tool_use`, `scan`) are ⬜ planned as first-class
> derived capabilities; today they are covered indirectly via `manipulate` +
> job-requirement unknowns.

## The MANIPULATION hierarchy

Manipulation is **not** a binary robot-level property and **not** decided by
category. It is grounded from hardware/action evidence on the configuration:

```
MANIPULATION
├─ arm_present         (arm_count >= 1)                         ✅
├─ dual_arm            (arm_count = 2)                          ✅
├─ end_effector
│  ├─ gripper                                                   ✅
│  ├─ hand (dexterous) (has_dexterous_hands / hand_dof)         ✅
│  ├─ suction / vacuum                                          🟡
│  ├─ clamp                                                     ⬜
│  └─ tool                                                      ⬜
├─ grasp                                                        🟡 (via manipulate)
├─ pick                                                         🟡
├─ place                                                        🟡
├─ carry               (payload + mobile)                       🟡
├─ push                                                         ⬜
├─ pull                                                         ⬜
├─ rotate                                                       ⬜
├─ insert                                                       ⬜
├─ handoff             (int.human_handoff primitive)            ⬜
├─ load                (claims_load_unload)                     ✅
├─ unload              (claims_load_unload)                     ✅
└─ tool_use                                                     ⬜
```

**Rule:** hardware evidence determines which of these are inferred. No arm / hand
/ effector evidence on the selected configuration ⇒ manipulation is `UNKNOWN`,
never asserted from company copy or morphology.

### Domain nuance (encoded)
- **Humanoids** inherently manipulate — `2 arms + 2 hands + vision + mobile body`
  ⇒ **likely mobile-manipulation platform** — but payload / reach / autonomy
  still require their own evidence.
- **AMRs manipulate when equipped** — telescoping grab-off-shelf, mounted arm,
  mobile-manipulator configuration. "AMR" ≠ "cannot manipulate".
- **Food prep and beverage prep are dexterous manipulation**, but are kept as
  **distinct** capabilities (`food_prep`, `beverage_prep`) so a fry/barista robot
  maps to food/beverage work and does **not** falsely match industrial CNC/case
  handling.
- **Human-in-the-loop picking is not robot manipulation** — person-to-goods /
  "workers pick" grounds transport, not manipulation.

## Transport vs mobility (encoded) ✅

- `mobile` ≠ `transport`. **Do not infer transport merely from mobility.**
- `transport` (point-to-point item delivery, incl. hospitality serving /
  luggage) requires `claims_item_delivery`; `tote_transport` requires
  warehouse tote/cart evidence.

See [`ROBOT_WORKFLOW_ONTOLOGY.md`](ROBOT_WORKFLOW_ONTOLOGY.md) for how
capabilities satisfy job requirements, and
[`ROBOT_INFERENCE_RULES.md`](ROBOT_INFERENCE_RULES.md) for the exact rule set.
