# Robot Hardware Ontology

**Purpose:** enumerate the physical components a configuration may have.
**Hardware evidence determines which capabilities can be inferred** — nothing
downstream may claim a capability the hardware doesn't support.

Each hardware fact carries a confidence state (`EXPLICIT` / `DERIVED` / `LIKELY`
/ `UNKNOWN` / `CONFLICTED`) and an evidence span + source. Facts are
subject-scoped (see [entity ontology](ROBOT_ENTITY_ONTOLOGY.md)).

## Hardware categories

### Mobility base
| Component | Predicate (fact) | Status |
|-----------|------------------|--------|
| Wheeled / omnidirectional / mecanum base | `has_mobile_base=true` | ✅ |
| Legs (bipedal) | `mobility_architecture=bipedal` | ✅ |
| Legs (quadruped) | `product_class=quadruped` | ✅ |
| Mobility architecture (omnidirectional/…) | `mobility_architecture` | ✅ |

### Arms & end effectors (the manipulation stack)
| Component | Predicate | Status |
|-----------|-----------|--------|
| Arm(s) present / count | `arm_count` (int) | ✅ |
| Dual arm | `arm_count>=2` | ✅ |
| Dexterous hands | `has_dexterous_hands=true`, `hand_dof` (int) | ✅ |
| End effector — gripper | `end_effector=gripper` | ✅ |
| End effector — vacuum / suction | `end_effector` ∈ {`vacuum`,`suction`} | 🟡 (recognized in derive `GRASP_EFFECTORS`) |
| End effector — dexterous hand | `end_effector=dexterous_hand` | ✅ |
| End effector — clamp / tool / tool-changer | `end_effector` ∈ {`clamp`,`tool`} | ⬜ planned vocab |

### Perception
| Component | Predicate | Status |
|-----------|-----------|--------|
| Autonomous navigation (LiDAR / SLAM / cameras / self-navigation) | `autonomous_navigation=true` | ✅ |
| Cameras / depth / force sensors (typed) | — | ⬜ planned (today folded into `autonomous_navigation`) |

### Payload & envelope
| Component | Predicate | Status |
|-----------|-----------|--------|
| Carrying capacity (weight) | `carrying_capacity` (value+units, scope-aware) | ✅ |
| Reach / work envelope | `reach_or_workspace` (value+units) | ✅ |
| Degrees of freedom | `degrees_of_freedom` (int) | ✅ |
| Max speed | `max_speed` | ✅ |
| Battery / runtime | `battery_runtime` | ✅ |
| Ingress protection | `ingress_protection` (IPxx) | ✅ |

### Load / transport interfaces
| Component | Predicate | Status |
|-----------|-----------|--------|
| Tote / cart interface | `supports_tote_handling=true` | ✅ |
| Lift / conveyor / pallet-jack module | — | ⬜ planned typed modules |
| Tool changer / payload interface | — | ⬜ planned |

## Scope discipline for numeric hardware facts ✅

- Payload scope is inferred: `per_tray` / `per_shelf` / `per_deck` / `per_arm` /
  `accessory` values are **rejected** as whole-robot payload
  (`facts.py::_infer_payload_scope`, `_numeric_value_plausible`).
- Marketing metrics are not hardware: "2X productivity" is never `arm_count=2`
  (`robot_inference_engine.py::_detect_arm_count`).
- Word-boundary matching: "handles" is not a "hand".

## The load-bearing rule

> A capability may be `EXPLICIT`/`DERIVED` **only** if the supporting hardware is
> grounded on the selected configuration. No hardware evidence ⇒ the capability
> is at most `LIKELY` (via a named derivation) or `UNKNOWN`.

See [`ROBOT_INFERENCE_RULES.md`](ROBOT_INFERENCE_RULES.md) for the exact mappings.
