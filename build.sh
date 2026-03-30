#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate --no-input

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

echo "Build completed successfully!"
