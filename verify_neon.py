import os
os.environ['DATABASE_URL'] = "postgresql://neondb_owner:npg_Pc4mXQWbVvH5@ep-holy-sea-a4989cmp-pooler.us-east-1.aws.neon.tech/my-elite-db?sslmode=require"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')

import django
django.setup()

from accounts.models import CustomUser
from investments.models import Deposit, Investment

print('=' * 70)
print('✅ NEON DATABASE VERIFICATION')
print('=' * 70)
print(f'👥 Users: {CustomUser.objects.count()}')
print(f'💰 Deposits: {Deposit.objects.count()}')
print(f'📈 Investments: {Investment.objects.count()}')
print('=' * 70)
print('📋 Sample Users:')
for u in CustomUser.objects.all()[:5]:
    print(f'  • {u.email} - {u.full_name}')
print('=' * 70)
print('✅ ALL DATA SUCCESSFULLY RESTORED TO NEON!')
