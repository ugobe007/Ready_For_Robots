# Hermes ↔ ReadyForRobots Intelligence Bridge

**Operating priority (2026-08-15):** Traffic experiment on `/experiment` beats research expansion.  
Read [`CAPABILITY_MODEL.md`](./CAPABILITY_MODEL.md) · [`EXPERIMENT_MODE.md`](./EXPERIMENT_MODE.md) · [`TRAFFIC_SPRINT.md`](./TRAFFIC_SPRINT.md).

| | |
|--|--|
| Production | `/experiment` live |
| Promise | Find Jobs for Robots |
| Engine | `CAPABILITIES → FIND WORK` |
| Audience | OEM · Distributor · Integrator |
| Primary behavior | `rdd_see_all_clicked` |
| Decision source | observed behavior |

**Traffic vs product:** Hermes may find prospects, draft **discovery content** from scored jobs (not promo spam), build outreach cohorts, monitor `rdd_*`, and report. Hermes must **not** respond to weak early numbers by changing the experiment (features, crawls, scoring). Soft traffic → better discoveries, not product rewrite. After enough behavior: *Who wants this most — and what kind of work makes them want more?*

Acquisition: [`DISCOVERY_CONTENT.md`](./DISCOVERY_CONTENT.md) · first sprint [`CONTENT_SPRINT.md`](./CONTENT_SPRINT.md) — editorial = **work**; content = sensor; Content→Work funnel by `src`.

**Frozen:** OEM 11–50, more distributors, Channel Match scoring, distributor UI, RDD Fly migrate, new ontology layers.

Full agent roster: find work, qualify, match vendors, find decision makers, ingest deployment evidence, track vendor/customer news — and **operate traffic** — **without expanding product surface until traffic evidence lands**.

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
rfr-customer-video-evidence ──POST──► /video-evidence/ingest
rfr-buying-windows       ──POST──►  /buying-window-overlay
rfr-workflow-improve     ──write──► docs/agent_improvement_log.md
rfr-signup-ux-audit      ──write──► docs/ux_signup_audit.md
```

Base path: `{RFR_API_BASE}/api/v1/market-graph/*`  
Default API: `https://ready-2-robot.fly.dev`

Also: [hermes_cal_bridge.md](hermes_cal_bridge.md) — how Hermes intelligence feeds Cal / Scout / Pipeline.

## Auth

Hermes does not have its own ReadyForRobots key. **`RFR_ADMIN_KEY` is an alias** for the Fly secret named **`ADMIN_KEY`** on app **`ready-2-robot`**.

| Name you see | Where it lives | What it is |
|--------------|----------------|------------|
| `ADMIN_KEY` | Fly → `ready-2-robot` secrets | Canonical ops key. Header `X-Admin-Key`. |
| `ADMIN_KEY` | Repo-root `.env` (gitignored) | Local copy. `./scripts/sync_fly_admin_key.sh` pushes this **to** Fly. |
| `ADMIN_KEY` | GitHub → repo **Settings → Secrets and variables → Actions** | Copy of the same Fly value (digest Action / harness). |
| `RFR_ADMIN_KEY` | Mac file `~/.hermes/.env` | Hermes env name for that **same** Fly `ADMIN_KEY`. |
| `SCRAPER_CRON_TOKEN` | Fly (optional) | Alternate auth: `?token=` on ingest URLs. |

`fly secrets list` prints a 16-character hex **fingerprint**, not the secret. Pasting that fingerprint as `X-Admin-Key` is rejected.

### Read the real value (Mac Terminal.app, with `flyctl` logged in)

Do **not** run this in Cursor Cloud or in the Hermes chat window.

```bash
fly ssh console -a ready-2-robot -C 'printenv ADMIN_KEY'
```

If you already have a repo checkout on the Mac:

```bash
grep '^ADMIN_KEY=' /path/to/Ready_For_Robots/.env
```

### Put it on Hermes (Mac only)

Nous Hermes Agent is a CLI on the Mac (`hermes`), not a bash builtin. Install/docs: https://github.com/nousresearch/hermes-agent — then:

```bash
# ~/.hermes/.env  (create if missing)
RFR_API_BASE=https://ready-2-robot.fly.dev
RFR_ADMIN_KEY='paste-the-printenv-value-here'
```

```bash
hermes doctor --fix
hermes gateway start
hermes cron list
```

Those three commands fail in Cursor’s cloud terminal and in Hermes chat because `hermes` is not on PATH there.

Never put keys in digests, watch state, or git.

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
| 8 | Buying windows | `rfr-buying-windows` | `POST .../buying-window-overlay` → `hermes_buying_window` |
| 9 | Customer use-case videos | `rfr-customer-video-evidence` | `POST .../video-evidence/ingest` → `hermes_video_evidence` |
| 10 | Vendor demo / field videos | `rfr-vendor-video-evidence` | `POST .../vendor-video-evidence/ingest` → vendor profiles |
| — | Video seed targets | (both video skills) | `GET .../video-evidence/seed-targets` |
| — | Workflow improve | `rfr-workflow-improve` | `docs/agent_improvement_log.md` |
| — | Signup UX audit | `rfr-signup-ux-audit` | `docs/ux_signup_audit.md` (recs only) |
| — | Sales floor manager | `rfr-sales-floor-manager` | Hourly Cal/OEM coach → `docs/cal_floor_manager_log.md` |

Qualify overlays use `truth_state: HERMES_OVERLAY` — not customer-confirmed CRM QUALIFY.

## Cron roster (America/Los_Angeles)

**Do not pin crons to AI Gateway, OpenAI, or Anthropic.** Those lookups burn paid tokens and fail with HTTP 402 when the Vercel gateway has no credit. Hermes must use **terminal-only** (`curl` to Fly). Intelligence runs on ReadyForRobots’ local inference engine.

**Daily digest cron is retired on Hermes.** Fly in-process + Celery Beat + `.github/workflows/cal-daily-digest.yml` send it. A leftover Hermes job named `RFR daily email digest` with `--provider ai-gateway` can 402; ignore it — the email still sends from Fly/GHA.

| Schedule | Skill |
|----------|-------|
| `0 6 * * *` | `research/rfr-deployment-evidence` |
| `0 7 * * *` | `research/rfr-job-orders` |
| `30 8 * * *` | `research/rfr-qualify-match` (POST `/infer-qualify`) |
| — | `research/rfr-daily-email-digest` **retired** — Fly/GHA POST `/daily-digest-send` |
| `0 9 * * *` | `research/rfr-buying-windows` |
| `0 10 * * *` | `research/rfr-decision-makers` |
| `0 11 * * *` | `research/rfr-vendor-customer-news` |
| `0 12 * * *` | `research/rfr-customer-video-evidence` (seed many buyer profiles) |
| `0 13 * * *` | `research/rfr-vendor-video-evidence` (OEM demos / field) |
| `20 * * * *` | `research/rfr-sales-floor-manager` (hourly coach) |
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

### Infer-qualify (preferred — local inference, no LLM)

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/infer-qualify" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{"dry_run": true, "limit": 12, "hermes_run_id": "smoke-infer"}'
```

Runs `lead_inference_engine` + WORK reconstruction on stored signals and writes `hermes_qualify`. Do **not** call OpenAI/Anthropic/AI Gateway to invent fit scores.

### Daily digest send (no AI Gateway)

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/daily-digest-send" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{"force": false, "period_hours": 24}'
```

Emails the Cal digest plus a heuristic industry brief. Skill: [rfr-daily-email-digest](skills/rfr-daily-email-digest.SKILL.md).

### Qualify overlay (manual / already-scored only)

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

### Buying-window overlay

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/buying-window-overlay" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "overlays": [{
      "company_id": 941,
      "urgency_0_100": 72,
      "window_label": "peer proof + FY Q4 push",
      "factors": [
        {"type": "peer_proof", "peer": "DHL Supply Chain", "robot": "Locus", "recency_days": 12}
      ],
      "cal_hint": "Reference peer deployment; offer briefing in next 10 days.",
      "confidence": 0.65
    }]
  }'
```

Persists under `company.crm_metadata.hermes_buying_window`. Timing urgency ≠ automation fit. Spec: [buying_window_intelligence_v0_1.md](buying_window_intelligence_v0_1.md).

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

### Customer use-case videos

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/video-evidence/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "videos": [{
      "company_name": "HelloFresh",
      "source_url": "https://www.youtube.com/watch?v=example",
      "platform": "youtube",
      "evidence_kind": "facility_tour",
      "title": "Inside a HelloFresh fulfillment center",
      "excerpt": "Associates and AMRs moving meal kits through pack stations.",
      "workflow_hint": "pack-out / meal kit assembly",
      "robot_visible": "AMR",
      "confidence": 0.72
    }]
  }'
```

Persists under `company.crm_metadata.hermes_video_evidence` (URL-deduped, last 25). Surfaces on Pipeline Hermes panel. Skill: `docs/skills/rfr-customer-video-evidence.SKILL.md`.

### Vendor demo / field videos

```bash
curl -s -X POST "$RFR_API_BASE/api/v1/market-graph/vendor-video-evidence/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{
    "dry_run": true,
    "videos": [{
      "vendor_name": "Agility Robotics",
      "source_url": "https://www.youtube.com/watch?v=example",
      "platform": "youtube",
      "evidence_kind": "oem_demo",
      "title": "Digit tote handling demo",
      "robot_model": "Digit",
      "confidence": 0.8
    }]
  }'
```

Writes to `robot_companies.market_intelligence.hermes_video_evidence` and matching `manufacturers.external_refs.hermes_video_evidence`.

Seed targets (customers and/or vendors still missing videos):

```bash
curl -s "$RFR_API_BASE/api/v1/market-graph/video-evidence/seed-targets?kind=both&only_missing=true&limit=40" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY"
```

### Deployment evidence

See [hermes_deployment_bridge.md](hermes_deployment_bridge.md).

## Watch state

| Skill | State dir |
|-------|-----------|
| deployment | `~/.hermes/rfr-deployment-watches/` |
| job-orders | `~/.hermes/rfr-job-order-watches/` |
| customer-video | `~/.hermes/rfr-customer-video-watches/` |
| vendor-video | `~/.hermes/rfr-vendor-video-watches/` |
| qualify-match | `~/.hermes/rfr-qualify-watches/` |
| buying-windows | `~/.hermes/rfr-buying-window-watches/` |
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
