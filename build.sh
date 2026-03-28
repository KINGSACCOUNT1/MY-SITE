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

# Create superuser if it doesn't exist (optional, can be done via shell later)
# python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='admin@elitewealthcapital.uk').exists() or User.objects.create_superuser('admin@elitewealthcapital.uk', 'admin@elitewealthcapital.uk', 'changeme123')"

echo "Build completed successfully!"
