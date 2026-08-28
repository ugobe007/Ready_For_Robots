# Outcome — pstack as Jobs release gate

**Branch:** `cursor/pstack-release-gate-009b`  
**Type:** build  
**Date:** 2026-08-28

## What shipped

pstack is the **merge authority** for Jobs FIND / CRM / matching. How / Act / Critic run in CI on **drafts**. Protocol chrome on `/` or Jobs CRM is not a pass and was not added back.

| Role | Encoded in |
|------|------------|
| How | `pstack/README.md`, `pstack/release.yaml`, `scripts/pstack_release.py` `phase_how` |
| Act | `phase_act` source canaries (`bindSubmittedRobot`, abort-before-setError, URL handoff, CRM desk) |
| Critic | `pstackRelease.ts` fixtures + live `POST /api/robot-job-search` |

CI: `.github/workflows/pstack-release.yml` and job `pstack How / Act / Critic` in `.github/workflows/agent-verify.yml`. Auto-merge needs **both** that job and Jobs verify, skip-green false, non-draft. Draft-skip was removed from verify.

## Checks that would have failed the Greenfield cascade

- **#173** `FIND_ABORT_FIXTURE`: AbortError and TypeError `Failed to fetch` must not become `Research failed` (`findUserFacingError` returns null). FIND catch must return on `isAbortError` before `setError`.
- **#172** `CRM_LEFTOVER_FIXTURE`: Greenfield URL desk must not keep `strawberry robot` / orchard rows.

Did **not** duplicate the sibling abort-controller runtime fix on `cursor/greenfield-research-failed-009b`.

## Tests

```
PYTHONPATH=/workspace pytest tests/test_pstack_release.py tests/test_pstack_protocol.py tests/test_agent_verify.py
  15 passed
pnpm vitest pstackRelease + pstackSite + robotUrlIdentity + jobsCrmAccount + jobsHandoffSnapshot
  35 passed
python3 scripts/pstack_release.py
  ok: Dexmate company_name=Dexmate state=matches
      Greenfield company_name=GREENFIELD ROBOTICS (not strawberry)
```

## Remaining gap

Production Vercel HTML/JS still needs `agent-verify` doctor after Fly/Vercel deploy. This gate does not replace that smoke. A first-click FIND abort in the browser still needs the sibling runtime PR; this gate fails the **class** of mistake (abort painted as Failed to fetch, leftover CRM identity) on the next Jobs PR.
