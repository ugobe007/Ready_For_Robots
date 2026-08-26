# Ready For Robots — Agent SDK project context

Read **AGENTS.md** for the full harness constitution. This file is loaded on every Agent SDK session via `settingSources: ["project"]`.

## Summary for every turn

0. **PMF focus:** read `docs/product_market_fit.md` and `docs/robot_employment_model.md`. We are the **employment layer for robots** — Job Cards, not leads. Every change should drive robot URL → credible jobs, not generic robotics content.
0a. **Jobs product:** `docs/CAPABILITY_MODEL.md` + `docs/EXPERIMENT_MODE.md` — `/` is Jobs (FIND → QUALIFY → PLACE later). Freeze SIGNAL/CRM/Cal-as-core and hypothesis expansion; **Understanding v1 Phases 1–3** (`docs/robot_understanding_v1.md`) is allowed integrity work. Loop: robot URL → credible jobs.
0b. **Competitive frame:** read `docs/competitive_positioning.md`. Users compare us to Explee/Apollo — win on **job requirements ↔ robot capabilities**, not company count.
0c. **Value first:** read `docs/value_first_principle.md`. Prove a Robot Job Card **before** signup or upgrade asks.
1. **North star order:** names/events → scores → rank → robot specs. Fix junk before ranking tweaks (infrastructure for PMF, not the product itself).
2. **Market thesis:** read `docs/market_thesis.md`; update backlog after research missions.
3. **One mission per cycle.** Write or follow `missions/YYYY-MM-DD-<slug>/brief.md`.
4. **Observe first:** `python3 scripts/harness_snapshot.py` then `python3 scripts/harness_compile_memory.py` → read `reports/compiled_memory_latest.json` (not chat). Product loop: `docs/product_integrity_loop.md`. ProductManager spec: `docs/agent-product-manager.md`. Vercel secrets: `docs/vercel_production_secrets.md`. Agents must not meter Vercel Preview/AI Gateway: `docs/vercel_agent_spend.md`.
5. **Verify:** run targeted pytest; **real** Vercel production (CLI secrets) + Fly; do not trust a 7s “Deploy frontend” skip.
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
