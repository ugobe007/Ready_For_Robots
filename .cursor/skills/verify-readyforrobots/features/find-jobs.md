# Find jobs

Find jobs lets an OEM or distributor paste a robot product URL (or pick a robot type) on the robot jobs board and see named Robot Jobs before signup. FIND opens on `/jobs`, bare `/?visit=jobs`, and `/#find` (redirects to `/jobs`). `/` is the home hero.

## Sub-features

- `find-open` shows FIND on `/` (and `/?visit=jobs`) with headline, URL field, and three live named-employer jobs as inline text. Those three jobs are the public board — they must load without submitting a robot URL.
- `find-submit` runs research + match for one URL.
- `find-lineup` asks which SKU when the page has several robots.
- `find-api` is the same path the UI calls (`POST /api/robot-job-match`).

## How to get to it (user POV)

- Open `https://readyforrobots.com/`.
- Click Jobs in the Jobs header (FIND). Wordmark is `/`.
- Click Find jobs → on About (`/intelligence`) — that link is `/?visit=jobs`.
- On `/`, paste the URL into the hero input labeled `Robot product URL` and click **Find jobs →**. That opens `/?visit=jobs&url=…`.
- On `/jobs` or bare `/?visit=jobs`, paste the URL into `#rank-robot-url` and click **Rank for my robot →**. That opens `/?visit=jobs&url=…`.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor reports `worth_driving: true`.
- Do not use SIGNAL `/pipeline` as the entry.

- **Open FIND.** The two entry points use different handles:
  - `/` (hero): input `aria-label="Robot product URL"`, placeholder `Paste a robot product URL (e.g. https://www.dexmate.ai)...`, button **Find jobs →**. The form has no accessible name; locate it by the input or `form.rfr-landing-hero-form`. Submitting goes to `/?visit=jobs&url=<encoded URL>`, which starts the search.
  - `/jobs` and bare `/?visit=jobs` (robot jobs board): input `#rank-robot-url` (label `Robot product page`), button **Rank for my robot →**. Submitting goes to `/?visit=jobs&url=<encoded URL>`.
  - Before any submit, both pages show the **Example jobs** tape. Every row and the row's modal say `Example`. Employer MATCH is a quiet link.
- **Submit a known robot.** Paste `https://www.dexmate.ai/` (or Fourier) and start Find jobs. One SKU continues to jobs on the same click; several SKUs must keep 01/02/03 as links.
- **API entry (CI).** Run `python3 scripts/agent_verify.py drive --feature find-jobs --evidence "$EVIDENCE"`. Expect HTTP 200, `state` `matches` or `thin_corpus`, `job_count > 0`, and job titles. When `matcher` is `requirement_v1`, at least one `company_name` is present.
- **Real URL (pstack Critic).** Run `python3 scripts/pstack_release.py` (or `drive --feature find-url`). Posts `POST /api/robot-job-search` for Dexmate and Greenfield. Fail if the payload is Research failed / Failed to fetch, or if Greenfield identity looks like strawberry / Agrobot. Diligent (`https://www.diligentrobots.com/`) is a held-out `healthcare_class` critic: fail if `robot_class=humanoid` or the empty copy is `No humanoid jobs for this robot yet.`
- **Proof.** `drive-find-jobs.json` plus `pstack-release.json`. A homepage screenshot alone is not proof.

## Gotchas

- `/` is FIND. Do not remount-loop the workspace. Do not require a URL submit to review the public job board.
- `GET /api/robot-jobs/preview` must be JSON (`jobs` array), never the Vite `index.html`. HTML 200 is an empty board.
- Lookup timeout, 500, abort, or Failed to fetch must stay on FIND with retry copy. That dump is `drive --feature find-stay`. Do not treat a 7-second skip-green badge as proof.
- Chip-only match may omit `required_task_models` — use a Understanding profile (Vega fixture) for cards.
- Diligent/Moxi is healthcare, not a humanoid torso tile. Empty copy must not be `No humanoid jobs for this robot yet.`
- URL workflow critic: `python3 scripts/url_workflow_critic.py --fixtures` then `python3 scripts/url_workflow_critic.py`. Fail mixed-range flatten, chrome-as-SKU, Lucidbots-as-scrubber, company-class dump.
- Do not hop the result onto `/pipeline`. Next is Jobs CRM, not SIGNAL buyers.
- Local Vite without `VITE_PUBLIC_API_URL` will not hit Fly; doctor production instead.
