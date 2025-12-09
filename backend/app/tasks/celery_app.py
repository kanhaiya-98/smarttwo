"""Celery tasks for background processing."""

# ==================== celery_app.py ====================
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    "pharmacy_supply_chain",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks.inventory_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'check-inventory-every-6-hours': {
        'task': 'app.tasks.inventory_tasks.check_inventory',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'update-supplier-performance-daily': {
        'task': 'app.tasks.inventory_tasks.update_supplier_performance',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
