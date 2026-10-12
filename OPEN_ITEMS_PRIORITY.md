# 🚨 Open Items - Priority Order

## Status: 5 Critical Items Need Attention

---

## 1. ❌ DELETE GUARD NOT CONFIRMED

**Status**: ⚠️ **SQL file exists but not confirmed as run in Supabase**

### What It Does
The delete guard (`migrations/sql/rfr_delete_guard_robot_jobs.sql`) prevents the 10/11 incident from happening again:

1. **ARCHIVE**: Every deleted row → `rfr_deleted_rows` table (as JSON)
2. **BRAKE**: Single statement can't delete >200 robot_jobs/signals or >50 companies without explicit opt-in
3. **UNDO**: `select restore_deleted_robot_jobs();` restores archived rows

### Protected Tables
- `robot_jobs` (limit: 200 rows)
- `job_evidence` (limit: 2,000 rows)
- `robot_job_matches` (limit: 5,000 rows)
- `signals` (limit: 200 rows)
- `companies` (limit: 50 rows)

### How to Override (Intentional Bulk Delete)
```sql
begin;
set local rfr.allow_bulk_delete = 'on';
delete from robot_jobs where ...;
commit;
```

### Action Required
**Run in Supabase SQL Editor**:
```bash
# Copy contents of migrations/sql/rfr_delete_guard_robot_jobs.sql
# Paste into Supabase → SQL Editor → Execute
```

**Verification**:
```sql
-- Should show triggers exist
SELECT tgname FROM pg_trigger WHERE tgname LIKE 'rfr_%';

-- Should show the archive table
SELECT * FROM rfr_deleted_rows LIMIT 1;
```

**Until this is run**: Another agent cleanup script could delete 14,500+ rows with no archive.

---

## 2. ❌ STAGE COUNTS NOT VERIFIED AFTER INDIRECT INTENT

**Status**: ⚠️ **Need to run `rank_buyers.py --apply` and verify counts**

### Why It Matters
With indirect intent + labor pressure scoring, the email will contain **significantly more companies**:
- **Evaluating**: Will grow (modernizing + labor pressure, exploring robots, cutting labor costs)
- **Preparing**: NEW stage (budgeting, modernizing alone, labor pressure alone)
- **Primed**: Will shrink (moved up to preparing/evaluating)

### Current Best Guess (Before Indirect Intent)
```
buying_now:       123
evaluating:       456
expanding:        234
primed:         8,901
watch:          3,456
```

### Expected After Indirect Intent
```
buying_now:       ~123 (unchanged - still requires explicit RFP/pilot)
evaluating:       ??? (could be 800-1,200+)
expanding:        ~234 (unchanged)
preparing:        ??? (NEW - could be 2,000-4,000+)
primed:           ??? (reduced significantly)
watch:            ??? (reduced)
```

### Email Impact
- **Old**: 499 companies (buying_now + evaluating)
- **New**: **Unknown** - could be 1,500+ or more

### Action Required

**On machine with DATABASE_URL** (local or Fly SSH):
```bash
python3 scripts/rank_buyers.py > /tmp/rank_preview.txt 2>&1

# Send the output showing:
# - Stage counts (buying_now, evaluating, expanding, preparing, primed, watch)
# - Top 40 companies with evidence
# - CSV location
```

**Then if counts look reasonable**:
```bash
python3 scripts/rank_buyers.py --apply
```

**Verification**: Check `reports/buyer_readiness.csv` for sanity.

---

## 3. ❌ DUPLICATE COMPANIES (Target)

**Status**: ⚠️ **Not checked - could be splitting evidence**

### The Problem
If Target has multiple rows in `companies`:
- Evidence split across rows
- Each row scores too low
- Target appears weaker than it really is

### Query to Check
```sql
SELECT name, COUNT(*) as row_count, 
       STRING_AGG(DISTINCT industry, ', ') as industries,
       STRING_AGG(DISTINCT website, ', ') as websites
FROM companies 
WHERE LOWER(name) LIKE '%target%'
GROUP BY name
HAVING COUNT(*) > 1
ORDER BY row_count DESC;
```

### If Duplicates Found
Need to:
1. Identify canonical row (best data completeness)
2. Merge signals from duplicates → canonical row
3. Update `signal.company_id` references
4. Delete duplicate rows
5. Re-run `rank_buyers.py --apply`

### Action Required
**Run the query** and report results. If Target (or other major buyers) have duplicates, we need to dedupe before the email goes out.

---

## 4. ❌ JUNK NAMES AT THE SOURCE

**Status**: ⚠️ **Scraper still saves junk as new companies**

### The Problem
Buyer ranking now **ignores**:
- Headline fragments ("How Robots Are Changing Airports")
- Place names ("Hoboken", "Henderson")
- Encoded strings (Base64 blobs)

**But the scraper still saves them** as new `companies` rows, so they keep accumulating.

### Where It Happens
- `app/scrapers/job_board_scraper_enhanced.py`
- `app/services/robot_job_extract.py`
- `app/services/robot_job_lifecycle.py`

### What's Needed
Add `buyer_name_problem()` check **before creating new company**:

```python
from app.services.buyer_readiness import buyer_name_problem

# Before saving new company
problem = buyer_name_problem(company_name)
if problem:
    logger.info(f"Skip company creation: {company_name} ({problem})")
    return None
```

### Impact if Not Fixed
- Database fills with junk company rows
- Wasted processing on every `rank_buyers.py` run
- Harder to find real buyers in company lists

### Action Required
Apply scraper-level filtering to prevent junk from being saved as companies in the first place.

---

## 5. ❌ API KEYS FOR BUYER-INTENT SOURCES

**Status**: ⚠️ **3 high-value source categories offline**

### Missing Keys (All Free)

#### SAM.gov (HIGHEST PRIORITY)
- **Why it matters**: Government RFPs/tenders → feeds directly into **Buying now**
- **26 searches** covering: robots, AMRs, autonomous scrubbers, ASRS, AutoStore, conveyors, etc.
- **Get key**: https://open.gsa.gov/api/sam-api/
- **Set on Fly**: `fly secrets set SAM_GOV_API_KEY="..."`

#### Adzuna
- **50 searches**: AMR tech, automation engineer at operators, hotel/kitchen robots
- **Get keys**: https://developer.adzuna.com/
- **Set on Fly**: `fly secrets set ADZUNA_APP_ID="..." ADZUNA_APP_KEY="..."`

#### Jooble
- **50 searches**: Same automation-hiring queries as Adzuna
- **Get key**: https://jooble.org/api/about
- **Set on Fly**: `fly secrets set JOOBLE_API_KEY="..."`

### Currently Running (No Keys Needed)
- ✅ 166 automation-hiring job board searches (Indeed, Monster, ZipRecruiter, etc.)
- ✅ 90 deployment news feeds (Google News RSS)
- ✅ 6 Amazon Jobs (RME, robotics, automation roles)
- ✅ 1 ATS boards seed (Greenhouse/Lever/Ashby - auto-discovered)

### Impact
Without SAM.gov: Missing federal/state/municipal **robot procurement tenders** - the highest-intent buying signals.

---

## Summary Priority Order

| # | Item | Severity | Blocks | Action |
|---|------|----------|--------|--------|
| 1 | **Delete guard** | 🔴 Critical | Future data safety | Run SQL in Supabase editor |
| 2 | **Stage counts** | 🟡 High | Tomorrow's email | Run rank_buyers.py, send counts |
| 3 | **Duplicate Target** | 🟡 High | Buyer scoring accuracy | Run deduplication query |
| 4 | **Junk at source** | 🟠 Medium | Database pollution | Add scraper-level filtering |
| 5 | **API keys** | 🟠 Medium | Buying now pipeline | Get free keys, set on Fly |

---

## Immediate Actions Needed

### Today (Before Tomorrow's Email)
1. ✅ Run delete guard SQL in Supabase
2. ✅ Run `rank_buyers.py` preview and send stage counts
3. ✅ Check for duplicate Target (and other major buyers)
4. ✅ If counts look good, run `rank_buyers.py --apply`

### This Week
1. ✅ Add junk name filtering to scraper
2. ✅ Get SAM.gov API key (highest priority)
3. ✅ Get Adzuna + Jooble keys

---

## Files Referenced

- `migrations/sql/rfr_delete_guard_robot_jobs.sql` - Delete guard (not confirmed as run)
- `scripts/rank_buyers.py` - Buyer ranking (needs DATABASE_URL)
- `app/scrapers/job_board_scraper_enhanced.py` - Needs junk filtering
- `docs/robot_opportunity_sources.csv` - Shows which sources need API keys

---

## Current Git State

```
4587e9d9 Document daily buyers email and indirect intent scoring
6c1b7098 Daily email sends robot buyers; read indirect intent and labor pressure
3046ad46 Document buyer readiness fixes: place name filtering with 8,908 locations
cf3262a7 Buyer readiness: catch every city/state/country as a place name
```

All code changes committed and pushed ✅  
**But operational setup incomplete** ⚠️
