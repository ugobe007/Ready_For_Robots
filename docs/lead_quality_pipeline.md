# Lead quality pipeline and feedback loop

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
