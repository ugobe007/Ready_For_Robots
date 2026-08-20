---
name: rfr-daily-email-digest
description: "Send RFR daily operator email via Fly. No OpenAI, Anthropic, or AI Gateway."
version: 0.2.0
author: Ready For Robots + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Robotics, Email, Digest, ReadyForRobots]
    related_skills: [rfr-sales-floor-manager, rfr-qualify-match]
---

# ReadyForRobots daily email digest

Send the operator digest by calling the ReadyForRobots API. **Do not** use OpenAI, Anthropic, or Vercel AI Gateway. A 402 from `ai-gateway` means this skill was misconfigured.

## Forbidden

- `--provider ai-gateway` / `--provider openai` / `--provider anthropic`
- Browsing api.openai.com, console.anthropic.com, or vercel.com/ai
- Drafting the email body with an LLM

## Required cron

Terminal-only. `deliver=local`. Workdir Ready_For_Robots.

```bash
curl -sS -X POST "$RFR_API_BASE/api/v1/market-graph/daily-digest-send" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $RFR_ADMIN_KEY" \
  -d '{"force": false, "period_hours": 24}'
```

Expect JSON with `"engine": "local_inference"` and `"paid_llm": false`. Fly builds the Cal digest + heuristic industry brief and emails it via Resend.

If `sent` is false and `reason` is `Already sent today`, that is success (idempotent).

## Fallback

In-app Cal digest already sends on a Fly scheduler. If curl fails, report the HTTP body — do not retry via a paid LLM provider.
