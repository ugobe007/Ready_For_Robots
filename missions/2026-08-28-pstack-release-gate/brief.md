# pstack as Jobs release gate

**Date:** 2026-08-28  
**Type:** build  
**Agents:** Deploy, ProductSurface

## Goal

Make How / Act / Critic the **merge authority** for Jobs FIND / CRM / matching PRs. pstack is not protocol chrome on `/` or Jobs CRM. Draft PRs must not skip the gate. Catch the Greenfield-class mistakes (#172 leftover strawberry CRM, #173 self-abort as Failed to fetch) before auto-merge.

## Acceptance

1. `pstack/` README + `release.yaml` name How / Act / Critic as the release gate. No JOBS AGENT PROTOCOL required on FIND/CRM.
2. `scripts/pstack_release.py` runs on every PR including drafts (`.github/workflows/pstack-release.yml` + `agent-verify.yml` job `pstack-release`). Auto-merge needs both pstack-release and verify, skip-green false, non-draft.
3. Critic fixtures fail #173 (AbortError / Failed to fetch → Research failed) and #172 (strawberry leftover after Greenfield URL). Live critic posts `POST /api/robot-job-search` for a real OEM URL.
4. AGENTS.md + verify-readyforrobots say **no Jobs product PR without pstack checks**.
5. Do not resurrect protocol chrome on FIND/CRM. Do not duplicate the sibling abort-controller runtime fix. No Fly hardcoded in `apiBase.ts`. No `reports/` or `.env`.

## Out of scope

Fix Greenfield Research failed runtime (sibling `cursor/greenfield-research-failed-009b`). Put a pstack banner back on `/` or the CRM desk. SIGNAL hop. Invent jobs.
