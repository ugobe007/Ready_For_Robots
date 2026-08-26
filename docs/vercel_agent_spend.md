# Vercel spend — agents must not meter compute or LLMs here

`readyforrobots.com` is a **static** Vercel site. Fly (`ready-2-robot`) is the API and the only place LLM keys belong. Agents must not treat Vercel as a Preview farm, an `/api` proxy lab, or an AI Gateway.

Investigation date: **2026-08-26** (operator report: ~$20 token/spend on **2026-08-25**). This VM has **no Vercel dashboard token**; invoices are not visible. Evidence is GitHub Actions + repo config + PR checks.

See also: [`vercel_production_secrets.md`](vercel_production_secrets.md) (the GitHub secret named `VERCEL_TOKEN` is an **auth credential**, not a billable AI token).

---

## What “token” is — and is not — on this project

| Candidate | In this repo? | Notes |
|-----------|---------------|--------|
| **Vercel AI Gateway / `@vercel/ai` / AI SDK routes** | **No** | No `@ai-sdk`, `@vercel/ai`, `AI_GATEWAY`, `generateText`, or Vercel-hosted LLM route. LLM calls that exist live in Fly Python (`app/services/llm_client.py`) behind paid flags. |
| **GitHub secret `VERCEL_TOKEN`** | Yes | CLI deploy auth. Does not bill per request. |
| **Vercel Git Preview** | **Yes — this is the agent-unique meter** | GitHub check `Vercel` / `Vercel Preview Comments` on `cursor/*` PRs. Full pnpm+Vite build per push. |
| **GHA `vercel deploy --prod`** | Yes | `.github/workflows/deploy-frontend.yml` on `main` when frontend paths change. Necessary. |
| **Fluid compute / function GB-hours** | Unlikely as the $20 line | Project is static (0 serverless). `/api/*` is a **rewrite** to Fly, not a Vercel function. Rewrites can still count as **Edge Requests / Fast Data Transfer** if clients hit `readyforrobots.com/api`. |
| **Hermes `--provider ai-gateway`** | Mac leftover, not GHA | Skills forbid it; 2026-08-20 leftover cron **402**. If the team later enabled AI Gateway billing, that **would** show as token spend — confirm in Vercel **Usage → AI Gateway**. Not invoked from this repo’s workflows. |

If the dashboard line item is literally **AI Gateway tokens**, the operator must cap or disable Gateway in the Vercel team (this PR cannot see that UI). Nothing in GitHub Actions calls it.

If the line item is **build minutes / deployments**, Preview-per-push is the fit.

Hobby/Pro seat ($20/month) can look like “$20” but is not agent-unique; 2026-08-25 traffic **is**.

---

## How agents used Vercel on 2026-08-25

`gh run list --created 2026-08-25` (first 100 runs; more existed):

| Workflow | Count (in that sample) | Hits Vercel? |
|----------|------------------------|--------------|
| CI | 31 | No |
| Harness hourly observe | 22 | **Yes** — `harness_diagnostics.py` GETs `https://readyforrobots.com/` pages **and** `/api/humanoid/robots` (rewrite → Fly). |
| Hermes Fly workflow | 22 | No (Fly) |
| Agent verify | 8 (added mid-day in #139) | **HTML/JS** from `readyforrobots.com`; **API** from `https://ready-2-robot.fly.dev` (`drive_find_jobs` POSTs Fly). |
| Deploy frontend to Vercel | **8** (full list for that workflow) | **Yes — real `--prod`**, ~50–80s, not skip-green. |
| Deploy to Fly.io | 8 | No |
| Harness daily | 1 | Fly API (`API_BASE=https://ready-2-robot.fly.dev`). Does not `vercel deploy`. |

**14 `cursor/*` PRs merged that UTC day** (#128–#142). Each push also created a **Vercel Preview** (PR checks named `Vercel`, `Vercel Preview Comments`, `Vercel Deployments`). Example: #140 `cursor/jobs-model-workflow-1962` → deployment `ready-for-robots/9mo9GinrpcXSTra67uYKcMt9DTWq`.

There is **no** GitHub workflow named “Vercel Preview”. Previews come from the **Vercel GitHub app** on every branch push. Cloud agents commit/push per iteration, so one PR is many Previews.

Hourly observe does **not** run `vercel deploy --prod`.

Agent-verify does **not** spawn a Preview; it reads production HTML for skip-green and Fly for FIND.

---

## Affordable protocol (going forward)

1. **API and LLMs = Fly** (or local / `ANTHROPIC_API_KEY` in GitHub). Never Vercel AI Gateway.
2. **Production frontend** = GitHub **Deploy frontend to Vercel** `--prebuilt --prod` when `readyforrobots-new/**` (or `vercel.json`) changes. ProductManager still requires a real `--prod`, not skip-green.
3. **Do not** `vercel deploy --prod` from hourly observe.
4. **Do not** use Preview URLs for agent-verify. Production + Fly only.
5. **Public reads** in the Jobs UI already use `getPublicReadApiBase()` → Fly on the marketing domain. Do not add new doctor/harness probes that POST through `readyforrobots.com/api` unless measuring the proxy itself.
6. **`cursor/*` and all Preview Git builds are ignored** via `vercel.json` `ignoreCommand` (exit 0 = skip).

---

## What this repo changed vs what the operator must click

**In git (this change):**

- Root `vercel.json` `ignoreCommand` skips Git builds when `VERCEL_ENV != production` **or** the ref is `cursor/*`. Vercel Git production on `main` can still build; GHA `--prod` is unchanged.
- Policy + tests: `scripts/vercel_git_build_policy.py`, `tests/test_vercel_git_build_policy.py`.

**Dashboard (this VM cannot do):**

1. Open [Vercel Usage](https://vercel.com/ugobe07-gmailcoms-projects/ready-for-robots) for **2026-08-25** and read the line items: AI Gateway vs Build Minutes vs Fast Data Transfer vs Edge Requests.
2. Project **Settings → Git**: confirm Ignored Build Step is not overriding `ignoreCommand` with a blank/always-build command. Optional: turn **off automatic Production deploys from Git** so only GHA `--prod` ships (stops a second production build on every merge).
3. If **AI Gateway** is enabled on the team: disable it or set a spend cap; remove leftover Mac Hermes `--provider ai-gateway`.
4. Do not add `AI_GATEWAY_API_KEY` to the Vercel project.
