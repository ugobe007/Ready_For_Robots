# Outcome: 1X NEO — insufficient robot evidence

**Date:** 2026-08-20
**Type:** build
**Status:** local verify pass; Fly deploy not run from this agent (no `flyctl` / `FLY_API_TOKEN`). Merge to `main` to ship via `.github/workflows/deploy.yml`.

## What was wrong

1X’s product page is Next.js. The sentence *“NEO is a fully electronic
humanoid robot”* lives in `application/json` / `__NEXT_DATA__`.
`_html_to_text` stripped every `<script>`, so v1 never saw `humanoid`.
Production also had `ROBOT_INFERENCE_ENGINE` off and reused a 6-hour
C/low cache (payload + IP only, morphology wrongly quadruped).

The Jobs UI was honest: no invented matches. Understanding failed to
ground manufacturer evidence.

## What we changed

- Collect JSON-LD / Next.js string claims into page text (source
  collection, not an extractor retune)
- Enable `ROBOT_INFERENCE_ENGINE=1` in Fly
- Do not cache or reuse `coverage_level=low` profiles
- Bump profile cache namespace to `robot_profile_v2`
- Remove IP + payload → quadruped
- Ground “works autonomously” as navigation evidence
- Humanoid / mobile-manipulator class emits `manipulate`

## Tests

```
python -m pytest tests/test_fetch_embedded_json.py \
  tests/test_robot_inference_engine.py \
  tests/test_tier_work_families.py \
  tests/test_robot_job_search.py \
  tests/test_zero_state.py -q
# 45 passed
```

## Local live compose (`https://www.1x.tech/neo`)

- `state`: matches
- `zero_reason`: None (was `insufficient_profile_evidence`)
- identity: 1X / Neo
- `product_class=humanoid`, `research_morphology=humanoid`
- capabilities: `dual_arm`, `manipulate`, `mobile`, `surface_clean`
- `coverage_level`: medium / B
- `job_count`: 40 (CNC load/unload, palletize, …)

## Follow-up: visual class + operator picker

If photos/text still cannot name a class, Jobs no longer dead-ends.
`state=qualify_robot` asks the operator to pick Humanoid / AMR / …
That selection is an explicit `product_class` fact; humanoid derives
`manipulate`, AMR derives `transport`, then jobs rematch.

- Manufacturer photo alts/filenames classify morphology (never SKU
  token `neo` → humanoid — Avidbots Neo is a scrubber)
- Optional vision ask is fail-open
- CLI: `python3 scripts/qualify_robot.py <product-url>`
- Jobs UI: class picker. Banned copy is gone:
  “We found _____, but we couldn't establish enough capability evidence
  to match it confidently”

```
./venv/bin/python -m pytest tests/test_robot_class_qualify.py \
  tests/test_fetch_embedded_json.py tests/test_robot_job_search.py \
  tests/test_zero_state.py tests/test_robot_inference_engine.py \
  tests/test_tier_work_families.py -q
# 55 passed
```

## Follow-ups

- Merge to `main` so GitHub Actions deploys Fly (`FLY_API_TOKEN` is a
  repo secret; this cloud VM has no Fly CLI)
- Confirm production `POST /api/robot-job-search` `{ "url": "https://www.1x.tech/neo" }`
  returns `state=matches` (or `qualify_robot` with a class picker — never
  the insufficient-evidence sentence)
- `claims_surface_cleaning` on a home humanoid is pre-existing extractor
  behavior, not this mission
