# pstack for ReadyForRobots (IDE only)

pstack is Cursor model routing: `how`, `why`, `unslop`, critics. It is not a website feature and not a Fly service.

Do not add a pstack npm package. Do not call pstack from Vite, Vercel, or the API.

## Jobs work

| When | Use |
|------|-----|
| Before Jobs UI or matcher edits | `how` for ownership. Do not invent a second matcher. |
| After Jobs UI copy | `unslop` |
| PRs that touch `readyforrobots-new/` or `robot_job_matcher.py` | `.cursor/skills/verify-readyforrobots/SKILL.md` |

FIND is `/`. Proof is `POST /api/robot-job-match` and Job Cards, not `/experiment`.

## Harness roster → pstack roles

| Harness | pstack |
|---------|--------|
| Orchestrator | parent |
| ProductSurface | frontend / feature work |
| LeadQuality | critics on names and events |
| Deploy | verify-readyforrobots |

There is no Hermes pstack role. Hermes is retired ([`hermes_retired.md`](hermes_retired.md)).

Checked-in rules: `.cursor/rules/pstack-jobs.mdc` and `.cursor/rules/pstack-rfr.mdc`. Cloud agents read those. Do not depend on `~/.cursor/rules/pstack-models.mdc`.
