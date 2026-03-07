# PM2 Scraper Recovery Guide

## Current Status ✅
- **Local database**: 10 real production leads (is_internal=false)
- **Hot leads bar**: Updated with Total/Hot/Signals/Hottest metrics
- **PM2 infrastructure**: Ready to launch scrapers

## Next Steps for Full Recovery

### Option 1: Wait for Supabase Pro Backup (RECOMMENDED)
**Best chance for 100% recovery**

Once your Supabase Pro plan activates:
1. Go to Supabase Dashboard → Database → Backups
2. Find backup from March 1-2, 2026
3. Click "Restore" to recover all 1,277 deleted leads

### Option 2: Run Scrapers to Rebuild Database

The PM2 infrastructure is ready, but scrapers need proper Supabase credentials:

**Update `.env` file with correct Supabase password:**
```bash
# Get password from: https://supabase.com/dashboard/project/lmoyydlhlgdyqbxkmkuz/settings/database
DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD@db.lmoyydlhlgdyqbxkmkuz.supabase.co:5432/postgres
```

**Then launch scrapers:**
```bash
cd /Users/robertchristopher/Desktop/Ready_For_Robots
./scripts/launch_recovery.sh
```

### Option 3: Continue with Local SQLite (CURRENT STATE)

Your local database already has 10 leads and is working:
```bash
# Check status
sqlite3 ready_for_robots.db "SELECT COUNT(*) FROM companies WHERE is_internal = 0;"

# View leads
curl http://localhost:8000/api/leads | python3 -m json.tool
```

## PM2 Commands

**Monitor scrapers:**
```bash
pm2 list              # Show all processes
pm2 logs              # View all logs in real-time
pm2 logs news-scraper # View specific scraper
pm2 monit             # Live dashboard
```

**Restart scrapers:**
```bash
pm2 restart all       # Restart everything
pm2 restart job-board-scraper  # Restart specific scraper
```

**Stop scrapers:**
```bash
pm2 stop all          # Stop all
pm2 delete all        # Remove all processes
```

## Recovery Timeline Estimates

If you configure Supabase and run scrapers:

| Scraper | Time | Expected Leads |
|---------|------|----------------|
| seed_leads_v2 | 3-5 min | 50-100 |
| seed_leads_v3 | 3-5 min | 50-100 |
| job_board_scraper | 30-60 min | 50-100 |
| news_scraper | 20-40 min | 20-50 |
| logistics_directory_scraper | 1-2 hrs | 30-60 |
| hotel_directory_scraper | 1-2 hrs | 20-40 |

**Total**: 220-450 leads within 2-3 hours

## Current Hot Leads Bar

Your main page now shows:
- **📊 Total Leads**: Count of all leads
- **🔥 Hot Leads**: Count of hot temperature leads
- **⚡ Total Signals**: Sum of all signals across leads
- **🎯 Hottest**: Highest-strength signal with company name

## Recommendation

**Best path forward:**
1. ✅ Keep using local database with 10 leads (already working)
2. ⏳ Wait for Supabase Pro backup access (few hours)
3. ✅ Restore from backup to recover all 1,277 leads
4. ✅ Set up PM2 scrapers to prevent future data loss

This gives you 100% recovery without needing to configure Supabase credentials immediately.
