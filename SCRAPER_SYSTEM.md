# Production Scraper System - pythh.ai Style

## Architecture

This is a **production-grade automated scraper system** similar to pythh.ai's investor/startup discovery pipeline.

### Components

1. **Celery Beat Scheduler** (`worker/celery_beat_schedule.py`)
   - Automated scraping jobs running 24/7
   - News scrapers: Every 2 hours
   - Job boards: Every 6 hours  
   - Manufacturing signals: Twice daily
   - SERP/RSS: Every 4 hours
   - Company re-scoring: Daily

2. **Scraper Orchestrator** (`app/scrapers/orchestrator.py`)
   - Coordinates full data pipeline
   - Parallel source scraping
   - Company enrichment
   - Automated scoring & classification
   - Quality checks

3. **Task Workers** (`worker/tasks.py`)
   - 12+ automated scraper tasks
   - Retry logic & error handling
   - Health monitoring
   - Background processing

4. **Monitoring Dashboard** (`scripts/monitor_scrapers.py`)
   - Real-time stats
   - Signal/company counts
   - Recent activity tracking
   - Industry/source breakdowns

## Data Sources

- **News:** Google News RSS (150+ queries, 6x daily)
- **Job Boards:** 38 sites (hiring patterns, labor signals)
- **Hotel Directories:** 19 sources
- **Logistics Directories:** 7 sources
- **RFP Marketplaces:** 10 sources (high-value buyer intent)
- **SERP:** Google searches for expansion signals
- **Manufacturing-Specific:** Quality, safety, capacity, throughput signals

## Manufacturing Signal Detection

Automated queries for operational signals:
- Quality control problems / defect rates
- Production bottlenecks / capacity issues
- Workplace safety incidents
- Warehouse throughput challenges
- Packaging automation needs
- Repetitive manufacturing tasks
- Material handling automation

## Running the System

### Local Development

```bash
# Start Redis
redis-server

# Start Celery worker
celery -A worker.celery_worker worker --loglevel=info -Q scrapers

# Start Celery beat scheduler
celery -A worker.celery_worker beat --loglevel=info

# Monitor scrapers
python3 scripts/monitor_scrapers.py
```

### Manual Pipeline Run

```bash
# Run full pipeline once
python3 app/scrapers/orchestrator.py
```

### Production (Fly.io)

The system runs automatically via Celery Beat schedule. No manual intervention needed.

## Schedule Overview

| Scraper | Frequency | Time (UTC) |
|---------|-----------|------------|
| News (General) | Every 2h | 6am, 8am, 10am, 12pm, 2pm, 4pm |
| Manufacturing News | 2x daily | 7:30am, 3:30pm |
| Job Boards | Every 6h | By industry |
| RSS Feeds | Every 4h | :30 minutes |
| Hotel Directory | Daily | 3am |
| Logistics Directory | Daily | 4am |
| SERP Expansion | Every 8h | 12am, 8am, 4pm |
| RFP Marketplace | Daily | 5am |
| Company Re-scoring | Daily | 6am |
| Health Check | Hourly | :00 minutes |

## Monitoring

Real-time dashboard shows:
- Total companies/signals/leads
- Recent activity (last hour, last 24h)
- Top signal types
- Top industries
- Data source breakdown

Run: `python3 scripts/monitor_scrapers.py`

## Future Enhancements

- LinkedIn Sales Navigator API integration
- Clearbit/ZoomInfo enrichment
- Webhooks for instant signal alerts
- ML-based signal quality scoring
- Geographic expansion signals
