#!/usr/bin/env python
"""
Manual database backup script for Elite Wealth Capital.

Usage:
    python backup_database.py

Saves a JSON backup of all critical data to backups/ folder.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')
django.setup()

from django.core import serializers
from accounts.models import CustomUser, Referral, ActivityLog
from investments.models import (Investment, InvestmentPlan, WalletAddress, 
                                Deposit, Withdrawal)
from notifications.models import Notification

def backup_database():
    """Create JSON backup of all data"""
    
    # Create backups directory
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{backup_dir}/backup_{timestamp}.json'
    
    print(f'🔄 Starting database backup...')
    print(f'📁 Backup file: {filename}')
    
    # Models to backup
    models_to_backup = [
        CustomUser,
        ActivityLog,
        Referral,
        InvestmentPlan,
        Investment,
        Deposit,
        Withdrawal,
        WalletAddress,
        Notification,
    ]
    
    # Collect all objects
    all_objects = []
    for model in models_to_backup:
        objects = model.objects.all()
        all_objects.extend(objects)
        print(f'✅ {model.__name__}: {objects.count()} records')
    
    # Serialize to JSON
    json_data = serializers.serialize('json', all_objects, indent=2)
    
    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_data)
    
    file_size = os.path.getsize(filename) / 1024  # KB
    
    print(f'\n✅ Backup completed successfully!')
    print(f'📊 Total records: {len(all_objects)}')
    print(f'💾 File size: {file_size:.2f} KB')
    print(f'📍 Location: {filename}')
    print(f'\n💡 To restore: python manage.py loaddata {filename}')

if __name__ == '__main__':
    try:
        backup_database()
    except Exception as e:
        print(f'❌ Backup failed: {e}')
        sys.exit(1)
