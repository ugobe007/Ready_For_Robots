# Workflow tests — landing fork live on Fly `b7ae3959`

**Date:** 2026-09-01  
**Production:** `https://readyforrobots.com` meta `rfr-release=git-b7ae39598f4b` (#208)  
**API:** `https://ready-2-robot.fly.dev` `/health` 200  
**Did not:** merge #195, deploy, or change product. No live break. No PR.

Doctor: Fly healthy, skip-green false, JS `/assets/index-Bp-kSTlQ.js`. Worth driving.

## Scripts

| Script | Result | Notes |
|--------|--------|--------|
| `python3 scripts/agent_verify.py map` | **PASS** | Feature files present |
| `python3 scripts/agent_verify.py doctor` | **PASS** | `worth_driving: true`, `skip_green: false` |
| `python3 scripts/agent_verify.py drive --feature find-jobs` | **PASS** | `state=matches`, 38 jobs, named employers (Fulcrum, Industrial Metal Supply, …) |
| `python3 scripts/agent_verify.py drive --feature job-cards` | **PASS** | Same match payload; task-model card contract present |
| `python3 scripts/agent_verify.py drive --feature find-url` | **PASS** | Dexmate `search_status=200`, identity Dexmate, not Research failed |
| `python3 scripts/agent_verify.py drive --feature jobs-chrome` | **PASS** | FIND headline, process labels, `jobs_activate` |
| `python3 scripts/agent_verify.py drive --feature jobs-crm` | **PASS** | Activate src in bundle; unlocked desk still needs session |
| `python3 scripts/agent_verify.py drive --feature about` | **PASS** | `/intelligence` 200, route in JS |
| `PYTHONPATH=. python3 scripts/pstack_release.py --local` | **PASS** | How / Act / Critic, live FIND skipped |
| `PYTHONPATH=. python3 scripts/pstack_release.py` (live) | **PASS** | Dexmate, Greenfield, Diligent healthcare critic |
| Targeted pytest (14 files) | **PASS** | 134 passed in 80s |
| Vitest jobs / landing / knownOemLineups | **PASS** | 15 files, 129 passed |
| `python3 scripts/url_workflow_critic.py --fixtures` | **PASS** | 8 fixture cases |
| `python3 scripts/harness_diagnostics.py --check all` | **PASS** | Site+code healthy. Conversion slice skipped: no local `DATABASE_URL` (not a product fail) |

Pytest files: `test_employer_robot_match.py`, `test_robot_job_search.py`, `test_robot_job_search_class_only.py`, `test_jobs_crm_keep_apply.py`, `test_jobs_crm_recruiter.py`, `test_jobs_apply_draft.py`, `test_pstack_release.py`, `test_pstack_protocol.py`, `test_pstack_healthcare_class.py`, `test_url_workflow_critic.py`, `test_class_picker_chrome.py`, `test_agent_verify.py`, `test_ontology_industry_language.py`, `test_robot_ontology.py`.

Vitest files: `jobsLanding.test.ts`, `jobsWorkflow.test.ts`, `knownOemLineups.test.ts`, plus chrome/CRM/pstack helpers listed in `agent-verify.yml`.

## Live paths (`https://readyforrobots.com`)

| Path | Result | Evidence |
|------|--------|----------|
| Landing fork `/` two doors | **PASS** | Who is this visit? Look for robot jobs / Look for robot candidates |
| **A.** Look for robot jobs → URL + I know the robot → Job Cards → Open CRM only → signup wall | **PASS** | Dexmate Vega, 5 Job Cards, `OPEN CRM →` with no sibling Apply on the list. Wall: `/signup?next=/pipeline?src=jobs_activate…` |
| **B.** Look for robot candidates → serving named catalog | **PASS** | 12 named robots (BellaBot / KettyBot / HolaBot / PuduBot 2 / Dinerbot / Keenon T8). No Seer Humanoid |
| **B.** mining empty honest copy | **PASS** | “No catalog robots for this work yet. Post the job so OEMs can find it.” No invented SKUs |

Pudu hub `https://www.pudurobotics.com/en` via `POST /api/robot-job-search`: **PASS** in 2s, `state=select_product`, company Pudu Robotics, named SKUs BellaBot, PuduBot 2, KettyBot, HolaBot, … Browser then used Dexmate for the Job Card → Open CRM click (allowed: pudu **or** dexmate). Multi-SKU picker is expected, not a hang.

Live `POST /api/employer-robot-match`: serving `state=matches` robot_count=12; mining `state=empty` with the same honest copy.

## Failures

None that are product breaks. No patch, no `cursor/workflow-test-fix-009b`, no PR.

Harness conversion metrics were unavailable in this VM (`DATABASE_URL` unset). Site and code checks were green.

## Do not

Do not merge #195. Do not deploy. Protocol footer on FIND is pre-existing chrome (`JobsPstackProtocol`); pstack `chrome_not_gate` still passes.
