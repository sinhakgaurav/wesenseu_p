from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "monitour",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        "check-sla-breaches-every-15min": {
            "task": "app.worker.tasks.check_sla_breaches",
            "schedule": 900.0,  # every 15 minutes
        },
        "check-low-stock-every-hour": {
            "task": "app.worker.tasks.check_low_stock",
            "schedule": 3600.0,
        },
        "escalate-overdue-tasks-every-30min": {
            "task": "app.worker.tasks.escalate_overdue_tasks",
            "schedule": 1800.0,
        },
    },
)
