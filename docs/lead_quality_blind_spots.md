# Lead quality: blind spots and mitigations

**Goals:** [lead_quality_north_star.md](lead_quality_north_star.md).

Heuristic filters will always miss some edge cases: headlines are infinite, and scrapers invent new failure modes. This doc explains the **layers** we use and how to tighten the system without false confidence.

## Layers (defense in depth)

1. **`lead_filter.is_junk`** — Fast substrings and regexes. Prone to **false positives** (e.g. a real two-letter brand) unless **allowlisted** (`app/services/known_brands.py`).
2. **`company_validator.is_valid_lead`** — Junk filter + legal suffix + distinctive noun + **structural** checks + vendor/publication blocks.
3. **`classify_lead`** — Used by the leads API and spotlight: **`is_junk` + Target false-positive helper + full `is_valid_lead` (skip duplicate junk)** so HOT/WARM cannot bypass the logic engine.
4. **Ingest** (`intelligence_news_scraper._get_or_create_company`) — Classifier + **`is_valid_lead` with entity hint** before insert.

When cleanup (`scripts/cleanup_leads.py`) deletes rows, the purge phase uses **`is_valid_lead`** (full logic engine, not `is_junk` alone) so it stays aligned with ingest and the API.

## Operational hygiene

- **Export decisions** — `scripts/export_quality_decision_log.py` for offline review and new rules.
- **Bounded scraper runs** — `--max-queries` + `--limit` for smoke tests.
- **Supabase** — Prefer the **transaction pooler** (port **6543**) for heavy jobs; session pooler slots are limited (see warnings in scripts).

## Adding a rule

Prefer **exact or tight patterns** over huge substrings. When in doubt, add a **test** in `tests/test_lead_filter_junk.py` and a **counterexample** you must not break.
