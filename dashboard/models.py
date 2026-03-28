from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
import uuid


class NewsArticle(models.Model):
    """Platform news and updates"""
    
    CATEGORY_CHOICES = [
        ('market_update', 'Market Update'),
        ('platform_news', 'Platform News'),
        ('crypto', 'Cryptocurrency'),
        ('education', 'Education'),
        ('announcement', 'Announcement'),
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt = models.TextField(help_text='Short summary')
    content = models.TextField(help_text='Full article content (HTML allowed)')
    
    # Metadata
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image_url = models.URLField(blank=True)
    
    # Publishing
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while NewsArticle.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Set published_at when first published
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the URL for this article"""
        return reverse('news_article', kwargs={'slug': self.slug})


class NewsletterSubscription(models.Model):
    """Newsletter email subscriptions"""
    
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Newsletter Subscription'
        verbose_name_plural = 'Newsletter Subscriptions'
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    """Contact form submissions"""
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class Dispute(models.Model):
    """Support tickets and appeals"""
    
    APPEAL_TYPE_CHOICES = [
        ('deposit', 'Deposit Issue'),
        ('withdrawal', 'Withdrawal Issue'),
        ('investment', 'Investment Issue'),
        ('account', 'Account Issue'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    # Submitter (can be user or guest)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='disputes')
    guest_name = models.CharField(max_length=255, blank=True)
    guest_email = models.EmailField(blank=True)
    
    # Dispute details
    appeal_type = models.CharField(max_length=50, choices=APPEAL_TYPE_CHOICES)
    category = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    
    # Financial details
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    transaction_id = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dispute'
        verbose_name_plural = 'Disputes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference} - {self.subject}"
    
    @property
    def reference(self):
        """Generate dispute reference number"""
        return f"APL-{str(self.id)[:8].upper()}" if self.id else "APL-PENDING"


class Certificate(models.Model):
    """Regulatory certificates and licenses"""
    
    CERT_TYPE_CHOICES = [
        ('license', 'Business License'),
        ('compliance', 'Compliance Certificate'),
        ('security', 'Security Audit'),
        ('financial', 'Financial License'),
        ('iso', 'ISO Certification'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=255, help_text='Certificate name')
    certificate_type = models.CharField(max_length=50, choices=CERT_TYPE_CHOICES)
    description = models.TextField(blank=True, help_text='Certificate details')
    
    # Document
    document = models.FileField(upload_to='certificates/')
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    
    # Metadata
    issuer = models.CharField(max_length=255, help_text='Issuing authority')
    certificate_number = models.CharField(max_length=255, unique=True)
    
    # Display
    is_active = models.BooleanField(default=True)
    display_on_site = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text='Display order')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        ordering = ['order', '-issue_date']
    
    def __str__(self):
        return f"{self.get_certificate_type_display()} - {self.name}"
    
    @property
    def is_expired(self):
        """Check if certificate is expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None


class AdminActivityLog(models.Model):
    """Log of all admin actions for audit trail"""
    
    ACTION_TYPES = [
        ('user_edit', 'User Edited'),
        ('user_suspend', 'User Suspended'),
        ('user_activate', 'User Activated'),
        ('user_delete', 'User Deleted'),
        ('deposit_approve', 'Deposit Approved'),
        ('deposit_reject', 'Deposit Rejected'),
        ('withdrawal_approve', 'Withdrawal Approved'),
        ('withdrawal_reject', 'Withdrawal Rejected'),
        ('kyc_approve', 'KYC Approved'),
        ('kyc_reject', 'KYC Rejected'),
        ('loan_approve', 'Loan Approved'),
        ('loan_reject', 'Loan Rejected'),
        ('content_create', 'Content Created'),
        ('content_edit', 'Content Edited'),
        ('content_delete', 'Content Deleted'),
        ('certificate_upload', 'Certificate Uploaded'),
        ('certificate_update', 'Certificate Updated'),
        ('settings_change', 'Settings Changed'),
        ('login', 'Admin Login'),
        ('logout', 'Admin Logout'),
        ('api_key_generate', 'API Key Generated'),
        ('other', 'Other Action'),
    ]
    
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='admin_activities')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    
    # Target information
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_actions_against')
    target_id = models.CharField(max_length=255, blank=True, help_text='ID of affected object')
    target_type = models.CharField(max_length=100, blank=True, help_text='Type of affected object')
    
    # Request information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Changes
    changes_before = models.JSONField(default=dict, blank=True)
    changes_after = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.email} - {self.get_action_type_display()}"


class SiteSettings(models.Model):
    """Site-wide configuration settings"""
    
    # API Configuration
    stripe_api_key = models.CharField(max_length=255, blank=True, help_text='Stripe API Key (production)')
    stripe_publishable_key = models.CharField(max_length=255, blank=True, help_text='Stripe Publishable Key')
    paypal_client_id = models.CharField(max_length=255, blank=True, help_text='PayPal Client ID')
    paypal_client_secret = models.CharField(max_length=255, blank=True, help_text='PayPal Client Secret')
    
    # Email Configuration
    smtp_host = models.CharField(max_length=255, blank=True, default='smtp.gmail.com')
    smtp_port = models.IntegerField(blank=True, default=587)
    smtp_username = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)
    from_email = models.EmailField(blank=True)
    
    # Company Contact Information
    company_name = models.CharField(max_length=255, default='Elite Wealth Capital', help_text='Company Name')
    company_email = models.EmailField(default='admin@elitewealthcapital.uk', help_text='Primary Company Email')
    company_phone = models.CharField(max_length=50, default='+44-XXX-XXXX-XXX', help_text='Company Phone Number')
    company_address = models.CharField(max_length=500, default='London, United Kingdom', help_text='Company Address')
    company_website = models.URLField(default='https://elitewealthcapital.uk', help_text='Company Website URL')
    support_email = models.EmailField(default='support@elitewealthcapital.uk', help_text='Support Email')
    
    # Site Configuration
    maintenance_mode = models.BooleanField(default=False, help_text='Enable maintenance mode')
    enable_registrations = models.BooleanField(default=True, help_text='Allow new user registrations')
    enable_deposits = models.BooleanField(default=True, help_text='Allow deposits')
    enable_withdrawals = models.BooleanField(default=True, help_text='Allow withdrawals')
    
    # Features
    enable_two_factor = models.BooleanField(default=True, help_text='Require 2FA for admins')
    enable_ip_whitelist = models.BooleanField(default=False, help_text='Enable IP whitelisting')
    session_timeout_minutes = models.IntegerField(default=30, help_text='Admin session timeout in minutes')
    
    # Compliance
    kyc_required = models.BooleanField(default=True, help_text='KYC required for trading')
    minimum_deposit = models.DecimalField(max_digits=15, decimal_places=2, default=100, help_text='Minimum deposit amount')
    maximum_withdrawal = models.DecimalField(max_digits=15, decimal_places=2, default=50000, help_text='Maximum daily withdrawal')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return 'Site Configuration'
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings_obj, _ = cls.objects.get_or_create(pk=1)
        return settings_obj


class AdminSession(models.Model):
    """Track admin sessions for security"""
    
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    login_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Admin Session'
        verbose_name_plural = 'Admin Sessions'
        ordering = ['-login_at']
    
    def __str__(self):
        return f"{self.admin_user.email} - {self.login_at}"
