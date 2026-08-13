# Agent Improvement Log

Proposals from Hermes `rfr-workflow-improve` (and manual reviews). Newest first.

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
