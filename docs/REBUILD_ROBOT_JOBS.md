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

## The goal (Bob, 2026-10-11)

We are looking for **companies ready to buy or pilot robots** — not robot labor
jobs. Labor postings are kept only as company-level pain evidence; they are
never leads by themselves.

## Get a buyer list from what survived (tonight)

`signals` (56,139 `robot_job` rows + every other signal type) and `companies` were
never touched. Rank companies straight from them:

```bash
python3 scripts/rank_buyers.py                     # dry run: stage counts, top 40, reports/buyer_readiness.csv
python3 scripts/rank_buyers.py --apply             # stamp companies.automation_profile.buyer_readiness
python3 scripts/rank_buyers.py --min-stage evaluating --csv hot_buyers.csv
```

Stages: **buying_now** (tender / pilot / vendor selection) → **evaluating**
(automation hires, automation program or investment, new automated facility) →
**expanding** (already runs robots) → **primed** (heavy pain at scale only, capped
at 45/100) → watch. Robot vendors are always "watch".

## Restore robot_jobs (optional)

```bash
python3 scripts/rebuild_robot_jobs.py count
python3 scripts/rebuild_robot_jobs.py from-backup --source-url "postgresql://…restored…" [--apply]
python3 scripts/rebuild_robot_jobs.py from-signals [--apply]    # restores only automation-intent postings
python3 scripts/reclassify_robot_jobs.py [--apply]              # re-tier; never deletes
```

## Never again

Run `migrations/sql/rfr_delete_guard_robot_jobs.sql` once in the Supabase SQL editor:

* every deleted row of `robot_jobs`, `job_evidence`, `robot_job_matches`, `signals`,
  `companies` is archived to `rfr_deleted_rows` first;
* one statement can't delete more than 200 jobs/signals (50 companies) unless the
  session runs `set local rfr.allow_bulk_delete = 'on'`;
* `select restore_deleted_robot_jobs();` undoes a purge.

Also: turn on Point-in-Time Recovery in Supabase (Database → Backups) if the plan
allows it, and keep agent sessions on a database role without DELETE on these tables.

## How evidence is scored

`app/services/workflow_ontology.py` classifies one posting/headline (48 workflow
families mapped to robot categories in `vendors.csv`): tier 1 = automation
intent → `robot_jobs`; tiers 2–3 = labor posting → `labor_pain` signal only;
tier 0 = vendors/builders/desk work → dropped.
`app/services/buyer_readiness.py` rolls all of a company's evidence into a stage
and score with the evidence lines that justify it.

## Sources

`app/scrapers/robot_opportunity_sources.py` — 389 buyer-intent sources
(full list: `docs/robot_opportunity_sources.csv`):

| Lane | Count | Key needed |
|---|---|---|
| Automation hiring at operators — job boards (AMR/robotics/automation techs & engineers, kitchen/hotel/cleaning robots), national + 15 metros + Las Vegas | 166 | no |
| Deployment & intent news (Google News RSS) — 30 robot vendors' named customers, pilots, automation programs, new automated facilities, RFP news | 90 | no |
| Amazon Jobs (RME / robotics / automation roles) | 6 | no |
| Adzuna + Jooble (same automation-hiring queries) | 100 | free |
| SAM.gov tenders (robot, AMR, scrubber, conveyor, ASRS …) | 26 | free |
| ATS boards (Greenhouse/Lever/Ashby/SmartRecruiters/Workday) | 1 seed + auto-discovered | no |

Job-board rotation now leads with these automation-hiring searches; the old
labor-title searches only fill 4 rotating slots (`JOB_SCRAPER_LEGACY_URLS_PER_RUN`).

Env knobs: `ENABLE_OPPORTUNITY_FEEDS`, `OPPORTUNITY_FEEDS_EVERY_MINUTES` (60),
`OPPORTUNITY_FEEDS_MAX_SOURCES` (60), `JOB_SCRAPER_LEGACY_URLS_PER_RUN` (4),
`ENABLE_ONTOLOGY_TARGETS`, and the API keys in `robot_opportunity_sources.py`.

## Indirect buying signals and the daily buyers email (2026-10-12)

Buyers rarely say "we will buy a robot". `buyer_readiness.py` now also reads:

* **Indirect intent** — budgeting / capex, modernizing or upgrading operations,
  redesigning or realigning workflows, efficiency and cost programs, labor-cost
  focus, workforce transformation, next-gen facilities, new DCs/plants/kitchens.
* **Labor pressure** — shortages, high turnover, can't staff, wage pressure,
  service cuts from staffing, injuries — weighted fully only in labor-heavy
  industries (restaurants, warehouses/logistics, retail/grocery, janitorial,
  airports, commercial laundry, hotels/casinos, factories, hospitals, farms).
* **Typed signals** already in `signals`: `budget_allocated`, `capex`,
  `scale_expansion`, `roi_documented`, `economics_driven`, `labor_shortage`, …

Rules: modernizing **and** under labor pressure → Evaluating. Indirect intent or
labor pressure alone → new **Preparing** stage. Job-posting boilerplate never
counts as company intent.

**Daily email** (same 14:00 UTC schedule, same endpoint/recipients) now sends
companies, not robot jobs: re-scores everyone, then lists every Buying now and
Evaluating company with up to 3 evidence lines and links, the top 40 Preparing,
and a CSV (`robot-buyers-YYYY-MM-DD.csv`) with all of them.

| Env | Default | |
|---|---|---|
| `DAILY_REPORT_MODE` | `buyers` | `jobs` restores the old robot-jobs email |
| `DAILY_BUYERS_STAGES` | `buying_now,evaluating,preparing` | which stages to send |
| `DAILY_BUYERS_REFRESH` | `1` | re-score all companies before sending |

## Duplicate companies and junk names (2026-10-12)

`app/services/company_identity.py` decides whether a string is a company and
which company it is.

* **At ingest** every scraper now reuses the existing row for name variants
  ("Target" / "Target Corporation" / "TARGET CORP." / "Target Stores", "Wal-Mart" /
  "Walmart", "Kenco Logistics" → "Kenco Group") or the same own website domain,
  instead of inserting a duplicate. Place names, encoded strings and headline
  fragments are refused before INSERT.
* **At ranking** duplicates that already exist are scored once on their pooled
  evidence; every row gets the same stage, one row is marked primary, and the
  daily email lists each company once ("Also listed as: …").
* Conservative: only legal/corporate suffixes are stripped; properties stay
  separate from parents (JW Marriott Las Vegas ≠ Marriott International);
  shared sites (linkedin.com, indeed.com, press-release wires) never link companies.

Existing rows: `python3 scripts/company_hygiene.py` writes
`reports/duplicate_companies.csv` and `reports/junk_company_names.csv`;
`--apply` tags them in `crm_metadata` (`identity`, `junk_name`). Nothing is deleted
or merged — review the CSVs first.
