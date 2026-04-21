# Lead quality pipeline and feedback loop

**Product goals (why this order exists):** [lead_quality_north_star.md](lead_quality_north_star.md).

This document matches the intended processing order for scraped and CRM-derived company names.

## Ordered stages

1. **Junk filter** (`app/services/lead_filter.py` — `is_junk`)  
   Fast regex and substring rules for obvious scraper noise, publications, and headline stubs.

2. **Logic engine** (`app/services/company_validator.py` — `is_valid_lead`)  
   Structured gates: junk (again), legal suffix fast-pass, generic-word / distinctive-noun check, structural headline checks, robotics vendor block, publication block. Optionally consumes a **text classifier hint** so the classifier does not run twice on the hot path.

3. **Run scripts** (operational layer)  
   Bounded scraper runs (`scripts/run_intelligence_scraper.py` with `--max-queries`), lead cleanup (`scripts/cleanup_leads.py`), audits (`scripts/audit_junk_names.py`, `scripts/scan_headline_fragment_names.py`), and exports for review.

4. **Logic engine (again)**  
   After cleanup or rule changes, re-evaluate remaining rows: same `is_valid_lead` contract, optionally with `classify()` passed as `entity_hint` when ingesting or when batch-auditing stored names.

5. **ML training on logs** (offline, iterative)  
   Export decisions with `scripts/export_quality_decision_log.py` to JSONL. Each line includes `is_junk`, classifier outputs, and `is_valid_lead` with and without the classifier hint. Human labels or error analysis feed back into:

   - new `is_junk` substrings/patterns or `_JUNK_EXACT` entries;
   - `text_classifier` template tweaks;
   - ontology / relevancy weights used by scrapers and scoring.

Keep training **off the request path**: export → notebook or training job → reviewed rule/weight changes → pytest → bounded scraper smoke.

## Commands (cheat sheet)

```bash
# Audit what the junk filter would still flag
python3 scripts/audit_junk_names.py --limit 200

# Purge junk names, optional headline renames, rebuild profiles; skip industry unless intentional
python3 scripts/cleanup_leads.py --apply --skip-industry

# Export for ML / spreadsheet review (stderr shows line count; stdout is JSONL only if -o omitted)
python3 scripts/export_quality_decision_log.py -o data/quality_log.jsonl --since-id 5700

# Automated checks for the record shape (CI)
python3 -m pytest tests/test_quality_decision_log.py -q
```

Record layout is implemented in `app/services/quality_decision_log.py` (`build_decision_record`); the script is a thin DB cursor over that function.

Why junk can still slip through sometimes — and how we layer defenses: **[lead_quality_blind_spots.md](lead_quality_blind_spots.md)**.

## Ingestion reference

`app/scrapers/intelligence_news_scraper.py` runs the text classifier first, then **`is_valid_lead(name, entity_hint=…)` immediately before insert** in `_get_or_create_company` (so the logic engine cannot be bypassed at persistence). Extraction still uses `is_valid_lead` in `_accept_company` without a hint; the insert-time pass uses the hint and matches production behavior.

## Inference engine — where `is_valid_lead` / `classify` run

| Location | What runs |
|----------|-----------|
| `app/scrapers/intelligence_news_scraper.py` | `text_classifier.classify(name)` then `is_valid_lead(name, entity_hint=tc)` before persisting companies. |
| `app/scrapers/base_scraper.py` | `is_valid_lead(name)` on extracted names. |
| `app/services/company_validator.py` | **`is_valid_lead`** — main gate (junk, legal suffix, classifier inference when no hint, distinctive word, structure, optional Wikidata/DNS, vendor/publication blocks). **`classify`** is invoked inside when `entity_hint` is absent. |
| `app/services/lead_filter.py` → `classify_lead` | Calls `is_valid_lead` with `skip_junk_check=True` so listing tiers align with the same engine. |
| `app/api/leads.py` | Uses `classify_lead` for tier/junk on API responses (not re-running full insert pipeline). |
| `app/api/admin.py` | `is_valid_lead` on CSV import rows. |
| `worker/tasks.py` | `is_valid_lead` in batch maintenance. |
| `app/services/headline_parser.py`, `sentence_parser.py`, `rectifier.py`, `quality_decision_log.py` | Various validation / audit paths. |

Operational export: `scripts/export_quality_decision_log.py` records `classify` + `is_valid_lead` with and without hints per row.

## OpenAI homepage hints (before generic web search in the UI)

When **`COMPANY_URL_OPENAI_RESOLVE=1`** and **`OPENAI_API_KEY`** are set, `app/api/leads.py` batches unresolved company names (no `website`, no http signal `source_url`) through **`app/services/company_url_openai.py`**, and passes the result into **`enrich_lead_link_fields`** as `llm_resolved_url`. The API then sets **`primary_link_url`** / **`primary_link_kind: inferred_openai`**, so the Next.js layer uses a real https link instead of falling through to DuckDuckGo.

Optional: **`COMPANY_URL_OPENAI_MODEL`** (default `gpt-4o-mini`), **`COMPANY_URL_OPENAI_CACHE_SEC`** (in-process URL cache TTL).

Fast DB purge of regex junk only (does not run the full classifier on every row):

```bash
python3 scripts/cleanup_leads.py --apply --purge-junk-only --skip-industry
```
