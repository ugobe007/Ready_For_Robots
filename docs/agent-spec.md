# Sales plan agent — specification

This is the **CRM copilot** spec. It is not Hermes. Hermes is retired ([`hermes_retired.md`](hermes_retired.md)). FIND does not call this agent.

This document defines the **role**, **inputs/outputs**, **guardrails**, and **implementation split** for the Ready For Robots CRM copilot. It aligns with these product decisions:

- **Org model:** **Teams** — all CRM entities are scoped to a `team_id` (or workspace); RLS and APIs enforce membership.
- **Company SSOT:** The **CRM account** (company) is the **system of record** for identity; **engagements** (opportunities/deals) are **separate rows** per sales motion so one customer can have multiple concurrent or sequential pursuits.
- **Model provider:** **OpenAI** for agent/plan generation (API keys server-side only). **Non–token paths** should use **deterministic inference** (rules, templates, scoring, retrieval) where appropriate to reduce cost and latency — the LLM is for judgment and synthesis, not for every branch.

---

## 1. Purpose

The agent helps reps **turn signals + context into an actionable, editable sales plan** — not to run outreach automatically or replace CRM updates.

**Success looks like:** structured plan → user review → **persisted tasks/notes** on the right account/opportunity, with traceability to signals.

---

## 2. Role (what the agent is and is not)

| The agent **is** | The agent **is not** |
|-------------------|----------------------|
| A **copilot** that proposes hypotheses, staged steps, risks, and talk-track bullets | A fully autonomous SDR or closer |
| **Grounded** in platform data (signals, tiers, industry) and user-supplied CRM fields | A source of private facts about individuals (names, emails) unless present in CRM |
| **Transparent** — every major recommendation should cite **which signals or fields** support it | A guarantor of ROI, legal outcomes, or closed-won |

---

## 3. Inputs (allowed)

Server-side only; never expose raw API keys to the browser.

**Required context (minimum):**

- `team_id`, `user_id` (actor)
- CRM **account** record (SSOT company): name, industry, any custom fields you store
- **Engagement** (opportunity) id: stage, value optional, name/description
- **Signals** attached to that account/lead linkage (types, text snippets, recency, scores) — as provided by your existing lead API

**Optional:**

- User’s short notes (ICP fit, competitive intel, “must-win” constraints)
- Playbook / workflow **template id** (if applying a template before or after LLM)
- Language / region (for tone only)

**Out of scope for v1 inputs:**

- Scraping the open web inside the agent call (unless you add a separate, audited tool later)

---

## 4. Outputs (structured — must validate)

The agent returns **JSON** matching a fixed schema (versioned, e.g. `plan_schema_version: 1`). Example sections:

- `executive_summary` (string, short)
- `hypothesis` (string) — why this account is winnable *now*
- `recommended_next_stage` (enum — must match your pipeline stages)
- `stakeholders` — array of `{ role, why_relevant, suggested_outreach_angle }` (roles, not names unless in CRM)
- `tasks` — array of `{ title, rationale, priority, due_offset_days, linked_signal_types[] }`
- `risks` — array of `{ risk, mitigation }`
- `talk_tracks` — short bullets for calls/emails
- `citations` — array of `{ signal_id or field, claim }` tying narrative to evidence

Downstream: **user edits** in UI → **commit** creates/updates `crm_tasks` / `crm_notes` with `source: agent` and stores `agent_run_id` for audit.

---

## 5. Guardrails

- **No fabrication:** If data is missing, say so and suggest **discovery tasks** instead of inventing facts.
- **Signal grounding:** Non-trivial claims should reference `citations` or be clearly labeled as **assumption**.
- **Safety & compliance:** No medical/legal/financial advice; no discriminatory targeting; keep outputs professional.
- **Rate limits / cost:** Cap context size; truncate old signals; batch non-LLM work in application code (see §7).

---

## 6. OpenAI usage (implementation notes)

- **Server-side** FastAPI route or worker: e.g. Chat Completions or Responses API with **JSON schema** / strict mode where available.
- **Store:** `agent_runs` table: `user_id`, `team_id`, `account_id`, `opportunity_id`, `model`, `prompt_version`, `input_hash`, `output_json`, `tokens_in`, `tokens_out`, `created_at`.
- **Secrets:** `OPENAI_API_KEY` in Fly secrets / env — not in Next.js `NEXT_PUBLIC_*`.

---

## 7. Inference engine vs LLM (non–token calls)

Use **deterministic logic** (your code) for:

- Pipeline **stage transitions** eligibility (rules)
- **Task instantiation** from playbook templates (no LLM)
- **Scoring / ranking** (reuse existing lead tier logic)
- **Deduplication** of tasks when regenerating a plan
- **Validation** of JSON output against schema; repair loop only if validation fails (optional second small call)

Use the **LLM** for:

- Synthesizing a **coherent narrative** plan from heterogeneous signals + CRM notes
- **Prioritization** and **wording** of tasks when templates are insufficient
- **Risk and talk-track** generation with citations

This keeps cost predictable and makes behavior testable without calling the model.

---

## 8. Phasing (recommended)

1. **CRM + team RLS + account + engagement** CRUD (no agent).
2. **Apply playbook → tasks** (rules only).
3. **Agent generate plan** (OpenAI + schema + commit flow + `agent_runs`).
4. Iteration: better prompts, streaming UI, optional tools (calendar, email) later.

---

## 9. Revision history

| Version | Date | Notes |
|---------|------|--------|
| 1 | 2026-04-04 | Initial spec: teams, SSOT company + engagements, OpenAI + inference split |
