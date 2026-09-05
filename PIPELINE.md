# Pipeline Configuration for 100-200 Leads/Day

## Overview
Automated lead generation pipeline that runs 24/7, scraping multiple sources for signals of automation readiness.

## Infrastructure

### Fly.io Resources
- **Machines**: 2 machines in `iad` region
- **Memory**: 1024MB per machine (upgraded from 512MB)
- **CPU**: 1 shared CPU per machine
- **Redis**: Upstash pay-as-you-go instance for Celery task queue

### Deployment Architecture
All three processes run in the same container:
1. **FastAPI App** (uvicorn) - API endpoints on port 8080
2. **Celery Worker** - Processes scraping tasks (concurrency: 2)
3. **Celery Beat** - Scheduler for automated tasks

## Scraping Sources

### Active Scrapers (122 configured targets)
1. **Job Boards** (Indeed.com)
   - Searches: warehouse, logistics, production, assembly, food service, retail
   - Schedule: Every 12 hours
   - Signals: labor_pain, labor_shortage, strategic_hire

2. **Hotel Directories**
   - Schedule: Every 12 hours
   - Signals: labor_pain, expansion

3. **News Feeds (RSS)**
   - Sources: TechCrunch, VentureBeat, etc.
   - Schedule: Every 4 hours (high freshness)
   - Signals: funding_round, ma_activity, expansion

4. **Search Engines (SERP)**
   - Queries: automation news, robot deployments, AI adoption
   - Schedule: Daily at 06:00 UTC
   - Signals: strategic_hire, capex

5. **Logistics Directories**
   - Schedule: Daily at 06:00 UTC
   - Signals: labor_pain, expansion

## Automation Schedule

```
News + RSS:        Every 4 hours  (6x/day)  → Fresh signals
Job Boards:        Every 12 hours (2x/day)  → Labor market signals
Hotels:            Every 12 hours (2x/day)  → Expansion signals
SERP:              Daily 06:00 UTC(1x/day)  → Strategic signals
Logistics:         Daily 06:00 UTC(1x/day)  → Industry signals
Score Recalc:      Every 6 hours  (4x/day)  → Updated rankings
```

## Manual Control

### Trigger All Scrapers
```bash
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run-all
```

### Trigger Specific Scraper
```bash
# Job boards
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/job_boards

# Hotels
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/hotels

# News feeds
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/news

# Search engines
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/serp

# Logistics directories
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/logistics
```

### Monitor Pipeline Status
```bash
# Run monitoring script
./scripts/monitor_pipeline.sh

# Or use API directly
curl https://ready-2-robot.fly.dev/api/scraper/status
curl "https://ready-2-robot.fly.dev/api/scraper/stats/daily?days=7"
```

## Performance Metrics

### Target: 100-200 Leads/Day
- **Current Scrape Targets**: 122 configured
- **Expected Output**: 
  - News: ~20-30 leads/day (6 runs × 5 avg)
  - Job Boards: ~40-60 leads/day (2 runs × 25 avg)
  - SERP: ~20-30 leads/day (1 run × 25 avg)
  - Hotels: ~10-20 leads/day (2 runs × 8 avg)
  - Logistics: ~10-20 leads/day (1 run × 15 avg)
  - **Total**: ~100-160 leads/day

### Monitoring Endpoints
- `/api/scraper/status` - Current scraper health and performance
- `/api/scraper/stats/daily?days=7` - Last 7 days statistics
- `/api/scraper-health` - Detailed health checks per scraper

### Key Metrics
- **Leads Last 24h**: Actual count from database
- **Target Daily Leads**: 150 (middle of 100-200 range)
- **On Track**: ✅ if >= 100 leads/24h, ⚠️ if < 100

## Scaling Recommendations

### If Below Target (<100/day)
1. Run manual scrape: `POST /api/scraper/run-all`
2. Check scraper health: `GET /api/scraper/status`
3. Increase scrape frequency in worker/celery_worker.py
4. Add more scrape targets in app/scrapers/scrape_targets.py

### If Above Capacity (errors/timeouts)
1. Scale machines: `flyctl scale count app=3`
2. Increase memory: `flyctl scale memory 2048`
3. Increase worker concurrency in start_all.sh
4. Add dedicated worker machines

## Deployment Commands

```bash
# Deploy updated configuration
flyctl deploy --remote-only

# Check deployment status
flyctl status

# View logs (all processes)
flyctl logs

# Scale resources
flyctl scale count app=2
flyctl scale memory 1024

# SSH into machine
flyctl ssh console

# Check Celery worker status
flyctl ssh console -C "celery -A worker.celery_worker status"

# Restart machines
flyctl machine restart <machine-id>
```

## Environment Variables

Required secrets set via `flyctl secrets set`:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis broker for Celery
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key

## Costs

### Current Infrastructure
- **Fly.io Machines**: ~$15-20/month (2 × 1024MB always on)
- **Redis (Upstash)**: ~$5-10/month (pay-as-you-go)
- **Estimated Total**: ~$20-30/month for 100-200 leads/day

### Optimization
- Enable auto_stop_machines if traffic is low
- Use min_machines_running=0 for automatic scaling
- Monitor Redis usage to stay in pay-as-you-go tier

## Troubleshooting

### Scraper Not Running
1. Check Celery worker: `flyctl logs --grep celery`
2. Verify Redis connection: `flyctl ssh console -C "redis-cli -u $REDIS_URL ping"`
3. Check scraper health: `GET /api/scraper/status`

### Low Lead Count
1. Verify scrapers completed: Check logs for "Scraper completed"
2. Check for errors: `flyctl logs --grep ERROR`
3. Run manual scrape to test
4. Review scrape targets configuration

### High Memory Usage
1. Monitor: `flyctl dashboard -a ready-2-robot`
2. Reduce worker concurrency (currently 2)
3. Scale memory: `flyctl scale memory 2048`

## Next Steps

1. ✅ Deploy pipeline (automated 24/7 scraping)
2. ⏳ Monitor first 24 hours for lead generation
3. ⏳ Verify 100-200 leads/day target is met
4. ⏳ Optimize scrape frequency if needed
5. ⏳ Add more scrape targets if below target
