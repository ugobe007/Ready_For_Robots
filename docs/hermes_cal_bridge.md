# Hermes ↔ Cal (and local RFR agents)

How external Hermes research correlates with in-app agents like **Cal** (buyer outreach), Scout, and Pipeline.

```
Hermes (Mac cron)                    ReadyForRobots (Fly)
─────────────────                    ───────────────────
job-orders / qualify / DMs / news
        │
        ▼
 market-graph ingest  ──────────►  companies / signals / contacts
                                   crm_metadata.hermes_*
        │                                    │
        │                                    ├─► Pipeline UI (Hermes intelligence panel)
        │                                    ├─► Cal autonomy pool (priority + draft grounding)
        │                                    └─► Scout / scores (via same HOT/WARM graph)
        │
        └── GET …/market-graph/cal-status ─► Redis heartbeat / autopilot (ops digest)
```

## Division of labor

| Agent | Owns | Does **not** |
|-------|------|----------------|
| **Hermes** | Public research: jobs, qualify overlays, DMs, vendor news, deployment evidence | Send buyer email; bypass Cal gates |
| **Floor Manager** | Hourly Cal/OEM scoreboard + max 3 coach actions (`rfr-sales-floor-manager`) | Send email; invent metrics |
| **Cal** | Draft → verify contact → assembly gate → Resend send → follow-ups | Invent deployment facts; scrape the open web |
| **Scout** | Public chat / discovery UX | Hermes cron research |
| **Pipeline** | Human operator CRM surface | Autonomy |

**Rule:** Hermes writes **intelligence**; Floor Manager **coaches**; Cal writes **outreach**. Never give Hermes a parallel send path.

### OemCal vs BuyerCal

| Mode | Surfaces | Voice |
|------|----------|-------|
| **OemCal** | Results, Signup, sticky CTA (`oemCalCopy.ts`) | “These buyers fit your robot — claim them” |
| **BuyerCal** | Outbound assembly (`cal_persona.py`) | Observation → interpretation → next step |

Floor Manager emits `VOICE` if conversion copy drifts into researcher essays.

## Shared data (correlation)

| Hermes write | Table / field | Cal use |
|--------------|---------------|---------|
| Job orders | `signals` (`hermes_job_order`) + WORK units | Improves HOT/WARM signals; draft grounding |
| Qualify | `crm_metadata.hermes_qualify` | Pool priority (`automation_fit` ≥ 60 first); optional reason line |
| Buying windows | `crm_metadata.hermes_buying_window` | Timing urgency (FY / shows / peer proof); pool reorder + optional `cal_hint` when `CAL_INCLUDE_BUYING_WINDOW=1` (default **off**) |
| Decision makers | `contacts` + `crm_metadata.hermes_decision_makers` | Contact waterfall / CRM evidence |
| Vendor / deployment news | `vendor_news_items` / deployment tables | Matching & proof — not auto-send |

Cal still requires verified/trusted email + assembly + bounce gates before any send.

## Cal behavior hooks (code)

In `app/services/cal_autonomy.py`:

1. **`prioritize_hermes_qualified`** — after unsent prioritization, prefer Hermes-qualified companies.
2. **`prioritize_buying_window`** — when `CAL_INCLUDE_BUYING_WINDOW=1`, prefer high `urgency_0_100` after qualify priority.
3. **`_hermes_context_reason`** — when `CAL_INCLUDE_HERMES_REASON=1` (default), may add a short grounded opener from Hermes job titles / qualify (not a full research dump). With buying-window flag on, may use `cal_hint` if no job/rationale clause.
4. Signal blob fold-in of Hermes rationale/jobs when `CAL_INCLUDE_SIGNAL_REASON=1`.

Env:

| Var | Default | Meaning |
|-----|---------|---------|
| `CAL_INCLUDE_HERMES_REASON` | `1` | Allow short Hermes-grounded opener |
| `CAL_INCLUDE_BUYING_WINDOW` | `0` | Reorder by timing urgency + allow `cal_hint` in opener |
| `CAL_INCLUDE_SIGNAL_REASON` | `0` | Broader signal-snippet reasons (noisier) |

## Hermes ops: Cal health

```
GET {RFR_API_BASE}/api/v1/market-graph/cal-status
Header: X-Admin-Key: {RFR_ADMIN_KEY}
```

Returns autopilot / Redis heartbeat summary for digests. Does **not** trigger sends.

## Email digests (Hermes path A)

Cron delivery target: `email:ugobe07@gmail.com` once Email gateway is configured.

Requires a **dedicated agent mailbox** (IMAP/SMTP) in `~/.hermes/.env`:

```bash
EMAIL_ADDRESS=hermes-agent@yourdomain-or-gmail.com   # NOT the personal inbox
EMAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx                   # Gmail App Password
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_HOME_ADDRESS=ugobe07@gmail.com
EMAIL_ALLOWED_USERS=ugobe07@gmail.com
```

Then:

```bash
hermes gateway restart   # or start
hermes cron edit <job_id> --deliver email:ugobe07@gmail.com
```

## Related docs

- [hermes_intelligence_bridge.md](hermes_intelligence_bridge.md) — ingest roster
- [hermes_deployment_bridge.md](hermes_deployment_bridge.md) — deployment evidence
- [cal_persona_spec.md](cal_persona_spec.md) — Cal voice
