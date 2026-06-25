# Ready For Robots — Agent SDK project context

Read **AGENTS.md** for the full harness constitution. This file is loaded on every Agent SDK session via `settingSources: ["project"]`.

## Summary for every turn

0. **PMF focus:** read `docs/product_market_fit.md`. We are the **automated sales pipeline for robot companies** — signup → automate funnel → native CRM or HubSpot. Every change should drive activated robot-company workspaces, not generic robotics content.
1. **North star order:** names/events → scores → rank → robot specs. Fix junk before ranking tweaks (infrastructure for PMF, not the product itself).
2. **Market thesis:** read `docs/market_thesis.md`; update backlog after research missions.
3. **One mission per cycle.** Write or follow `missions/YYYY-MM-DD-<slug>/brief.md`.
4. **Observe first:** `python3 scripts/harness_snapshot.py` → read `reports/harness_snapshot_latest.json` (especially `intelligence`).
5. **Verify:** run targeted pytest; deploy autonomously when mission requires it.
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
