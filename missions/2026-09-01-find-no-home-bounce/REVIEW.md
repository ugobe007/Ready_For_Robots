# FIND no home bounce

**Date:** 2026-09-01  
**Type:** build  
**Branch:** `cursor/find-timeout-no-home-a883`  
**Did not** merge #195. **Did not** Fly-deploy. Landing copy from #210 stays.

## Root cause

After the landing fork, `/` and `/?new=1` are the homepage. FIND is `/?visit=jobs`. Losing that query, or painting landing while it is still present, *is* the bounce.

Two things stacked:

1. **90s hang.** `fetchRobotJobSearch` used `getApiBase()`, so production FIND POSTed same-origin `/api/robot-job-search` and waited on the Vercel rewrite to Fly. The client abort does not kill that proxy. Vercel sits until the rewrite dies (~90s), then the SPA fails. 30s composed-search / 12s identity timeouts were still longer than a user will wait, and they did not cut the rewrite.
2. **Landing paint.** `Jobs.tsx` listened for `JOBS_FRESH_HOME_EVENT` and set `forcedLanding=true`, which rendered the landing fork even when the document still had `?visit=jobs`. Wordmark / header Jobs fires that event on purpose. A fail after a long wait, or any fresh-home event during FIND, dumped them onto "Put your robot to work." `submitFind` itself did not call `goJobsFreshHome`, but the page treated that event as unconditional landing.

Fail-fast is the product fix. 90s then success is still a break.

## What changed

- FIND catch calls `ensureFindStayVisit()` and `setStage("find")`. Never `/?new=1`.
- `Jobs.tsx` only honors `forcedLanding` when search visit is already landing.
- Search hits Fly (`getPublicReadApiBase`). Identity 8s. Composed search 12s.
- Employer MATCH walks the vendor index once (`lru_cache`), stored class only. No `listing_from_catalog`, no live OEM scrape. Client timeout 2.5s.
- **I know the robot** is an emerald panel on FIND step 1 (`border-2 border-emerald-400`, glow, `text-xl` / `text-emerald-200`). Label unchanged.
- Employer post: pdf/docx/txt plus title / employer / workplace / description. Filename always stored. Txt body extracted. PDF/Word keep the filename and the details fields. No invented employer or email. Hunter exists in-repo behind `HUNTER_API_KEY`; this door does not call it.

## Latency

| Path | Before | After |
|------|--------|-------|
| FIND identity | 12s client, same-origin Vercel rewrite (~90s if the proxy ignores abort) | 8s, Fly direct |
| FIND composed search | 30s client, same Vercel rewrite | 12s, Fly direct |
| Employer MATCH | `listing_from_catalog` on every SKU, every request | catalog snapshot, cached; pytest budget < 3s; client 2.5s |

## Tests that would have caught the bounce

- Vitest `findResearch.test.ts`: timeout / 500 / Failed to fetch / abort stay on `/?visit=jobs`; `/` and `/?new=1` bounce.
- Vitest `jobsLanding.test.ts`: `Jobs.tsx` cannot force landing while `visit=jobs`.
- Vitest `pstackRelease.test.ts` + critic gate `find_no_home`.
- `python3 scripts/agent_verify.py drive --feature find-stay` fails if `submitFind` calls `goJobsFreshHome`, writes `/?new=1`, or omits `ensureFindStayVisit`. Skip-green is a fail. A 7-second Deploy frontend skip is not proof.
- Employer: `drive --feature employer-match` plus pytest `< 3s` once `catalog_only` is live.

## Honest job-board answers

Verified in `app/api/employer_jobs.py`, `app/services/robot_job_lifecycle.py`, scrapers, Jobs CRM. Not guessed.

**Do employer posts go to an external job board, or only RFR `robot_jobs`?**  
Only RFR `robot_jobs`. `POST /api/employer-job-draft` calls `upsert_robot_job_from_extract`. There is no Indeed, LinkedIn, or outbound syndication from this door. Indeed URLs in `app/scrapers/scrape_targets.py` are **inbound** scrape sources for human job ads we turn into Robot Jobs. They are not a place we publish employer posts.

**Where does that board surface outside readyforrobots.com?**  
It does not. Employer drafts are rows in our database. They can show up later as FIND Job Cards on readyforrobots.com if the matcher picks them. There is no public job-board API, embed, or partner feed for these posts.

**Do we track candidate submissions for employers?**  
Not for this MATCH/POST door. There is no employer applicant inbox on `/?visit=candidates`. `JobApplication` in Jobs CRM is the other direction: a robot owner keeps a Job Card and applies. `employer_public_payload` is that OEM application token, not a queue of robots applying to an employer-posted draft.

**Do we introduce or schedule meetings with robot candidates?**  
No. This PR does not add a scheduler. OEM CRM can paste an `https` meeting URL (`we_schedule_with_employer`). Held interview slots are on that apply path. Employer-post copy does not promise intros or calendar.

Hunter.io is the future contact source (not Apollo). Page-only contacts still apply. No Hunter calls on this door unless a later PR finds `HUNTER_API_KEY` and wires it on purpose.
