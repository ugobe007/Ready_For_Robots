# pstack release authority (Jobs)

pstack here is the **product-release gate**, not a banner on `/` or Jobs CRM.

How / Act / Critic must pass before a Jobs PR merges. Chrome copy on the desk is not proof. `#149` protocol chrome is not the product. `#167` / `#172` removed JOBS AGENT PROTOCOL from CRM; do not put it back.

Roles come from Cursor pstack (`how`, critics, prove-it-works). This folder **encodes** those roles so CI can fail a PR that did not check its work.

```
How  → name the owner before editing FIND, Job Cards, CRM, or matching
Act  → change the Jobs path only; keep the signup wall; no SIGNAL hop
Critic → drive a real OEM URL; identity, abort, leftover CRM, matcher, class picker
```

## Run

```bash
python3 scripts/pstack_release.py --local     # How + Act + fixtures (no Fly)
python3 scripts/pstack_release.py             # + Critic FIND drive on Fly
python3 scripts/agent_verify.py pstack
```

CI: `.github/workflows/agent-verify.yml` job `pstack-release` and `.github/workflows/pstack-release.yml`. Both run on **draft** PRs. Skip-green Vercel still fails verify. `cursor/*` auto-merge needs this job green.

## What Critic must catch (Greenfield cascade)

| Miss | Fixture |
|------|---------|
| Self-abort FIND shown as Research failed / Failed to fetch (`#173`) | `isSilentFindError` / `findUserFacingError` — AbortError and Failed to fetch are silent |
| CRM leftover strawberry robot (`#172`) | `crmDeskForCurrentRobot` after a Greenfield URL |
| Identity not keyed to submitted URL (`#173`) | `canonicalRobotUrl` + `beginJobsHandoffForUrl` |
| FIND is not `/` | critic gate `find` |
| Class-picker click is a no-op (`Agtonomy` → Agriculture) | `qualifyActive` always POSTs `/api/robot-job-search`; empty is named |

Live Critic posts `POST /api/robot-job-search` (the URL FIND actually calls), not a chip-only matcher stub.

## Not this folder

- Customer chatbot
- Matcher replacement (`app/services/robot_job_capability_match.py` stays code)
- Protocol marketing on FIND or Jobs CRM
- Hermes / Vercel AI Gateway

Checklist: [`release.yaml`](release.yaml). Runtime roles: `readyforrobots-new/client/src/lib/pstackSite.ts`, `app/services/pstack_protocol.py`. Gate helpers: `pstackRelease.ts`.
