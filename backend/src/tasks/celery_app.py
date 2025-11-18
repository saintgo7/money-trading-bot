from celery import Celery
from celery.schedules import crontab
from ..core.config import settings

# Create Celery app
celery_app = Celery(
    "trading_bot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "run-trading-bots-every-hour": {
        "task": "src.tasks.trading_tasks.run_all_active_bots",
        "schedule": 3600.0,  # Every hour
    },
    "update-market-data-every-5-minutes": {
        "task": "src.tasks.trading_tasks.update_market_data",
        "schedule": 300.0,  # Every 5 minutes
    },
    "check-bot-health-every-10-minutes": {
        "task": "src.tasks.trading_tasks.check_bot_health",
        "schedule": 600.0,  # Every 10 minutes
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.tasks"])
