from celery import Celery
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
    }
)

if __name__ == "__main__":
    celery_app.start()