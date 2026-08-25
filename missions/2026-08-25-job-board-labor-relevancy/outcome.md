# Outcome — operational titles persist as Robot Jobs

**Mission:** `missions/2026-08-25-job-board-labor-relevancy`

## What shipped

- Relevancy scoring now includes `LABOR_PAIN_KEYWORDS` (line cook, housekeeper, picker) so operational cards pass the 0.15 gate.
- Buyer/automation title regexes actually count (VP of Operations no longer scores 0).
- Robot-builder titles still score 0.
- SimplyHired `.SerpJob-jobCard` / `.jobposting-*` selectors.
- Page yield logs: `found / robot_jobs / skipped_relevancy`.
- Rejected company names still upsert a Robot Job (`company_id` null).

Jobs UI, matcher ranking, and intelligence news loop unchanged.

## Tests

`pytest tests/test_job_board_scraper_pipeline.py tests/test_robot_job_extract.py` — 17 passed.
