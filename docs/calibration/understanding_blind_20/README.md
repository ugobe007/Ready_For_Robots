# Understanding Blind 20 — Phase 1–3 release gate (holdout)

**Status:** Company-binding fix + Blind 20 rerun complete — see [`outcome.md`](./outcome.md) (**FAIL** — critical recall 78%; company/disentanglement **100%**).  
**Scope:** Robot Profile only (SOURCE → FACT). No jobs. No QUALIFY. No Phase 4–5.

This is the full **blind holdout** Understanding evaluation. Smoke OEMs and Blind 5
robots were used to author/tune or stage the system — they are **out of cohort**.
Do not change the Blind 20 cohort or ground truth to chase scores.

## Why Blind 20

Blind 5 was a cheaper adversarial probe. Blind 20 is the Phase 1–3 gate:

- 20 fresh robots across locked physics mix
- Independent human ground truth before agent outputs
- Aggregate + **by-class** metrics
- Failures classified into general mechanisms only — **no mid-run fixes**

## Freeze rules

Until `outcome.md` for this Blind 20 run is written:

1. Do **not** change `app/services/robot_understanding_v1/`.
2. Do **not** add OEM-specific branches for cohort members.
3. Do **not** improve smoke OEMs or Blind 5 robots for Understanding mid-gate.
4. Do **not** mix QUALIFY / Pursuit Brief research into profile building.
5. Do **not** open Phase 4–5 even if Blind 20 fails.
6. If Blind 20 fails: document general mechanisms in `outcome.md` only.

Allowed during freeze: eval harness, ground-truth authoring, scoring, docs.

See [`FREEZE.md`](./FREEZE.md) for git tip + tree checksum.

## Exclusions

| Set | Robots |
|-----|--------|
| Smoke | Agility Digit, Dexmate Vega, Locus Origin, Avidbots Neo |
| Blind 5 | MiR250, Figure 03, UR10e, Spot, Moxi |

## Cohort mix (locked)

| Physics | Count | IDs |
|---------|-------|-----|
| AMR | 4 | b20-01 … b20-04 |
| Humanoid / mobile manipulator | 4 | b20-05 … b20-08 |
| Cleaning | 3 | b20-09 … b20-11 |
| Cobot / industrial arm | 3 | b20-12 … b20-14 |
| Inspection | 2 | b20-15 … b20-16 |
| Service | 2 | b20-17 … b20-18 |
| Unusual / ambiguous | 2 | b20-19 … b20-20 |

Machine-readable: [`cohort.json`](./cohort.json)

## Process (strict order)

1. **Freeze** — record checksum (`FREEZE.md`) before any Blind 20 work beyond freeze/docs/harness.
2. **Select cohort** — write `cohort.json` (exclusions held).
3. **Human ground truth** — author all 20 in `ground_truth/` from public manufacturer pages **independently** (do not invent expected facts from agent profiles).
4. **Run agent** — frozen pipeline only:
   ```bash
   python3 scripts/run_understanding_blind20.py
   ```
5. **Score** — finish all 20, then score aggregate + by class:
   ```bash
   python3 scripts/score_understanding_blind20.py
   ```
6. **Outcome** — write `outcome.md` (pass/fail vs bars, per-robot, general mechanisms). Update `docs/robot_understanding_v1.md` pointer.

## Pass bars (Blind 20)

| Gate | Target |
|------|--------|
| Company identity | ≥95% |
| Product identity | ≥90% |
| Source hygiene | ≥95% |
| Source grounding | ≈100% |
| Critical fact recall | ≥80% |
| Overall fact recall | ≥60% |
| Material sibling contamination | 0 |
| Unsupported material facts | <5% |
| Tier calibration ±1 | ≥90% |
| Numeric scope accuracy | ≥95% |
| Canonical company binding | ≥95% |

Also report per-class tables (AMR, humanoid/mm, cleaning, cobot/arm, inspection, service, unusual).

**Sibling contamination:** material facts must not inherit sibling-SKU payloads/constraints when the subject is bound.

**Tier note:** obscure or marketing-thin sites may correctly be Tier C — professional ≠ every URL is A.

## Metrics (Understanding only)

Identity (company + product separately) · source-pack hygiene · Source Grounding Rate · fact precision/recall · critical recall · sibling contamination · unsupported material facts · tier calibration (±1).

**Not scored:** job match, QUALIFY, capability derivation, workflow inference.

## Separation from QUALIFY

Blind 20 answers only: *What is this machine?*
