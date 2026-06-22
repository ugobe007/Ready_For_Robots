# Ready For Robots — Agent Harness Constitution

This file is the **master charter** for autonomous development loops (Claude Agent SDK). It defines roles, priorities, gates, and how missions are run. Persistent rules live here and in `harness/` — not in one-off chat prompts.

## Purpose

Continuously improve **ReadyForRobots** toward product success by running closed loops:

**Observe → Orient → Decide → Act → Verify → Learn**

Human approval stays on destructive or production-facing actions until trust is established.

## North star (strict priority)

From `docs/lead_quality_north_star.md` — optimize in this order:

1. **Names & events** — real buyer companies, not headline junk in `companies.name`
2. **Score events** — defensible signal strength on clean text
3. **Rank** — HOT/WARM/COLD reflects business rules
4. **Robot specs / opportunity** — `automation_profile`, `robot_types_needed`

**Rule:** Never tune (4) while (1) is broken. Partnership compounds, RSS headline merges, and vendor rows are **not** buyer opportunities.

## Agent roster

| Agent | Scope | Primary docs |
|-------|--------|--------------|
| **Orchestrator** | Pick one mission per cycle; spawn subagents; enforce budgets | This file, `harness/gates.yaml`, latest `reports/harness_snapshot.json` |
| **PipelineHealth** | Cache freshness, empty feed, tier mix, refresh scripts | `docs/pipeline_process_and_scripts.md` |
| **LeadQuality** | `lead_filter`, quarantine, cleanup scripts, tests | `docs/lead_quality_north_star.md`, `docs/lead_quality_pipeline.md` |
| **ProductSurface** | `readyforrobots-new/` UI, experiment page, home hero | `docs/readyforrobots-ux.md` |
| **Deploy** | git, pytest subset, Fly deploy, smoke checks | `DEPLOYMENT.md`, `SCRIPTS.md` |
| **ScraperOps** | Source drift, blocklist, orchestrator stats | `SCRAPER_SYSTEM.md` |

Subagents get **minimal tools** for their scope. The Orchestrator does not implement code directly when a specialist exists.

## Mission contract

Each mission is a folder under `missions/`:

```
missions/YYYY-MM-DD-<slug>/
  brief.md      # goal, acceptance criteria, agent assignment
  outcome.md    # filled when done: diff, metrics delta, follow-ups
```

One mission = one primary goal. Split hero swap from pipeline cleanup.

## Harness artifacts

| Path | Role |
|------|------|
| `harness/metrics.yaml` | What to measure each observe cycle |
| `harness/gates.yaml` | Blockers before commit/deploy |
| `scripts/harness_snapshot.py` | Writes `reports/harness_snapshot.json` |
| `scripts/run_mission.py` | Agent SDK mission runner (Orchestrator entry) |

Run observe before every mission:

```bash
python3 scripts/harness_snapshot.py
```

## Tool & safety policy

### Always allowed (read / analyze)

- `Read`, `Glob`, `Grep`, `WebFetch` (docs only)
- Run tests: `python3 -m pytest tests/test_lead_filter_junk.py` (and targeted paths)
- `python3 scripts/harness_snapshot.py`
- Dry-run cleanup scripts (no `--apply`)

### Requires human approval (Orchestrator must stop and ask)

- `git commit`, `git push`
- `fly deploy`
- Any script with `--apply`, `--delete`, quarantine apply, or hard delete
- Schema migrations beyond `alembic upgrade` on production
- Changing secrets or `.env` values

### Never

- Force push to `main`
- Hard delete companies without `pipeline_delete_policy` alignment
- Run **local and Fly** pipeline cache refresh **simultaneously** (DB pool exhaustion)
- Commit files under `reports/` (generated artifacts)
- Weaken fail-open behavior in Cursor/Harness hooks

## Deploy verification

After approved deploy to `ready-2-robot`:

1. `curl -sS https://ready-2-robot.fly.dev/api/leads/pipeline` — expect `built_at` and non-empty `leads` when cache healthy
2. Re-run `harness_snapshot.py` and attach before/after to `outcome.md`

Use `fly deploy --wait-timeout 600` if Alembic release command times out.

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
| Tests (lead quality) | `tests/test_lead_filter_junk.py` |

Legacy `frontend/nextjs/` — avoid new product work unless explicitly requested.

## Related docs

- [docs/lead_quality_north_star.md](docs/lead_quality_north_star.md)
- [docs/pipeline_process_and_scripts.md](docs/pipeline_process_and_scripts.md)
- [docs/agent-spec.md](docs/agent-spec.md) — CRM copilot (separate from harness Orchestrator)
