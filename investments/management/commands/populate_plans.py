"""
Management command to populate sample investment plans
Usage: python manage.py populate_plans
"""
from django.core.management.base import BaseCommand
from investments.models import InvestmentPlan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate sample investment plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Starter Plan',
                'description': 'Perfect for beginners starting their investment journey',
                'min_amount': Decimal('50.00'),
                'max_amount': Decimal('999.99'),
                'daily_roi': Decimal('2.5'),
                'duration_days': 30,
                'icon': 'fa-rocket',
                'is_active': True,
                'is_featured': False,
                'sort_order': 1
            },
            {
                'name': 'Bronze Plan',
                'description': 'Balanced returns for steady growth',
                'min_amount': Decimal('1000.00'),
                'max_amount': Decimal('4999.99'),
                'daily_roi': Decimal('3.5'),
                'duration_days': 30,
                'icon': 'fa-medal',
                'is_active': True,
                'is_featured': False,
                'sort_order': 2
            },
            {
                'name': 'Silver Plan',
                'description': 'Enhanced returns for serious investors',
                'min_amount': Decimal('5000.00'),
                'max_amount': Decimal('14999.99'),
                'daily_roi': Decimal('5.0'),
                'duration_days': 45,
                'icon': 'fa-gem',
                'is_active': True,
                'is_featured': True,
                'sort_order': 3
            },
            {
                'name': 'Gold Plan',
                'description': 'Premium returns for high-net-worth individuals',
                'min_amount': Decimal('15000.00'),
                'max_amount': Decimal('49999.99'),
                'daily_roi': Decimal('7.0'),
                'duration_days': 60,
                'icon': 'fa-crown',
                'is_active': True,
                'is_featured': True,
                'sort_order': 4
            },
            {
                'name': 'Platinum Plan',
                'description': 'Maximum returns for elite investors',
                'min_amount': Decimal('50000.00'),
                'max_amount': Decimal('999999.99'),
                'daily_roi': Decimal('10.0'),
                'duration_days': 90,
                'icon': 'fa-trophy',
                'is_active': True,
                'is_featured': False,
                'sort_order': 5
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for plan_data in plans:
            plan, created = InvestmentPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            # Calculate and display total return
            total_return = plan_data['daily_roi'] * plan_data['duration_days']
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created {plan_data["name"]}: '
                        f'{plan_data["daily_roi"]}% daily for {plan_data["duration_days"]} days '
                        f'(Total: {total_return}%)'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated {plan_data["name"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Investment plans population complete!'
                f'\n  Created: {created_count}'
                f'\n  Updated: {updated_count}'
                f'\n  Total: {created_count + updated_count}'
            )
        )
