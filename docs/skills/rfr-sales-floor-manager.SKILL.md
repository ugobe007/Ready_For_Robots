---
name: rfr-sales-floor-manager
description: "Hourly sales coach for Cal — KPIs, kill switches, OemCal vs BuyerCal."
version: 0.1.0
author: Ready For Robots + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Robotics, Sales, Cal, FloorManager, ReadyForRobots]
    related_skills: [rfr-daily-email-digest, rfr-signup-ux-audit, rfr-qualify-match, rfr-workflow-improve]
---

# ReadyForRobots Sales Floor Manager

This skill **does not** call OpenAI, Anthropic, or Vercel AI Gateway. Read Fly APIs with `curl`. Daily email is `rfr-daily-email-digest` (POST `/api/v1/market-graph/daily-digest-send`), not an LLM draft.

Division of labor: [docs/hermes_cal_bridge.md](../../docs/hermes_cal_bridge.md) · OemCal UI copy: `readyforrobots-new/client/src/lib/oemCalCopy.ts`

## When to Use

- Hourly cron (`20 * * * *` America/Los_Angeles)
- "How is Cal this hour?" / "Reprioritize Cal"
- After a quiet conversion window or a bad send streak

**No paid LLM.** Scoreboard is `curl` to Fly. Daily operator email is skill `rfr-daily-email-digest`, not an AI Gateway draft.

## Environment

| Var | Purpose |
|-----|---------|
| `RFR_API_BASE` | e.g. `https://ready-2-robot.fly.dev` |
| `RFR_ADMIN_KEY` | `X-Admin-Key` for cal-status / scraper status |

State: `~/.hermes/rfr-sales-floor-watches/core.json`  
Log (append): `docs/cal_floor_manager_log.md` (repo workdir)

## Scoreboard (read every tick)

1. **Cal health**

```
GET {RFR_API_BASE}/api/v1/market-graph/cal-status
Header: X-Admin-Key: {RFR_ADMIN_KEY}
```

Note: autopilot on/off, last heartbeat age, error reason. Never print the admin key.

2. **Scraper / intake**

```
GET {RFR_API_BASE}/api/scraper/status
```

Note: `leads_last_24h` vs `target_daily_leads`, `on_track`.

3. **Pipeline stamp (Hermes → Cal fuel)**

```
GET {RFR_API_BASE}/api/leads/pipeline
```

Count HOT leads; sample how many expose `hermes_qualify` / `hermes_buying_window` / `hermes_decision_makers` (non-empty). Thin stamp = research not reaching the sales floor.

4. **Conversion (if harness snapshot available)**

Read `reports/harness_snapshot_latest.json` → `conversion.signup_funnel_7d` (`signup_start`, `signup_complete`, `first_save`) when present. Do not fabricate.

Also note `/experiment` funnel if visit events show `rdd_*` / `funnel: robot_jobs` — **See All CTR by persona** is the active product test (`docs/TRAFFIC_SPRINT.md`). Do not recommend channel/product expansion while that test is running. If traffic is thin: `ALERT` for outreach gap — never treat soft early CTR as a reason to change the product.

5. **Prior hour**

Read watch `core.json` → `last_actions`, `last_alerts`. Avoid repeating the same adjustment twice in a row unless still red.

## Decisions (max 3 actions per tick)

Allowed action types only:

| Action | Meaning |
|--------|---------|
| `ALERT` | Operator must see (scraper offline, Cal error, signup funnel collapsed) |
| `PRIORITY` | Prefer Hermes-qualified / HOT pool ordering (document why; no code edit required) |
| `VOICE` | Reminder: use **OemCal** on Results/Signup; **BuyerCal** on outbound — cite `oemCalCopy.ts` / `cal_persona.py` |
| `KILL_SEND` | Recommend pause outbound if bounce/error streak (operator confirms) |
| `INGEST_GAP` | Qualify/DM coverage too thin on HOT — nudge next Hermes research tick |
| `SILENT` | All green — write one line and exit |

Hard rules:

- Never send as Cal / never call Resend.
- Never invent reply rates, dollar amounts, or company facts.
- Never flip `CAL_INCLUDE_BUYING_WINDOW` without operator review.
- Max **3** non-`SILENT` actions; prefer `ALERT` when red.

## Procedure — Tick

1. Load `~/.hermes/rfr-sales-floor-watches/core.json` (create from example if missing).
2. Pull scoreboard endpoints above.
3. Choose 0–3 actions.
4. Append a dated section to `docs/cal_floor_manager_log.md`:

```markdown
## YYYY-MM-DD HH:MM TZ
- Scoreboard: cal=… scraper=… hermes_stamp=… funnel=…
- Actions: …
- Next hour watch: …
```

5. Update watch JSON: `last_run`, `last_run_id`, `last_actions`, `last_alerts`, bump `cutoff_iso`.
6. Digest: 5–10 lines for local deliver **or** `[SILENT]` if truly quiet and no actions.

## OemCal vs BuyerCal (coach reminder)

| Mode | Surface | Job |
|------|---------|-----|
| **OemCal** | Results, Signup, sticky CTA | “These buyers fit *your* robot — claim them” |
| **BuyerCal** | Outbound email / draft assembly | Observation → interpretation → next step; no hype |

If Results/Signup copy drifts into researcher essays, emit `VOICE` pointing at `oemCalCopy.ts`.

## Pitfalls

- Treating daily digest as a substitute for this hourly loop
- Adding more research bots instead of fixing ingest→pipeline stamp
- Changing Cal persona banned phrases without a learning-log row

## Verification

- [ ] cal-status fetched without leaking secrets
- [ ] Log appended when any non-SILENT action fires
- [ ] Watch `last_run` advances each successful tick
- [ ] No outbound send attempted
