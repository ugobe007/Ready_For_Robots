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

# Import production schedule
from worker.celery_beat_schedule import CELERYBEAT_SCHEDULE

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "worker.tasks.*": {"queue": "scrapers"}
    },
    
    # Production-grade automated schedule (pythh.ai style)
    beat_schedule=CELERYBEAT_SCHEDULE,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

if __name__ == "__main__":
    celery_app.start()