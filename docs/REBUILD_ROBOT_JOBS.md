# Rebuilding Robot Jobs after the 2026-10-11 purge

## What happened

`scripts/clean_human_labor_from_robot_jobs.py` (commit `0ed0c14`) deleted every
`robot_jobs` row whose title contained an occupation word (*cook, picker,
driver, receiver…*) **or** hiring language (*$, hiring, full-time, benefits…*).
That is nearly every Robot Job. `job_evidence` and `robot_job_matches` went with
them (ON DELETE CASCADE). In the same commit the scraper was changed to **reject**
those postings at ingest, so re-scraping rebuilt nothing.

Both are reverted in thinking and in code: an operational posting is the evidence
that work a robot can do exists at a named employer. It is the product.

## Recover (in this order)

```bash
# 0. What survived? (signals + companies were never touched)
python3 scripts/rebuild_robot_jobs.py count

# 1. Best: a Supabase backup from before 2026-10-11 ~5pm PT.
#    Restore it into a NEW project or branch — not over production — then:
python3 scripts/rebuild_robot_jobs.py from-backup --source-url "postgresql://…restored…"          # dry run
python3 scripts/rebuild_robot_jobs.py from-backup --source-url "postgresql://…restored…" --apply  # copy jobs + evidence + matches

# 2. Also (or instead): rebuild from surviving `signals` rows (signal_type = 'robot_job')
python3 scripts/rebuild_robot_jobs.py from-signals            # dry run, prints sample + counts
python3 scripts/rebuild_robot_jobs.py from-signals --apply

# 3. Re-tier everything with the new ontology (never deletes)
python3 scripts/reclassify_robot_jobs.py --apply
```

Both recovery paths upsert on `job_key`, so they are safe to re-run and safe to
combine. `from-signals` restores employer, title, location, pay, specs, status,
source URL and original timestamp; full descriptions come back on the next scrape
of the same posting (same `job_key`).

## Never again

Run `migrations/sql/rfr_delete_guard_robot_jobs.sql` once in the Supabase SQL editor:

* every deleted row of `robot_jobs`, `job_evidence`, `robot_job_matches`, `signals`,
  `companies` is archived to `rfr_deleted_rows` first;
* one statement can't delete more than 200 jobs/signals (50 companies) unless the
  session runs `set local rfr.allow_bulk_delete = 'on'`;
* `select restore_deleted_robot_jobs();` undoes a purge.

Also: turn on Point-in-Time Recovery in Supabase (Database → Backups) if the plan
allows it, and keep agent sessions on a database role without DELETE on these tables.

## How opportunities are scored now

`app/services/workflow_ontology.py` — 48 workflow families (picking, palletizing,
machine tending, warewash, EVS, security patrol, harvest, sorting, …), each mapped
to robot categories from `docs/calibration/vendor_seed_sheets/vendors.csv`.

| Tier | Meaning | Example |
|---|---|---|
| 1 | **Automation intent** — robots/AMRs named, automation/CI hire at an operator, RFP | "Maintenance Tech — palletizing robots", SAM.gov "Autonomous scrubbers" |
| 2 | **Automation-ready** — automatable work + staffing pain, or work robots already do at scale | Order Picker with sign-on bonus, EVS Tech, Janitor |
| 3 | **Automatable work** — fit only | Line Cook, Dishwasher, Room Attendant |
| 0 | Not an opportunity — robot builders, desk work. The only thing dropped. | Robotics Software Engineer at an OEM |

`requirements.opportunity` stores the score, families, robot categories, example
vendors, and the intent/pain evidence for each job.

## Sources

`app/scrapers/robot_opportunity_sources.py` generates 431 sources from the ontology
(full list: `docs/robot_opportunity_sources.csv`):

| Lane | Count | Key needed |
|---|---|---|
| Job-board searches (Indeed/SimplyHired), all families + 15 metros + Las Vegas casino roles | 220 | no |
| Intent news (Google News RSS: deployments, new DCs, labor shortage, RFPs) | 60 | no |
| Amazon Jobs JSON | 12 | no |
| Adzuna / Jooble (one query per family) | 96 | free |
| USAJOBS | 16 | free |
| SAM.gov tenders (robot / automation / scrubber / AMR …) | 26 | free |
| ATS boards (Greenhouse/Lever/Ashby/SmartRecruiters/Workday) | 1 seed + auto-discovered | no |

ATS boards are discovered from apply links seen while scraping and polled hourly;
boards that 404 three times are disabled.

Env knobs: `ENABLE_OPPORTUNITY_FEEDS`, `OPPORTUNITY_FEEDS_EVERY_MINUTES` (60),
`OPPORTUNITY_FEEDS_MAX_SOURCES` (60), `JOB_SCRAPER_ONTOLOGY_URLS_PER_RUN` (8),
`ENABLE_ONTOLOGY_TARGETS`, plus the API keys listed in `robot_opportunity_sources.py`.
