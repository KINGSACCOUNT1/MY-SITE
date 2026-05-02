#!/usr/bin/env python
"""
Restore Database to Neon PostgreSQL
Restores 12 users + 2 deposits from Render backup

Usage:
    python restore_to_neon.py <neon-connection-string>
    
Example:
    python restore_to_neon.py "postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/elite_wealth_capital?sslmode=require"
"""

import os
import sys
import django
from datetime import datetime

if len(sys.argv) < 2:
    print('❌ Error: Neon connection string required')
    print()
    print('Usage:')
    print('  python restore_to_neon.py <neon-connection-string>')
    print()
    print('Example:')
    print('  python restore_to_neon.py "postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require"')
    print()
    sys.exit(1)

# Get Neon database URL from command line
NEON_DATABASE_URL = sys.argv[1]

# Set environment
os.environ['DATABASE_URL'] = NEON_DATABASE_URL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.core.management import call_command
from django.db import connection

def restore_to_neon(backup_file):
    """Restore database to Neon from backup"""
    
    if not os.path.exists(backup_file):
        print(f'❌ Backup file not found: {backup_file}')
        print()
        print('Available backups:')
        if os.path.exists('backups'):
            for f in sorted(os.listdir('backups')):
                if f.endswith('.json'):
                    size = os.path.getsize(f'backups/{f}') / 1024
                    print(f'  - backups/{f} ({size:.2f} KB)')
        return False
    
    print('=' * 70)
    print('🚀 RESTORING TO NEON POSTGRESQL')
    print('=' * 70)
    print(f'📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'📁 Backup: {backup_file}')
    print(f'🗄️  Target: Neon PostgreSQL')
    print('=' * 70)
    print()
    
    # Test Neon connection
    print('🔄 Testing Neon connection...')
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
        print(f'✅ Connected to Neon successfully!')
        print(f'   PostgreSQL: {version.split(",")[0]}')
        print()
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        print()
        print('💡 Check your Neon connection string:')
        print('   - Must include ?sslmode=require')
        print('   - User must have permissions')
        print('   - Database must exist')
        return False
    
    # Warning
    print('⚠️  WARNING: This will OVERWRITE all data in Neon database!')
    print()
    response = input('Continue? (yes/no): ')
    
    if response.lower() not in ['yes', 'y']:
        print('❌ Restoration cancelled')
        return False
    
    print()
    print('🔄 Running migrations...')
    try:
        call_command('migrate', '--noinput', verbosity=1)
        print('✅ Migrations completed')
    except Exception as e:
        print(f'⚠️  Migration warning: {e}')
    
    print()
    print('📦 Loading data from backup...')
    print('   This may take a few minutes for 12 users + deposits...')
    print()
    
    try:
        call_command('loaddata', backup_file, verbosity=2)
        
        # Verify restoration
        from accounts.models import CustomUser
        from investments.models import Deposit
        
        users_count = CustomUser.objects.count()
        deposits_count = Deposit.objects.count()
        
        print()
        print('=' * 70)
        print('✅ RESTORATION COMPLETED SUCCESSFULLY!')
        print('=' * 70)
        print(f'👥 Users restored: {users_count}')
        print(f'💰 Deposits restored: {deposits_count}')
        print()
        print('📋 NEXT STEPS:')
        print('1. Update render.yaml with Neon connection string')
        print('2. Push to GitHub')
        print('3. Redeploy on Render')
        print('4. Verify users can login')
        print('=' * 70)
        
        return True
        
    except Exception as e:
        print(f'❌ Restoration failed: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Find latest backup
    backup_file = 'backups/render_production_20260502_061326.json'
    
    if not os.path.exists(backup_file):
        # Find any render_production backup
        if os.path.exists('backups'):
            backups = [f for f in os.listdir('backups') if f.startswith('render_production') and f.endswith('.json')]
            if backups:
                backup_file = f'backups/{sorted(backups)[-1]}'
    
    print()
    print('🎯 Using backup:', backup_file)
    print()
    
    try:
        success = restore_to_neon(backup_file)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print('❌ Restoration cancelled by user')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
