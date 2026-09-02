# Cal is not performing

**Date:** 2026-09-01  
**Type:** research. No code rewrite. No deploy.  
**Branch:** `cursor/cal-agent-persona-research-009b` from `origin/main` @ `26fff643`  
**Product constraint:** EXPERIMENT_MODE freezes Cal-as-core. Jobs path stays FIND → Job Cards → CRM.

This is the review. `report.md` in this folder has URLs.

Spelling: the operator said Boardsy. The live product is **Boardy** at [boardy.ai](https://boardy.ai). Boardsi.com is a different company that matches executives to board seats. This review is about Boardy.

## Verdict

Cal fails because he is a name and a voice guide sitting on a frozen SIGNAL emailer. He is not a person with a job, tools, and a loop on the Jobs desk. Boardy works because he interviews you, remembers what you said, matches both sides, books the call, and stays in the thread. The missing piece is not a warmer personality. It is a job description plus tools that actually run plus a place he is allowed to speak. Recommended next build: after Open CRM, Cal asks the missing apply facts and prepares the employer draft. He does not sit on FIND and he does not send buyer mail.

## What's wrong with Cal today

The docs and the runtime do not agree on who he is. Then production turns him off. Users on the product path never meet him.

### 1. Three jobs, one name

`docs/cal_persona_spec.md` and `app/services/cal_persona.py` say Cal is a **jobs advisor**. He finds Robot Jobs a machine can do. He does not sell robots to operating companies.

`docs/cal_voice_and_persona.md` still says he is a **research and sales intelligence agent** who works both sides of the market: help factories buy robots, help OEMs find buyers.

`app/services/agent_messaging.py` still signs him as a **deployment sherpa for capturing qualified buyers**. `CAL_VENDOR_ROLE_LINE` is "help robot companies capture qualified buyers… instead of noisy list traffic."

`readyforrobots-new/client/src/lib/oemCalCopy.ts` is a third voice. OemCal on `/results` and `/signup` talks about matched **buyers** and unlocking 15 sales leads. BuyerCal in `cal_persona.py` is the outbound note. Floor Manager in `docs/skills/rfr-sales-floor-manager.SKILL.md` exists to keep those two from bleeding. That skill is retired with Hermes. The copy files are still there.

A named agent cannot perform when the company has not picked the job.

### 2. Production froze the only loop he had

That loop was SIGNAL outreach.

```
research/signals → draft → assembly gate → Resend intro → follow-up sequences
```

`fly.toml` has `CAL_AUTONOMY_ENABLED=0` and `ENABLE_SCHEDULED_CAL_AUTONOMY=0` since 2026-08-26. `CAL_BUYER_SALES_ENABLED` defaults off. `docs/hermes_retired.md` says buyer outreach is not the Jobs product. Scheduled draft create/refresh and due follow-ups stay paused. Tests lock the digest copy to "Cal sales outreach is frozen."

The daily digest in `app/services/cal_daily_digest.py` is now an operator status mail. Jobs-path counts, then "Cal sales must stay 0," then leftover HOT/WARM rows that are **not a send list.** Cal's surviving public act is telling the operator he is off.

`docs/cal_floor_manager_log.md` has never had a cron tick. Hermes was the hourly coach. Hermes is retired. Nobody is watching a floor.

### 3. He does not live where Jobs users work

FIND `/` has no Cal. A live GET of `https://readyforrobots.com/` does not mention him. The only "cal" hit in the HTML is Google Calendar OAuth on `/calendar`.

Jobs CRM is `JobsCrmDesk` on `/pipeline?src=jobs_activate`. Zero Cal strings. Tests in `jobsWorkflow.test.ts` assert Jobs chrome does **not** render `Cal queue` or `CalLeadDrop`. `docs/jobs_crm.md` says signup copy must not promise Cal. Employer scheduling is explicitly "not Cal, not Google Meet."

`ScoutChat.tsx` is a SIGNAL FAB that does not chat. It opens a modal that says "Activate SIGNAL." It is hidden on Jobs chrome. `PSTACK_CUSTOMER_CHAT_FORBIDDEN = true` in `pstackSite.ts`. pstack is the merge gate, not a customer bot. See `docs/pstack_jobs.md`.

The CRM copilot in `docs/agent-spec.md` and `app/services/sales_plan_agent.py` is a **fourth** agent. It generates a SIGNAL sales plan on `/crm` via `POST /api/crm/accounts/{id}/generate-plan`. Fallback tasks include "Send Cal intro" and "Validate via Apollo." `Crm.tsx` skips that whole desk when `src=jobs_activate`. Jobs users never hit generate-plan. SIGNAL users get a copilot that still thinks Cal is an SDR.

### 4. Voice without tools

Cal has an unusually thick persona.

- ~600-line voice guide
- six-dimension send rubric in `docs/CAL_LEARNING_SYSTEM.md`
- operator card `docs/cal_stage1_operator_card.md`
- corpus of **two** samples in `docs/cal_corpus/`: one Excellent PFG first-touch, one Not Cal label-stack
- learning log last written 2026-08-13
- assembly agent in `app/services/cal_assembly_agent.py` that reviews **email copy** before send

What he cannot do on Jobs CRM:

- open a kept job
- ask which task model the OEM will use
- fill the apply offer
- prepare the employer draft the operator already reviews
- hold an interview slot
- remember the last FIND SKU

He was built to talk about work. The product now is placing work. Those are different jobs.

### 5. Conversion docs still sell the old Cal

`docs/conversion_agent_challenges.md` still treats "full Cal draft visible before signup" on `/pipeline` as the value proof. That is SIGNAL. `docs/EXPERIMENT_MODE.md` freezes Cal. `docs/feature_map.md` says SIGNAL/Cal are frozen as core. `docs/agent-product-manager.md` says ProductManager is not a SIGNAL/Cal expansion agent.

The operator feels Cal is not performing because the daily mail says frozen, FIND never introduces him, CRM never uses him, and the leftover persona still sounds like a buyer SDR. That read is correct.

## What Boardy and peers do that we don't

### Boardy

[boardy.ai](https://boardy.ai) is a named person with one job: introduce you to someone useful, then make the meeting happen.

| Ingredient | Boardy | Cal today |
| --- | --- | --- |
| Job | Super-connector. Warm intros, then scheduling and follow-through. | Name on frozen outreach plus a Jobs-advisor rewrite that never shipped into a UI. |
| When he speaks | He calls you. LinkedIn, WhatsApp, email. You do not hunt for a chat widget on a marketing page. | Operator digest at 15:00 UTC. Admin autopilot switch. SIGNAL `/preview` lead drops. Not FIND. Not Jobs CRM. |
| Tools that run | Calendar connect, double-opt-in intro, book Google Meet, CC-on-thread scheduling, join Meet/Zoom/Teams. | Draft/send/follow-up to operating companies. Flags off. Assembly reviews copy. No Jobs tools. |
| Memory | He remembers what you told him on the last call. Next intro uses that. | Corpus of two emails. No per-OEM memory of kept jobs or task-model answers. |
| Trust | "Works for himself." He will not burn one side of the network to please the other. Double opt-in. | BuyerCal was supposed to be vendor-neutral. OemCal still claims buyers. Jobs path forbids that hop. |
| Does the work | Books Thursday at 11. Puts the invite on both calendars. | Writes a note about a warehouse, if anyone turns autopilot on. |

TechCrunch, 24 Oct 2024, describes the loop. You give Boardy a number. He calls. You say what you are building. He matches against people he has actually spoken with. Both sides opt in. The intro goes out by email. Andrew D'Souza said you cannot tell Boardy what to do, which is why people trust him. The 2026 Pro tier is explicit that the intro is 10% of the work. The other 90% is scheduling, showing up, and follow-up.

That is the pattern the operator is pointing at. A person who does a job in-product. Not a chat box with a name.

### Intercom Fin

Fin is a support agent with a **procedure**: when it runs, the steps, the tools, when to stop. Procedures combine natural-language instructions with Stripe/Shopify/Linear connectors. If the customer interrupts, Fin re-plans. If a human teammate sends a message, Fin's session ends. Simulations pass/fail a full conversation before the procedure goes live. Inbox folders: Resolved, Escalated, Pending. Unknown-resolution is "Fin only greeted." That is evaluation, not vibes.

Cal has a send rubric for emails. He has no simulation of "OEM opens CRM with five kept jobs and no task model." He has no interrupt rule because he is not in the conversation.

### Harvey

Harvey's line is "Delegate the work. Own the judgment." The unit is a **task**, not a prompt. Agents return cited, review-ready work product. Human approves the plan before it runs. Nudges pull the lawyer in when judgment is needed. Memory carries preferences across sessions. Connectors hit the firm's DMS. Ethical walls inherit from existing systems.

Cal's learning system sounds similar on paper: Research → Draft → Evaluate → Send → Observe → Learn. In production the Send step is illegal and Observe is a digest that celebrates zero intros. There is no "review-ready apply pack" for a kept Robot Job.

### Sierra

Sierra agents are brand-specific people who **complete transactions**: refund, exchange, update a subscription. Goals and guardrails are declared. Skills compose. Voice handles interruption. Handoff to a human includes a generated summary. They publish τ-bench because an agent that cannot use tools against a policy is a chatbot.

Cal has guardrails for what not to say in an email. He has no skill called `prepare_jobs_crm_apply` or `ask_task_model_source`.

### Claygent, as a warning

Claygent is a research column that browses the web and returns a schema. Useful. Also the shape of SIGNAL Cal: enrich a company, write copy, maybe send. Apollo sits in the CRM copilot fallback as contact validation. That is the hop EXPERIMENT_MODE forbids. Do not import Clay/Apollo as Cal's new personality. Import only the discipline: structured output, citation, permission to return "unknown."

### Cursor, analogy only

The Cursor agent is not a homepage chatbot. It has a job, tools that mutate the repo, a loop, a user queue that interrupts, and tests as evaluation. Use that as a shape. Do not put a Cursor-like agent on FIND. Jobs still come from `POST /api/robot-job-match`.

## What's missing

Persona is not a name. Persona is **job + tools + loop**, plus a room he is allowed to enter.

| Piece | What it means here |
| --- | --- |
| Job | One sentence the OEM would hire him for. "Help me apply these five kept jobs without sounding like a list broker." |
| Tools | Functions that change CRM state or produce a reviewable artifact: ask task-model source, attach PoC, quote rental, prepare apply draft, show employer thread. |
| Loop | Trigger → gather missing facts → act → human gate → observe. Same shape as Boardy understand/match/connect, Fin procedure, Harvey plan-then-run. |
| When he speaks | After Open CRM on a kept job, or when apply is missing a required field. Never on FIND. Never as a second home. |
| Memory | This robot, this SKU, last FIND, which jobs were kept, what task-model answer they gave. |
| Evaluation | Did the draft send? Did the employer reply? Did we ask a question we already knew? Not "did the email sound human." |
| Interrupt / handoff | Operator send button already exists. Keep it. Cal prepares. Human sends. Employer tokens stay human. |
| Voice | Keep the good Cal: complete sentences, evidence, no slogan stack. Point it at placement, not buyer intros. |

We already wrote a lot of voice. We never gave him the job the product now needs.

## Recommendation that stays on the Jobs path

Cal becomes the **Jobs floor manager / recruiter copilot on CRM after Open CRM**. Not a second home. Not SIGNAL. Not FIND chrome.

Tiny loop:

```
Open CRM → Cal sees kept jobs
  → for each job, ask what apply still lacks
       task-model source: named pack, we train, or unknown
       monthly rental, already required to Place
       PoC / video, preferred and skippable
  → prepare the employer draft the operator already reviews
  → human sends
```

The task-model question on draft PR #202 can be **this Cal prompt**, not a new Cal product and not a FIND intercept. Leave #202 draft. Do not undraft it for this research. If CRM-first landing fights the current desk listing, keep the desk. Steal only the question Cal should ask.

Reuse, do not rebuild:

- Apply prepare/send already lives in `docs/jobs_crm.md` F11. Operator reviews, then `POST /api/jobs-crm/applications/{id}/send`.
- Decline already asks a task-model reason code.
- `cal_persona.py` identity line already says jobs advisor. Point the LLM at apply drafts, not buyer intros.
- Digest already reports matcher / kept / applications. Next version can say "Cal asked 3 OEMs for a task model" instead of "intros sent: 0."

What this is not: unfreezing `CAL_AUTONOMY_ENABLED`. Not emailing operating companies. Not a chat FAB on `/`. Not generate-plan on SIGNAL accounts.

Size: one CRM-desk prompt plus wiring into the existing prepare-apply path. If the first slice cannot be described in one PR that a critic can drive FIND → cards → Open CRM → see Cal ask one question, it is too big. Stop.

## What not to do

- **Cal-as-core.** EXPERIMENT_MODE freezes him as a product hypothesis. A copilot on the desk after value is proven is allowed. A Cal homepage is not.
- **SIGNAL hop.** Do not send Jobs traffic to HOT buyers, Cal queue, `CalLeadDrop`, or `/pipeline` without `src=jobs_activate`. Claygent/Apollo stay off this path.
- **Generic chatbot on FIND.** Matcher stays code. pstack stays off the page. ScoutChat stays frozen and hidden on Jobs chrome.
- **Unfreeze buyer autonomy** so Cal "has something to do." Zero robot-sales intros is the correct number.
- **Rewrite the 600-line voice guide** and call it a fix. Voice is not the bottleneck.
- **Stand up Hermes or Floor Manager cron** as a Jobs agent.
- **Merge or undraft #202** from this research. CRM-first stays on its own branch.
- **Merge #195 / #197.** Out of scope.
- **Deploy.** Out of scope.

## Next build

One sentence: on Jobs CRM after Open CRM, Cal asks the missing apply facts, including task-model source, and prepares the employer draft the operator already reviews.

Evidence for a later Act PR would be a signed desk with kept jobs where Cal asks one question and the apply draft updates. Not a new home. Not a chat on `/`.
