# Backup Restore Guide - Path to 1,000 Leads

## Current Status
- ✅ March 1-2 backup restored: **162 real leads, 1,333 signals**
- 🎯 Goal: **1,000 leads**
- 📊 Progress: **16.2%** (838 more needed)

## Restore Strategy

### Phase 1: Restore More Backups ⏳ IN PROGRESS
Continue restoring backup files in Supabase dashboard:

1. Go to: https://supabase.com/dashboard/project/lmoyydlhlgdyqbxkmkuz
2. Navigate to: Settings → Database → Backups
3. Restore backups from:
   - February 25-28, 2026
   - February 20-24, 2026
   - February 15-19, 2026
   - (Keep going back until you hit 800-900 leads)

**After each restore, monitor progress:**
```bash
./scripts/monitor_lead_count.sh
```

### Phase 2: Run Scrapers (Once at 800+ leads)
When you're at 800-900 leads from backups, run scrapers to fill the gap:

**Option A: Deploy scrapers to Fly.io (RECOMMENDED)**
```bash
# Fly.io has IPv6 and will connect to Supabase
flyctl deploy --remote-only

# Then SSH in and run scrapers
flyctl ssh console
export DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"
python3 /app/scripts/scraper_batch_runner.py
```

**Option B: Use Supabase Functions (Alternative)**
Upload scrapers as Supabase Edge Functions to run directly in Supabase environment

**Option C: Local via VPN/Proxy (If IPv6 fixed)**
Only works if you can resolve the IPv6 connection issue from your Mac

### Phase 3: Verify & Celebrate
```bash
# Check final count
./scripts/monitor_lead_count.sh

# View dashboard with 1,000+ leads
open https://ready-2-robot.fly.dev
```

## Monitoring Tools

### Quick Lead Count Check
```bash
./scripts/monitor_lead_count.sh
```

Shows:
- Current lead count (real vs test)
- Progress to 1,000 goal
- Top industries
- Signal count
- Visual progress bar

### API Check (Raw Data)
```bash
curl -s 'https://ready-2-robot.fly.dev/api/leads' | python3 -c \
  'import sys, json; leads = json.load(sys.stdin); \
   print(f"Total: {len(leads)}, Real: {len([l for l in leads if not l.get(\"is_internal\")])}")'
```

### Database Direct Query (via Supabase SQL Editor)
```sql
-- Total leads
SELECT COUNT(*) FROM companies;

-- Real vs test
SELECT is_internal, COUNT(*) FROM companies GROUP BY is_internal;

-- Industry breakdown
SELECT industry, COUNT(*) as count 
FROM companies 
WHERE is_internal = false 
GROUP BY industry 
ORDER BY count DESC;

-- Signal count
SELECT COUNT(*) FROM signals;
```

## Scraper Capabilities (When Ready)

| Scraper | Est. Leads | Speed | Industries |
|---------|-----------|-------|------------|
| Seed Leads v2 | 50 | Fast | Core (Logistics, Hospitality, Healthcare) |
| Seed Leads v3 | 40 | Fast | Extended (Food Service, Retail, Pharma) |
| Job Board | 100 | Medium | All (hiring signals) |
| News Scraper | 80 | Medium | All (funding, expansion) |
| Logistics Dir | 60 | Slow | Logistics, Warehousing |
| Hotel Dir | 50 | Slow | Hospitality |

**Total potential:** ~380 new leads from scrapers

## Connection Issues

Your Mac has IPv6 connection issues to Supabase direct port 5432:
```
❌ db.lmoyydlhlgdyqbxkmkuz.supabase.co:5432 - Connection refused (IPv6)
```

**Solutions:**
1. ✅ **Use Fly.io** - Deployment has full IPv6 support
2. Use Supabase SQL Editor for direct DB access
3. Fix local IPv6 routing (advanced, not recommended)

## Next Steps

1. **Keep restoring backups** until you reach 800-900 leads
2. **Monitor progress** with `./scripts/monitor_lead_count.sh`
3. **When ready**, deploy scrapers to Fly.io to reach 1,000+
4. **Celebrate** when you hit the goal! 🎉

## Important Notes

- ✅ Scrapers will ADD leads (not delete existing)
- ✅ All scrapers mark real leads as `is_internal=false`
- ✅ Duplicate detection prevents double-adding same companies
- ✅ Fly.io deployment already connected to Supabase
- ✅ Frontend shows all restored data in real-time

## Questions?

- Check dashboard: https://ready-2-robot.fly.dev
- Monitor script: `./scripts/monitor_lead_count.sh`
- View this guide: `cat BACKUP_RESTORE_GUIDE.md`
