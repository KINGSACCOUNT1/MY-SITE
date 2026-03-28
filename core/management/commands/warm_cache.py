"""Django management command to warm cache with frequently accessed data."""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from investments.models import InvestmentPlan
from accounts.models import CustomUser
from django.db.models import Sum, Count


class Command(BaseCommand):
    help = 'Warm cache with frequently accessed data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Cache Warming'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')

        # Cache investment plans
        self.stdout.write('Caching investment plans...')
        plans = list(InvestmentPlan.objects.filter(is_active=True).order_by('sort_order'))
        cache.set('all_investment_plans', plans, 3600)  # 1 hour
        self.stdout.write(self.style.SUCCESS(f'✓ Cached {len(plans)} active plans'))

        # Cache site statistics
        self.stdout.write('Caching site statistics...')
        total_users = CustomUser.objects.count()
        verified_users = CustomUser.objects.filter(kyc_status='verified').count()
        
        stats = {
            'total_users': total_users,
            'verified_users': verified_users,
        }
        cache.set('site_statistics', stats, 600)  # 10 minutes
        self.stdout.write(self.style.SUCCESS(f'✓ Cached statistics ({total_users} users, {verified_users} verified)'))

        # Cache active plans count
        self.stdout.write('Caching plan summaries...')
        active_plans_count = InvestmentPlan.objects.filter(is_active=True).count()
        cache.set('active_plans_count', active_plans_count, 3600)
        self.stdout.write(self.style.SUCCESS(f'✓ Cached {active_plans_count} active plans count'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Cache warming complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
