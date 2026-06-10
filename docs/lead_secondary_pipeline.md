# Lead secondary pipeline

**North star:** [lead_quality_north_star.md](lead_quality_north_star.md) — names/events first, then score, rank, specs.

Primary ingestion (scrapers) optimizes for **speed and coverage**. Secondary logic runs **decoupled** on a schedule to turn raw corpus rows into **sales-ready, ranked opportunities**.

## Five pillars

| # | Pillar | What it does | Code |
|---|--------|--------------|------|
| 1 | **Missing data** | Detect absent website, contact, industry, CRM descriptors, inference dossier | `lead_gap_audit.py` |
| 2 | **Optimize data** | Rescue passes fill/normalize fields; industry re-inference; contact waterfall | `lead_secondary_pass.py` rescue passes |
| 3 | **Quality gate** | Junk vs sales lead — rectifier, `classify_lead`, entity type check; quarantine on fail | `rectifier.py` + assessment `quality_gate` |
| 4 | **Additional data** | Agent QA, ontology gaps, signal backfill, procurement/timing cues, GTM stage | `lead_enrichment_agent.py`, `crm_extractor.py` |
| 5 | **Opportunity rank** | Weight data dimensions for the sale; `sales_opportunity_rank` | `lead_secondary_assessment.py` |

### Opportunity rank formula

```
sales_opportunity_rank =
  45% × lead_value_score   (deal quality: spec, procurement, firmographics)
+ 35% × intent_score       (ML intent from signals)
+ 20% × (data_value × completeness)
```

**Data value weights** (how much each filled dimension matters for outreach):

| Dimension | Weight |
|-----------|--------|
| contact | 0.18 |
| lead_inference | 0.16 |
| crm_descriptors | 0.14 |
| website | 0.12 |
| signals | 0.12 |
| quality_passed | 0.12 |
| industry | 0.08 |
| agent_enrichment | 0.08 |

Stored on each lead as `crm_metadata.secondary_assessment` after every secondary pass.

## Architecture map (Pythh → Ready For Robots)

| Pythh layer | Ready For Robots |
|-------------|------------------|
| `automated-scraper.yml` (12h) | Celery Beat scrapers |
| `startup_events` → intake | `signals` → `companies` |
| `resolved_events` ledger | `crm_metadata.enrichment_ledger` |
| `holding-review-worker` | rectification pass |
| `event-resolver.js` | `lead_secondary_pass_task` |
| `pythia-sage-review` | agent QA + assessment |
| `god-score-recalculation` | `rescore_all_companies_task` |

## Rescue passes (pillar 2 + 3 + 4)

| Gap | Pass | Fills |
|-----|------|-------|
| `website` | `website_rescue` | Official homepage |
| `industry` | `industry_rescue` | Industry from signal corpus |
| `contact` | `contact_rescue` | Apollo → role inbox → Contact row |
| `crm_descriptors` | `crm_rescue` | budget, timing, automation_requirements |
| `lead_inference` | `inference_rescue` | Problem, robots, timetable dossier |
| `low_signals` | `signal_backfill` | Company news search |
| `unrectified` | `rectification` | Junk vs lead sniff test |
| `ontology_gaps` | `agent_qa` | Rich facts, ontology candidates |
| *(always)* | `value_assessment` | `secondary_assessment` + rank |

## Automatic execution (production)

Fly runs **`SKIP_CELERY=1`** on the web machine, so Celery Beat alone does not fire jobs. Secondary logic is automatic via:

| Mechanism | When | Config |
|-----------|------|--------|
| **In-app scheduler** | Every 24h, first run 60m after deploy | `ENABLE_SCHEDULED_SECONDARY_PASS=1` in `fly.toml` |
| **Cron HTTP** (backup) | External cron hits API | `GET /api/scraper/cron/run-secondary-pass?token=$SCRAPER_CRON_TOKEN` |
| **Celery Beat** | 05:00 UTC daily | Only when worker + beat run (`SKIP_CELERY` unset) |

In-app thread: `app/main.py` → `_scheduled_secondary_pass_loop` → `_run_secondary_pass_sync`.

## Schedule (UTC, Celery worker deployments)

```
02:30  rectify-crm-nightly
05:00  lead-secondary-pass-daily
06:00  rescore-all-companies
07:00  enrich-existing-companies
10:15  lead-research-daily
```

## Commands

```bash
PYTHONPATH=. python3 scripts/run_lead_secondary_pass.py --audit-only --limit 30
PYTHONPATH=. python3 scripts/run_lead_secondary_pass.py --limit 25 --no-rescore

curl -X POST "https://ready-2-robot.fly.dev/api/admin/leads/secondary-pass?limit=50" \
  -H "X-Admin-Key: $ADMIN_KEY"

# Cron (cron-job.org) — daily 05:00 UTC backup trigger
curl "https://ready-2-robot.fly.dev/api/scraper/cron/run-secondary-pass?token=$SCRAPER_CRON_TOKEN&limit=120"
```

## Code touchpoints

- Gap audit: `app/services/lead_gap_audit.py`
- Rescue orchestrator: `app/services/lead_secondary_pass.py`
- Assessment + rank: `app/services/lead_secondary_assessment.py`
- Contact fallback: `app/services/lead_enrichment.py`
- Admin trigger: `POST /api/admin/leads/secondary-pass`
- Celery: `worker/tasks.py` → `lead_secondary_pass_task`
