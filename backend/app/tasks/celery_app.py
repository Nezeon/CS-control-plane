from celery import Celery

from app.config import settings

# Use Redis if available, otherwise fall back to eager (synchronous) execution
_has_redis = bool(settings.REDIS_URL)
broker_url = settings.REDIS_URL if _has_redis else "memory://"
backend_url = settings.REDIS_URL if _has_redis else "rpc://"

celery_app = Celery(
    "cs_control_plane",
    broker=broker_url,
    backend=backend_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=270,
    task_track_started=True,
    # Without Redis, run tasks synchronously in the API process
    task_always_eager=not _has_redis,
    task_eager_propagates=True,
    # Retry broker connection on startup (handles Render cold starts)
    broker_connection_retry_on_startup=True,
    # Periodic beat schedule
    beat_schedule={
        "sync-fathom-periodic": {
            "task": "sync_fathom_meetings",
            "schedule": 3600.0 * 6,  # Every 6 hours
            "args": [7],  # Sync last 7 days
        },
    },
)
