# Elite Wealth Capital - Django Settings
# Celery is optional - only imported if you want to use background tasks
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not configured - investments will auto-update on dashboard visits instead
    pass