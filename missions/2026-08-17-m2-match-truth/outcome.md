# Outcome — M2 Match Truth

**Date:** 2026-08-17  
**Mission:** [`brief.md`](./brief.md)

## Result

Requirement matching against frozen Understanding profiles produces different, explainable verdicts for the same job. No match percentage. Understanding extractors were not reopened.

### Novolex Kinston — Case conveyor → outbound pallet

| Robot | Verdict | Notes |
|-------|---------|--------|
| Dexmate Vega | POSSIBLE MATCH | Dual-arm + mobile + 2.2 m reach. Case weight, conveyor geometry, gripper, cycle time unknown. No blocker. |
| Agility Digit | POSSIBLE MATCH | Dual-arm / load-unload grounded. Payload and cell geometry unknown. |
| Locus Origin | NOT A MATCH | Blocker: case acquisition and pallet placement; no grounded manipulation. |
| Avidbots Neo | NOT A MATCH | Same blocker — scrub profile cannot palletize cases. |

### Four-physics

| Work | Discrimination observed |
|------|-------------------------|
| Novolex palletize | Vega/Digit possible vs Origin/Neo rejected |
| CuraScript tote return | Origin/Digit possible vs Neo/fixed arm rejected |
| Airport hard-floor scrub | Neo possible vs Vega/Digit/Origin rejected |
| Inspection route | Spot possible vs Origin/Vega/Neo rejected |

Corpus top boards split by work physics (Vega pallet/gripper, Origin transport, Neo scrub). Digit keeps tote/cart as valid possible matches but ranks distinctive manipulation / mobile-manipulation work first.

## Tests

`python3 -m pytest tests/test_m2_requirement_match.py -q` — pass

## Production (2026-08-17, commit `33fdc69`)

Clean GitHub checkout of `33fdc69` built image `index-mLvyi8N_.js` on Fly. OpenAPI has **no** hermes/worksite paths. GitHub Actions marked the deploy **failed** because `release_command` (Alembic) timed out — no new migrations in this commit; web is serving the new image anyway (`matcher=requirement_v1`). Vercel `readyforrobots.com` already has the matcher surface (`Possible match` / `still_unknown`); no extra Vercel deploy was required. Matcher logic was **not** changed after freeze.

Live smoke (`POST /api/robot-profile` then `/api/robot-job-match` with that profile):

| Robot | Tier | Top-10 physics | Novolex |
|-------|------|----------------|---------|
| Dexmate Vega | B | gripper 7 + pallet 3 | POSSIBLE MATCH — dual-arm, mobile, 2.2 m reach; job-side unknowns kept |
| Agility Digit | B | transport/cart 8 + gripper 2 | POSSIBLE MATCH (not in top-10; tote ranks first because tote facts are more grounded) |
| Locus Origin | C | transport/cart 10 | NOT A MATCH — unmet manipulation named |
| Avidbots Neo | A | scrub 10 | NOT A MATCH — unmet manipulation named |

Zero cross-physics bleed: Vega has no tote/scrub; Origin has no pallet/scrub; Neo has no pallet/tote.

### MATCH TRUTH bar (production boards — after utilization ranking)

Human review of the first live boards: Dexmate **PASS**, Locus **PASS**, Avidbots **PASS**, Digit match correctness **PASS**, Digit top-10 relevance **needed one general ranking fix** (not a Digit rule).

Truth was working; ranking was not. Among jobs that already pass the requirements gate, rank higher the jobs that exercise more of **this robot’s distinctive grounded capabilities**. No family quota.

Re-rank of the same four live production profiles (Understanding frozen; ranking only):

| Robot | Tier | Top-10 physics | Novolex |
|-------|------|----------------|---------|
| Dexmate Vega | B | gripper 7 + pallet 3 | POSSIBLE MATCH — in top 10 |
| Agility Digit | B | gripper 7 + pallet 3 | POSSIBLE MATCH — tote/cart remain possible, first tote at rank 17 (`origin_curascript_tempe`) |
| Locus Origin | C | transport 7 + cart 3 | NOT A MATCH — unmet manipulation named |
| Avidbots Neo | A | scrub 10 | NOT A MATCH — unmet manipulation named |

| Clause | Result |
|--------|--------|
| Same job, different verdicts | **PASS** (Novolex) |
| Every positive match has Why | **PASS** |
| Every hard rejection names unmet requirement | **PASS** (Origin/Neo Novolex) |
| Unknowns stay unknown | **PASS** |
| Zero obvious cross-physics violations | **PASS** |
| Vega board looks like Vega | **PASS** — CNC/palletize |
| Neo / Origin boards look like those robots | **PASS** — Origin tote #1 is an excellent Origin match |
| Digit board uses more of Digit first | **PASS** — CNC / machine load-unload, then pallet; legitimate tote/cart lower |

**MATCH TRUTH (matcher):** **PASS** on this ranking. Fly still serves `33fdc69` until this commit deploys. Traffic / C04 stay paused until **auth continuity + telemetry**. No further matcher research unless those tests reveal an actual failure.

Evidence (do not commit): `reports/m2_prod_smoke_20260817/` · `reports/m2_rank_rerun_20260817/`
