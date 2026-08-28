# Product Integrity Loop — ReadyForRobots as a product

**This is not the market graph.** The market graph (`docs/rfr_intelligence_architecture.md`) maps robot ↔ work. This loop maps **the product itself**: Jobs workflow, site, deploys, database, agent memory.

**ProductManager agent spec (role / I/O / guardrails):** [`agent-product-manager.md`](agent-product-manager.md) — this file is the loop, that file is the agent.  
**Vercel production secrets:** [`vercel_production_secrets.md`](vercel_production_secrets.md)

Canonical market loop: [`docs/market_graph_loop.md`](market_graph_loop.md)  
Ontology: [`ontology/rfr_product_loop.v1.json`](../ontology/rfr_product_loop.v1.json)  
Compiler: `python3 scripts/harness_compile_memory.py`  
Observe: `python3 scripts/harness_diagnostics.py --check site`

---

## Opinion (locked)

A swarm of agents that **post and merge PRs every hour** will not produce a Jobs product. It will produce the last week: serial UI leaks, false-green deploys, and forgotten constraints.

Founders who get remarkable results from agents do three unglamorous things:

1. **One owner per cycle** — a Product Manager agent that picks *one* mission, not twelve parallel “find a bug” chats.
2. **Compiled memory** — a file the next agent *must* read. Chat is not memory. Outcome.md scattered across `missions/` is not memory until a compiler folds it.
3. **Honest gates** — tests, Vercel *production* truth (not a 7-second GitHub skip), Fly, database, Jobs smoke, **pstack How / Act / Critic**. Merge is a privilege those gates grant. Draft PRs do not skip pstack.

Hourly **observe**. Daily **one act**. Weekly **learn**. Auto-merge to `main` is allowed **only** after `.github/workflows/agent-verify.yml` job `pstack-release` (How / Act / Critic, including drafts) **and** Jobs verify (Fly + Vercel JS canaries + Jobs drive) are green — never after a skip-green frontend deploy, never from hourly observe, never because protocol chrome rendered.

---

## Graph (product structure)

Center is **JOBS_WORKFLOW**, not a backlog of tickets.

```
FIND (robot URL)
    → JOB CARDS (employer / workplace / work / Conditional)
        → CRM (5 unlocked jobs, src=jobs_activate on /pipeline)
            → WATCH (email when work changes)
```

Surrounding nodes the Product Manager must see:

| Family | What |
|--------|------|
| **SURFACE** | `/`, `/pipeline?src=jobs_activate`, header chrome, Vercel HTML |
| **DEPLOY** | Vercel production (custom domain), Fly API, GitHub Actions *actual* steps |
| **DATABASE** | snapshot telemetry, pipeline cache, jobs-watch |
| **MISSION** | `missions/*/brief.md` + `outcome.md` |
| **MEMORY** | `reports/compiled_memory_latest.json` (generated, not committed) |

---

## Loop (product learning)

```
OBSERVE HEALTH → COMPILE MEMORY → PICK ONE MISSION
    → ACT → VERIFY (Vercel prod + Fly + DB + Jobs path) → LEARN → NOTIFY
```

| Cadence | Who | Allowed |
|---------|-----|---------|
| **Hourly** | ProductManager observe | Site + deploy truth + DB ping. Write compiled memory. **No PR. No merge.** |
| **Daily** | Orchestrator + ProductManager | One mission. Commit + PR. Deploy only if gates pass. |
| **Weekly** | ProductThesis + MarketIntel | Rank backlog. Do not expand SIGNAL/Cal as core. |

### What hourly must not do

- Invent jobs or labor dollars
- Merge PRs
- Tune matcher / SIGNAL ranking
- Open a second mission because the first one “looked small”

---

## Product Manager agent

| | |
|--|--|
| **Name** | ProductManager |
| **Job** | Continually test and improve the ReadyForRobots *Jobs workflow* and the site that serves it |
| **Inputs** | Compiled memory, harness snapshot, Vercel/Fly truth, last mission outcome |
| **Outputs** | One ranked next mission in compiled memory; hourly alerts; daily brief if acting |
| **Not** | A second Orchestrator. Orchestrator still spawns specialists. ProductManager *chooses the Jobs-path mission* and *fails the cycle* if production did not actually deploy |

### Mission test (every ProductManager cycle)

```
readyforrobots.com /
  → header has no Pipeline
  → paste a known OEM URL (Fourier) → Job Cards
  → Open CRM → signup wall → /pipeline?src=jobs_activate (5 jobs on the CRM desk, no SIGNAL OEMs)
  → Fly /api health + database snapshot reachable
  → Vercel production SHA == origin/main (not a skipped 7s GHA)
```

If Vercel production is stale, **that is the mission**. Do not hunt another UI leak.

---

## Second brain (the compiler)

Agents lose the plot because they reread chat. The compiler is a **deterministic fold**, not another LLM:

```bash
python3 scripts/harness_compile_memory.py
```

Reads last mission outcomes + optional snapshot + Vercel/Fly/GHA signals. Writes `reports/compiled_memory_latest.json`:

- `jobs_loop` — FIND / cards / CRM / watch status
- `deploys.vercel_production` — skipped vs shipped
- `deploys.fly` — last production SHA
- `database` — snapshot available?
- `open_followups` — from recent `outcome.md`
- `next_mission` — one slug + why (Jobs-path only)

**Rule:** every agent turn starts by reading compiled memory *then* `docs/product_market_fit.md`. If those disagree, the docs win and the compiler is wrong — fix the compiler, do not improvise.

Chat transcripts, Linear, and “I think last time we…” are not memory.

---

## Deploy truth (Vercel)

GitHub job **Deploy frontend to Vercel** is not a deploy until `VERCEL_TOKEN` is set. A 6–11s green run is a skip. A ~30s red run with `Must not contain: " "` is a token paste with a trailing space. A ~30s red run with `Could not retrieve Project Settings` is CLI 59 `vercel pull` on a **project-scoped** token — the workflow must use `vercel deploy --prod`, not pull. See `docs/vercel_production_secrets.md`. **Preview** Git builds for `cursor/*` (and all non-production) are skipped (`vercel.json` `ignoreCommand`); agents verify production + Fly, not Preview. **Production** (`readyforrobots.com`) does not move unless the CLI `--prod` path runs or a remaining Preview is promoted. Spend protocol: [`vercel_agent_spend.md`](vercel_agent_spend.md).

ProductManager treats skip-green as **P0**. Workflow: `.github/workflows/deploy-frontend.yml` must **fail** when secrets are missing so the lie cannot hide in a success badge.
