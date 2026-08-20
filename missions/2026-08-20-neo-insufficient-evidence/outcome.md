# Outcome: 1X NEO — insufficient robot evidence

**Date:** 2026-08-20
**Type:** build
**Status:** local verify pass; Fly deploy follows this commit

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

## Follow-ups

- Confirm production POST `/api/robot-job-search` after Fly deploy
- `claims_surface_cleaning` on a home humanoid is pre-existing extractor
  behavior, not this mission
