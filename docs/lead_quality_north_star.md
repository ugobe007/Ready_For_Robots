# North Star: lead quality and pipeline goals

Sales value flows **downstream** from recognition. Scores, ranks, and automation specs are only trustworthy if **companies and events** are identified correctly first.

## Goals (strict order)

| Priority | Goal | What “good” looks like | Primary code touchpoints |
|----------|------|------------------------|---------------------------|
| **1** | **Names & events** | Real buyer-like **companies** in `companies`; factual **signals** in `signals` (not headline titles in the name field). | `lead_filter.is_junk`, `company_validator.is_valid_lead`, `text_classifier.classify`, `headline_parser` / intelligence extraction, `BaseScraper._name_is_valid` before insert |
| **2** | **Score events** | Each signal has a defensible **strength / relevancy** given clean text. | Scoring helpers (`calculate_relevancy_score` and related), signal writers |
| **3** | **Rank** | Ordering reflects business rules (score, freshness, diversity). | API / queries, `scores` usage |
| **4** | **Robot specs / opportunity** | **Industry + automation_profile** (and related rules) describe *what kind* of automation opportunity this is. | `industry_inference`, `automation_profile`, CRM-facing rules |

**Rule:** Invest in **(1)** before tuning **(4)**. Bulk relabeling industry (`cleanup_leads --force-industry`) without fixing bad names or noisy signals **amplifies noise** in the UI.

## Ingestion contract (non-negotiable)

- **Intelligence path:** classify → **`is_valid_lead(name, entity_hint=…)`** at insert — see `intelligence_news_scraper._get_or_create_company`.
- **Other scrapers:** **`BaseScraper._name_is_valid`** → `is_valid_lead(name)` before creating companies (e.g. news/serp/logistics variants).

If a new scraper writes `Company` rows, it must reuse **`is_valid_lead`** (with classifier hint when the scraper already classified the string) — never only a local regex.

## Feedback loop

1. Run **`scripts/export_quality_decision_log.py`** → JSONL for review / labeling.
2. Adjust **`lead_filter`**, **`text_classifier`**, or **`ontology`** weights — not only industry keywords.
3. Re-run **`scripts/cleanup_leads.py`** (purge + optional renames + profiles) after rule changes.
4. Keep heavy ML **off the hot path**; ship **reviewed** rule changes — see [lead_quality_pipeline.md](lead_quality_pipeline.md).

## Ingestion audit (engineering)

| Path | Gate |
|------|------|
| `BaseScraper.save_company` / `_name_is_valid` | `is_valid_lead` |
| `intelligence_news_scraper._get_or_create_company` | `classify` + `is_valid_lead(..., entity_hint=…)` |
| `news_scraper`, `serp_scraper`, `serp_scraper_enhanced`, `logistics_directory_scraper`, `news_scraper_enhanced` | `_name_is_valid` before insert |
| `worker/tasks.run_rfp_marketplace_scraper_task` | `is_valid_lead` before `Company` create |
| `POST /api/admin/import/companies` | `is_valid_lead` (aligned with scrapers; replaces `is_junk`-only) |

Scripts (`seed_*`, `emergency_recovery`, etc.) are operational — not hot-path ingestion.

## Related docs

- [lead_quality_pipeline.md](lead_quality_pipeline.md) — stage order, commands, export.
- [lead_quality_blind_spots.md](lead_quality_blind_spots.md) — why junk still slips through and how defenses stack.
