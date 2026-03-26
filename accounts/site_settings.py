"""
Site Settings Model - Centralized website configuration
"""
import uuid
from datetime import datetime
from django.db import models
from django.core.cache import cache


def _default_copyright_text():
    """Return copyright text with the current year at instance creation."""
    return f'© {datetime.now().year} Elite Wealth Capital. All rights reserved.'


class SiteSettings(models.Model):
    """Singleton model for site-wide settings."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Company Information
    site_name = models.CharField(max_length=100, default='Elite Wealth Capital')
    site_tagline = models.CharField(max_length=200, default='Your Gateway to Financial Freedom')
    company_email = models.EmailField(default='admin@elitewealthcapita.uk')
    company_phone = models.CharField(max_length=20, default='+44 20 7946 0958')
    company_address = models.TextField(default='London, United Kingdom')
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, default='')
    twitter_url = models.URLField(blank=True, default='')
    instagram_url = models.URLField(blank=True, default='')
    linkedin_url = models.URLField(blank=True, default='')
    telegram_url = models.URLField(blank=True, default='')
    
    # Financial Settings
    min_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=30)
    max_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=1000000)
    min_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=10)
    max_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=100000)
    withdrawal_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Referral Settings
    referral_bonus_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5, help_text='% of first deposit')
    enable_referrals = models.BooleanField(default=True)
    
    # Agent Settings
    agent_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10, help_text='Default agent commission %')
    enable_agent_applications = models.BooleanField(default=True)
    
    # Security Settings
    max_login_attempts = models.IntegerField(default=5)
    lockout_duration_minutes = models.IntegerField(default=30)
    require_email_verification = models.BooleanField(default=True)
    require_kyc_for_withdrawal = models.BooleanField(default=True)
    
    # Maintenance Mode
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default='Site is under maintenance. Please check back later.')
    
    # SEO Settings
    meta_description = models.TextField(blank=True, default='Elite Wealth Capital - Professional investment platform')
    meta_keywords = models.CharField(max_length=500, blank=True, default='investment, trading, forex, cryptocurrency')
    
    # Homepage Content
    hero_title = models.CharField(max_length=200, default='Invest Smart, Grow Wealthy')
    hero_subtitle = models.TextField(default='Start your journey to financial freedom with our professional investment platform.')
    
    # Footer Content
    footer_about = models.TextField(default='Elite Wealth Capital is a leading investment platform providing secure and profitable investment opportunities.')
    copyright_text = models.CharField(max_length=200, default=_default_copyright_text)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            existing = SiteSettings.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
        # Clear cache when settings change
        cache.delete('site_settings')
    
    @classmethod
    def get_settings(cls):
        """Get or create site settings."""
        settings = cache.get('site_settings')
        if not settings:
            settings, created = cls.objects.get_or_create(pk=cls.objects.first().pk if cls.objects.exists() else None)
            cache.set('site_settings', settings, 3600)  # Cache for 1 hour
        return settings
