#!/usr/bin/env python
"""
Backup CURRENT Render PostgreSQL Database for Neon Migration
Backs up: 12 users + 2 deposits + all data
"""

import os
import sys
import django
from datetime import datetime

# Current Render Database URL
RENDER_DATABASE_URL = "postgresql://my_site_db_c5bj_user:sK9GbpAegQL62xJTjk3drX2vZFhu9PiH@dpg-d7cm0vho3t8c7393jj20-a.oregon-postgres.render.com/my_site_db_c5bj"

# Set environment
os.environ['DATABASE_URL'] = RENDER_DATABASE_URL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.core.management import call_command
from accounts.models import CustomUser
from investments.models import Deposit, Investment

def backup_render_database():
    """Backup current Render PostgreSQL database"""
    
    # Create backups directory
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{backup_dir}/render_production_{timestamp}.json'
    
    print('=' * 70)
    print('🚀 RENDER POSTGRESQL DATABASE BACKUP FOR NEON MIGRATION')
    print('=' * 70)
    print(f'📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'🗄️  Source: Render PostgreSQL (my_site_db_c5bj)')
    print(f'📁 Output: {filename}')
    print('=' * 70)
    print()
    
    # Check database contents
    print('🔍 Checking database contents...')
    try:
        users_count = CustomUser.objects.count()
        deposits_count = Deposit.objects.count()
        investments_count = Investment.objects.count()
        
        print(f'✅ Connected to database successfully!')
        print(f'   👥 Users: {users_count}')
        print(f'   💰 Deposits: {deposits_count}')
        print(f'   📈 Investments: {investments_count}')
        print()
        
        if users_count == 0:
            print('⚠️  WARNING: No users found in database!')
            response = input('Continue anyway? (yes/no): ')
            if response.lower() not in ['yes', 'y']:
                print('❌ Backup cancelled')
                return False
        
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False
    
    print('📦 Exporting all data...')
    print()
    
    # Apps to backup
    apps_to_backup = [
        'accounts',
        'investments',
        'dashboard',
        'kyc',
        'notifications',
        'contenttypes',
        'auth',
    ]
    
    try:
        # Export with UTF-8 encoding
        with open(filename, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                *apps_to_backup,
                '--natural-foreign',
                '--natural-primary',
                '--indent=2',
                stdout=f,
                verbosity=1
            )
        
        file_size = os.path.getsize(filename) / 1024  # KB
        
        print()
        print('=' * 70)
        print('✅ BACKUP COMPLETED SUCCESSFULLY!')
        print('=' * 70)
        print(f'💾 File size: {file_size:.2f} KB')
        print(f'📍 Location: {filename}')
        print(f'👥 Users backed up: {users_count}')
        print(f'💰 Deposits backed up: {deposits_count}')
        print()
        print('📋 NEXT STEPS:')
        print('1. Create Neon PostgreSQL database')
        print('2. Get Neon connection string')
        print('3. Run: python restore_to_neon.py <neon-connection-string>')
        print('=' * 70)
        
        return True
        
    except Exception as e:
        print(f'❌ Backup failed: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print()
    print('⚠️  IMPORTANT: Backing up CURRENT Render database!')
    print('   Database: my_site_db_c5bj')
    print('   Expected: 12 users + 2 deposits')
    print()
    
    try:
        success = backup_render_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print('❌ Backup cancelled by user')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
