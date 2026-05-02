#!/usr/bin/env python
"""
Production Database Backup Script for Render PostgreSQL
Downloads complete database from old Render deployment

Usage:
    python backup_production_db.py
"""

import os
import sys
import django
from datetime import datetime
import subprocess

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

# Old Render Production Database URL
OLD_DATABASE_URL = "postgresql://elite_admin_acc:ENIIWPFknHA5m4XQREVRymlVq8QhVSRI@dpg-d73r90qdbo4c738iabug-a.oregon-postgres.render.com/elite_wealth_capital"

def backup_postgres_to_json():
    """Backup PostgreSQL database to JSON using dumpdata"""
    
    # Create backups directory
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f'{backup_dir}/production_backup_{timestamp}.json'
    
    print('=' * 70)
    print('🚀 PRODUCTION DATABASE BACKUP')
    print('=' * 70)
    print(f'📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'🗄️  Source: Render PostgreSQL (Oregon)')
    print(f'📁 Output: {json_filename}')
    print('=' * 70)
    print()
    
    # Set environment variable for database connection
    os.environ['DATABASE_URL'] = OLD_DATABASE_URL
    
    # Initialize Django with production database
    django.setup()
    
    from django.core.management import call_command
    
    print('🔄 Connecting to production database...')
    
    # Test connection
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print('✅ Connected to production database successfully!')
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False
    
    print()
    print('📦 Exporting data...')
    print()
    
    # Export all data excluding certain tables
    apps_to_backup = [
        'accounts',
        'investments',
        'dashboard',
        'kyc',
        'notifications',
        'auth',  # For permissions
        'contenttypes',  # Required for auth
    ]
    
    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                *apps_to_backup,
                '--natural-foreign',
                '--natural-primary',
                '--indent=2',
                stdout=f
            )
        
        file_size = os.path.getsize(json_filename) / 1024  # KB
        
        print()
        print('=' * 70)
        print('✅ BACKUP COMPLETED SUCCESSFULLY!')
        print('=' * 70)
        print(f'💾 File size: {file_size:.2f} KB')
        print(f'📍 Location: {json_filename}')
        print()
        print('📋 NEXT STEPS:')
        print('1. Deploy new Render service from render_new.yaml')
        print('2. Wait for deployment to complete')
        print('3. Run: python restore_production_db.py')
        print('=' * 70)
        
        return True
        
    except Exception as e:
        print(f'❌ Backup failed: {e}')
        return False


def backup_postgres_to_sql():
    """Backup PostgreSQL database to SQL dump (alternative method)"""
    
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sql_filename = f'{backup_dir}/production_backup_{timestamp}.sql'
    
    print()
    print('🔄 Creating SQL dump (alternative backup)...')
    
    # Parse database URL
    db_url = OLD_DATABASE_URL.replace('postgresql://', '')
    user_pass, host_db = db_url.split('@')
    user, password = user_pass.split(':')
    host_port, database = host_db.split('/')
    host = host_port.split(':')[0]
    
    # Set password environment variable for pg_dump
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    try:
        cmd = [
            'pg_dump',
            '-h', host,
            '-U', user,
            '-d', database,
            '-F', 'c',  # Custom format
            '-f', sql_filename
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(sql_filename) / 1024
            print(f'✅ SQL backup created: {sql_filename} ({file_size:.2f} KB)')
            return True
        else:
            print(f'⚠️  SQL backup failed (pg_dump not available or error)')
            print(f'   Error: {result.stderr}')
            return False
            
    except FileNotFoundError:
        print('⚠️  pg_dump not found - SQL backup skipped')
        print('   JSON backup is sufficient for restoration')
        return False
    except Exception as e:
        print(f'⚠️  SQL backup error: {e}')
        return False


if __name__ == '__main__':
    print()
    print('⚠️  IMPORTANT: This will connect to PRODUCTION database!')
    print('   Old Render Database: elite_wealth_capital')
    print()
    
    try:
        # JSON backup (primary method)
        success = backup_postgres_to_json()
        
        if success:
            # SQL backup (optional, if pg_dump available)
            backup_postgres_to_sql()
            
            print()
            print('🎉 Backup process completed!')
            print()
            
    except KeyboardInterrupt:
        print()
        print('❌ Backup cancelled by user')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
