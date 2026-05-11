"""
Django management command to process investment profits
Can be run manually or via cron job
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from investments.tasks import process_all_investments
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process all active investments - credit daily profits and complete matured investments'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Process investments for a specific user only',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f'Starting investment processing at {timezone.now()}'))
        
        user_id = options.get('user_id')
        
        if user_id:
            # Process specific user
            from investments.tasks import process_single_user_investments
            result = process_single_user_investments(user_id)
            self.stdout.write(self.style.SUCCESS(f'Processed user {user_id}: {result}'))
        else:
            # Process all investments
            result = process_all_investments()
            
            self.stdout.write(self.style.SUCCESS('Investment processing complete!'))
            self.stdout.write(f'  Users processed: {result["users_processed"]}')
            self.stdout.write(f'  Investments completed: {result["investments_completed"]}')
            self.stdout.write(f'  Investments updated: {result["investments_updated"]}')
            self.stdout.write(f'  Total profits credited: ${result["total_profits_credited"]:.2f}')
            self.stdout.write(f'  Total principal returned: ${result["total_principal_returned"]:.2f}')
