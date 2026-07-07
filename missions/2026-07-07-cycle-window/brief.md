# Mission: Widen Cal's cycle window to reach real send runway

Type: build
Agent: ProductSurface / PipelineHealth

## Goal

Cal's autonomy cycle only pulled the top-100 HOT/WARM buyers (`_hot_warm_companies(limit=max(draft_limit,100))`). Hypothesis: real unsent runway sits deeper in the list, buried behind the bounce-era top ranks. Widen the window and prioritize never-contacted buyers so Cal reaches actionable leads.

## Acceptance criteria

- Pool window decoupled from draft batch, env-configurable.
- Never-contacted buyers prioritized to the front of the window (stable within score order).
- Unit tests for the prioritization.
- Supervised dry-run shows the cycle reaching beyond the top-100; sends stay verified-gated (no junk/guessed sends).

## Outcome

**Shipped**
- `CAL_AUTONOMY_POOL` (default 400) decouples the pool window from `CAL_AUTONOMY_DRAFT_BATCH`.
- `prioritize_unsent(companies, accounts)` — stable sort moving never-sent buyers to the front so the draft batch (`[:draft_limit]`) and send loop reach actionable/reset runway first. Critical enabler: reset accounts scattered at rank 200-400 now get re-drafted instead of staying buried behind 400 already-sent accounts.
- 3 unit tests (`test_prioritize_unsent_*`) — unsent-first ordering, missing-account = unsent, stable when all unsent.
- `cal_runway.py` gained a `--limit` flag to measure the runway curve.

**Key finding — the window was NOT the bottleneck**

Runway curve (measured on prod):

| window | pool | eligible | already contacted | eligible + unsent |
|-------:|-----:|---------:|------------------:|------------------:|
| 100    | 100  | 99       | 99                | 0 |
| 400    | 400  | 395      | 392               | 3 |
| 1000   | 450  | 443      | 440               | 3 |

The **entire HOT/WARM pool is only ~450 companies**, and ~440 are marked contacted. Widening the window to 1000 unlocks only **3** additional unsent leads — and all 3 fail the verified-recipient gate (domain-inferred / invalid format), so the supervised dry-run sent 0 (gate working, no junk).

Outreach status distribution: **323 bounced, 210 sent, 57 delivered**. Recovery analysis (by account): 50 landed, 80 bounced at the real domain (dead mailbox), 1 guessed-domain recoverable.

**The real runway is locked behind the ~397 already-contacted accounts, most of which bounced at guessed mailboxes.** A wide verified-retry dry-run (`cal_bounce_recovery.py --verified-retry`) scanned 81 never-landed accounts and found **10 that resolve to a Hunter-verified contact at the real domain today** (King Faisal Hospital, Choctaw Casinos, Core-Mark, Wendy's, Red Hat, etc.). This is the actionable runway.

## Follow-ups

1. **Run the verified-retry reset at scale** (`cal_bounce_recovery.py --verified-retry --limit N --apply`) — the widened+prioritized window now makes reset accounts re-draftable. This is the actual runway unlock (~10 confirmed at scan 81; likely more across the 323 bounced with a deeper scan). Some hits (Microsoft, Sumitomo, LG CNS) look off-ICP — tighten the eligibility gate or curate the ramp.
2. **Grow the pool** — only ~450 HOT/WARM total. Real scale needs more discovery/ingestion of in-ICP buyers, not a wider window.
3. **Add `ZERO_BOUNCE_API_KEY`** to catch stale Hunter mailboxes pre-send (currently DNS-only).
