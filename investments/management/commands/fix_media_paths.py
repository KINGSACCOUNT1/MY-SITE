"""
Fix duplicate 'media/' prefix in image paths.

Usage:
    python manage.py fix_media_paths --dry-run   # Preview changes
    python manage.py fix_media_paths             # Apply fixes
"""
from django.core.management.base import BaseCommand
from investments.models import Deposit
from kyc.models import KYCDocument
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Fix duplicate media/ prefix in image paths'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def fix_path(self, path):
        """Remove duplicate media/ prefix from path"""
        if path and path.startswith('media/'):
            return path[6:]  # Remove 'media/' prefix
        return path

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fixed_count = 0

        self.stdout.write(self.style.NOTICE(
            f"{'[DRY RUN] ' if dry_run else ''}Scanning for duplicate media/ paths..."
        ))

        # Fix Deposit proof_image
        deposits = Deposit.objects.exclude(proof_image='').exclude(proof_image__isnull=True)
        for deposit in deposits:
            if deposit.proof_image and str(deposit.proof_image).startswith('media/'):
                old_path = str(deposit.proof_image)
                new_path = self.fix_path(old_path)
                self.stdout.write(f"  Deposit #{deposit.id}: {old_path} → {new_path}")
                if not dry_run:
                    deposit.proof_image.name = new_path
                    deposit.save(update_fields=['proof_image'])
                fixed_count += 1

        # Fix CustomUser profile_image
        users = CustomUser.objects.exclude(profile_image='').exclude(profile_image__isnull=True)
        for user in users:
            if user.profile_image and str(user.profile_image).startswith('media/'):
                old_path = str(user.profile_image)
                new_path = self.fix_path(old_path)
                self.stdout.write(f"  User {user.email}: {old_path} → {new_path}")
                if not dry_run:
                    user.profile_image.name = new_path
                    user.save(update_fields=['profile_image'])
                fixed_count += 1

        # Fix KYC documents
        try:
            kyc_docs = KYCDocument.objects.all()
            for doc in kyc_docs:
                changed = False
                
                if doc.document_front and str(doc.document_front).startswith('media/'):
                    old_path = str(doc.document_front)
                    new_path = self.fix_path(old_path)
                    self.stdout.write(f"  KYC #{doc.id} front: {old_path} → {new_path}")
                    if not dry_run:
                        doc.document_front.name = new_path
                        changed = True
                    fixed_count += 1
                
                if doc.document_back and str(doc.document_back).startswith('media/'):
                    old_path = str(doc.document_back)
                    new_path = self.fix_path(old_path)
                    self.stdout.write(f"  KYC #{doc.id} back: {old_path} → {new_path}")
                    if not dry_run:
                        doc.document_back.name = new_path
                        changed = True
                    fixed_count += 1
                
                if doc.selfie and str(doc.selfie).startswith('media/'):
                    old_path = str(doc.selfie)
                    new_path = self.fix_path(old_path)
                    self.stdout.write(f"  KYC #{doc.id} selfie: {old_path} → {new_path}")
                    if not dry_run:
                        doc.selfie.name = new_path
                        changed = True
                    fixed_count += 1
                
                if changed and not dry_run:
                    doc.save()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Could not check KYC docs: {e}"))

        if fixed_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No duplicate paths found!"))
        else:
            action = "Would fix" if dry_run else "Fixed"
            self.stdout.write(self.style.SUCCESS(f"✅ {action} {fixed_count} image path(s)"))
            if dry_run:
                self.stdout.write(self.style.NOTICE("Run without --dry-run to apply fixes"))
