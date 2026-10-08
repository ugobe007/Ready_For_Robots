# Find stay

FIND lookup timeout, 500, abort, or Failed to fetch stays on OEM step 1 (`/` or `/?visit=jobs`) with retry copy. It does not dump the visitor onto employer MATCH. Fail-fast is better than a 90s hang then a bounce.

## Sub-features

- `find-error-stay` keeps `?visit=jobs` after lookup failure and paints honest error copy on step 1.
- `find-no-new1` forbids `goJobsFreshHome` and `/?visit=candidates` from FIND lookup failure.
- `find-fail-fast` caps unknown-OEM search at 8s and catalog SKU search at 12s, hitting Fly directly so Vercel cannot sit on the rewrite for ~90s.
- `employer-catalog` is MATCH from the vendor index only, with a 3s client budget. No live OEM scrape.
- `employer-jd` uploads a pdf/docx/txt with the post-job draft. No invented employer or email.

## How to get to it (user POV)

- Open `https://readyforrobots.com/` or load `/?visit=jobs`.
- Paste a robot URL and click Find jobs. If lookup times out or the API returns 500, you stay on that FIND form with an error. Retry on the same step.
- Wordmark / Jobs returns to FIND. Lookup failure stays on FIND.
- Employer door: **Robots for Jobs** → match catalog robots → post the job, optionally with a job-description file.

## Driving it with verify-readyforrobots

Preconditions:

- Doctor reports `worth_driving: true`. Skip-green JS is a fail, not a 7-second pass.

- **Source.** `python3 scripts/agent_verify.py drive --feature find-stay --evidence "$EVIDENCE"`. Fail if `submitFind` calls `goJobsFreshHome`, writes `/?new=1`, or omits `ensureFindStayVisit`. Fail if Jobs.tsx paints a landing fork instead of RobotJobsWorkspace.
- **Employer budget.** `python3 scripts/agent_verify.py drive --feature employer-match --evidence "$EVIDENCE"`. Source must be catalog snapshot only. When production returns `catalog_only: true`, elapsed must be under 3s.
- **Both paths after error.** After a FIND error, `/` still has the URL field. After an employer match error, `/?visit=candidates` still has the work tiles.
- **pstack.** Critic gate `find_no_home`. `python3 scripts/pstack_release.py --local`.

## Gotchas

- `/` is FIND. Dumping lookup failure onto `/?visit=candidates` is the bounce.
- Vercel `/api` rewrites can hang ~90s if the client talks same-origin. FIND search hits Fly (`getPublicReadApiBase`).
- Self-abort of a superseded URL stays silent. Live timeout / Failed to fetch / 500 must show retry copy on step 1.
- Do not trust a 7-second “Deploy frontend” skip. Doctor `skip_green` fails the proof.
- Hunter.io is the future contact source. This path does not call Hunter or invent emails.
