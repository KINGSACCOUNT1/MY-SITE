import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.core.validators import MinValueValidator


class InvestmentPlan(models.Model):
    """Investment plans available to users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-chart-line')
    
    min_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    max_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    daily_roi = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        help_text='Daily ROI percentage',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    duration_days = models.IntegerField()
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Investment Plan'
        verbose_name_plural = 'Investment Plans'
        ordering = ['sort_order', 'min_amount']
    
    def __str__(self):
        return f"{self.name} ({self.daily_roi}% daily)"
    
    @property
    def total_roi(self):
        return self.daily_roi * self.duration_days
    
    def save(self, *args, **kwargs):
        """Invalidate plan caches when a plan is saved."""
        super().save(*args, **kwargs)
        # Clear the cached plans when any plan is updated
        cache.delete('all_investment_plans')
        cache.delete('home_featured_plans')
    
    def delete(self, *args, **kwargs):
        """Invalidate plan caches when a plan is deleted."""
        super().delete(*args, **kwargs)
        # Clear the cached plans when any plan is deleted
        cache.delete('all_investment_plans')
        cache.delete('home_featured_plans')


class Investment(models.Model):
    """User investments in plans."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.PROTECT, related_name='investments')
    
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    expected_profit = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    actual_profit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    profit_paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text='Admin notes about this investment')
    
    class Meta:
        verbose_name = 'Investment'
        verbose_name_plural = 'Investments'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - ${self.amount}"
    
    def clean(self):
        """Validate investment amount against plan limits."""
        from django.core.exceptions import ValidationError
        if self.amount < self.plan.min_amount:
            raise ValidationError(f'Minimum investment for {self.plan.name} is ${self.plan.min_amount:,.2f}')
        if self.amount > self.plan.max_amount:
            raise ValidationError(f'Maximum investment for {self.plan.name} is ${self.plan.max_amount:,.2f}')
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.expected_profit:
            self.expected_profit = self.amount * (self.plan.daily_roi / 100) * self.plan.duration_days
        if not self.end_date:
            from datetime import timedelta
            from django.utils import timezone
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)
    
    def is_matured(self):
        """Check if investment has reached maturity date."""
        from django.utils import timezone
        return timezone.now() >= self.end_date
    
    @property
    def days_remaining(self):
        """Get number of days until maturity."""
        from django.utils import timezone
        if self.is_matured():
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)
    
    @property
    def progress_percentage(self):
        """Get progress towards maturity as percentage."""
        from django.utils import timezone
        total_days = (self.end_date - self.start_date).days
        elapsed = (timezone.now() - self.start_date).days
        return min(100, max(0, (elapsed / total_days) * 100)) if total_days > 0 else 100

    @property
    def maturity_date(self):
        """Alias for end_date — the date the investment matures."""
        return self.end_date

    @property
    def duration_days(self):
        """Total duration of the investment in days."""
        if not self.start_date or not self.end_date:
            return 0
        return max(0, (self.end_date - self.start_date).days)

    @property
    def days_elapsed(self):
        """Number of days elapsed since the investment started."""
        if not self.start_date:
            return 0
        from django.utils import timezone
        elapsed = (timezone.now() - self.start_date).days
        return max(0, min(elapsed, self.duration_days))


class Withdrawal(models.Model):
    """User withdrawal requests."""
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether USDT'),
        ('USDC', 'USD Coin'),
        ('LTC', 'Litecoin'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Withdrawal method (crypto or bank)
    withdrawal_method = models.CharField(
        max_length=20,
        choices=[('crypto', 'Cryptocurrency'), ('bank', 'Bank Transfer')],
        default='crypto'
    )
    
    # Crypto withdrawal fields
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_CHOICES, blank=True)
    wallet_address = models.CharField(max_length=255, blank=True)
    
    # Bank withdrawal fields
    bank_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    tx_hash = models.CharField(max_length=255, blank=True)
    
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='processed_withdrawals'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Withdrawal'
        verbose_name_plural = 'Withdrawals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} {self.crypto_type}"
    
    def clean(self):
        """Validate withdrawal amount against user balance."""
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        MIN_WITHDRAWAL = Decimal('10')
        if self.amount < MIN_WITHDRAWAL:
            raise ValidationError(f'Minimum withdrawal amount is ${MIN_WITHDRAWAL:,.2f}')
        if self.user.balance < self.amount:
            raise ValidationError(f'Insufficient balance. Available: ${self.user.balance:,.2f}')
    
    def save(self, *args, **kwargs):
        if self.pk is None:  # Only validate on creation
            self.clean()
        super().save(*args, **kwargs)


class Deposit(models.Model):
    """User deposit submissions."""
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether USDT'),
        ('USDC', 'USD Coin'),
        ('LTC', 'Litecoin'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_CHOICES)
    tx_hash = models.CharField(max_length=255, blank=True)
    proof_image = models.ImageField(upload_to='deposits/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='confirmed_deposits'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} {self.crypto_type}"


class WalletAddress(models.Model):
    """Company wallet addresses for receiving deposits."""
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether USDT'),
        ('USDC', 'USD Coin'),
        ('LTC', 'Litecoin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_CHOICES)
    address = models.CharField(max_length=255)
    label = models.CharField(max_length=100, blank=True)
    qr_code = models.ImageField(upload_to='wallets/qr/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Wallet Address'
        verbose_name_plural = 'Wallet Addresses'
        ordering = ['crypto_type']
    
    def __str__(self):
        return f"{self.crypto_type} - {self.address[:20]}..."


class Loan(models.Model):
    """User loan applications."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('repaying', 'Repaying'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]
    
    DURATION_CHOICES = [
        (30, '30 Days'),
        (60, '60 Days'),
        (90, '90 Days'),
        (180, '6 Months'),
        (365, '12 Months'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=5.0, 
        help_text='Monthly interest rate %',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    duration_days = models.IntegerField(choices=DURATION_CHOICES)
    
    total_repayment = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    amount_repaid = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    purpose = models.TextField(blank=True)
    collateral_description = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_loans'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} Loan"
    
    def save(self, *args, **kwargs):
        if not self.total_repayment:
            months = self.duration_days / 30
            interest = self.amount * (self.interest_rate / 100) * months
            self.total_repayment = self.amount + interest
        super().save(*args, **kwargs)
    
    @property
    def remaining_balance(self):
        return self.total_repayment - self.amount_repaid
    
    @property
    def is_fully_repaid(self):
        return self.amount_repaid >= self.total_repayment
    
    def is_overdue(self):
        """Check if loan is past due date."""
        from django.utils import timezone
        return self.due_date and timezone.now() > self.due_date and not self.is_fully_repaid
    
    @property
    def days_until_due(self):
        """Get days until loan is due."""
        from django.utils import timezone
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now()
        return max(0, delta.days)
    
    def mark_defaulted(self):
        """Mark loan as defaulted."""
        if self.is_overdue() and self.status != 'defaulted':
            self.status = 'defaulted'
            self.save(update_fields=['status'])
            return True
        return False


class LoanRepayment(models.Model):
    """Track loan repayments."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='balance')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Loan Repayment'
        verbose_name_plural = 'Loan Repayments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.loan.user.email} - ${self.amount} repayment"


class VirtualCard(models.Model):
    """Virtual debit cards for users."""
    
    CARD_TYPE_CHOICES = [
        ('standard', 'Standard Card'),
        ('premium', 'Premium Card'),
        ('platinum', 'Platinum Card'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='virtual_cards')
    
    card_number = models.CharField(max_length=19, unique=True, blank=True)  # TODO: Encrypt using django-fernet-fields or similar
    # CVV removed per PCI-DSS compliance - NEVER store CVV
    # cvv = models.CharField(max_length=3, blank=True)  # DELETED - CVV must not be stored
    expiry_month = models.IntegerField(default=12)
    expiry_year = models.IntegerField(default=2028)
    
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES, default='standard')
    card_holder_name = models.CharField(max_length=100)
    billing_address = models.TextField(blank=True)
    
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    daily_limit = models.DecimalField(max_digits=15, decimal_places=2, default=1000)
    monthly_limit = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_online_enabled = models.BooleanField(default=True)
    is_international_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Virtual Card'
        verbose_name_plural = 'Virtual Cards'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.card_type} Card"
    
    def save(self, *args, **kwargs):
        if not self.card_number:
            self.card_number = self._generate_card_number()
        if not self.cvv:
            import random
            self.cvv = str(random.randint(100, 999))
        super().save(*args, **kwargs)
    
    def _generate_card_number(self):
        import random
        # Generate 16-digit card number (starting with 4 for Visa-like)
        number = '4' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
        # Format with spaces
        return f"{number[:4]} {number[4:8]} {number[8:12]} {number[12:16]}"
    
    @property
    def masked_number(self):
        if self.card_number:
            return f"**** **** **** {self.card_number[-4:]}"
        return "****"


class Coupon(models.Model):
    """Promotional coupons/promo codes."""
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Off'),
        ('fixed', 'Fixed Amount'),
        ('bonus', 'Bonus Credit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text='Percentage or fixed amount',
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    min_deposit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        help_text='Minimum deposit to use coupon',
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_discount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text='Maximum discount amount',
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    uses_limit = models.IntegerField(default=0, help_text='0 = unlimited')
    uses_count = models.IntegerField(default=0)
    uses_per_user = models.IntegerField(default=1, help_text='How many times each user can use')
    
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}"
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if self.uses_limit > 0 and self.uses_count >= self.uses_limit:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True


class CouponUsage(models.Model):
    """Track coupon usage by users."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    deposit = models.ForeignKey(Deposit, on_delete=models.SET_NULL, null=True, blank=True, related_name='coupon_usage')
    
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Coupon Usage'
        verbose_name_plural = 'Coupon Usages'
    
    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"


class AgentApplication(models.Model):
    """Agent/affiliate applications."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_application')
    
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    experience = models.TextField(help_text='Describe your experience in finance/investments')
    marketing_plan = models.TextField(help_text='How will you promote Elite Wealth Capital?')
    expected_referrals = models.IntegerField(help_text='Expected monthly referrals')
    
    social_media_links = models.TextField(blank=True, help_text='Your social media profiles')
    website = models.URLField(blank=True)
    
    id_document = models.ImageField(upload_to='agent_docs/', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0, help_text='Commission % on referral investments')
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_agent_apps'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Agent Application'
        verbose_name_plural = 'Agent Applications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - Agent Application"


class AccountUpgrade(models.Model):
    """Account upgrade requests."""
    
    TIER_CHOICES = [
        ('intermediate', 'Intermediate - $500'),
        ('advanced', 'Advanced - $2,000'),
        ('vip', 'VIP - $10,000'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid - Awaiting Confirmation'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]
    
    TIER_PRICES = {
        'intermediate': 500,
        'advanced': 2000,
        'vip': 10000,
    }
    
    TIER_BENEFITS = {
        'intermediate': ['5% higher ROI', 'Priority support', 'Weekly market insights'],
        'advanced': ['10% higher ROI', '24/7 support', 'Daily market insights', 'Lower withdrawal fees'],
        'vip': ['15% higher ROI', 'Personal account manager', 'Exclusive investment plans', 'Zero withdrawal fees', 'VIP events access'],
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='upgrade_requests')
    
    current_tier = models.CharField(max_length=20)
    requested_tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=20, default='balance')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='processed_upgrades'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Account Upgrade'
        verbose_name_plural = 'Account Upgrades'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.current_tier} → {self.requested_tier}"


class CryptoTicker(models.Model):
    """
    Admin-managed list of cryptocurrencies shown in the live price ticker.
    Prices are fetched from the CoinGecko public API using coingecko_id.
    """

    symbol = models.CharField(max_length=20, unique=True, help_text="Trading symbol, e.g. BTC, ETH")
    name = models.CharField(max_length=100, help_text="Display name, e.g. Bitcoin, Ethereum")
    coingecko_id = models.CharField(
        max_length=100,
        help_text="CoinGecko coin ID used to fetch prices (e.g. bitcoin, ethereum, tether)",
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Crypto Ticker'
        verbose_name_plural = 'Crypto Tickers'
        ordering = ['display_order', 'symbol']

    def __str__(self):
        return f"{self.symbol} ({self.name})"
