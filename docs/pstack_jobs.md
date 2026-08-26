# pstack for ReadyForRobots (site protocol + IDE routing)

pstack is role routing: How, Act, Critic, plus Cursor skills (`how`, `unslop`, critics). It is not a customer chatbot and not a Fly model API.

Jobs still come from the robot ontology and `POST /api/robot-job-match` (`app/services/robot_job_capability_match.py`). pstack does not pick employers.

Hermes is retired ([`hermes_retired.md`](hermes_retired.md)). Do not call Vercel AI Gateway.

## On the site

| Piece | Path |
|-------|------|
| Protocol (client) | `readyforrobots-new/client/src/lib/pstackSite.ts` |
| Protocol (API) | `app/services/pstack_protocol.py` |
| Chrome | `JobsPstackProtocol` on `/`, About (`/intelligence#jobs-protocol`), Jobs CRM desk |
| CRM generate-plan | tagged pstack Act; How-check says this is not the matcher |
| ScoutChat | frozen SIGNAL shell; customer pstack chat is forbidden |

## Jobs work

| When | Use |
|------|-----|
| Before Jobs UI or matcher edits | How for ownership. Do not invent a second matcher. |
| Implement on `/` or Jobs CRM | Act. Keep the signup wall. Keep step 03 labeled CRM. |
| After Jobs UI copy | `unslop` |
| PRs that touch `readyforrobots-new/` or the matcher | Critic = `.cursor/skills/verify-readyforrobots/SKILL.md` |

FIND is `/`. Proof is `POST /api/robot-job-match` and Job Cards, not `/experiment`.

## Harness roster → pstack roles

| Harness | pstack |
|---------|--------|
| Orchestrator | parent |
| ProductSurface | Act / frontend |
| LeadQuality | critics on names and events |
| Deploy | Critic / verify-readyforrobots |

There is no Hermes pstack role.

Checked-in rules: `.cursor/rules/pstack-jobs.mdc` and `.cursor/rules/pstack-rfr.mdc`. Cloud agents read those. Do not depend on `~/.cursor/rules/pstack-models.mdc`.
