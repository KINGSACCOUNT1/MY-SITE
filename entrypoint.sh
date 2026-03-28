#!/bin/bash
set -e

echo "=== Collecting Static Files ==="
python manage.py collectstatic --noinput

echo "=== Database Migration Fix ==="

# Check if we can connect to DB
python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection(); print('DB Connected!')" || {
    echo "DB connection failed!"
    exit 1
}

# Run migrations normally
python manage.py migrate --noinput

echo "=== Creating superuser if needed ==="
python manage.py create_superuser || echo "Superuser check complete"

echo "=== Starting Gunicorn server ==="
WORKERS=$(python -c "import os; print(min(int(os.cpu_count() or 1) * 2 + 1, 8))")
PORT=${PORT:-8000}
exec gunicorn --workers $WORKERS --timeout 120 --bind 0.0.0.0:$PORT elite_wealth.wsgi:application