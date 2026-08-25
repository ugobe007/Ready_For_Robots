# Outcome — operational titles persist as Robot Jobs

**Mission:** `missions/2026-08-25-job-board-labor-relevancy`

## What shipped

- Relevancy scoring now includes `LABOR_PAIN_KEYWORDS` (line cook, housekeeper, picker) so operational cards pass the 0.15 gate.
- Title stems (Cook, Server, Warehouse Worker, EVS, Palletizer) count; the second exact-phrase `pain_score` gate no longer drops them.
- Buyer/automation title regexes actually count (VP of Operations no longer scores 0).
- Robot-builder titles still score 0. Generic GM is not persisted as a Robot Job.
- SimplyHired `.SerpJob-jobCard` / `.jobposting-*` selectors.
- JSON-LD `JobPosting` fallback when CSS cards are missing; fill company from JSON-LD.
- Operational `robot_job` URLs are scraped before buyer-persona URLs.
- Page yield logs: `found / robot_jobs / skipped_relevancy`.
- Rejected company names still upsert a Robot Job (`company_id` null). Persist counts only after a successful upsert.

Jobs UI, matcher ranking, and intelligence news loop unchanged.

## Tests

`pytest tests/test_job_board_scraper_pipeline.py tests/test_robot_job_extract.py`
