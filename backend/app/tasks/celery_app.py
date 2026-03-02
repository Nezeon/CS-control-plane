from celery import Celery

from app.config import settings

celery_app = Celery(
    "cs_control_plane",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
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
)
