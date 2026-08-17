# Ready For Robots — Agent Harness Constitution

This file is the **master charter** for autonomous development loops (Claude Agent SDK). It defines roles, priorities, gates, and how missions are run. Persistent rules live here and in `harness/` — not in one-off chat prompts.

## Purpose

Continuously improve **ReadyForRobots** toward product success by running closed loops:

**Observe → Orient → Decide → Act → Verify → Learn → Notify**

The harness operates **autonomously**: commit, push, deploy, and apply scripts when missions require it. The operator is **notified after changes**, not asked for approval before each step.

## Product / market fit (primary focus)

Read `docs/product_market_fit.md` and **`docs/value_first_principle.md`** before every mission. **Users do not buy unless they see value** — prove outcomes (live leads, pitch actions, outreach drafts) before signup or upgrade asks.

**EXPERIMENT MODE:** Read `docs/EXPERIMENT_MODE.md` and **`docs/CAPABILITY_MODEL.md`**. The experiment is now the product: **`/` = Jobs terminal** (FIND → QUALIFY → PLACE later). Freeze SIGNAL/CRM/Cal-as-core and hypothesis expansion — but **Robot Understanding v1 Phases 1–3** (`docs/robot_understanding_v1.md`) is allowed product-integrity work. Tiny loop: robot URL → credible jobs. Interviews falsify; they don’t grant permission to expand.

**All agents optimize toward this outcome:**

> ReadyForRobots is the **automated sales pipeline for robot companies**. Customers sign up to **automate their sales funnel** (SIGNAL-ranked leads, outreach, deal advance). They run in the **native CRM** (`/pipeline`, `/crm`) or **sync to HubSpot**.

| Lens | Question every mission must answer |
|------|-----------------------------------|
| **ICP** | Does this help a robot OEM/integrator sell more robots? |
| **Activation** | Does this move browse → signup → first saved lead → pipeline motion? |
| **CRM path** | Does this work for native CRM *and* HubSpot-connected teams? |
| **Trust** | Does the pipeline surface defensible buyer intent (not junk/news)? |
| **Value proof** | Can an anonymous user see a concrete win (draft, action, robot SKU) before signup? |

Lead-quality north star (below) is **infrastructure for PMF** — fix junk before ranking tweaks, but do not confuse data cleanup with product success. ProductSurface missions default to the conversion funnel in `docs/conversion_agent_challenges.md`.

## North star (strict priority)

From `docs/lead_quality_north_star.md` — optimize in this order:

1. **Names & events** — real buyer companies, not headline junk in `companies.name`
2. **Score events** — defensible signal strength on clean text
3. **Rank** — HOT/WARM/COLD reflects business rules
4. **Robot specs / opportunity** — `automation_profile`, `robot_types_needed`

**Rule:** Never tune (4) while (1) is broken. Partnership compounds, RSS headline merges, and vendor rows are **not** buyer opportunities.

## Market intelligence

**Product architecture (WORK graph + learning loop):** `docs/rfr_intelligence_architecture.md`  
Ontology: `docs/ontology/rfr_graph.v1.json` · Spine: `docs/work_unit_reconstruction.md` · Deployment Evidence: `docs/deployment_evidence_engine.md` · Worker: `docs/market_graph_loop.md`

- **Graph** = structure (what connects robot ↔ job). Center is **WORK**, not company or robot.
- **Loop** = OBSERVE LABOR → MATCH ROBOT → OBSERVE DEPLOYMENTS → STRENGTHEN/WEAKEN → KEEP WATCHING.
- **Knowledge** generates predictions; **Deployment Evidence** (public sources) strengthens/weakens them — live telemetry is optional later.

Read `docs/market_thesis.md` before choosing missions. The intelligence loop feeds the execution loop:

| Loop | Cadence | Output |
|------|---------|--------|
| **Intelligence** | Weekly (or first cycle of week) | Updated thesis, ranked backlog |
| **Execution** | Daily | Code, deploy, metrics delta |
| **Market graph** | Worker (~12h) | Tension + match edges → cache (`/api/v1/market-graph/*`) |

Snapshot `intelligence` slice (junk reasons, gap frequency, industry deltas) drives FrictionMiner and mission selection.

## Agent roster

| Agent | Scope | Primary docs |
|-------|--------|--------------|
| **Orchestrator** | Pick one mission per cycle; spawn subagents; enforce budgets; notify | This file, `docs/product_market_fit.md`, `harness/gates.yaml`, `docs/market_thesis.md`, latest snapshot |
| **MarketIntel** | External scan: earnings, trade press, competitor moves (Explee, Apollo, Clay), category trends | `docs/market_thesis.md`, `docs/competitive_positioning.md` |
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
| `scripts/harness_daily.py` | Full daily loop: snapshot → mission → notify |
| `scripts/harness_notify.py` | Post-mission notification (file + optional email) |

Run observe before every mission:

```bash
python3 scripts/harness_snapshot.py
python3 scripts/harness_diagnostics.py --check all   # site + code + conversion
```

**Daily operator report** (email + `reports/harness_daily_report_latest.md`):

| Section | Agent role | What it covers |
|---------|------------|----------------|
| Executive summary | Orchestrator | Signups 7d, paid subs, CRM activation — fundability metrics |
| Site health | PipelineHealth | Robots/pipeline API latency, page uptime, Stripe enabled |
| Code review | ProductSurface + Deploy | Public-read API routing, auth checkout helpers, open conversion board |
| Agent mission | Orchestrator | What shipped today + recommended next build |

Conversion is the **primary daily lens** — see `docs/conversion_agent_challenges.md`. Site performance and code conventions are guardrails so signup flows stay fast and checkout redirects work.

```bash
python3 scripts/harness_snapshot.py   # requires DATABASE_URL or HARNESS_DATABASE_URL in .env
python3 scripts/run_mission.py --mission missions/2026-06-23-friction-baseline
python3 scripts/harness_notify.py --mission missions/2026-06-23-friction-baseline
```

### Daily automation (recommended)

One command runs the full loop (snapshot → cache refresh if needed → agent mission → notify):

```bash
python3 scripts/harness_daily.py
```

| Method | When | Setup |
|--------|------|--------|
| **GitHub Actions** | 14:00 UTC daily + manual dispatch | Secrets: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `ADMIN_KEY`, **`RESEND_API_KEY`** (copy from Fly). Notify: `ugobe07@gmail.com` via `HARNESS_NOTIFY_EMAIL` in workflow. Workflow: `.github/workflows/harness-daily.yml` |
| **macOS launchd** | 7:00 local daily | `./scripts/install_harness_launchd.sh` (uses `.venv-harness` + repo `.env`) |

Pipeline cache refresh is async on Fly (~15–20 min). Use `python3 scripts/refresh_pipeline_cache.py --remote --wait` to block until `built_at` is set.

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

Run `scripts/harness_notify.py --mission <path>`. Writes `reports/harness_notification_latest.md`. Sends email to **`ugobe07@gmail.com`** (default) when `RESEND_API_KEY` is set. Test: `RESEND_API_KEY=… python3 scripts/harness_notify.py --test-email`.

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

- [docs/value_first_principle.md](docs/value_first_principle.md)
- [docs/product_market_fit.md](docs/product_market_fit.md)
- [docs/competitive_positioning.md](docs/competitive_positioning.md)
- [docs/market_thesis.md](docs/market_thesis.md)
- [docs/conversion_agent_challenges.md](docs/conversion_agent_challenges.md)
- [docs/lead_quality_north_star.md](docs/lead_quality_north_star.md)
- [docs/pipeline_process_and_scripts.md](docs/pipeline_process_and_scripts.md)
- [docs/agent-spec.md](docs/agent-spec.md) — CRM copilot (separate from harness Orchestrator)
