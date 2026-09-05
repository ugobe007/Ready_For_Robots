# Agent verification + feature map

**Date:** 2026-08-25  
**Type:** build  
**Status:** done

## Diff

- `.cursor/skills/verify-readyforrobots/` — pstack launch / doctor / drive / evidence / cleanup + feature recipes
- `docs/feature_map.md` — nav, process bar, panels, surfaced results, workflow
- `scripts/agent_verify.py` — doctor + drive + `ci`
- `.github/workflows/agent-verify.yml` — PR check; squash auto-merge for `cursor/*` after green (not skip-green; `do-not-merge` blocks)
- `tests/test_agent_verify.py`, harness gate, AGENTS.md pointer

## Metrics

Production proof (evidence survives cleanup):

- doctor: Fly `/health` 200; pipeline `built_at` present; Vercel JS canaries FIND + `jobs_activate`; not skip-green
- drive find-jobs: Vega/Dexmate `requirement_v1`, 38 jobs, named employers
- `ci` drives find-jobs, jobs-chrome, about, jobs-crm all ok
- pytest `tests/test_agent_verify.py` 3 passed

## Follow-ups

- Hourly observe still must not merge
- Enable GitHub auto-merge on the repo if `enablePullRequestAutoMerge` is preferred over immediate squash
- Keep Vercel production SHA honest; skip-green still fails verify
