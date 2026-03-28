"""
Celery configuration for Elite Wealth Capital
Handles async tasks like daily ROI calculation, email notifications
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

app = Celery('elite_wealth_capital')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'calculate-daily-profits': {
        'task': 'investments.tasks.calculate_daily_profits',
        'schedule': crontab(hour=0, minute=1),  # Run at 12:01 AM daily
    },
    'check-mature-investments': {
        'task': 'investments.tasks.check_mature_investments',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}
