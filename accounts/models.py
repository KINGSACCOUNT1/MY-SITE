import uuid
import random
import string
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom User model with investment platform features"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('starter', 'Starter Plan'),           # $30-399
        ('advance', 'Advance Plan'),           # $400-999
        ('intro', 'Intro Plan'),               # $1000-2999
        ('region', 'Region Plan'),             # $3000-4999
        ('pro', 'Pro Plan'),                   # $5000-9999
        ('premium', 'Premium Plan'),           # $10000-24999
        ('executive', 'Executive Plan'),       # $25000-49999
        ('elite', 'Elite Plan'),               # $50000-99999
        ('platinum', 'Platinum Plan'),         # $100000-249999
        ('diamond', 'Diamond Plan'),           # $250000+
    ]
    
    KYC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    CARD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    CARD_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('platinum', 'Platinum'),
    ]
    
    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Authentication
    email = models.EmailField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # Personal Information
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Financial Fields
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    total_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    referral_bonus = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    
    # Referral System
    referral_code = models.CharField(max_length=8, unique=True, editable=False)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    # Account Status
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='beginner')
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='pending')
    
    # Security
    two_fa_enabled = models.BooleanField(default=False)
    two_fa_secret = models.CharField(max_length=32, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.CharField(max_length=100, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Virtual Card Fields
    has_virtual_card = models.BooleanField(default=False)
    card_status = models.CharField(max_length=20, choices=CARD_STATUS_CHOICES, blank=True)
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES, blank=True)
    card_number = models.CharField(max_length=16, blank=True)
    card_expiry = models.CharField(max_length=7, blank=True)  # MM/YYYY
    card_cvv = models.CharField(max_length=3, blank=True)
    card_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    card_applied_date = models.DateTimeField(null=True, blank=True)
    card_approved_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
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
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Generate referral code if not exists
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        """Generate unique 8-character alphanumeric referral code"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not CustomUser.objects.filter(referral_code=code).exists():
                return code
    
    def get_available_balance(self):
        """Returns balance minus pending withdrawals"""
        from investments.models import Withdrawal
        pending_withdrawals = Withdrawal.objects.filter(
            user=self,
            status='pending'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return self.balance - pending_withdrawals
    
    def can_withdraw(self, amount):
        """Check if user can withdraw specified amount"""
        return (
            self.email_verified and
            self.kyc_status == 'verified' and
            self.get_available_balance() >= amount and
            amount >= 10  # Minimum withdrawal
        )
    
    def has_pending_kyc(self):
        """Check if user has pending KYC"""
        return self.kyc_status in ['pending', 'submitted']
    
    @property
    def active_investments_count(self):
        """Returns count of active investments"""
        return self.investments.filter(status='active').count()
    
    @property
    def total_invested(self):
        """Returns current invested amount"""
        return self.invested_amount
    
    @property
    def total_earnings(self):
        """Returns total earnings (profit + referral bonus)"""
        return self.total_profit + self.referral_bonus


class ActivityLog(models.Model):
    """Track user activities for security audit"""
    
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('password_reset', 'Password Reset'),
        ('kyc_submitted', 'KYC Submitted'),
        ('investment_created', 'Investment Created'),
        ('deposit_submitted', 'Deposit Submitted'),
        ('withdrawal_requested', 'Withdrawal Requested'),
        ('profile_updated', 'Profile Updated'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.created_at}"


class Referral(models.Model):
    """Track referral relationships and bonuses"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('credited', 'Credited'),
        ('cancelled', 'Cancelled'),
    ]
    
    referrer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrer_records')
    referred = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referred_records')
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, default=30.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    credited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
        ordering = ['-created_at']
        unique_together = ['referrer', 'referred']
    
    def __str__(self):
        return f"{self.referrer.email} referred {self.referred.email}"
