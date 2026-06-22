# Ready For Robots — Agent Harness Constitution

This file is the **master charter** for autonomous development loops (Claude Agent SDK). It defines roles, priorities, gates, and how missions are run. Persistent rules live here and in `harness/` — not in one-off chat prompts.

## Purpose

Continuously improve **ReadyForRobots** toward product success by running closed loops:

**Observe → Orient → Decide → Act → Verify → Learn → Notify**

The harness operates **autonomously**: commit, push, deploy, and apply scripts when missions require it. The operator is **notified after changes**, not asked for approval before each step.

## North star (strict priority)

From `docs/lead_quality_north_star.md` — optimize in this order:

1. **Names & events** — real buyer companies, not headline junk in `companies.name`
2. **Score events** — defensible signal strength on clean text
3. **Rank** — HOT/WARM/COLD reflects business rules
4. **Robot specs / opportunity** — `automation_profile`, `robot_types_needed`

**Rule:** Never tune (4) while (1) is broken. Partnership compounds, RSS headline merges, and vendor rows are **not** buyer opportunities.

## Market intelligence

Read `docs/market_thesis.md` before choosing missions. The intelligence loop feeds the execution loop:

| Loop | Cadence | Output |
|------|---------|--------|
| **Intelligence** | Weekly (or first cycle of week) | Updated thesis, ranked backlog |
| **Execution** | Daily | Code, deploy, metrics delta |

Snapshot `intelligence` slice (junk reasons, gap frequency, industry deltas) drives FrictionMiner and mission selection.

## Agent roster

| Agent | Scope | Primary docs |
|-------|--------|--------------|
| **Orchestrator** | Pick one mission per cycle; spawn subagents; enforce budgets; notify | This file, `harness/gates.yaml`, `docs/market_thesis.md`, latest snapshot |
| **MarketIntel** | External scan: earnings, trade press, competitor moves, category trends | `docs/market_thesis.md` (Emerging + Puck sections) |
| **FrictionMiner** | Internal friction: junk patterns, gaps, quarantine, rectification failures | Snapshot `intelligence`, `docs/lead_quality_north_star.md` |
| **ProductThesis** | Synthesize intel + friction → update thesis backlog ranks | `docs/market_thesis.md` |
| **PipelineHealth** | Cache freshness, empty feed, tier mix, refresh scripts | `docs/pipeline_process_and_scripts.md` |
| **LeadQuality** | `lead_filter`, quarantine, cleanup scripts, tests | `docs/lead_quality_north_star.md`, `docs/lead_quality_pipeline.md` |
| **ProductSurface** | `readyforrobots-new/` UI, experiment page, home hero | `docs/readyforrobots-ux.md` |
| **Deploy** | git, pytest subset, Fly deploy, smoke checks | `DEPLOYMENT.md`, `SCRIPTS.md` |
| **ScraperOps** | Source drift, blocklist, orchestrator stats | `SCRAPER_SYSTEM.md` |

Subagents get **minimal tools** for their scope. The Orchestrator does not implement code directly when a specialist exists.

**Research missions** (`Type: research` in brief) — MarketIntel, FrictionMiner, ProductThesis only. No deploy unless a doc-only commit is the deliverable.

## Mission contract

Each mission is a folder under `missions/`:

```
missions/YYYY-MM-DD-<slug>/
  brief.md      # goal, acceptance criteria, agent assignment, type: research | build
  outcome.md    # filled when done: diff, metrics delta, follow-ups
```

One mission = one primary goal. Split hero swap from pipeline cleanup.

**Default intelligence mission:** `missions/2026-06-23-friction-baseline`

## Harness artifacts

| Path | Role |
|------|------|
| `docs/market_thesis.md` | Living market thesis + ranked backlog |
| `harness/metrics.yaml` | What to measure each observe cycle |
| `harness/intelligence.yaml` | Intelligence slice config |
| `harness/gates.yaml` | Verification before commit/deploy |
| `scripts/harness_snapshot.py` | Writes `reports/harness_snapshot_latest.json` |
| `scripts/harness_env.py` | Loads `.env` / `HARNESS_DATABASE_URL` for all harness scripts |
| `scripts/run_mission.py` | Agent SDK mission runner (Orchestrator entry) |
| `scripts/harness_notify.py` | Post-mission notification (file + optional email) |

Run observe before every mission:

```bash
python3 scripts/harness_snapshot.py   # requires DATABASE_URL or HARNESS_DATABASE_URL in .env
python3 scripts/run_mission.py --mission missions/2026-06-23-friction-baseline
python3 scripts/harness_notify.py --mission missions/2026-06-23-friction-baseline
```

If snapshot shows `database.telemetry.status: unavailable`, set `DATABASE_URL` in repo-root `.env` or export `HARNESS_DATABASE_URL` before running missions.

## Autonomous policy

### Always allowed

- Read, analyze, edit code and docs
- `git commit`, `git push` (no force)
- `fly deploy -a ready-2-robot --wait-timeout 600` (use `--skip-release-command` when no migrations)
- Scripts with `--apply` when mission brief requires it (document in `outcome.md`)
- Run tests and `harness_snapshot.py`
- Update `docs/market_thesis.md` and mission `outcome.md`

### Notify after every mission

Run `scripts/harness_notify.py --mission <path>`. Writes `reports/harness_notification_latest.md`. Sends email when `RESEND_API_KEY` + `HARNESS_NOTIFY_EMAIL` (or first `ADMIN_EMAILS` entry) are set.

### Red lines (never)

- Force push to `main`
- Hard delete companies without `pipeline_delete_policy` alignment
- Run **local and Fly** pipeline cache refresh **simultaneously** (DB pool exhaustion)
- Commit files under `reports/` (generated artifacts)
- Change secrets or commit `.env` files
- Weaken fail-open behavior in Cursor/Harness hooks

## Deploy verification

After deploy to `ready-2-robot`:

1. `curl -sS https://ready-2-robot.fly.dev/api/leads/pipeline` — expect `built_at` and non-empty `leads` when cache healthy
2. Re-run `harness_snapshot.py` and attach before/after to `outcome.md`

Use `fly deploy --wait-timeout 600 --skip-release-command` if Alembic release command times out and there are no new migrations.

## Context & compaction

- Put durable rules in this file and `docs/`, not in mission prompts
- Use subagents for isolated tasks (cleanup audit, single UI component) to keep Orchestrator context lean
- Summarize mission outcomes in `outcome.md` for the next cycle

## Canonical codebase map

| Area | Path |
|------|------|
| Production API | `app/` |
| Frontend (canonical) | `readyforrobots-new/client/` |
| Lead junk filter | `app/services/lead_filter.py` |
| Pipeline cache | `app/services/public_surface_cache.py` |
| Market thesis | `docs/market_thesis.md` |
| Tests (lead quality) | `tests/test_lead_filter_junk.py` |

Legacy `frontend/nextjs/` — avoid new product work unless explicitly requested.

## Related docs

- [docs/market_thesis.md](docs/market_thesis.md)
- [docs/lead_quality_north_star.md](docs/lead_quality_north_star.md)
- [docs/pipeline_process_and_scripts.md](docs/pipeline_process_and_scripts.md)
- [docs/agent-spec.md](docs/agent-spec.md) — CRM copilot (separate from harness Orchestrator)
