"""
Celery configuration for Elite Wealth Capital
Handles background tasks like auto-crediting investment profits
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

app = Celery('elite_wealth_capital')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    'process-daily-investment-profits': {
        'task': 'investments.tasks.process_all_investments',
        'schedule': crontab(hour=0, minute=5),  # Run daily at 00:05 AM
    },
    'process-hourly-investment-profits': {
        'task': 'investments.tasks.process_all_investments',
        'schedule': crontab(minute=0),  # Run every hour on the hour
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
