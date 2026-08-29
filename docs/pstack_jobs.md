# pstack for ReadyForRobots (release authority)

pstack is **How / Act / Critic for Jobs product releases**. It is the merge gate, not a banner on `/` or Jobs CRM, not a customer chatbot, and not a Fly model API.

Jobs still come from the robot ontology and `POST /api/robot-job-match` (`app/services/robot_job_capability_match.py`). FIND submit calls `POST /api/robot-job-search`. pstack does not pick employers.

Hermes is retired ([`hermes_retired.md`](hermes_retired.md)). Do not call Vercel AI Gateway.

**No Jobs product PR without pstack release checks.** Draft PRs do not skip the gate.

```bash
python3 scripts/pstack_release.py --local
python3 scripts/pstack_release.py
python3 scripts/agent_verify.py pstack
```

## How / Act / Critic (encoded)

| Role | Where | Must prove |
|------|--------|------------|
| **How** | `pstack/README.md`, `pstackSite.ts` how, `pstack_protocol.py` | Name the owner. FIND is `/`. Matcher stays code. Chrome is not the gate. |
| **Act** | FIND/CRM/matching diff | `bindSubmittedRobot`, URL identity, signup wall, no SIGNAL hop, no leftover robot. |
| **Critic** | `scripts/pstack_release.py` + verify-readyforrobots | Real OEM URL on `POST /api/robot-job-search`. No Research failed / Failed to fetch from self-abort. Identity equals that URL. CRM is not a prior strawberry robot. Diligent/Moxi is healthcare, not humanoid empty. |

CI: `.github/workflows/pstack-release.yml` and job `pstack-release` in `.github/workflows/agent-verify.yml`. Both run on drafts. `cursor/*` auto-merge needs pstack-release **and** Jobs verify, skip-green false.

## On the site

| Piece | Path |
|-------|------|
| Release gate | [`pstack/README.md`](../pstack/README.md), `scripts/pstack_release.py` |
| Protocol (client) | `readyforrobots-new/client/src/lib/pstackSite.ts`, `pstackRelease.ts` |
| Protocol (API) | `app/services/pstack_protocol.py` |
| About (optional explainer) | `JobsPstackProtocol` on `/intelligence#jobs-protocol` only as documentation |
| FIND / Jobs CRM | **No protocol chrome required.** Do not put JOBS AGENT PROTOCOL on the desk. |
| CRM generate-plan | tagged pstack Act; How-check says this is not the matcher |
| ScoutChat | frozen SIGNAL shell; customer pstack chat is forbidden |

## Jobs work

| When | Use |
|------|-----|
| Before Jobs UI or matcher edits | How for ownership. Do not invent a second matcher. |
| Implement on `/` or Jobs CRM | Act. Keep the signup wall. Keep step 03 labeled CRM. |
| After Jobs UI copy | `unslop` |
| Before merge | Critic = `python3 scripts/pstack_release.py` + `.cursor/skills/verify-readyforrobots/SKILL.md` |

FIND is `/`. Proof is a real OEM URL through `POST /api/robot-job-search` and Job Cards, not `/experiment`.

## Harness roster → pstack roles

| Harness | pstack |
|---------|--------|
| Orchestrator | parent |
| ProductSurface | Act / frontend |
| LeadQuality | critics on names and events |
| Deploy | Critic / `pstack_release.py` + verify-readyforrobots |

There is no Hermes pstack role.

Checked-in rules: `.cursor/rules/pstack-jobs.mdc` and `.cursor/rules/pstack-rfr.mdc`. Cloud agents read those. Do not depend on `~/.cursor/rules/pstack-models.mdc`.
