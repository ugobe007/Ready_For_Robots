---
name: rfr-qualify-match
description: "Qualify RFR pipeline companies via the local inference engine. No paid LLM."
version: 0.2.0
author: Ready For Robots + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Robotics, Qualify, Inference, ReadyForRobots]
    related_skills: [rfr-job-orders, rfr-daily-email-digest]
---

# ReadyForRobots qualify + match

Score automation fit from **stored signals** using ReadyForRobots `lead_inference_engine` (rules + evidence). **Do not** look up companies on OpenAI or Anthropic.

## Forbidden

- `--provider ai-gateway` / OpenAI / Anthropic
- Inventing automation_fit, job titles, or decision-makers with an LLM

## Cron step

```bash
curl -sS -X POST "$RFR_API_BASE/api/v1/market-graph/infer-qualify" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{"limit": 20, "dry_run": false, "hermes_run_id": "qualify-cron"}'
```

That endpoint:

1. Reads company signals
2. Runs `evaluate_lead_candidate` + WORK reconstruction
3. Writes `company.crm_metadata.hermes_qualify` (`truth_state: HERMES_OVERLAY`)

Optional dry run: `"dry_run": true`.

Job ingest remains `POST /api/v1/market-graph/job-signals/ingest` with public job text you already fetched (web/terminal), not LLM-generated text.
