# Agent Improvement Log

Proposals from Hermes `rfr-workflow-improve` (and manual reviews). Newest first.

## 2026-08-24 — Mac Hermes status (proceed)

### Findings

- `hermes status` on the Mac: gateway running, **12/12 jobs**, **0 chat sessions**. OpenAI + Anthropic set. **Gemini not set.** Model is Anthropic `claude-opus-4-6`. Email home `ugobe07@gmail.com`. Nous Portal has no paid credits.
- Cloud cannot attach to that TUI. Status CLI is not a chat thread.
- Live Fly after deploy: tracks 8–10 on OpenAPI; `loop.healthy` true. Pipeline still 5/5 qualify, 2 DM overlays, 0 buying-window/video until Mac crons POST. Merge #113 so `main` matches Fly.

### Ranked proposals

1. **[done]** Fly deploy from this branch: tracks 8–10 on production OpenAPI; `loop.healthy` true. Merge PR #113 so `main` matches Fly. — owner: `deploy`
2. **[H/L]** Smoke tracks 8–10 dry_run on Fly (this cycle). Real buying-window/video overlays still need Mac crons. Do not flip `CAL_INCLUDE_BUYING_WINDOW`. — owner: `hermes`

## 2026-08-23 — Hermes workflow test (Sunday)

### Findings

- Hermes ingest **auth works**. Unauth 403, fingerprint 401, JWT 401. GitHub `ADMIN_KEY` = Fly `ADMIN_KEY` = Hermes `RFR_ADMIN_KEY`.
- Public pipeline **5/5 `hermes_qualify`** after infer-qualify on live IDs + cache rebuild (23:18Z). Job titles / buying windows / video still empty until tracks 8–10 deploy.
- Market graph snapshot **completed** 23:04Z: 8 tensions, 40 matches, 7 work units (Knowledge layer). Web `scheduler.last_run` is empty by design; heartbeat is snapshot `generated_at`.
- GHA Cal digest last failed 403 at 15:12Z (before the key was proven). Next scheduled send is the retest.
- Qualify/contacts `dry_run` used to query `companies` even when `dry_run=true` (fixed this cycle).

### Done (this cycle)

- Skip DB on qualify/contacts dry_run.
- Implement buying-window + video ingest + seed-targets.
- Health probe now checks ingest auth + documented routes.

### Ranked proposals

1. **[done]** GitHub `ADMIN_KEY` matches Fly (GHA run `32672185240`: cal-status 200, infer-qualify apply accepted 12). Same string as Hermes `RFR_ADMIN_KEY`. If it diverges, `hermes-fly-smoke.yml` fails.
2. **[H/M]** Deploy market-graph ingest (this PR) so tracks 8–10 exist on Fly. — owner: `deploy`
3. **[done]** infer-qualify on public pipeline IDs + cache refresh. Public GET 23:18Z: 5/5 `hermes_qualify` (Accor, Stellantis, MGM, Dubai Airports, Zoox).
4. **[ignore / upstream]** `hermes doctor` npm hits on `web` + `ui-tui` are Hermes Agent devDependency advisories ([#68736](https://github.com/NousResearch/hermes-agent/issues/68736)), not RFR. `hermes setup` is Nous/LLM keys; `RFR_ADMIN_KEY` already authenticates.

## 2026-08-23 — Hermes is not reaching Fly

### Findings

- Public pipeline (5 leads, `built_at` 2026-08-23) has **empty** `hermes_qualify` / job titles / DMs / buying windows / video evidence.
- Floor manager log still says “Awaiting first cron tick” (skill stood up 2026-08-14). Hourly `rfr-sales-floor-manager` has not written.
- GHA **Cal daily digest** failed HTTP **403** on 2026-08-20/21/22. `ADMIN_KEY` is set in Actions but Fly rejects it (`Invalid X-Admin-Key or token`). Common cause: GitHub secret is the 16-char `fly secrets list` digest, not the real `ADMIN_KEY`.
- Hermes Mac crons still likely pinned to `--provider ai-gateway` (HTTP 402, 2026-08-20). Skills in-repo are terminal `curl` only; the Mac job list was never confirmed.
- **`ADMIN_KEY` is not a Supabase secret.** Gemini is correct that Supabase has no such key. Fly `ADMIN_KEY` = Hermes `RFR_ADMIN_KEY` (homemade random string). `SERVICE_ROLE_KEY` is a different JWT. `fly ssh … printenv ADMIN_KEY` is not how you retrieve it — push `RFR_ADMIN_KEY` to Fly with `fly secrets set`.

### Done (this cycle)

- Ingest auth (`_require_ingest_auth`) rejects the 16-char fingerprint with an explicit message.
- GHA digest prints the Fly error body instead of a bare curl 403.

### Ranked proposals

1. **[H/L]** On the Mac: `fly secrets set "ADMIN_KEY=${RFR_ADMIN_KEY}" -a ready-2-robot` (after `fly auth login`). Do not send `SERVICE_ROLE_KEY`. Then `hermes doctor --fix`, `hermes gateway start`, `hermes cron list` — remove `--provider ai-gateway`.
2. **[H/L]** GitHub Actions `ADMIN_KEY` = that same Hermes `RFR_ADMIN_KEY` (not the `fly secrets list` fingerprint, not the service_role JWT).
3. **[M/L]** After auth works, POST `/api/v1/market-graph/infer-qualify` once so overlays appear on pipeline.

## 2026-08-20 — Stop paid LLM lookups (Hermes 402)

### Findings

- Cron `RFR daily email digest` failed HTTP 402 on Vercel AI Gateway (no credit, including BYOK).
- Hermes skills were pinned to `--provider ai-gateway --model anthropic/claude-sonnet-4.6`, which spends tokens on OpenAI/Anthropic sites for lookups we already run locally.
- Industry brief, newsletter force-rebuild, and company URL resolve still called paid providers when keys were present.

### Done

- Paid LLM gated behind `RFR_ALLOW_PAID_LLM` (default off) in `llm_client.llm_json_completion` / `active_provider`.
- Company OpenAI URL resolve disabled unless that flag is on.
- Newsletter + industry brief use heuristic / inference engine.
- New Fly endpoints: `POST /api/v1/market-graph/infer-qualify`, `POST /api/v1/market-graph/daily-digest-send`.
- Hermes must curl those endpoints with terminal tools only — never AI Gateway.

### Ranked proposals

1. **[H/L] DONE** Digest send is owned in-repo: Fly in-process (web backup when `SKIP_CELERY=1`) + Celery Beat + GitHub Action `cal-daily-digest.yml`. Hermes AI Gateway cron is retired. — owner: `fly`
2. **[M/L]** Confirm Fly secrets do **not** need `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for digest/qualify. — owner: `ops`

## 2026-08-13 — Commercial maturity thesis

### Findings

- Matching supply/demand is secondary. Asymmetry is **commercial maturity**: buyers often outpace young robot companies in deployment knowledge.
- Brand dual meaning: customer ready for robots *and* robot company ready for the customer.
- Cal = commercial judgment layer, not AI SDR. **R1 × C4** is high risk without coaching.
- Third axis: **Opportunity Maturity** (Signal → Scale) changes the next conversation even when R and C are fixed.

### Done

- Spec IP v1.1: `docs/commercial_maturity_models.md` — R1–R4 + RCMS, C1–C4 + CAMS, O1–O9, 4×4 matrix
- Mission: `missions/2026-08-13-commercial-maturity-models/`
- PMF / thesis / competitive / Cal docs updated

### Ranked proposals

1. **[H/M]** Manual-tag 20 robot companies (R) + 20 buyers (C) + sample opps (O); validate matrix cells. — owner: `product`
2. **[M/M]** Cal coaching by (R,C,O); warn R1 × C4 before send. — owner: `cal`
3. **[M/L]** Implement RCMS / CAMS from deployments + public evidence. — owner: `engineering`

## 2026-08-13 — Cal Learning System

### Findings

- Optimizing copy alone is insufficient. Cal needs a loop: Research → Draft → Evaluate → Send → Observe → Learn → Update.
- Operator corrections (label stacks, missing intro, billboard openers) are generalizable rules, not one-off rewrites.
- Voice must not manufacture Intelligence; Accuracy stays a separate gate from the 6-dimension voice score.

### Done

- Spec: `docs/CAL_LEARNING_SYSTEM.md`
- Log: `docs/cal_learning_log.md` (seeded with today's rules)
- Corpus: `docs/cal_corpus/` (PFG Excellent + label-stack Not Cal)
- Persona spec updated to reference learning system + golden intro shape

### Ranked proposals

1. **[H/M]** Stage 1 manual: score drafts before send; append every correction to the learning log. — owner: `cal`
2. **[M/M]** Stage 2: pre-send LLM/human rubric gate (≥24/30 + Accuracy pass). — owner: `engineering`
3. **[M/L]** Grow corpus to 50–100 Excellent examples by situation/audience. — owner: `cal`

## 2026-08-13 — Conversion + Cal curiosity

### Findings

- Anonymous `/pipeline` drafts were **client-built** (`pipelineLeadMap`) with salesy “Hey / Find Companies Ready For Robots” — not Cal server templates. Fixed to Cal curiosity voice.
- Server buyer variants were consultant sermons (Robert/RFQ closes). Rewritten to ~100-word curiosity peers.

### Done

- Mission `missions/2026-08-13-conversion-cal-curiosity/`
- Cal variants + persona + tests; later replaced by operator-approved conversational golden (PFG)
- Digest-winner qualify overlays ×7 (PFG, Medline, DHL, HelloFresh, FedEx, Apple, GM)
- `CAL_INCLUDE_BUYING_WINDOW` still off

### Ranked proposals

1. **[H/L]** `vercel login` then `vercel --prod` in `readyforrobots-new/` if custom domain is still Vercel. — owner: `deploy`
2. **[M/M]** Watch `/pipeline` signup starts this week; iterate Cal samples from OEM feedback. — owner: `product`
3. **[L/M]** After buying-window overlays look good, flip `CAL_INCLUDE_BUYING_WINDOW=1`. — owner: `cal`

### Findings

- Anonymous `/pipeline` drafts were **client-built** (`pipelineLeadMap`) with salesy “Hey / Find Companies Ready For Robots” — not Cal server templates. Fixed to Cal curiosity voice.
- Server buyer variants were consultant sermons (Robert/RFQ closes). Rewritten to ~100-word curiosity peers.

### Done

- Mission `missions/2026-08-13-conversion-cal-curiosity/`
- Cal variants + persona + tests (35 passed); Fly deploy live
- Digest-winner qualify overlays ×7 (PFG, Medline, DHL, HelloFresh, FedEx, Apple, GM)
- `CAL_INCLUDE_BUYING_WINDOW` still off

### Ranked proposals

1. **[H/L]** `vercel login` then `vercel --prod` in `readyforrobots-new/` if custom domain is still Vercel. — owner: `deploy`
2. **[M/M]** Watch `/pipeline` signup starts this week; iterate Cal samples from OEM feedback. — owner: `product`
3. **[L/M]** After buying-window overlays look good, flip `CAL_INCLUDE_BUYING_WINDOW=1`. — owner: `cal`

## 2026-08-12 — Credits restored; buying-window track started

### Findings

- AI Gateway credits topped up; manual job-orders / qualify / DMs / vendor-news succeeded ~06:15–06:29 PT.
- Scheduled ticks also healthy: job-orders 07:08 (8 accepted), qualify 08:34 (PFG 82 HOT, Medline 65 WARM; XPO skipped as contaminated), DMs 10:07, vendor-news 11:07.
- **Deployment-evidence 06:00 FAILED** on HTTP 402 (pre-top-up). Manual re-run 15:33 **succeeded** → `[SILENT]` (no new public deployment hits).
- Evening digest (`24b6229d3a4e`) still due ~18:00 PT → `email:ugobe07@gmail.com`.

### Done

- Spec: `docs/buying_window_intelligence_v0_1.md` — FY / trade shows / peer FOMO as **urgency ≠ fit**.
- Skill draft: `docs/skills/rfr-buying-windows.SKILL.md` (installed under `~/.hermes/skills/research/rfr-buying-windows/`).
- Re-ran deployment-evidence cron `4396dcf22338` after credits restored (`[SILENT]`).
- Shipped `POST /api/v1/market-graph/buying-window-overlay` + Cal `prioritize_buying_window` behind `CAL_INCLUDE_BUYING_WINDOW` (default off).
- Evening digest 2026-08-12 delivered (Eli Lilly / Apple / GM jobs; PFG+Medline qualify; Agility Digit V5 + Figure BMW escalations).

### Ranked proposals

1. **[H/M]** Deploy Fly so buying-window ingest is live; run first `rfr-buying-windows` tick. — owner: `deploy` / `hermes`
2. **[M/M]** After overlay quality review, set `CAL_INCLUDE_BUYING_WINDOW=1` on Fly. — owner: `cal`
3. **[M/L]** Locus-city DC operator qualify pass (carry from 08-11). — owner: `hermes`
4. **[L/L]** Optional: morning digests → email (evening already does). — owner: `hermes`

## 2026-08-11 — Locus / Nimble buyer chase (no LLM)

Manual follow-up from job-orders digest `7ea352deba2c` (2026-08-10). AI Gateway credits deferred → research done without Hermes tick.

### Findings

- **Nimble Burlington, NJ** is Nimble’s **own robotic 3PL** (opened ~2024-09), not a customer-owned DC. Maker-operated. Public brand customers include BlendJet, Steeped Coffee; strategic alliance with **FedEx Fulfillment**.
- **Locus onsite engineer cities** (Southaven MS, Fort Worth TX, Las Vegas NV, North East MD, Louisville KY) are customer sites but **customer names are not public** in the job posts. Prior deployment evidence already ties Locus → DHL Supply Chain / HelloFresh.
- CRM presence (Fly `/api/leads?search=`): **DHL Supply Chain** `#348` HOT; **FedEx Ground** `#407` HOT; **Schnucks** `#7771` HOT. Missing: HelloFresh, BlendJet, Steeped Coffee, Locus/Nimble as vendor rows (expected — buyers matter more).

### Done

- Seeded buyers via market-graph ingest (`hermes_run_id=buyer-chase-seed-2026-08-11`):
  - **HelloFresh** `#11034` — Hermes fit 82 · Locus · scored **HOT** (71.1)
  - **BlendJet** `#11035` — Hermes fit 74 · Nimble 3PL · scored **HOT** (57.1)
  - **Steeped Coffee** `#11036` — Hermes fit 72 · Nimble 3PL · scored **HOT** (68.2)

### Ranked proposals

1. **[H/M]** Prioritize Cal pool / Pipeline on **DHL Supply Chain** + **FedEx Ground** with Hermes/deployment context (Locus + Nimble/FedEx). — owner: `cal` / ops
2. ~~Seed HelloFresh / BlendJet / Steeped~~ — done (landed HOT, not WARM)
3. **[M/L]** After credits restored, re-run qualify-match focused on DC operators in the five Locus cities (not Locus itself). — owner: `hermes`
4. **[L/L]** Optional: route morning Hermes digests to `email:ugobe07@gmail.com` (evening digest already does). — owner: `hermes`
5. **[L/L]** Set websites on `#11034–11036` (currently null) + normalize industry labels. — owner: `ops`

## 2026-08-10 — Initial intelligence loop standup

### Findings

- Deployment evidence cron is live and ingesting (oem-core).
- New tracks (jobs, qualify, DMs, vendor news) shipped as Hermes skills + RFR ingest APIs.
- Gateway LaunchAgent exists but may not be loaded after reboot — cron depends on a running gateway process.

### Ranked proposals

1. **[H/L]** Confirm `hermes gateway start` / LaunchAgent loaded after reboot so 6–11am jobs fire. — owner: `hermes`
2. **[H/M]** After first job-orders tick, verify Pipeline shows `hermes_job_order` signals + Work Match overlays. — owner: `rfr-api` / product
3. **[M/M]** Expand OTTO / Rockwell query seeds (deployment tick often finds nothing). — owner: `hermes` watch files
4. **[M/L]** Pin all new crons to `ai-gateway` + `anthropic/claude-sonnet-4.6` (avoid spend-skip on drift). — owner: `hermes`
5. **[L/M]** Surface `hermes_qualify` overlay on pipeline lead detail (read-only badge). — owner: `frontend`
