# Hermes → ReadyForRobots Deployment Evidence Bridge

Concrete integration: Hermes crawls public OEM/customer deployment news nightly; RFR stores structured **Deployment Evidence** (not live telemetry).

```
┌─────────────────────────┐         POST /api/v1/market-graph/
│  Hermes Agent           │         deployment-evidence/ingest
│  skill: rfr-deployment- │ ──────► │ ReadyForRobots (Fly)     │
│  evidence               │  X-Admin-Key                      │
│  + cron daily           │         │ parse → stage/metrics     │
│  web_search / extract   │         │ persist deployment_*      │
└─────────────────────────┘         │ Work Match enrichment     │
                                    └───────────────────────────┘
```

## Pieces

| Side | Asset |
|------|--------|
| Hermes | `optional-skills/research/rfr-deployment-evidence/SKILL.md` (hermes-agent clone) |
| RFR API | `POST /api/v1/market-graph/deployment-evidence/ingest` |
| RFR engine | `app/services/deployment_evidence_engine.py` |
| RFR tables | `deployment_sources`, `deployment_events`, `deployment_evidence`, `deployment_metrics` |

## Auth

- Header: `X-Admin-Key: <ADMIN_KEY>` (Fly secret), **or**
- Query: `?token=<SCRAPER_CRON_TOKEN>`

Never put the key in digests or skill state files committed to git.

For the full multi-track agent roster (jobs, qualify, DMs, news, UX audit), see [hermes_intelligence_bridge.md](hermes_intelligence_bridge.md).

## Hermes setup (once)

```bash
# On the Hermes host
export RFR_API_BASE=https://ready-2-robot.fly.dev
export RFR_ADMIN_KEY='…'   # same as Fly ADMIN_KEY

# Install optional skill (from hermes-agent tree or copy SKILL.md to ~/.hermes/skills/)
hermes skills install official/research/rfr-deployment-evidence
# or: mkdir -p ~/.hermes/skills/research && cp -r optional-skills/research/rfr-deployment-evidence ~/.hermes/skills/research/

# Chat: "Set up RFR deployment evidence watch for Agility, Figure, OTTO, Locus, Geek+"
# Skill writes ~/.hermes/rfr-deployment-watches/oem-core.json and creates cron.
```

## Tick contract

1. Search/extract from last cutoff (OEM + customer queries).
2. Normalize stage (agreement ≠ commercial) + quantity hygiene.
3. Deduplicate by underlying deployment.
4. POST claims batch to ingest.
5. Digest material events only; advance cutoff per successful vendor.

## Example ingest (dry run)

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/deployment-evidence/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "hermes_run_id": "manual-smoke",
    "claims": [{
      "text": "Digit moved more than 100,000 totes at GXO and accumulated more than 65,000 operating hours across nine customer facilities. Digit unloading totes from AMRs onto a conveyor feeding pack-out.",
      "source_url": "https://example.com/agility-gxo",
      "source_type": "oem_press_release",
      "source_date": "2025-11-20",
      "vendor_name": "Agility Robotics",
      "robot_model": "Digit",
      "customer_name": "GXO",
      "facility_name": "Flowery Branch, GA",
      "industry": "Logistics",
      "work_type": "Tote handling",
      "workflow": {"origin": "AMR", "action": "Unload tote", "destination": "Conveyor"}
    }]
  }'
```

## What RFR does with each claim

1. `parse_deployment_claim` → stage, evidence_level A–F, metrics, performed_primitives  
2. `persist_deployment_event` → upsert source + event + evidence + metrics  
3. Pipeline / Work Match can attach `comparable_deployment` when primitives overlap  

## Ops checklist

- [ ] Fly migrate applied (`deployment_*` tables exist)
- [ ] `ADMIN_KEY` set on Fly; Hermes has matching `RFR_ADMIN_KEY`
- [ ] Dry-run ingest returns `accepted: 1` with stage/metrics
- [ ] Hermes cron job listed (`hermes cron list`)
- [ ] First live tick: `GET /api/v1/market-graph/deployment-evidence` shows new rows

## Out of scope (later)

- Full 500-vendor continuous search fan-out (start with ~10–30 priority OEMs)
- Automatic Work Match score boost from evidence_level (conceptual today; wire numerically next)
- Customer telemetry ingestion (explicitly not this path)
