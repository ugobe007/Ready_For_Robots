# Outcome: Hermes local inference (no paid LLM)

**Date:** 2026-08-20
**Status:** complete

## What shipped

Paid OpenAI/Anthropic/AI Gateway lookups are off unless `RFR_ALLOW_PAID_LLM=1`.

- `llm_json_completion` / `active_provider` return None by default
- Company homepage OpenAI resolve is off
- Newsletter + industry brief use the heuristic engine
- Cal daily digest attaches that heuristic brief
- `POST /api/v1/market-graph/infer-qualify` qualifies via `lead_inference_engine`
- `POST /api/v1/market-graph/daily-digest-send` emails the digest without an LLM
- Hermes skills/docs: terminal `curl` only — never `--provider ai-gateway`

## Tests

```
/tmp/rfr-venv/bin/python -m pytest tests/test_paid_llm_gate.py tests/test_hermes_local_inference.py tests/test_lead_inference_engine.py tests/test_hermes_intelligence_ingest.py tests/test_cal_daily_digest.py tests/test_lead_primary_link.py -q
```

32 collected: 30 passed. Two pre-existing ingest dry-run failures (sqlite missing `companies` table) are unrelated.

## Operator follow-up

Reconfigure the Hermes cron **RFR daily email digest**:

- Remove `--provider ai-gateway` / Anthropic / OpenAI
- Run the skill `rfr-daily-email-digest` (curl Fly `daily-digest-send`)
- Qualify cron: curl `infer-qualify`
