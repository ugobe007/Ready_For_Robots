# Maturity tagging sheet — validation pack v0.1

**Purpose:** Manually tag **20 robot sellers** and **20 buyer accounts** to validate the ReadyForRobots maturity matrix before scoring automation.

**Canonical model:** [commercial_maturity_models.md](../commercial_maturity_models.md)

**Files**

| File | Role |
|------|------|
| [`maturity_sellers_20_v0_1.csv`](./maturity_sellers_20_v0_1.csv) | Tag robot companies R1–R4 + RCMS notes |
| [`maturity_buyers_20_v0_1.csv`](./maturity_buyers_20_v0_1.csv) | Tag customers C1–C4 + CAMS notes |
| [`maturity_matrix_pairs_v0_1.csv`](./maturity_matrix_pairs_v0_1.csv) | Cross-product pairs to test Cal motion by cell |

---

## How to tag (15–20 min)

### Sellers (`maturity_sellers_20_v0_1.csv`)

1. Leave `hypothesized_r` as a strawman — overwrite `tagged_r` with your judgment.
2. Fill evidence columns briefly (deployments, repeats, support) — not essays.
3. Set `confidence` to `high` / `med` / `low`.
4. Optional: rough `rcms_estimate` 0–100 using the RCMS weights in the model doc.

**Rule:** Age is a hint. Deployments + commercial capability win.

### Buyers (`maturity_buyers_20_v0_1.csv`)

1. Tag the **organization’s automation capability**, not how “robot-interested” the title sounds.
2. A company can be C4 at Walmart scale and C2 at a single plant with no robotics org — note facility scope in `scope_notes`.
3. Fill `tagged_c` + evidence of deployments / automation org / procurement sophistication.

### Pairs (`maturity_matrix_pairs_v0_1.csv`)

1. For each row, confirm `seller_r` and `buyer_c` after tagging the source sheets.
2. Record `matrix_cell` from the model (e.g. `R1×C4 → High maturity gap`).
3. Answer: **What should Cal do?** (1–2 sentences)
4. Answer: **Would more leads help or hurt?** (`help` / `hurt` / `neutral`)
5. Flag `matrix_holds` = `yes` / `no` / `partial` — if `no`, write why in `revision_note`.

---

## Success criteria for this pack

| Gate | Pass if |
|------|---------|
| Coverage | All 20 sellers have `tagged_r`; all 20 buyers have `tagged_c` |
| Spread | At least 2 of each R1–R4 and C1–C4 represented (or note gaps) |
| Gap cells | At least 3 pairs tagged as R1×C3 or R1×C4 |
| Matrix check | ≥10 pairs have `matrix_holds` filled; majority `yes` or documented revisions |
| Cal motion | Every pair has a one-line Cal action that is **not** identical |

---

## Strawman mix (expected after tagging)

Sellers were chosen to *approximate* a spread across R1–R4 (young humanoids → AMR scale-ups → seasoned AMRs → professional automation). Buyers mix plant-level opportunity accounts from RFR calibration packs with known fleet/automation operators.

**Do not treat hypothesized columns as truth.**

---

## After tagging

1. Update this file’s status to `validated` or list matrix revisions.
2. Feed disagreements into [agent_improvement_log.md](../agent_improvement_log.md).
3. Next build: Stage 1 manual tags in product DB / CRM fields (`robot_maturity_level`, `customer_maturity_level`).
