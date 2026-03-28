import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

# Import SiteSettings
from .site_settings import SiteSettings


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email as username."""
    
    ACCOUNT_TYPES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('vip', 'VIP'),
    ]
    
    KYC_STATUS = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    CARD_STATUS = [
        ('none', 'No Card'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    CARD_TYPES = [
        ('standard', 'Standard'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Financial fields
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    referral_bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Referral system
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    # Account status
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='beginner')
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS, default='pending')
    
    # Security
    # TODO: SECURITY - These fields store sensitive tokens in plain text
    # Should use Django's default_token_generator or hash before storage
    two_fa_enabled = models.BooleanField(default=False)
    two_fa_secret = models.CharField(max_length=32, blank=True)  # TODO: Hash this
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)  # TODO: Use Django's token generator
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)  # TODO: Use Django's token generator
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Virtual Card fields
    has_virtual_card = models.BooleanField(default=False)
    card_status = models.CharField(max_length=20, choices=CARD_STATUS, default='none')
    card_type = models.CharField(max_length=20, choices=CARD_TYPES, default='standard')
    card_number = models.CharField(max_length=20, blank=True)
    card_expiry = models.CharField(max_length=10, blank=True)
    card_cvv = models.CharField(max_length=5, blank=True)
    card_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    card_applied_date = models.DateTimeField(null=True, blank=True)
    card_approved_date = models.DateTimeField(null=True, blank=True)
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['kyc_status']),
            models.Index(fields=['date_joined']),
            models.Index(fields=['referral_code']),
        ]
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)
    
    def _generate_referral_code(self):
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        while CustomUser.objects.filter(referral_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return code
    
    @property
    def total_earnings(self):
        return self.total_profit + self.referral_bonus
    
    def get_available_balance(self):
        """Get available balance (excluding pending withdrawals)."""
        from investments.models import Withdrawal
        pending_withdrawals = Withdrawal.objects.filter(
            user=self, status__in=['pending', 'approved']
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return max(0, self.balance - pending_withdrawals)
    
    def can_withdraw(self, amount):
        """Check if user can withdraw specified amount."""
        from decimal import Decimal
        return (
            self.kyc_status == 'verified' and
            self.get_available_balance() >= Decimal(str(amount)) and
            Decimal(str(amount)) >= Decimal('10')
        )
    
    def has_pending_kyc(self):
        """Check if user has submitted KYC documents pending review."""
        return hasattr(self, 'kyc_document') and self.kyc_status == 'pending'
    
    @property
    def active_investments_count(self):
        """Count of active investments."""
        return self.investments.filter(status='active').count()
    
    @property
    def total_invested(self):
        """Total amount currently invested."""
        return self.investments.filter(status='active').aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class ActivityLog(models.Model):
    """Track user activity for security and auditing."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action}"


class Referral(models.Model):
    """Track referral relationships and bonuses."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('credited', 'Credited'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    referrer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals_made')
    referred = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referral_record')
    bonus_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    credited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
        unique_together = ['referrer', 'referred']
        indexes = [
            models.Index(fields=['referrer', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.referrer.email} -> {self.referred.email}"
