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

Corpus top boards split by work physics (Vega pallet/gripper, Origin transport, Neo scrub, Digit tote+manip mix).

## Tests

`python3 -m pytest tests/test_m2_requirement_match.py -q` — pass

## Follow-ups (not this mission)

- Deploy API (Fly) + Jobs UI (Vercel) so live match uses `requirement_v1` (pass Understanding profile). Do not deploy from a dirty tree that contains unrelated worksite/hermes changes.
- Human robotics reviewer ~8/10 on top jobs before MATCH TRUTH = PASS
- Auth return + telemetry
- Then C04 / invite traffic
