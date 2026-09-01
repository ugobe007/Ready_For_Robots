# Find jobs

Find jobs lets an OEM or distributor paste a robot product URL (or pick a named catalog SKU) after **Look for robot jobs** and see named Robot Jobs before signup. `/` is the landing fork first.

## Sub-features

- `find-open` shows FIND on `/?visit=jobs` with headline and URL field.
- `find-submit` runs research + match for one URL.
- `find-lineup` asks which SKU when the page has several robots.
- `find-api` is the same path the UI calls (`POST /api/robot-job-match`).

## How to get to it (user POV)

- Open `https://readyforrobots.com/` and click **Look for robot jobs**, or load `/?visit=jobs`.
- Click Jobs in the Jobs header (returns to the landing fork). Wordmark is `/?new=1`.
- Click Find jobs → on About (`/intelligence`) — that link is `/?visit=jobs`.
- Submit the FIND form labeled `Find jobs for your robot`, or pick a class / named catalog SKU.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor reports `worth_driving: true`.
- Do not use SIGNAL `/pipeline` as the entry.

- **Open FIND.** Load `/?visit=jobs` (or `/` then Look for robot jobs). Heading is `Find Jobs for Robots.` URL placeholder is `Paste robot product URL`. Form name is `Find jobs for your robot`.
- **Submit a known robot.** Paste `https://www.dexmate.ai/` (or Fourier) and start Find jobs. One SKU continues to jobs on the same click; several SKUs must keep 01/02/03 as links.
- **API entry (CI).** Run `python3 scripts/agent_verify.py drive --feature find-jobs --evidence "$EVIDENCE"`. Expect HTTP 200, `state` `matches` or `thin_corpus`, `job_count > 0`, and job titles. When `matcher` is `requirement_v1`, at least one `company_name` is present.
- **Real URL (pstack Critic).** Run `python3 scripts/pstack_release.py` (or `drive --feature find-url`). Posts `POST /api/robot-job-search` for Dexmate and Greenfield. Fail if the payload is Research failed / Failed to fetch, or if Greenfield identity looks like strawberry / Agrobot. Diligent (`https://www.diligentrobots.com/`) is a held-out `healthcare_class` critic: fail if `robot_class=humanoid` or the empty copy is `No humanoid jobs for this robot yet.`
- **Proof.** `drive-find-jobs.json` plus `pstack-release.json`. A homepage screenshot alone is not proof.

## Gotchas

- `/?new=1` is the landing fork, not FIND. Do not remount-loop the workspace.
- Chip-only match may omit `required_task_models` — use a Understanding profile (Vega fixture) for cards.
- Diligent/Moxi is healthcare, not a humanoid torso tile. Empty copy must not be `No humanoid jobs for this robot yet.`
- URL workflow critic: `python3 scripts/url_workflow_critic.py --fixtures` then `python3 scripts/url_workflow_critic.py`. Fail mixed-range flatten, chrome-as-SKU, Lucidbots-as-scrubber, company-class dump.
- Do not hop the result onto `/pipeline`. Next is Jobs CRM, not SIGNAL buyers.
- Local Vite without `VITE_PUBLIC_API_URL` will not hit Fly; doctor production instead.
