#!/usr/bin/env python
"""
Restore Production Database to New Render Deployment

Usage:
    python restore_production_db.py backups/production_backup_YYYYMMDD_HHMMSS.json
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def restore_database(backup_file):
    """Restore database from JSON backup"""
    
    if not os.path.exists(backup_file):
        print(f'❌ Backup file not found: {backup_file}')
        return False
    
    print('=' * 70)
    print('🔄 DATABASE RESTORATION')
    print('=' * 70)
    print(f'📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'📁 Backup: {backup_file}')
    print(f'🗄️  Target: {connection.settings_dict.get("NAME", "Unknown")}')
    print('=' * 70)
    print()
    
    # Test connection
    print('🔄 Testing database connection...')
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print('✅ Connected to target database successfully!')
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False
    
    print()
    print('⚠️  WARNING: This will overwrite existing data!')
    print()
    response = input('Continue? (yes/no): ')
    
    if response.lower() not in ['yes', 'y']:
        print('❌ Restoration cancelled')
        return False
    
    print()
    print('🔄 Running migrations...')
    try:
        call_command('migrate', verbosity=1)
        print('✅ Migrations completed')
    except Exception as e:
        print(f'⚠️  Migration warning: {e}')
    
    print()
    print('📦 Loading data from backup...')
    
    try:
        call_command('loaddata', backup_file, verbosity=2)
        
        print()
        print('=' * 70)
        print('✅ RESTORATION COMPLETED SUCCESSFULLY!')
        print('=' * 70)
        print()
        print('📋 NEXT STEPS:')
        print('1. Verify data in admin panel: /admin/')
        print('2. Test login with existing users')
        print('3. Configure domain: elitewealthcapita.uk')
        print('4. Update DNS A record to new Render IP')
        print('=' * 70)
        
        return True
        
    except Exception as e:
        print(f'❌ Restoration failed: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python restore_production_db.py <backup_file>')
        print()
        print('Available backups:')
        if os.path.exists('backups'):
            backups = sorted([f for f in os.listdir('backups') if f.endswith('.json')])
            for backup in backups:
                size = os.path.getsize(f'backups/{backup}') / 1024
                print(f'  - backups/{backup} ({size:.2f} KB)')
        else:
            print('  No backups found')
        sys.exit(1)
    
    backup_file = sys.argv[1]
    
    try:
        success = restore_database(backup_file)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print('❌ Restoration cancelled by user')
        sys.exit(1)
