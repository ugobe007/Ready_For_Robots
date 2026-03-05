# 🤖 Pipeline Deployment - Quick Reference

## ✅ Deployment Complete!

Your automated lead generation pipeline is now running 24/7 on Fly.io.

### 🎯 What's Running

- **FastAPI Application**: Serving your frontend and API
- **Celery Worker**: Processing scraping tasks (concurrency: 2)
- **Celery Beat Scheduler**: Triggering automated scrapes

### 📊 Expected Performance

- **Target**: 100-200 new leads per day
- **Scrape Targets**: 122 configured sources
- **Automation Schedule**:
  - News feeds: Every 4 hours
  - Job boards: Every 12 hours
  - SERP & logistics: Daily at 6am UTC

### 🔍 Monitor Your Pipeline

```bash
# Run the monitoring dashboard
./scripts/monitor_pipeline.sh

# Or check via API
curl https://ready-2-robot.fly.dev/api/scraper/status
```

### 🚀 Manual Controls

```bash
# Trigger all scrapers immediately
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run-all

# Trigger specific scraper
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/job_boards
curl -X POST https://ready-2-robot.fly.dev/api/scraper/run/news
```

### 📈 View Statistics

```bash
# Last 7 days
curl "https://ready-2-robot.fly.dev/api/scraper/stats/daily?days=7"
```

### 🛠️ Management

```bash
# View live logs
flyctl logs

# Check app status
flyctl status

# Scale if needed
flyctl scale count app=3
flyctl scale memory 2048
```

### 📚 Full Documentation

- **Pipeline Details**: See [PIPELINE.md](PIPELINE.md)
- **Quick Start Guide**: Run `./scripts/quick_start.sh`

### 🔗 Links

- **App**: https://ready-2-robot.fly.dev
- **API Docs**: https://ready-2-robot.fly.dev/api/docs
- **Fly Dashboard**: https://fly.io/apps/ready-2-robot/monitoring

---

**Next Steps:**
1. Monitor first 24 hours of lead generation
2. Verify 100-200 leads/day target is met
3. Adjust scrape frequency if needed (see PIPELINE.md)
