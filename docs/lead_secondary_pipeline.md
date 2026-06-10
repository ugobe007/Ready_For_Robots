# Lead secondary pipeline (missing-data rescue)

**North star order:** [lead_quality_north_star.md](lead_quality_north_star.md) — names/events first, then score, rank, specs.

Primary ingestion (scrapers) optimizes for **speed and coverage**. Secondary logic runs **decoupled** on a schedule to repair missing fields before scoring and delivery — same pattern as Pythh `batch-platform-daily.yml`.

## Architecture map (Pythh → Ready For Robots)

| Pythh layer | Ready For Robots |
|-------------|------------------|
| `automated-scraper.yml` (12h) | Celery Beat: intelligence/news/RSS/SERP/job scrapers (`worker/celery_beat_schedule.py`) |
| `startup_events` → `discovered_startups` | `signals` → `companies` (intake via scrapers + `is_valid_lead` gate) |
| `startup_uploads` (canonical corpus) | `companies` with `is_internal=True` after rectifier |
| `resolved_events` (idempotency) | `companies.crm_metadata.enrichment_ledger` |
| `holding-review-worker` | `rectify_and_enrich_crm_task` → `rectifier.validate` |
| `oracle-signal-backfill` | `research_active_leads_task` → `lead_research_agent` |
| `enrich-from-rss-news` (re-run) | `run_enrich_companies_task` + `run_company_news_task` |
| **`event-resolver.js` (rescue pass)** | **`lead_secondary_pass_task`** → `lead_secondary_pass.run_secondary_pass_batch` |
| `pythia-sage-review` | `lead_enrichment_agent.enrich_lead_with_agent` (agent QA pass) |
| `god-score-recalculation` (2h) | `rescore_all_companies_task` (daily 6:00 UTC + queued after secondary pass) |
| portfolio digest / newsletter | `refresh_public_surface_caches_task`, `incremental_newsletter_update_task` |

## Gap types audited

`app/services/lead_gap_audit.py` flags open gaps per lead:

| Gap | Rescue pass | Fills |
|-----|-------------|-------|
| `website` | `website_rescue` | `companies.website` (OpenAI → DuckDuckGo → brand slug) |
| `industry` | `industry_rescue` | `companies.industry` from name + signal text |
| `contact` | `contact_rescue` | `contacts` + outreach email (Apollo waterfall) |
| `crm_descriptors` | `crm_rescue` | `crm_metadata.budget`, `.timing`, `.automation_requirements` |
| `lead_inference` | `inference_rescue` | `crm_metadata.lead_inference` dossier |
| `low_signals` | `signal_backfill` | Additional signals via company news search |
| `unrectified` | `rectification` | Sniff test; quarantine on fail |
| `ontology_gaps` | `agent_qa` | `crm_metadata.agent_enrichment` + ontology candidates |

Candidates are ranked by intent score + gap severity (website/contact gaps weighted highest).

## Schedule (UTC)

```
02:30  rectify-crm-nightly          (gate + CRM extract on recent corpus)
05:00  lead-secondary-pass-daily     (gap-driven rescue — NEW)
06:00  rescore-all-companies        (reads enriched fields)
07:00  enrich-existing-companies    (signal backfill by staleness)
10:15  lead-research-daily          (HOT/WARM news agent, gated by env)
```

Secondary pass queues rescore when any leads were processed so scores reflect new website/contact/CRM fields.

## Idempotency

Each pass stamps `crm_metadata.enrichment_ledger[pass_name]`:

```json
{
  "status": "filled|skipped|failed|passed",
  "last_run": "2026-05-25T05:00:12+00:00",
  "fields_filled": ["website"],
  "detail": null
}
```

Default **24h cooldown** per pass prevents thrashing; failed passes may retry sooner.

## Commands

```bash
# Audit only — see gaps and suggested passes
python3 scripts/run_lead_secondary_pass.py --audit-only --limit 30

# Run rescue batch (local)
python3 scripts/run_lead_secondary_pass.py --limit 25 --no-rescore

# Celery (production worker)
celery -A worker.celery_worker call worker.tasks.lead_secondary_pass_task --kwargs='{"limit": 50}'
```

## Code touchpoints

- Gap audit: `app/services/lead_gap_audit.py`
- Rescue orchestrator: `app/services/lead_secondary_pass.py`
- Celery task: `worker/tasks.py` → `lead_secondary_pass_task`
- Beat entry: `worker/celery_beat_schedule.py` → `lead-secondary-pass-daily`

## What stays on the primary path

Scrapers still run light enrichment inline (`_maybe_enrich_website`, `enrich_limit` on intelligence runs). Secondary pass is the **authoritative rescue** for leads that missed fields during fast ingestion — do not block scrapers on Apollo/LLM latency.
