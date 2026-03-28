"""Django management command to optimize static assets."""
from django.core.management.base import BaseCommand
import subprocess
import sys


class Command(BaseCommand):
    help = 'Optimize CSS, JS, and images for production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip image optimization (images only)',
        )
        parser.add_argument(
            '--skip-minify',
            action='store_true',
            help='Skip CSS/JS minification',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Elite Wealth Capital - Asset Optimization'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')

        # Minify CSS/JS
        if not options['skip_minify']:
            self.stdout.write(self.style.WARNING('Running CSS/JS minification...'))
            try:
                result = subprocess.run(
                    [sys.executable, 'build_tools/minify.py'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.stdout.write(result.stdout)
                self.stdout.write(self.style.SUCCESS('✓ Minification complete'))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f'✗ Minification failed: {e}'))
                self.stdout.write(self.style.ERROR(e.stderr))
        
        # Optimize images
        if not options['skip_images']:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Running image optimization...'))
            try:
                result = subprocess.run(
                    [sys.executable, 'build_tools/optimize_images.py'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.stdout.write(result.stdout)
                self.stdout.write(self.style.SUCCESS('✓ Image optimization complete'))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f'✗ Image optimization failed: {e}'))
                self.stdout.write(self.style.ERROR(e.stderr))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Optimization complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Update templates to use .min.css and .min.js files')
        self.stdout.write('2. Test with DEBUG=False locally')
        self.stdout.write('3. Deploy to production')
