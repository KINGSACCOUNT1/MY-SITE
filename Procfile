web: gunicorn elite_wealth_capital.wsgi:application --log-file -
worker: celery -A elite_wealth_capital worker --loglevel=info
beat: celery -A elite_wealth_capital beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
