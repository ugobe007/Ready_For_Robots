# 🎯 Buyer Readiness System — Implementation Complete

## Executive Summary

**ReadyForRobots has been transformed from a job board scraper into a buyer intelligence platform.**

The patch `rebuild-robot-jobs__1__e01b.patch` has been applied successfully to `main`. All 13 new tests pass. The system now classifies **companies** by their readiness to buy or pilot robots, rather than treating labor postings as individual leads.

---

## What Changed (Architecture)

### Before
- **Unit of value**: Individual job posting (e.g. "warehouse picker needed")
- **Problem**: 56,139 signals, mostly labor postings, treated as robot opportunities
- **Outcome**: "9 months of building the job listings and it is all garbage" — user quote

### After
- **Unit of value**: Company buying readiness stage (buying_now → evaluating → expanding → primed → watch)
- **Evidence model**: All signals per company (news, RFPs, hiring patterns, labor pain) → one classification
- **Outcome**: Real buyers surface automatically with evidence lines that justify the stage

---

## Buyer Readiness Stages

| Stage | What It Takes | Score Range | Example Evidence |
|-------|--------------|-------------|------------------|
| **buying_now** | Tender/RFP, pilot, "evaluating vendors" for robots or automation | 70-100 | "RFP for autonomous floor scrubbing robots" |
| **evaluating** | Hiring automation/robotics staff at operator; automation investment; new automated facility | 50-70 | "$200M automation investment announced" |
| **expanding** | Already runs robots (e.g. "maintain AMRs", "work alongside robots") | 40-50 | "AMR technician needed to maintain fleet" |
| **primed** | Heavy automatable work pain, but no buying intent yet | 15-45 | "20 open warehouse positions, hiring bonuses" |
| **watch** | Robot vendors, software "automation" (QA/RPA/marketing) | <15 | "Locus Robotics raises Series D" |

**Key rule**: Labor postings alone **cap at 45 points** (primed stage). They never make a company a buyer by themselves.

---

## New Files & Services

### 1. `app/services/buyer_readiness.py` (237 lines)

Company classification engine. Core function:

```python
assess_company(company_name: str, signals: list[dict]) -> BuyerReadiness
```

Returns:
- `stage`: buying_now | evaluating | expanding | primed | watch
- `score`: 0-100
- `evidence`: Top evidence lines with labels (tender/RFP, pilot, automation program, etc.)
- `why`: One-line summary
- `workflows`: Identified automatable workflows (picking, packing, cleaning, etc.)
- `pain_labels`: Labor shortage, hazardous work, etc.

**Signal scoring**:
- **BUY_NOW** patterns: +25 to +40 points (RFP, tender, pilot, vendor selection, purchase)
- **EVALUATING** patterns: +12 to +25 points (automation program, investment, new facility)
- **EXPANDING** patterns: +18 points (robot ops roles, "work alongside robots")
- **PAIN** patterns: +2 to +6 points per posting (labor shortage, bonuses, urgent hiring, hazardous work)

**Exclusions**:
- Robot vendors (Locus, Symbotic, Bear, Knightscope, etc.) → always "watch"
- Vendor funding/launch stories → not buyer evidence
- Software "automation" (QA, RPA, marketing automation, Selenium) → not robot work

### 2. `scripts/rank_buyers.py` (104 lines)

Batch ranking script that reads **every signal per company** and stamps the database.

**Usage**:

```bash
# Dry run: stage counts, top 40, CSV
python3 scripts/rank_buyers.py

# Stamp companies.automation_profile.buyer_readiness
python3 scripts/rank_buyers.py --apply

# Only export hot buyers (buying_now + evaluating)
python3 scripts/rank_buyers.py --min-stage evaluating --csv hot_buyers.csv

# Show top 100 instead of 40
python3 scripts/rank_buyers.py --top 100
```

**Output**: `reports/buyer_readiness.csv` with columns:
- company, stage, score, why
- evidence_1, evidence_2, evidence_3, evidence_url
- workflows, open_automatable_postings, pain
- industry, city, state, website

### 3. `tests/test_buyer_readiness.py` (13 tests, all passing)

Test coverage:
- ✅ Tenders/RFPs → buying_now (Clark County, Hilton, MGM)
- ✅ Automation investment → evaluating (Sysco, Walmart, Kroger)
- ✅ Already running robots → expanding (GEODIS)
- ✅ Labor postings alone → primed (capped at 45)
- ✅ Robot vendors excluded → watch (Locus Robotics)
- ✅ Software "automation" excluded → watch (SaaSCo QA)
- ✅ End-to-end script test (dry run mode)

---

## Scraper Changes

### `app/scrapers/job_board_scraper_enhanced.py`

**Old behavior**: Every job posting → `robot_jobs` table

**New behavior**:
- **Tier 1** (automation intent): "AMR technician", "automation engineer at operator", "maintain robots" → `robot_jobs` (opportunities)
- **Tier 2-3** (labor pain): "warehouse picker", "dishwasher", "forklift driver" → `labor_pain` signals only (background evidence)
- **Tier 0** (not relevant): Robot vendor jobs, software QA, RPA → dropped

### `app/scrapers/robot_opportunity_sources.py`

**389 buyer-targeted sources** (was: generic job board searches):

| Lane | Count | Description | API Key |
|------|-------|-------------|---------|
| **automation_hiring** | 166 | AMR/ASRS/automation tech & engineer searches at operators; hotel/kitchen/cleaning robot roles (15 metros + Las Vegas) | no |
| **deployment_news** | 90 | Google News RSS: 30 robot vendors' named customers (Locus, Symbotic, Brain Corp, Bear, Knightscope, etc.), pilots, RFPs, automation investments, new facilities | no |
| **amazon_jobs** | 6 | RME / robotics / automation roles at Amazon | no |
| **adzuna** | 50 | Same automation-hiring queries on Adzuna | free API key |
| **jooble** | 50 | Same automation-hiring queries on Jooble | free API key |
| **sam_gov** | 26 | Federal tenders (robot, AMR, scrubber, conveyor, ASRS) | free API key |
| **ats_boards** | 1 seed | Greenhouse/Lever/Ashby/SmartRecruiters/Workday (auto-discovered from news/posting links) | no |

Full list: `docs/robot_opportunity_sources.csv` (header + 389 rows)

---

## Your 56,139 Signals Are Safe

Nothing was deleted. The ranking script reads:
- `signals` table (intact: all 56,139+ `robot_job` signals + every other type)
- `companies` table (intact: all company records)

Expected distribution after first run:
- **primed**: ~80-90% (most signals are labor posting titles = pain evidence only)
- **buying_now**: ~1-3% (RFPs, pilots, vendor selection from existing news/tender signals)
- **evaluating**: ~5-10% (automation hires, investments, new facilities from existing signals)
- **expanding**: ~2-5% (robot ops roles already in the data)
- **watch**: ~5-10% (robot vendors, software automation)

**As new sources run**, more companies will move from "primed" to active buyer stages.

---

## What to Run Next

### 1. Preview the buyer list (local or Fly)

**Local** (if you have DATABASE_URL in `.env`):
```bash
python3 scripts/rank_buyers.py
```

**Fly SSH**:
```bash
fly ssh console -a ready-2-robot
cd /code
python3 scripts/rank_buyers.py
```

**Expected output**:
```
companies by stage:
  buying_now       123
  evaluating       456
  expanding        234
  primed         8,901  ← Most companies (labor pain evidence only)
  watch          3,456

top 40:
  buying_now   87.5  Clark County School District   tender / RFP: request for proposals autonomous floor scrubbing
  buying_now   85.0  Hilton Hotels Corporation      pilot / trial: piloting autonomous room service robots
  evaluating   68.0  Sysco Corporation              automation program: $200M automation investment announced
  ...

CSV: reports/buyer_readiness.csv  (9,714 companies at stage >= primed)
DRY RUN — companies not stamped. Re-run with --apply.
```

### 2. Apply buyer stages to database

After verifying the preview:
```bash
python3 scripts/rank_buyers.py --apply
```

This stamps `companies.automation_profile.buyer_readiness` with stage, score, evidence, and workflows for each company (commits in batches of 500).

### 3. Check signal type distribution

```sql
SELECT signal_type, COUNT(*) 
FROM signals 
GROUP BY 1 
ORDER BY 2 DESC;
```

Expected:
- `job_posting` → largest (labor pain evidence)
- `news` → buying intent (deployments, investments, RFPs)
- `rfp` → strong buying intent (tenders)
- `company_info` → metadata

### 4. Query buyer pipeline

After `--apply`:

```sql
-- Hot buyers (buying_now + evaluating)
SELECT name, 
       automation_profile->>'buyer_readiness'->>'stage' as stage,
       automation_profile->>'buyer_readiness'->>'score' as score,
       automation_profile->>'buyer_readiness'->>'why' as why
FROM companies
WHERE automation_profile->>'buyer_readiness'->>'stage' IN ('buying_now', 'evaluating')
ORDER BY (automation_profile->>'buyer_readiness'->>'score')::float DESC
LIMIT 50;
```

---

## Git History

```
03123c7a Add buyer readiness deployment guide
316b8239 Target companies ready to buy robots, not labor postings
b41f3dfe Rebuild robot_jobs after purge; ontology-driven opportunity scoring; 431 sources
```

All committed to `main` and pushed to `origin`.

---

## Test Results

```bash
$ python3 -m pytest tests/test_buyer_readiness.py -v

tests/test_buyer_readiness.py::test_stages[Clark County-signals0-buying_now] PASSED
tests/test_buyer_readiness.py::test_stages[Hilton-signals1-buying_now] PASSED
tests/test_buyer_readiness.py::test_stages[MGM Resorts-signals2-buying_now] PASSED
tests/test_buyer_readiness.py::test_stages[Sysco-signals3-evaluating] PASSED
tests/test_buyer_readiness.py::test_stages[Walmart-signals4-evaluating] PASSED
tests/test_buyer_readiness.py::test_stages[Kroger-signals5-evaluating] PASSED
tests/test_buyer_readiness.py::test_stages[GEODIS-signals6-expanding] PASSED
tests/test_buyer_readiness.py::test_stages[Big Grocer DC-signals7-primed] PASSED
tests/test_buyer_readiness.py::test_not_buyers[Wynn Las Vegas-signals0] PASSED
tests/test_buyer_readiness.py::test_not_buyers[SaaSCo-signals1] PASSED
tests/test_buyer_readiness.py::test_not_buyers[Locus Robotics-signals2] PASSED
tests/test_buyer_readiness.py::test_labor_postings_alone_never_exceed_primed PASSED
tests/test_buyer_readiness.py::test_rank_buyers_script_end_to_end PASSED

============================== 13 passed in 0.66s ==============================
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SIGNALS (56,139+ rows)                       │
│  • job_posting (labor titles)                                    │
│  • news (deployments, investments, RFPs)                         │
│  • rfp (tenders)                                                 │
│  • company_info                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │  scripts/rank_buyers.py                │
        │  • Groups signals by company           │
        │  • Calls assess_company() per company  │
        │  • Writes CSV + stamps DB              │
        └────────────┬───────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │  app/services/buyer_readiness.py       │
        │  • BUY_NOW patterns (+25 to +40)       │
        │  • EVALUATING patterns (+12 to +25)    │
        │  • EXPANDING patterns (+18)            │
        │  • PAIN patterns (+2 to +6, capped)    │
        │  • Vendor exclusion                    │
        │  • Returns stage + score + evidence    │
        └────────────┬───────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │  COMPANIES.automation_profile          │
        │  {                                     │
        │    "buyer_readiness": {                │
        │      "stage": "buying_now",            │
        │      "score": 87.5,                    │
        │      "why": "tender / RFP: ...",       │
        │      "evidence": [...],                │
        │      "workflows": ["picking"],         │
        │      "pain_labels": ["labor shortage"] │
        │    }                                   │
        │  }                                     │
        └────────────────────────────────────────┘
```

---

## Why This Works

1. **Ontology-grounded**: Buyer patterns (RFPs, pilots, automation hires) are explicit and defensible
2. **Evidence-based**: Every stage has 1-3 evidence lines showing **why** the company is at that stage
3. **Conservative**: Labor postings alone **cap at 45** (primed), never buyer status
4. **Vendor-aware**: Locus, Symbotic, Bear, etc. are **always** excluded from buyer pipeline
5. **Comprehensive**: Uses **all** existing signals (56k+ rows) without re-scraping
6. **Targeted sources**: 389 new sources focus on **operators hiring automation staff** and **news about deployments/RFPs**

---

## Next Steps After Database Run

1. **Export hot buyers**: `python3 scripts/rank_buyers.py --min-stage evaluating --csv hot_buyers.csv`
2. **Verify Jobs frontend** uses buyer_readiness data for qualification/ranking
3. **Run new scraper sources** to populate buying_now/evaluating pipeline (tenders, pilots, automation hires)
4. **Monitor stage distribution** over time (expect shift from primed → evaluating → buying_now as new sources run)

---

## Questions?

- **"Why are most companies primed?"** — Because most of your 56k signals are labor posting titles (pain evidence only). As buyer-targeted sources run, the pipeline will fill with real buyers.
- **"Are labor postings deleted?"** — No. They're kept as `labor_pain` signals (company-level background evidence).
- **"What about the old robot_jobs table?"** — The script reads from `signals` (not `robot_jobs`). You can optionally restore `robot_jobs` from signals with `scripts/rebuild_robot_jobs.py from-signals`.
- **"Can I see the evidence for a company?"** — Yes: `companies.automation_profile.buyer_readiness.evidence` after `--apply`, or in the CSV columns `evidence_1`, `evidence_2`, `evidence_3`.

---

## Success Metrics

✅ All 13 buyer readiness tests passing  
✅ 389 buyer-targeted sources loaded  
✅ Vendor exclusion working (Locus → watch)  
✅ Labor posting cap working (45 max for pain alone)  
✅ Patch applied cleanly to main  
✅ No signals deleted (56,139+ intact)  
✅ Zero new test failures in existing test suite  

**Status**: Ready to run `python3 scripts/rank_buyers.py` and generate your first buyer list. 🚀
