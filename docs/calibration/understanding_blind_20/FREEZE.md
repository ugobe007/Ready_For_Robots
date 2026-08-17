# FREEZE — Understanding v1 Phases 1–3 (Blind 20 window)

**Git tip:** `dffbc1a133d7c32a3554b280d7bec447cab3f66f`  
**Working-tree checksum** (`*.py` under `app/services/robot_understanding_v1/`):  
`TREE 4de9d6f556253c7a08239b6a890f26496fa9d2097d15caf684f1d5be57fa65f7` (8 files)  
Recorded 2026-08-17T01:07:22Z.

## What is frozen

| Path | Role |
|------|------|
| `app/services/robot_understanding_v1/` | Phases 1–3 pipeline |
| `scripts/build_robot_profile.py` | CLI |
| `app/api/robot_profile.py` | Shadow API |

**Hard rule:** Do **not** change Understanding code during Blind 20. No mid-run fixes. No OEM-specific branches.

## What is explicitly out of scope for this freeze window

- Yield tuning against smoke OEMs (Agility / Dexmate / Locus / Avidbots)
- OEM-specific extraction rules for Blind 5 or Blind 20 cohort members
- Phase 4–5 (capability → workflow → job)
- QUALIFY / Pursuit Brief influence on research
- Job matching evaluation
- Fixing Understanding code even if Blind 20 fails

## Excluded from cohort (author/tune contamination)

**Smoke:** Agility Digit, Dexmate Vega, Locus Origin, Avidbots Neo  
**Blind 5:** MiR250, Figure 03 / Figure AI, UR10e / Universal Robots, Spot / Boston Dynamics, Moxi / Diligent

## Allowed

- `docs/calibration/understanding_blind_20/**`
- `scripts/run_understanding_blind20.py`
- `scripts/score_understanding_blind20.py`
- Human ground truth authoring (independent of agent outputs)
- Scoring + outcome writeup
- Pointer update in `docs/robot_understanding_v1.md`

## After Blind 20 outcome

Classify failures into **general mechanisms** only in `outcome.md`.  
Do **not** open Phase 4. Do **not** fix Understanding code in this mission.

**Post-outcome lock (2026-08-17):** Phases 1–3 frozen as **v1.0 calibration** — see [`V1_0_FREEZE.md`](./V1_0_FREEZE.md). Gate FAIL left open; no Blind 20 retune.
