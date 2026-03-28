"""
Create initial SiteSettings with company details
Run: python manage.py shell < create_site_settings.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')
django.setup()

from dashboard.models import SiteSettings

# Get or create settings
settings, created = SiteSettings.objects.get_or_create(pk=1)

# Update company information
settings.company_name = 'Elite Wealth Capital'
settings.company_email = 'admin@elitewealthcapital.uk'
settings.support_email = 'support@elitewealthcapital.uk'
settings.company_phone = '+44 20 7946 0958'
settings.company_address = 'London, United Kingdom'
settings.company_website = 'https://elitewealthcapital.uk'

# Site configuration defaults
settings.maintenance_mode = False
settings.enable_registrations = True
settings.enable_deposits = True
settings.enable_withdrawals = True
settings.kyc_required = True
settings.enable_two_factor = True

settings.save()

if created:
    print("✅ Created new SiteSettings instance")
else:
    print("✅ Updated existing SiteSettings instance")

print("\nCompany Information:")
print(f"  Name: {settings.company_name}")
print(f"  Email: {settings.company_email}")
print(f"  Support: {settings.support_email}")
print(f"  Phone: {settings.company_phone}")
print(f"  Address: {settings.company_address}")
print(f"  Website: {settings.company_website}")
print("\nAdmin can edit at: http://localhost:8000/admin/dashboard/sitesettings/1/change/")
