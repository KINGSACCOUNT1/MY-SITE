#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=== Starting Build Process ==="

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations with smart conflict handling
echo "=== Applying Migrations ==="

# First, check if there are any migration conflicts
python manage.py showmigrations --plan 2>&1 | head -20 || true

# Try to apply migrations, handling "already exists" errors
python manage.py migrate --no-input 2>&1 && echo "Migrations applied successfully" || {
    echo "Migration error detected, checking for conflicts..."
    
    # Handle case where table exists but migration not recorded
    python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

import django
django.setup()

from django.db import connection
from django.core.management import call_command

# Check django_migrations table for investments 0003
with connection.cursor() as cursor:
    cursor.execute(\"SELECT COUNT(*) FROM django_migrations WHERE app='investments' AND name='0003_cryptoticker_agentapplication_user_and_more'\")
    migration_exists = cursor.fetchone()[0] > 0
    
    cursor.execute(\"SELECT to_regclass('investments_cryptoticker')\")
    table_exists = cursor.fetchone()[0] is not None

print(f'Migration 0003 recorded: {migration_exists}')
print(f'CryptoTicker table exists: {table_exists}')

if table_exists and not migration_exists:
    print('Table exists but migration not recorded - faking migration...')
    call_command('migrate', 'investments', '0003_cryptoticker_agentapplication_user_and_more', '--fake', '--no-input')
    print('Migration 0003 marked as applied')
    
    # Now run remaining migrations
    call_command('migrate', '--no-input')
elif migration_exists:
    print('Migration already applied, continuing...')
else:
    print('Neither table nor migration exists - this is unexpected')
"
}

# Populate wallet addresses for payment methods
python manage.py populate_wallets || echo "Wallet population skipped"

# Populate investment plans
python manage.py populate_plans || echo "Plan population skipped"

# Create superuser if it doesn't exist (uses environment variables for security)
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
admin_email = os.environ.get('ADMIN_EMAIL', 'admin@elitewealthcapita.uk')
admin_password = os.environ.get('ADMIN_PASSWORD', '')
if admin_password and not User.objects.filter(email=admin_email).exists():
    User.objects.create_superuser(email=admin_email, password=admin_password)
    print(f'Admin user {admin_email} created')
else:
    print('Admin user already exists or ADMIN_PASSWORD not set')
"

echo "=== Build completed successfully! ==="
