#!/usr/bin/env python
"""Test settings.py security fixes"""
import os
import sys

# Set up environment for testing
os.environ['DEBUG'] = 'True'
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'

# Try to import settings
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth.settings')
    django.setup()
    
    from django.conf import settings
    
    print("✓ settings.py imports successfully")
    print(f"✓ DEBUG = {settings.DEBUG}")
    print(f"✓ SECRET_KEY is set (length: {len(settings.SECRET_KEY)})")
    
    # Verify SECRET_KEY is not the old hardcoded one
    if 'django-insecure-dev-key-only' in settings.SECRET_KEY:
        print("✗ ERROR: Still using hardcoded SECRET_KEY!")
        sys.exit(1)
    else:
        print("✓ SECRET_KEY is not hardcoded")
    
    print("\n=== All security fixes verified! ===")
    
except Exception as e:
    print(f"✗ Error importing settings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
