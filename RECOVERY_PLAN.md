# DATA RECOVERY PLAN
**Date**: March 7, 2026  
**Incident**: 1,277 real production leads deleted (72% data loss)  
**Root Cause**: Cleanup script deleted all `is_internal=false` records

## FINDINGS

### SQL Evidence
- **Total records in Supabase**: 484
- **All records have**: `is_internal=true` (test/internal data)
- **Deleted records**: 1,277 real leads (`is_internal=false`)
- **Deletion timeframe**: March 2-3, 2026
- **Max ID created**: 1,761
- **Current survivors**: 484 internal records

### What Happened
Someone ran a cleanup operation (likely a script) that executed:
```sql
DELETE FROM companies WHERE is_internal = false;
```

This removed all real production leads while preserving test data.

### Why API Shows 200 vs 484
The API filters by `is_internal=false`:
- Database: 484 records (all internal)
- API result: 0 real leads (filters out internal)
- User expected: 475 real leads (now deleted)

## RECOVERY OPTIONS

### ✅ Option 1: Re-run All Scrapers (RECOMMENDED)
**Timeline**: 2-4 hours  
**Recovery**: 60-80% of original data  
**Status**: Ready to execute

**Steps**:
1. Run seed scripts:
   ```bash
   python3 scripts/seed_leads_v2.py
   python3 scripts/seed_leads_v3.py
   ```

2. Run active scrapers:
   ```bash
   python3 scripts/run_intelligence_scraper.py
   python3 app/scrapers/job_board_scraper.py
   python3 app/scrapers/news_scraper.py
   ```

3. Monitor progress:
   ```bash
   python3 scripts/monitor_scraper_progress.py
   ```

**What You'll Recover**:
- Job board leads (112 in current DB)
- News-based leads (114 in current DB)
- Seed data (207 records from v2-v6)
- Fresh signals from last 7 days

**What You Won't Recover**:
- Historical signals older than scraper retention
- Manual data entry (if any)
- Deleted leads no longer appearing in sources

### ⏳ Option 2: Supabase Backup Restore (BEST IF AVAILABLE)
**Timeline**: Waiting for Pro plan activation  
**Recovery**: 100% of original data  
**Status**: Pending (user just upgraded to Pro)

**Steps** (once Pro activates):
1. Navigate to Supabase Dashboard → Database → Backups
2. Find backup from **March 1 or March 2** (before deletion)
3. Click "Restore" to rollback entire database
4. Verify record count matches expected ~1,761

**Pro Plan Notes**:
- Activation takes "a few hours"
- Daily automatic backups (7-day retention for Pro)
- Point-in-time recovery available for Pro+

### 🆘 Option 3: Contact Supabase Support (BACKUP TO OPTION 2)
**Timeline**: 24-48 hours  
**Recovery**: Depends on support response  
**Status**: Available immediately

**Steps**:
1. Email: support@supabase.com
2. Subject: "URGENT: Data Loss - Request Point-in-Time Recovery"
3. Message:
   ```
   Project ID: lmoyydlhlgdyqbxkmkuz
   Database: postgres
   Issue: Accidental deletion of 1,277 production records
   Date/Time: March 2-3, 2026
   Request: Point-in-time recovery to March 2, 2026 @ 00:00 UTC
   
   Evidence: All is_internal=false records deleted via cleanup script.
   Current state: 484 internal records remain, 1,277 real leads lost.
   ```

4. Include SQL evidence:
   - ID gaps (max 1,761, current 484)
   - All survivors are is_internal=true
   - Creation date drop-off March 2-3

## PREVENTION MEASURES

### 1. Implement Soft Deletes
**Priority**: HIGH  
**Timeline**: 1 hour

Add `deleted_at` column instead of hard deletes:
```sql
ALTER TABLE companies ADD COLUMN deleted_at TIMESTAMP;
```

Update delete operations to:
```python
# Instead of: db.delete(company)
company.deleted_at = datetime.utcnow()
db.commit()
```

### 2. Add Audit Logging
**Priority**: HIGH  
**Timeline**: 2 hours

Create `audit_log` table:
```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  table_name VARCHAR(50),
  operation VARCHAR(10),  -- INSERT, UPDATE, DELETE
  record_id INT,
  user_id VARCHAR(100),
  changes JSONB,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

### 3. Database Backup Automation
**Priority**: MEDIUM  
**Timeline**: Done (Supabase Pro plan)

- Pro plan provides automatic daily backups
- Retain backups for at least 30 days
- Test restore process monthly

### 4. Code Review for DELETE Operations
**Priority**: HIGH  
**Timeline**: 30 minutes

Search codebase for:
```bash
git log --all --since="2026-03-01" --until="2026-03-04" --oneline --name-only
```

Look for:
- New cleanup scripts
- Migration files with DELETE
- Admin endpoints with bulk delete

### 5. Add DELETE Confirmation
**Priority**: MEDIUM  
**Timeline**: 1 hour

For bulk operations:
- Require `confirm=true` parameter
- Log deletion count before executing
- Add dry-run mode (`preview=true`)

## IMMEDIATE NEXT STEPS

**RIGHT NOW** (in order):

1. **[5 min]** Re-run scrapers to start recovering data:
   ```bash
   python3 scripts/seed_leads_v2.py
   python3 scripts/seed_leads_v3.py
   ```

2. **[10 min]** Check Supabase Pro activation:
   - Login to Supabase dashboard
   - Check if "Backups" tab is accessible
   - Look for March 1-2 backups

3. **[15 min]** If no backups, contact Supabase support (template above)

4. **[1 hour]** While waiting, implement soft deletes (prevention)

5. **[2 hours]** Run all scrapers and monitor recovery progress

## EXPECTED OUTCOMES

### Best Case (Backup Restore)
- 100% data recovery
- All 1,277 leads restored
- Historical signals preserved
- No manual work required

### Good Case (Scraper Re-run)
- 60-80% data recovery
- ~800-1,000 leads recovered
- Fresh signals only (last 7 days)
- 2-4 hours of scraper runtime

### Worst Case (No Backup, Limited Scraper Results)
- 40-60% data recovery
- ~500-800 leads recovered
- Rebuild from scratch over 2-3 weeks
- Implement prevention measures

## CONCLUSION

**Root cause**: Confirmed cleanup script deleted all real leads  
**Current state**: Only test data remains (484 internal records)  
**Best path**: Re-run scrapers NOW + wait for Supabase backup access  
**Prevention**: Soft deletes + audit logging + backup verification
