# 🚨 Required Actions - Database & Account Access Needed

## Current Status

✅ **All code changes complete and tested**  
✅ **All commits pushed to `origin/main`**  
⚠️ **3 operational tasks require YOUR access** (database + accounts)

---

## Tasks Requiring Your Action (In Order)

### 1. 🔴 CRITICAL: Run Delete Guard SQL (2 minutes)

**Why first**: Protects against accidental mass deletes before any row merging or AI agent database access.

**How**:
1. Open Supabase → SQL Editor
2. Copy entire contents of `migrations/sql/rfr_delete_guard_robot_jobs.sql`
3. Paste and Execute
4. Verify:
   ```sql
   -- Should show triggers
   SELECT tgname FROM pg_trigger WHERE tgname LIKE 'rfr_%';
   
   -- Should show archive table
   SELECT COUNT(*) FROM rfr_deleted_rows;
   ```

**What it does**:
- Archives every deleted row before deletion (undo possible)
- Blocks deletes >200 robot_jobs/signals or >50 companies without explicit opt-in
- Prevents another 14,500-row wipe

**Priority**: Do this BEFORE hygiene/ranking scripts run.

---

### 2. 🟡 Run Hygiene + Ranking Scripts (Need DATABASE_URL)

**Location**: Machine with `DATABASE_URL` configured (local or Fly SSH)

#### Step A: Hygiene Preview
```bash
python3 scripts/company_hygiene.py > /tmp/hygiene_output.txt 2>&1
```

**What to look for** (first lines of output):
```
Duplicate groups: ???
  Companies in groups: ???
  Total signals in grouped companies: ???

Junk company names: ???
  Total signals on junk: ???

Top duplicate groups by signals:
  Target (? rows, ??? signals)
    - Target (id=..., primary, ?? signals, target.com)
    - Target Corporation (id=..., ?? signals, target.com)
  Walmart (? rows, ??? signals)
    ...
  [Show top 15 groups]
```

**Send me**:
- Duplicate group count
- Total rows collapsed
- Top 15 duplicate groups with details

#### Step B: Re-score with Pooled Evidence
```bash
python3 scripts/rank_buyers.py > /tmp/rank_output.txt 2>&1
```

**What to look for**:
```
companies by stage:
  buying_now        ???
  evaluating        ???
  expanding         ???
  preparing         ??? (NEW)
  primed            ???
  watch             ???

top 40:
  buying_now  87.5  Clark County Department...
  buying_now  85.0  Hilton Hotels...
  evaluating  68.0  Target...
  ...
```

**Send me**:
- Stage counts (all 6 stages)
- Top 40 companies with stages + scores

**Then if counts look good**:
```bash
python3 scripts/rank_buyers.py --apply
```

**Why important**: Tomorrow's 14:00 UTC email will contain these companies. Need to verify:
- Evaluating + Preparing counts are reasonable (not 5,000 companies)
- Duplicate grouping didn't merge unrelated companies
- Major buyers (Target, Walmart, etc.) are in correct stages

---

### 3. 🟠 Set API Keys on Fly (Free Sign-ups)

#### SAM.gov (HIGHEST PRIORITY)
- **Why**: 26 government RFP/tender searches → feeds directly into **Buying now**
- **Sign up**: https://open.gsa.gov/api/sam-api/
- **Set on Fly**:
  ```bash
  fly secrets set SAM_GOV_API_KEY="your-key-here" -a ready-2-robot
  ```

#### Adzuna
- **Why**: 50 automation-hiring job searches (AMR tech, automation engineers at operators)
- **Sign up**: https://developer.adzuna.com/
- **Set on Fly**:
  ```bash
  fly secrets set ADZUNA_APP_ID="your-app-id" ADZUNA_APP_KEY="your-app-key" -a ready-2-robot
  ```

#### Jooble
- **Why**: 50 automation-hiring job searches (same queries as Adzuna)
- **Sign up**: https://jooble.org/api/about
- **Set on Fly**:
  ```bash
  fly secrets set JOOBLE_API_KEY="your-key-here" -a ready-2-robot
  ```

**All three are free** - just need account sign-up.

---

## After Review: Actual Row Merge (Future)

**Not done yet** - current state:
- ✅ Evidence pooled at scoring time (Target scores correctly)
- ✅ Email lists each company once with "Also listed as"
- ✅ Rows tagged in `crm_metadata.identity`
- ⚠️ Physical rows still separate in database

**When you're ready** (after reviewing duplicate CSV):
- I can write a merge script that:
  - Points all signals at primary company
  - Points all contacts at primary company
  - Points all CRM records at primary company
  - Soft-deletes duplicate rows
  - **Dry run first** to show exactly what will change

**Should happen**:
1. ✅ After delete guard is in place (protects from mistakes)
2. ✅ After you've reviewed `reports/duplicate_companies.csv`
3. ✅ After confirming grouping looks correct

---

## What I'm Waiting For

### From Task #1 (Delete Guard)
Just confirmation: "Delete guard SQL executed successfully"

### From Task #2 (Hygiene + Ranking)
**Hygiene output** (first ~30 lines):
- Duplicate group count + total rows
- Top 15 duplicate groups with row counts and signals
- Junk name count

**Ranking output** (stage section):
- 6 stage counts (buying_now, evaluating, expanding, preparing, primed, watch)
- Top 40 companies

**Critical question**: Does the duplicate grouping look right?
- Is Target grouped correctly?
- Any obvious mistakes (unrelated companies merged)?
- Are the stage counts reasonable for tomorrow's email?

### From Task #3 (API Keys)
Just confirmation when keys are set. Sources will auto-enable once env vars are present.

---

## Timeline Concern

**Tomorrow 14:00 UTC** = daily email goes out with buyer list

**Need before then**:
1. ✅ Delete guard (protects future operations)
2. ✅ Stage counts verified (email won't be unexpectedly huge)
3. ⚠️ API keys can wait (won't affect tomorrow's email, just future sourcing)

---

## Current Data Reality Check

**Last known real figure**: 11,750 companies with signals

**Unknown until hygiene script runs**:
- How many duplicate groups?
- How many rows collapse?
- How many junk names?
- Stage distribution with indirect intent + pooled evidence?

All estimates in documentation were **guesses without data**. Real numbers come from the scripts you'll run.

---

## Files Ready for You

| File | Purpose | Location |
|------|---------|----------|
| Delete guard SQL | Protect from mass deletes | `migrations/sql/rfr_delete_guard_robot_jobs.sql` |
| Hygiene script | Find duplicates + junk | `scripts/company_hygiene.py` |
| Ranking script | Score with pooled evidence | `scripts/rank_buyers.py` |
| Hygiene output | Duplicate + junk CSVs | `reports/duplicate_companies.csv` + `reports/junk_company_names.csv` |
| Ranking output | Buyer list CSV | `reports/buyer_readiness.csv` |

---

## Summary

**Code complete**: ✅ All functionality implemented and tested  
**Deployed**: ✅ All commits pushed to `main`  
**Blocked on**: ⚠️ Your database access + account credentials

Next step: **You run the 3 tasks above and send me the outputs.**

I'll review the duplicate grouping and stage counts, then confirm it's safe for tomorrow's email to go out at 14:00 UTC.
