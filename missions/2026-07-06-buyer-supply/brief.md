# Mission: Buyer-supply tightening — real deliverable buyers, not junk volume

**Date:** 2026-07-06
**Type:** build
**Agents:** FrictionMiner (audit), LeadQuality (ingestion filter), Orchestrator

## Why

Cleaning Cal's queue + gating outreach revealed the true constraint: Cal is
**out of eligible audience**. Of a 300-company HOT/WARM pool, only ~179 are
real, in-ICP, deliverable buyers — and 177 were already contacted. ~121 are
**junk/off-ICP/no-domain** records that were only ever "sent to" via guessed
addresses (the source of the old ~50% bounce rate).

The binding constraint is no longer send safety (gated) — it is **buyer supply**.
The discovery pipeline is manufacturing ~1 junk/off-ICP "buyer" for every ~1.5
real ones. We must tighten inflow so the HOT/WARM buyer pool is mostly real,
deliverable, in-ICP operating buyers.

## North-star alignment

Order: names/events → scores → rank → specs. This mission is squarely at layer 1
(names/events): stop admitting non-buyers into the buyer pool before they get
scored/ranked/drafted.

## Acceptance criteria

1. **Diagnosis:** categorized breakdown of the ~121 ineligible HOT/WARM records
   by reason (off-ICP industry / no-real-domain / vendor-OEM) with source trace
   (which ingestion path created them). Written to `outcome.md`.
2. **Fix:** ingestion/classification tightened so at least the clearest leaks are
   closed — vendors and no-domain headline fragments should not enter the buyer
   pool as HOT/WARM; off-ICP handling decided (exclude vs. keep-but-flag).
3. **Metric:** re-run runway report — eligible share of HOT/WARM pool improves
   (target: ineligible share materially down from ~40%). Record before/after.
4. **Safety:** no regression to real buyers (Amazon Fulfillment, UPS/DHL/FedEx
   Supply Chain, HCA Healthcare, etc. remain eligible). Tests cover this.
5. **No junk to real buyers:** Cal autopilot remains ON and safe throughout.

## Out of scope

- Growing raw discovery volume (new sources) — this mission is about *precision*,
  not recall. Recall expansion is a follow-up once inflow is clean.
- Changing outreach copy or send cadence.

## Verify

- `python scripts/cal_runway.py` before/after (eligible vs ineligible).
- Targeted pytest for any ingestion/classification changes.
- Deploy to `ready-2-robot`; re-run runway on Fly.

## Outcome

_Filled on completion._
