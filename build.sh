#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=== Starting Build Process ==="

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
echo "=== Applying Migrations ==="
python manage.py migrate --no-input

# Fix any duplicate media paths in database
echo "=== Fixing Media Paths ==="
python manage.py fix_media_paths || echo "Media path fix skipped"

# Load investment plans fixture (if exists)
echo "=== Loading Investment Plans ==="
python manage.py loaddata investments/fixtures/investment_plans.json || echo "Investment plans fixture skipped"

# Populate wallet addresses for payment methods
python manage.py populate_wallets || echo "Wallet population skipped"

# Populate investment plans (fallback if fixture didn't work)
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

# Setup cron job for investment processing (runs every hour)
echo "=== Setting up investment processing cron job ==="
python manage.py process_investments || echo "Initial investment processing skipped"

echo "=== Build completed successfully! ==="
