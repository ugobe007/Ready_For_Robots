# Cal agent personas — sources

**Date:** 2026-09-01  
**Mission:** `missions/2026-09-01-cal-agent-personas/`  
**Review:** `REVIEW.md`  
**Live FIND check:** GET `https://readyforrobots.com/` 2026-09-01. No Cal product copy. Only `/calendar` OAuth in the HTML.

Operator said "Boardsy." Live product researched: **Boardy** (`boardy.ai`). Also noted so it is not mixed in: **Boardsi** (`boardsi.com`) is board-seat matchmaking.

## Repo evidence, Cal today

| Claim | Where |
| --- | --- |
| Jobs advisor identity | `docs/cal_persona_spec.md`, `app/services/cal_persona.py` `CAL_IDENTITY` |
| Sales-intelligence identity | `docs/cal_voice_and_persona.md` §§1–3, §21 |
| Buyer-capture vendor lines | `app/services/agent_messaging.py` `CAL_VENDOR_*` |
| OemCal buyer copy | `readyforrobots-new/client/src/lib/oemCalCopy.ts` |
| OemCal vs BuyerCal split | `docs/skills/rfr-sales-floor-manager.SKILL.md`, `docs/hermes_cal_bridge.md` |
| Autonomy off | `fly.toml` `CAL_AUTONOMY_ENABLED=0`, `ENABLE_SCHEDULED_CAL_AUTONOMY=0` |
| Buyer sales default off | `app/services/cal_autonomy.py` `cal_buyer_sales_enabled()` |
| Hermes retired, Cal not Jobs | `docs/hermes_retired.md` |
| Digest frozen copy | `app/services/cal_daily_digest.py`, `tests/test_cal_daily_digest.py` |
| Floor manager never ticked | `docs/cal_floor_manager_log.md` |
| Jobs CRM has no Cal | `readyforrobots-new/client/src/components/JobsCrmDesk.tsx`, `docs/jobs_crm.md`, `jobsWorkflow.test.ts` |
| ScoutChat is SIGNAL, not chat | `readyforrobots-new/client/src/components/ScoutChat.tsx` |
| Customer pstack chat forbidden | `readyforrobots-new/client/src/lib/pstackSite.ts` `PSTACK_CUSTOMER_CHAT_FORBIDDEN` |
| pstack is release gate | `docs/pstack_jobs.md` |
| CRM copilot is SIGNAL sales plan | `docs/agent-spec.md`, `app/services/sales_plan_agent.py`, `Crm.tsx` `generate-plan` |
| Copilot fallback still Apollo / Cal intro | `app/services/sales_plan_agent.py` `_fallback_plan` |
| Cal freeze as core | `docs/EXPERIMENT_MODE.md`, `docs/feature_map.md`, `docs/agent-product-manager.md` |
| Conversion still values Cal drafts on SIGNAL pipeline | `docs/conversion_agent_challenges.md` |
| Learning system / corpus | `docs/CAL_LEARNING_SYSTEM.md`, `docs/cal_corpus/README.md`, `docs/cal_learning_log.md` |
| Assembly reviews email, not Jobs actions | `app/services/cal_assembly_agent.py` |
| Task models are QUALIFY, not Cal | `docs/robot_task_models.md` |
| Apply already operator-reviewed | `docs/jobs_crm.md` F11 |
| #202 task-model question | https://github.com/ugobe007/Ready_For_Robots/pull/202 draft. Do not undraft from this mission. |
| Prior Cal digest freeze | `missions/2026-08-27-cal-jobs-digest/outcome.md` |

## Boardy

| Source | URL | Used for |
| --- | --- | --- |
| Product | https://boardy.ai | Job, understand/match/connect, calendar, CC-on-thread, join meetings, first-person copy |
| TechCrunch pre-seed | https://techcrunch.com/2024/10/24/ai-networking-startup-boardy-raises-3m-pre-seed/ | Voice call loop, double opt-in, "works for himself," cannot be ordered against the network |
| Boardy Pro explainer | https://blastra.io/blog/boardy-ai-networking-guide/ | Intro is 10% of work; Pro does scheduling, join-call, notes, follow-up; LinkedIn / phone / WhatsApp |
| Career posting using Boardy as hiring agent | https://capd.mit.edu/jobs/boardy-ai-founding-go-to-market/ | After apply, candidate talks to Boardy; Boardy schedules the screen. Named agent does recruiting work. |

## Boardsi, not the operator's example

| Source | URL | Note |
| --- | --- | --- |
| FAQ | https://boardsi.com/faq/ | Hybrid AI + human board-seat matchmaking. Different company. |
| Board Suite | https://boardsi.com/the-board-suite/ | AI as back-office matcher, humans still place. |

## Intercom Fin

| Source | URL | Used for |
| --- | --- | --- |
| Procedures | https://www.intercom.com/help/en/articles/12495167-fin-procedures-explained | Job = resolve the ticket. Tools = connectors. Interrupt = re-plan. Simulations = eval. Handoff. |
| Workflows + Fin | https://www.intercom.com/help/en/articles/10032299-use-fin-ai-agent-in-workflows | Human message stops Fin. Do not let Fin re-enter a teammate thread. |
| Inbox views | https://www.intercom.com/help/en/articles/7860256-view-fin-ai-agent-s-conversations-from-the-inbox | Resolved / Escalated / Pending / unknown-resolution. |
| Fin Agent API | https://developers.intercom.com/docs/guides/fin-agent-api.md | Status machine: thinking, replying, awaiting_user_reply, complete, escalated. |

## Harvey

| Source | URL | Used for |
| --- | --- | --- |
| Agents product | https://www.harvey.ai/platform/agents | Delegate work, own judgment. Plan preview. Nudges. Citations. Memory. Connectors. |
| Introducing agents | https://www.harvey.ai/blog/introducing-harvey-agents | Workflows = goal + agents. Task not prompt. |
| Agents for legal work | https://www.harvey.ai/blog/ai-agents-for-legal-work | Work product is the output. 500+ pre-built agents. Custom builder. |
| Ethical walls | https://www.harvey.ai/blog/agents-and-ethical-walls | Inherit existing access rules. Do not invent a parallel permission system. |

## Sierra

| Source | URL | Used for |
| --- | --- | --- |
| Agent SDK | https://sierra.ai/product/agent-sdk | Goals, guardrails, composable skills, simulations, action tools, contact-center handoff with summary |
| τ-bench | https://sierra.ai/uk/blog/benchmarking-ai-agents | Eval = tools + policy + user simulator, not chat quality |
| Secondary guides | https://www.getmacha.com/blog/sierra-ai-complete-guide , https://cybernews.com/ai-tools/sierra-ai-review/ | Transactions not answers. Brand-specific agent. Voice interruption. |

## Claygent / Apollo, negative space

| Source | URL | Used for |
| --- | --- | --- |
| Claygent research | https://www.clay.com/guides/how-to-use-claygent-for-prospect-research | Structured schema, citation, permission to return Not found |
| Claygent Builder | https://university.clay.com/docs/claygent-builder | Skills = methodology. Still GTM enrichment. Do not hop SIGNAL. |

Apollo is named only as what the CRM copilot fallback still suggests in `sales_plan_agent.py`. No Apollo product URL in the recommendation.

## Cursor

Internal analogy only. No Cursor marketing URL required. Shape: job, tools, loop, interrupt queue, tests. Not a FIND chatbot.

## What this mission did not do

- No Cal rewrite in `app/` or `readyforrobots-new/`
- No `CAL_AUTONOMY_ENABLED` flip
- No merge or undraft of #202, #195, #197
- No Fly/Vercel deploy
- No `reports/` commit
