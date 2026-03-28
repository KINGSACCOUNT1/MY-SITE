# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=elite_wealth_capital.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . /app/

# Create directories
RUN mkdir -p /app/media /app/staticfiles

# Expose port
EXPOSE 10000

# Startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput --clear\n\
echo "Starting Gunicorn..."\n\
exec gunicorn elite_wealth_capital.wsgi:application --bind 0.0.0.0:10000 --workers 3 --timeout 120 --log-level info\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
