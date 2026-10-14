# Ready For Robots — Agent SDK project context

Read **AGENTS.md** for the full harness constitution. This file is loaded on every Agent SDK session via `settingSources: ["project"]`.

## What RFR is (read first, every turn)

**Ready For Robots finds companies that are ready to buy or pilot robots** and tells robot sellers *which company, which workflow, and why now*.

- **Robot sales opportunities are jobs for robots, not people.** A "robot job" = a workflow at a company that a robot could be hired to do. Whenever code or docs say "jobs" or "Job Cards," that is the only meaning.
- **A robot job (buyer opportunity) = company × workflow × readiness signals.** That is the unit of the product.
- **RFR is NOT:**
  - job postings for people as the product (cooks, pickers, housekeepers, security guards);
  - generic robotics news or lists of robot makers.
- **Robot makers are SUPPLY.** RFR indexes them only to classify their robots. They are never buyer opportunities.
- **Think per workflow, not per company.** A company that deployed robots in one workflow is committed *there*, not as a company. Example: a resort using cleaning robots may still be open for sanitizing, food prep, room-service delivery, or entertainment robots.
- **The sales window is before a company commits in a workflow:** budgeting, modernizing, labor pressure, exploring, piloting. **A published RFP means budget is confirmed — the strongest signal.**
- **Robotics hiring is an indirect readiness signal, not a lead source by itself.**
  - A *potential buyer* hiring robotics or automation roles (e.g., a hospital's "robotics program manager," a 3PL's "automation engineer," a hotel group's "robotics operations lead") signals they plan to use robots. Attach it as a signal on that company's opportunity, in the workflow the role points to.
  - A *robot maker* hiring (e.g., Grace Gong's lists, robot-maker career pages) is supply-side market context only. It never creates a buyer opportunity and never defines the product or the market thesis.
- **Method:** read each company's intentions per workflow and score them against RFR's own prediction of what that company is trying to accomplish.

## How matching works

1. **Classify robots** with `tests/fixtures/taxonomy.v1.json` (single source of truth): company → products → functions → industries → form + primary class. Closed values only; anything that doesn't fit goes in `unclassified_notes`. Never invent values.
2. **Index buyers with the same industry list** as robots.
3. **Robot → buyer = join** on industry and function/workflow, ranked by readiness signals.
4. **Never match robots to people's job postings.** "Jobs" in RFR means jobs for robots (buyer opportunities). If code or docs treat jobs as human job listings, flag it; don't extend it.

## Guardrails

- **Database:** no deletes, bulk updates, or schema changes without Bob's explicit approval and a confirmed backup. (In Oct 2026 an agent erased ~14,500 records.)
- **PRs:** work on a branch, open a **draft** PR, stop. Bob merges.
- **Benchmarks:** the answer key and scorer are frozen. Never tune them to fit model output; report failures as they are.
- **Signals vs. sources of truth:** indirect sources (hiring lists, news, career pages) are signals attached to a buyer's opportunity, never authoritative definitions of the product or market. Supply-side hiring (robot makers) may be kept as market context in its own clearly labeled doc, not in `docs/market_thesis.md`.
- **Report honestly:** say what was actually run and verified. Don't present estimates as results.

## Summary for every turn

0. **Value first:** prove a buyer-opportunity card (company, workflow, readiness signals, matching robots) **before** signup or upgrade asks. See `docs/value_first_principle.md`.
0a. **Competitive frame:** users compare us to Explee/Apollo. Win on **buyer readiness per workflow ↔ classified robots**, not company count. See `docs/competitive_positioning.md`.
0b. **Hermes retired:** do not spawn Hermes. Do not follow `docs/hermes_intelligence_bridge.md` as production. Matcher + harness stay. Cursor pstack is the release authority (How / Act / Critic in `pstack/` + `scripts/pstack_release.py`). Not a customer chatbot. See `docs/hermes_retired.md` and `docs/pstack_jobs.md`.
1. **North star order:** names/events → scores → rank → robot specs. Fix junk before ranking tweaks.
2. **Market thesis:** read `docs/market_thesis.md`; update backlog after research missions. Demand-side (buyer) intelligence only.
3. **One mission per cycle.** Write or follow `missions/YYYY-MM-DD-<slug>/brief.md`.
4. **Observe first:** `python3 scripts/harness_snapshot.py` then `python3 scripts/harness_compile_memory.py` → read `reports/compiled_memory_latest.json` (not chat). Product loop: `docs/product_integrity_loop.md`. ProductManager spec: `docs/agent-product-manager.md`. Vercel secrets: `docs/vercel_production_secrets.md`. Agents must not meter Vercel Preview/AI Gateway: `docs/vercel_agent_spend.md`.
5. **Verify:** run targeted pytest; **real** Vercel production (CLI secrets) + Fly; do not trust a 7s "Deploy frontend" skip.
6. **Notify:** `python3 scripts/harness_notify.py --mission <path>` when done.
7. **Frontend:** `readyforrobots-new/` (Vite + wouter). API: `https://ready-2-robot.fly.dev`.
8. **Do not commit** `reports/` artifacts.

## Default first mission (intelligence)

```bash
python3 scripts/harness_snapshot.py
python3 scripts/run_mission.py --mission missions/2026-06-23-friction-baseline
python3 scripts/harness_notify.py --mission missions/2026-06-23-friction-baseline
```

## Daily automation

```bash
python3 scripts/harness_daily.py
```

GitHub Actions runs this at 14:00 UTC (`.github/workflows/harness-daily.yml`). macOS: `./scripts/install_harness_launchd.sh`.

## Compaction — always preserve

When summarizing conversation history, keep:

- What RFR is (the section above) — verbatim
- Current mission objective and acceptance criteria
- Files modified and test results
- Metrics before/after from harness snapshot (`intelligence` deltas)
- Thesis backlog changes and open blockers

## Subagent delegation

| Task | Delegate to |
|------|-------------|
| Market / puck direction | MarketIntel |
| Junk / gaps / friction | FrictionMiner |
| Backlog synthesis | ProductThesis |
| Pipeline cache / API feed | PipelineHealth |
| Junk rules / quarantine | LeadQuality |
| Home / experiment UI | ProductSurface |
| git / fly / smoke | Deploy |
