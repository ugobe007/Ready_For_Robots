# Hermes ↔ ReadyForRobots Intelligence Bridge

Full agent roster: find work, qualify, match vendors, find decision makers, ingest deployment evidence, track vendor/customer news, then improve the loop and signup UX.

```
Hermes skills (cron)                    ReadyForRobots (Fly)
─────────────────────                   ────────────────────
rfr-deployment-evidence  ──POST──►  /deployment-evidence/ingest
rfr-job-orders           ──POST──►  /job-signals/ingest
rfr-qualify-match        ──POST──►  /qualify-overlay
                         ──POST──►  /reconstruct  (dry match)
rfr-decision-makers      ──POST──►  /contacts/ingest
rfr-vendor-customer-news ──POST──►  /vendor-news/ingest
                         ──POST──►  /deployment-evidence/ingest (escalations)
rfr-workflow-improve     ──write──► docs/agent_improvement_log.md
rfr-signup-ux-audit      ──write──► docs/ux_signup_audit.md
```

Base path: `{RFR_API_BASE}/api/v1/market-graph/*`  
Default API: `https://ready-2-robot.fly.dev`

## Auth

- Header: `X-Admin-Key: <ADMIN_KEY>` (Fly secret / Hermes `RFR_ADMIN_KEY`), **or**
- Query: `?token=<SCRAPER_CRON_TOKEN>`

Never put keys in digests, watch state, or git.

Hermes env:

| Var | Purpose |
|-----|---------|
| `RFR_API_BASE` | e.g. `https://ready-2-robot.fly.dev` |
| `RFR_ADMIN_KEY` | Same as Fly `ADMIN_KEY` |

## Track map

| # | Track | Skill | Endpoint / artifact |
|---|--------|-------|---------------------|
| 1 | Deployments | `rfr-deployment-evidence` | `POST .../deployment-evidence/ingest` |
| 2 | Open job orders | `rfr-job-orders` | `POST .../job-signals/ingest` |
| 3 | Qualify | `rfr-qualify-match` | `POST .../qualify-overlay` |
| 4 | Vendor match | `rfr-qualify-match` | `POST .../reconstruct` + digest |
| 5 | Decision makers | `rfr-decision-makers` | `POST .../contacts/ingest` |
| 6 | Deployment metrics/methods | (deployment skill digest) | same as #1 |
| 7 | Vendor + customer news | `rfr-vendor-customer-news` | `POST .../vendor-news/ingest` |
| — | Workflow improve | `rfr-workflow-improve` | `docs/agent_improvement_log.md` |
| — | Signup UX audit | `rfr-signup-ux-audit` | `docs/ux_signup_audit.md` (recs only) |

Qualify overlays use `truth_state: HERMES_OVERLAY` — not customer-confirmed CRM QUALIFY.

## Cron roster (America/Los_Angeles)

Pin every job: `--provider ai-gateway --model anthropic/claude-sonnet-4.6`, `deliver=local`, toolsets `web`+`terminal`, workdir Ready_For_Robots.

| Schedule | Skill |
|----------|-------|
| `0 6 * * *` | `research/rfr-deployment-evidence` |
| `0 7 * * *` | `research/rfr-job-orders` |
| `30 8 * * *` | `research/rfr-qualify-match` |
| `0 10 * * *` | `research/rfr-decision-makers` |
| `0 11 * * *` | `research/rfr-vendor-customer-news` |
| `0 9 * * 0` | `research/rfr-workflow-improve` |
| `0 9 * * 1` | `research/rfr-signup-ux-audit` |

## Endpoint sketches

### Job signals

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/job-signals/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "hermes_run_id": "smoke-jobs",
    "jobs": [{
      "job_title": "Warehouse Associate - AMR Operator",
      "employer": "GXO Logistics",
      "excerpt": "Operate AMRs and unload totes from robots onto conveyor for pack-out.",
      "source_url": "https://example.com/jobs/1",
      "location": "Flowery Branch, GA, USA"
    }]
  }'
```

Creates/updates Company + `hermes_job_order` Signal, reconstructs WORK unit.

### Qualify overlay

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/qualify-overlay" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "overlays": [{
      "company_id": 123,
      "automation_fit": 78,
      "labor_intensity": "high",
      "facility_clarity": "named_site",
      "blockers": [],
      "rationale": "AMR + tote language in open roles",
      "vendor_shortlist": [{"vendor": "Agility Robotics", "model": "Digit"}]
    }]
  }'
```

Persists under `company.crm_metadata.hermes_qualify`.

### Contacts

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/contacts/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "contacts": [{
      "company_id": 123,
      "name": "Jane Operations",
      "title": "VP Operations",
      "linkedin_url": "https://www.linkedin.com/in/example",
      "confidence": 70,
      "source_url": "https://example.com/team"
    }]
  }'
```

Confidence floor 40. Never invent emails.

### Vendor news

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/vendor-news/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "items": [{
      "entity_name": "Agility Robotics",
      "entity_kind": "vendor",
      "news_type": "capability",
      "text": "New Digit navigation stack for mixed-SKU tote handling.",
      "source_url": "https://example.com/news"
    }]
  }'
```

`news_type`: `capability` | `pricing` | `foundation_model` | `product` | `customer_signal`.

### Deployment evidence

See [hermes_deployment_bridge.md](hermes_deployment_bridge.md).

## Watch state

| Skill | State dir |
|-------|-----------|
| deployment | `~/.hermes/rfr-deployment-watches/` |
| job-orders | `~/.hermes/rfr-job-order-watches/` |
| qualify-match | `~/.hermes/rfr-qualify-watches/` |
| decision-makers | `~/.hermes/rfr-dm-watches/` |
| vendor-customer-news | `~/.hermes/rfr-news-watches/` |

## Related code

| Side | Path |
|------|------|
| API | `app/api/v1/market_graph.py` |
| Ingest helpers | `app/services/hermes_intelligence_ingest.py` |
| Vendor news model | `app/models/vendor_news.py` |
| Deployment engine | `app/services/deployment_evidence_engine.py` |
| Hermes skills | `~/.hermes/skills/research/rfr-*` + `hermes-agent/optional-skills/research/rfr-*` |
