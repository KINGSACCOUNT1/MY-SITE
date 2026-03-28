"""Django management command to clear all cached data."""
from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear all cached data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm cache clearing (required)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING('Cache NOT cleared.'))
            self.stdout.write('Use --confirm flag to clear cache:')
            self.stdout.write('  python manage.py clear_cache --confirm')
            return

        self.stdout.write(self.style.WARNING('Clearing all cache...'))
        cache.clear()
        self.stdout.write(self.style.SUCCESS('✓ All cache cleared!'))
        self.stdout.write('')
        self.stdout.write('Consider warming the cache again:')
        self.stdout.write('  python manage.py warm_cache')
