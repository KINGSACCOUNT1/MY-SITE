#!/bin/bash
# Cron job script to process investment profits
# Should be run hourly via Render cron job or system crontab

# Navigate to project directory
cd /opt/render/project/src

# Activate virtual environment if needed
# source venv/bin/activate

# Run the management command
python manage.py process_investments

# Log the completion
echo "Investment processing completed at $(date)" >> /var/log/investments_cron.log
