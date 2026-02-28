from celery import Celery
from celery.schedules import crontab
import os

REDIS = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ready_for_robots",
    broker=REDIS,
    backend=REDIS,
    include=["worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "worker.tasks.*": {"queue": "scrapers"}
    },

    # ── Automatic scraper schedule ─────────────────────────────────────────
    # News + RSS feeds: every 4 hours (highest signal freshness)
    # Job boards + hotel dirs: every 12 hours (slower-moving data)
    # SERP + logistics dir: once daily at 06:00 UTC (expansion queries)
    # Score recalculation: every 6 hours (after scrapers have run)
    beat_schedule={
        "news-scraper-4h": {
            "task": "worker.tasks.run_news_scraper_task",
            "schedule": crontab(minute=0, hour="*/4"),
        },
        "rss-scraper-4h": {
            "task": "worker.tasks.run_rss_scraper_task",
            "schedule": crontab(minute=20, hour="*/4"),
        },
        "serp-scraper-daily": {
            "task": "worker.tasks.run_serp_scraper_task",
            "schedule": crontab(minute=0, hour=6),
        },
        "logistics-scraper-daily": {
            "task": "worker.tasks.run_logistics_scraper_task",
            "schedule": crontab(minute=30, hour=6),
        },
        "job-scraper-12h": {
            "task": "worker.tasks.run_job_scraper_task",
            "schedule": crontab(minute=45, hour="*/12"),
        },
        "hotel-scraper-12h": {
            "task": "worker.tasks.run_hotel_scraper_task",
            "schedule": crontab(minute=15, hour="*/12"),
        },
        "score-recalc-all-6h": {
            "task": "worker.tasks.recalculate_all_scores_task",
            "schedule": crontab(minute=0, hour="*/6"),
        },
    },
)

if __name__ == "__main__":
    celery_app.start()