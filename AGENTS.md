# Ready For Robots — Agent Harness Constitution

This file is the **master charter** for autonomous development loops (Claude Agent SDK). It defines roles, priorities, gates, and how missions are run. Persistent rules live here and in `harness/` — not in one-off chat prompts.

## Purpose

Continuously improve **ReadyForRobots** toward product success by running closed loops:

**Observe → Orient → Decide → Act → Verify → Learn → Notify**

The harness operates **autonomously**: commit, push, deploy, and apply scripts when missions require it. The operator is **notified after changes**, not asked for approval before each step.

## Product / market fit (primary focus)

Read `docs/product_market_fit.md`, **`docs/value_first_principle.md`**, and **`docs/robot_employment_model.md`** before every mission. **Users do not buy unless they see value** — prove Robot Job Cards (employer + work) before signup or upgrade asks.

**EXPERIMENT MODE:** Read `docs/EXPERIMENT_MODE.md` and **`docs/CAPABILITY_MODEL.md`**. The experiment is now the product: **`/` = Jobs terminal** (FIND → QUALIFY → PLACE later). Freeze SIGNAL/CRM/Cal-as-core and hypothesis expansion — but **Robot Understanding v1 Phases 1–3** (`docs/robot_understanding_v1.md`) is allowed product-integrity work. Tiny loop: robot URL → credible jobs. Interviews falsify; they don’t grant permission to expand.

**All agents optimize toward this outcome:**

> ReadyForRobots is **recruitment and placement infrastructure for robotic labor**. The unit of value is the **Robot Job**. Customers register a robot as available for work and receive jobs it is qualified to perform. They keep those jobs in **native CRM** (`/pipeline?src=jobs_activate`) or HubSpot. A sale is an outcome of placement — not the object we optimize.

| Lens | Question every mission must answer |
|------|-----------------------------------|
| **ICP** | Does this help a robot OEM/integrator **place robots into work**? |
| **Activation** | Does this move URL → Job Cards → signup → unlocked jobs in CRM? |
| **CRM path** | Does Jobs CRM stay on jobs (not SIGNAL buyers)? |
| **Trust** | Are Job Cards real work with named employers, not invented economics? |
| **Value proof** | Can an anonymous user see a Robot Job Card before signup? |

Lead-quality north star (below) is **SIGNAL infrastructure**, not the product. Fix junk on that path; do not hop Jobs traffic onto HOT buyers.

**Hermes is retired (2026-08-26).** Do not spawn Hermes for FIND or Jobs. Do not follow [`docs/hermes_intelligence_bridge.md`](docs/hermes_intelligence_bridge.md) as production. The product loop is robot URL → Job Cards (`POST /api/robot-job-match`). Cursor **pstack** is IDE model routing only — never on readyforrobots.com, Vite, Vercel, or Fly. See [`docs/hermes_retired.md`](docs/hermes_retired.md) and [`docs/pstack_jobs.md`](docs/pstack_jobs.md). `.cursor/rules/pstack-jobs.mdc` + `.cursor/rules/pstack-rfr.mdc`.

## North star (strict priority)

From `docs/lead_quality_north_star.md` — optimize in this order:

1. **Names & events** — real buyer companies, not headline junk in `companies.name`
2. **Score events** — defensible signal strength on clean text
3. **Rank** — HOT/WARM/COLD reflects business rules
4. **Robot specs / opportunity** — `automation_profile`, `robot_types_needed`

**Rule:** Never tune (4) while (1) is broken. Partnership compounds, RSS headline merges, and vendor rows are **not** buyer opportunities.

## Market intelligence

**Product architecture (WORK graph + learning loop):** `docs/rfr_intelligence_architecture.md`  
Ontology: `ontology/rfr_graph.v1.json` · Spine: `docs/work_unit_reconstruction.md` · Deployment Evidence: `docs/deployment_evidence_engine.md` · Worker: `docs/market_graph_loop.md`

**Ontology library (copilot source of truth):** [`ontology/README.md`](ontology/README.md) — linked ontologies (Entity · Hardware · Capability · Task model · Workflow · Job) + [`ROBOT_INFERENCE_RULES.md`](ontology/ROBOT_INFERENCE_RULES.md). Core rule: `COMPANY → PRODUCT → CONFIGURATION → HARDWARE → CAPABILITIES → TASK MODELS → WORKFLOWS → JOB REQUIREMENTS → MATCH`; never `company → category → jobs`. Capabilities are grounded in hardware on the selected configuration and carry a confidence state (`EXPLICIT`/`DERIVED`/`LIKELY`/`UNKNOWN`/`CONFLICTED`). A task model is the trained policy for a specific physical job — hardware in the room is not enough.

- **Graph** = structure (what connects robot ↔ job). Center is **WORK**, not company or robot.
- **Loop** = OBSERVE LABOR → MATCH ROBOT → OBSERVE DEPLOYMENTS → STRENGTHEN/WEAKEN → KEEP WATCHING.
- **Knowledge** generates predictions; **Deployment Evidence** (public sources) strengthens/weakens them — live telemetry is optional later.

Read `docs/market_thesis.md` before choosing missions. The intelligence loop feeds the execution loop:

| Loop | Cadence | Output |
|------|---------|--------|
| **Intelligence** | Weekly (or first cycle of week) | Updated thesis, ranked backlog |
| **Execution** | Daily | Code, deploy, metrics delta |
| **Market graph** | Worker (~12h) | Tension + match edges → cache (`/api/v1/market-graph/*`) |
| **Product integrity** | Hourly observe / daily one act | Compiled memory + Jobs-path mission. Charter: `docs/product_integrity_loop.md` |

Snapshot `intelligence` slice (junk reasons, gap frequency, industry deltas) drives FrictionMiner and mission selection.

## Agent roster

| Agent | Scope | Primary docs |
|-------|--------|--------------|
| **Orchestrator** | Pick one mission per cycle; spawn subagents; enforce budgets; notify | This file, `docs/product_market_fit.md`, `harness/gates.yaml`, `docs/market_thesis.md`, latest snapshot, compiled memory |
| **ProductManager** | Test Jobs workflow + site + deploys + DB; compile memory; rank the next Jobs-path mission. Hourly observe only. Does not merge. | `docs/agent-product-manager.md`, `docs/product_integrity_loop.md`, `scripts/harness_compile_memory.py` |
| **MarketIntel** | External scan: earnings, trade press, competitor moves (Explee, Apollo, Clay), category trends | `docs/market_thesis.md`, `docs/competitive_positioning.md` |
| **FrictionMiner** | Internal friction: junk patterns, gaps, quarantine, rectification failures | Snapshot `intelligence`, `docs/lead_quality_north_star.md` |
| **ProductThesis** | Synthesize intel + friction → update thesis backlog ranks | `docs/market_thesis.md` |
| **PipelineHealth** | Cache freshness, empty feed, tier mix, refresh scripts | `docs/pipeline_process_and_scripts.md` |
| **LeadQuality** | `lead_filter`, quarantine, cleanup scripts, tests | `docs/lead_quality_north_star.md`, `docs/lead_quality_pipeline.md` |
| **ProductSurface** | `readyforrobots-new/` UI, Jobs `/`, home hero | `docs/readyforrobots-ux.md` |
| **Deploy** | git, pytest subset, Fly deploy, smoke checks | `DEPLOYMENT.md`, `SCRIPTS.md` |
| **ScraperOps** | Source drift, blocklist, orchestrator stats | `SCRAPER_SYSTEM.md` |

pstack role map (IDE only): Orchestrator = parent; ProductSurface = frontend; LeadQuality = critics on names; Deploy = verify-readyforrobots. There is no Hermes pstack role.

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

**Agent verification (PRs + missions):** [`.cursor/skills/verify-readyforrobots/SKILL.md`](.cursor/skills/verify-readyforrobots/SKILL.md) — doctor, drive FIND / Job Cards / chrome, evidence. Feature map (nav, process bar, panels, results): [`docs/feature_map.md`](docs/feature_map.md). CI: `.github/workflows/agent-verify.yml`. Auto-merge `cursor/*` only after that job is green (not skip-green). Hourly observe does not merge.

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

## Vercel is not an agent meter

Frontend stays on Vercel; **API and LLMs stay on Fly**. Agents must not use Vercel as compute or an AI Gateway. `cursor/*` (and all Preview) Git builds are skipped via `vercel.json` `ignoreCommand`. Production HTML still ships through GitHub **Deploy frontend to Vercel** `--prod` when frontend paths change — never from hourly observe, never skip-green. Agent-verify reads `readyforrobots.com` HTML for skip-green and **Fly** for `/api`. Protocol: [`docs/vercel_agent_spend.md`](docs/vercel_agent_spend.md).

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
- [docs/feature_map.md](docs/feature_map.md) — Jobs chrome (nav, process bar, panels, results)
- [docs/jobs_crm.md](docs/jobs_crm.md) — Jobs CRM spec (signup wall, free 5 / 15×month / 7-day, export)
- [docs/agent-spec.md](docs/agent-spec.md) — CRM copilot (not Hermes; Hermes retired)
- [docs/hermes_retired.md](docs/hermes_retired.md) — Hermes is not a Jobs agent
- [docs/pstack_jobs.md](docs/pstack_jobs.md) — Cursor pstack is IDE-only
- [docs/vercel_agent_spend.md](docs/vercel_agent_spend.md) — agents must not meter Vercel Preview / AI Gateway
