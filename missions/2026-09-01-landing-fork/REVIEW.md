# Landing fork: jobs vs candidates

**Date:** 2026-09-01
**Type:** build
**Branch:** `cursor/landing-fork-jobs-candidates-009b` from `origin/main` @ `df9c1c5c` (#206 and #207 already on main)

This is the review. Operator asked for two options only. No third product.

## Routing

`/` and `/?new=1` ask who this visit is. Two cards.

Look for robot jobs → `/?visit=jobs` → OEM FIND step 1 (URL plus I know the robot). Process bar stays 01 Show us your robot / 02 Available jobs / 03 CRM. Open CRM and Cal stay on this path.

Look for robot candidates → `/?visit=candidates` → employer step 1 (work tiles + optional description). Process bar is 01 What is the work / 02 Matching robots / 03 Post the job. Employer CRM is their postings and shortlisted robots. Cal does not move here.

Wordmark is still `/?new=1`. Leaving an empty Jobs CRM desk goes to `/?visit=jobs`, not the fork. About Find jobs → goes to FIND.

## What I changed

Landing is `JobsLanding` on `pages/Jobs.tsx`. FIND workspace is unchanged after the click, plus named catalog SKUs from `knownOemLineups`. Class click selects. Find jobs for this type → or a named SKU starts `POST /api/robot-job-search`. No invented SKUs.

Employer MATCH is `POST /api/employer-robot-match` against the vendor catalog. Empty mining copy is "No catalog robots for this work yet. Post the job so OEMs can find it." Draft is `POST /api/employer-job-draft` onto `robot_jobs` when the DB will take a real employer name. No invented email.

## Tests

Vitest `jobsLanding.test.ts` + `jobsWorkflow.test.ts`: 39 passed.

Pytest `test_employer_robot_match.py` + `test_robot_job_search_class_only.py`: 6 passed.

`PYTHONPATH=. python3 scripts/pstack_release.py` How / Act / Critic: ok. Live Dexmate, Greenfield, Diligent FIND still pass. No Fly deploy.

Browser (local Vite, catalog MATCH on local :8010, URL FIND through the Fly proxy): landing, OEM URL Dexory, OEM serving → BellaBot Job Cards, employer mining empty, employer serving named robots, post-job draft kept on device (no local DATABASE_URL).

## Do not

Do not Fly-deploy unless you want employer MATCH on production. Draft PR.

Do not merge #195.
