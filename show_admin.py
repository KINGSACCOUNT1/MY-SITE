import os
os.environ['DATABASE_URL'] = "postgresql://neondb_owner:npg_Pc4mXQWbVvH5@ep-holy-sea-a4989cmp-pooler.us-east-1.aws.neon.tech/my-elite-db?sslmode=require"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

import django
django.setup()

from accounts.models import CustomUser

print('=' * 70)
print('🔐 ADMIN/SUPERUSER ACCOUNTS')
print('=' * 70)

# Find superusers
superusers = CustomUser.objects.filter(is_superuser=True)
staff_users = CustomUser.objects.filter(is_staff=True)

print(f'\n👑 Superusers ({superusers.count()}):')
for user in superusers:
    print(f'   • Email: {user.email}')
    print(f'     Name: {user.full_name}')
    print(f'     Username: {user.username if hasattr(user, "username") else "N/A"}')
    print(f'     Staff: {user.is_staff}')
    print(f'     Active: {user.is_active}')
    print()

print(f'📋 Staff Users ({staff_users.count()}):')
for user in staff_users:
    if not user.is_superuser:  # Don't duplicate
        print(f'   • Email: {user.email}')
        print(f'     Name: {user.full_name}')
        print()

print('=' * 70)
print('⚠️  PASSWORD NOTE:')
print('Passwords are hashed in the database for security.')
print('If you need to reset admin password, use:')
print('  python manage.py changepassword <email>')
print('=' * 70)
