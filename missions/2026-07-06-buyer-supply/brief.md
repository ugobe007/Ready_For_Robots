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

## Outcome (2026-07-06)

**Premise was partly wrong — corrected mid-mission.** The ~121 "off-ICP" HOT/WARM
records were NOT junk. All had real, verified website domains and were real,
reputable companies (Marriott, MGM, United, IHG). Sources: 86 `news_discovery`,
30 `seed`/`seed_v2`/`seed_v3`, 1 `manual_las_vegas_cleaning_robot_prospects` —
i.e. hospitality/aviation/gaming were **deliberately seeded as cleaning/service/
delivery-robot buyers**. The off-ICP industry gate was overcorrecting.

### Changes shipped
1. **Narrowed the off-ICP gate** (`app/services/cal_autonomy.py`) to pure
   non-buyers only (publishing/newspaper/market research). Re-admitted hospitality/
   aviation/gaming/food service. Eligible HOT/WARM pool: **179 → 295** (ineligible
   121 → 5). Tests updated (`tests/test_cal_autonomy.py`).
2. **Diagnostics added:** `scripts/cal_ineligible_breakdown.py`,
   `scripts/cal_runway.py`, `scripts/cal_bounce_recovery.py`,
   `scripts/cal_live_cycle_monitor.py`, `scripts/cal_dryrun.py`.

### Root-cause finding (the real bottleneck)
- Outreach status all-time: **321 bounced / 208 sent-unconfirmed / 53 delivered** (~55% bounce).
- Of bounced accounts: 46 landed, **91 bounced at the REAL domain** (bad guessed
  mailbox), only **1** at a wrong domain. Domain correction cannot recover them.
- **Cal lacks real contact emails.** It guesses `info@`/`name@`, which bounce even
  at valid domains. The recipient-trust gate blocks fake *domains* but still allows
  domain-matched *mailbox guesses* — so the bounce pattern can recur.

### Metric delta
- Eligible HOT/WARM buyers: 179 → **295**.
- Ineligible: 121 → **5**.
- Runway (eligible + unsent): **2** — supply is contacted-but-bounced, not absent.

### Recommended next mission (buyer-contact enrichment)
1. Enrich real contact emails (Apollo/Hunter/website mailto) for the 295 eligible
   buyers before send — replace mailbox guessing.
2. Harden recipient gate: send only to **verified-source** emails (drop trust for
   domain-matched guesses), or verify guessed mailboxes (ZeroBounce) pre-send.
3. Optionally reset the 91 real-domain bounces once real mailboxes are available.

### Not done (deliberately)
- Did not apply bounce reset (only 1 recoverable — not worth it).
- Did not expand discovery volume (out of scope; precision first).
