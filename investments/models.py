import random
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.cache import cache


class InvestmentPlan(models.Model):
    """Investment plans with ROI details"""
    
    CATEGORY_CHOICES = [
        ('crypto', 'Crypto Trading'),
        ('real_estate', 'Real Estate'),
        ('oil_gas', 'Oil & Gas'),
        ('agriculture', 'Agriculture'),
        ('solar', 'Solar Energy'),
        ('stocks', 'Global Shares'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='crypto', help_text='Investment sector')
    icon = models.CharField(max_length=50, default='fa-chart-line', help_text='FontAwesome icon class')
    
    # Amount limits
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # ROI Configuration
    daily_roi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Daily ROI percentage'
    )
    duration_days = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Display settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Investment Plan'
        verbose_name_plural = 'Investment Plans'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.daily_roi}% daily for {self.duration_days} days)"
    
    @property
    def total_roi(self):
        """Calculate total ROI percentage"""
        return self.daily_roi * self.duration_days
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate cache
        cache.delete('all_investment_plans')
        cache.delete('home_featured_plans')
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete('all_investment_plans')
        cache.delete('home_featured_plans')


class Investment(models.Model):
    """User investments"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.PROTECT, related_name='investments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Profit tracking
    expected_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Timeline
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    profit_paid_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Investment'
        verbose_name_plural = 'Investments'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        # Calculate end_date if not set
        if not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
        
        # Calculate expected profit if not set
        if not self.expected_profit:
            daily_profit = self.amount * (self.plan.daily_roi / 100)
            self.expected_profit = daily_profit * self.plan.duration_days
        
        super().save(*args, **kwargs)
    
    @property
    def days_remaining(self):
        """Days until investment matures"""
        if self.status != 'active':
            return 0
        remaining = (self.end_date - timezone.now()).days
        return max(0, remaining)
    
    @property
    def progress_percentage(self):
        """Investment progress percentage"""
        if self.status != 'active':
            return 100
        elapsed = (timezone.now() - self.start_date).days
        total_days = self.plan.duration_days
        return min(100, int((elapsed / total_days) * 100))
    
    def is_matured(self):
        """Check if investment has matured"""
        return timezone.now() >= self.end_date
    
    @property
    def days_elapsed(self):
        """Days since investment started"""
        return (timezone.now() - self.start_date).days
    
    @property
    def duration_days(self):
        """Total duration in days"""
        return self.plan.duration_days
    
    @property
    def maturity_date(self):
        """Investment maturity date"""
        return self.end_date


class Deposit(models.Model):
    """User deposits"""
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether (USDT)'),
        ('USDC', 'USD Coin'),
        ('LTC', 'Litecoin'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0.01)])
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_CHOICES)
    
    # Proof of payment
    tx_hash = models.CharField(max_length=255, blank=True, help_text='Transaction hash')
    proof_image = models.ImageField(upload_to='deposits/', blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_deposits'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} ({self.crypto_type}) - {self.status}"


class Withdrawal(models.Model):
    """User withdrawals"""
    
    METHOD_CHOICES = [
        ('crypto', 'Cryptocurrency'),
        ('bank', 'Bank Transfer'),
    ]
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether (USDT)'),
        ('USDC', 'USD Coin'),
        ('LTC', 'Litecoin'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(10)])
    withdrawal_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    
    # Crypto details
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_CHOICES, blank=True)
    wallet_address = models.CharField(max_length=255, blank=True)
    
    # Bank details
    bank_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_withdrawals'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    tx_hash = models.CharField(max_length=255, blank=True)
    admin_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Withdrawal'
        verbose_name_plural = 'Withdrawals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} - {self.status}"


class WalletAddress(models.Model):
    """Company wallet addresses for deposits"""
    
    CRYPTO_CHOICES = [
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether (USDT)'),
        ('USDC', 'USD Coin'),
        ('LTC', 'Litecoin'),
        ('BNB', 'Binance Coin'),
        ('BANK', 'Bank Transfer'),
    ]
    
    crypto_type = models.CharField(max_length=10, choices=CRYPTO_CHOICES, unique=True)
    address = models.CharField(max_length=255)
    label = models.CharField(max_length=100, blank=True)
    network = models.CharField(max_length=50, blank=True, help_text='e.g., ERC-20, TRC-20, BEP-20')
    qr_code = models.ImageField(upload_to='wallets/qr/', blank=True, null=True)
    qr_code_image = models.ImageField(upload_to='wallets/qr/', blank=True, null=True)
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
    """User loan applications"""
    
    DURATION_CHOICES = [
        (30, '30 Days'),
        (60, '60 Days'),
        (90, '90 Days'),
        (180, '180 Days'),
        (365, '365 Days'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('repaying', 'Repaying'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(100)])
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Monthly interest rate percentage'
    )
    duration_days = models.IntegerField(choices=DURATION_CHOICES)
    
    # Calculated amounts
    total_repayment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    amount_repaid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Loan details
    purpose = models.TextField()
    collateral_description = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_loans'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Calculate total repayment if not set
        if not self.total_repayment:
            months = self.duration_days / 30
            interest = self.amount * (self.interest_rate / 100) * Decimal(months)
            self.total_repayment = self.amount + interest
        
        # Set due date when disbursed
        if self.status == 'disbursed' and not self.due_date:
            self.due_date = timezone.now() + timezone.timedelta(days=self.duration_days)
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_balance(self):
        """Remaining amount to be repaid"""
        return self.total_repayment - self.amount_repaid
    
    @property
    def is_fully_repaid(self):
        """Check if loan is fully repaid"""
        return self.amount_repaid >= self.total_repayment
    
    def is_overdue(self):
        """Check if loan is overdue"""
        if self.due_date and self.status in ['disbursed', 'repaying']:
            return timezone.now() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        """Days until loan is due"""
        if self.due_date and self.status in ['disbursed', 'repaying']:
            remaining = (self.due_date - timezone.now()).days
            return max(0, remaining)
        return 0
    
    def mark_defaulted(self):
        """Mark loan as defaulted"""
        self.status = 'defaulted'
        self.save(update_fields=['status'])


class LoanRepayment(models.Model):
    """Loan repayment transactions"""
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=50, default='balance')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Loan Repayment'
        verbose_name_plural = 'Loan Repayments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Loan #{self.loan.id} - ${self.amount} repayment"


class VirtualCard(models.Model):
    """Virtual card applications"""
    
    CARD_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('platinum', 'Platinum'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='virtual_card_model')
    
    # Card details
    card_number = models.CharField(max_length=16, unique=True)
    cvv = models.CharField(max_length=3)
    expiry_month = models.IntegerField(default=12)
    expiry_year = models.IntegerField(default=2028)
    card_holder_name = models.CharField(max_length=255)
    billing_address = models.TextField()
    
    # Card type and limits
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES, default='standard')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=1000)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2, default=10000)
    
    # Features
    is_online_enabled = models.BooleanField(default=True)
    is_international_enabled = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Virtual Card'
        verbose_name_plural = 'Virtual Cards'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.masked_number}"
    
    def save(self, *args, **kwargs):
        # Generate card number if not exists (Visa format starting with 4)
        if not self.card_number:
            self.card_number = '4' + ''.join([str(random.randint(0, 9)) for _ in range(15)])
        
        # Generate CVV if not exists
        if not self.cvv:
            self.cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        
        # Auto-fill card holder name from user if not provided
        if not self.card_holder_name:
            self.card_holder_name = self.user.full_name
        
        super().save(*args, **kwargs)
    
    @property
    def masked_number(self):
        """Return masked card number"""
        if self.card_number:
            return f"**** **** **** {self.card_number[-4:]}"
        return ""


class Coupon(models.Model):
    """Promotional coupons"""
    
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('bonus', 'Bonus'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Restrictions
    min_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uses_limit = models.IntegerField(default=0, help_text='0 = unlimited')
    uses_count = models.IntegerField(default=0)
    uses_per_user = models.IntegerField(default=1)
    
    # Validity
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '$'}"
    
    @property
    def is_valid(self):
        """Check if coupon is valid"""
        if not self.is_active:
            return False
        
        # Check usage limit
        if self.uses_limit > 0 and self.uses_count >= self.uses_limit:
            return False
        
        # Check date range
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        
        return True


class CouponUsage(models.Model):
    """Track coupon usage"""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    deposit = models.ForeignKey(Deposit, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Coupon Usage'
        verbose_name_plural = 'Coupon Usages'
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"


class AgentApplication(models.Model):
    """Agent recruitment applications"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Applicant information
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    # Business details
    experience = models.TextField(help_text='Previous experience in financial services')
    marketing_plan = models.TextField(help_text='How you plan to market our services')
    expected_referrals = models.IntegerField(help_text='Expected monthly referrals')
    social_media_links = models.TextField(blank=True)
    website = models.URLField(blank=True)
    
    # Documents
    id_document = models.ImageField(upload_to='agent_docs/')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        help_text='Commission percentage on referral investments'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_agent_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Agent Application'
        verbose_name_plural = 'Agent Applications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.status}"


class AccountUpgrade(models.Model):
    """Account tier upgrade requests"""
    
    TIER_CHOICES = [
        ('intermediate', 'Intermediate - $500'),
        ('advanced', 'Advanced - $2,000'),
        ('vip', 'VIP - $10,000'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]
    
    TIER_AMOUNTS = {
        'intermediate': 500,
        'advanced': 2000,
        'vip': 10000,
    }
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account_upgrades')
    current_tier = models.CharField(max_length=20)
    requested_tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='balance')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_upgrades'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Account Upgrade'
        verbose_name_plural = 'Account Upgrades'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.requested_tier} - {self.status}"
    
    @staticmethod
    def get_tier_benefits(tier):
        """Get benefits for each tier"""
        benefits = {
            'intermediate': {
                'roi_boost': '5%',
                'support': 'Priority Support',
                'insights': 'Weekly Market Insights',
            },
            'advanced': {
                'roi_boost': '10%',
                'support': '24/7 Support',
                'insights': 'Daily Market Insights',
                'fees': 'Lower Transaction Fees',
            },
            'vip': {
                'roi_boost': '15%',
                'support': 'Personal Account Manager',
                'insights': 'Exclusive Investment Plans',
                'fees': 'Zero Transaction Fees',
                'events': 'VIP Events Access',
            },
        }
        return benefits.get(tier, {})


class CryptoTicker(models.Model):
    symbol = models.CharField(max_length=20, unique=True, help_text="Trading symbol, e.g. BTC, ETH")
    name = models.CharField(max_length=100, help_text="Display name, e.g. Bitcoin, Ethereum")
    coingecko_id = models.CharField(max_length=100, help_text="CoinGecko coin ID (e.g. bitcoin, ethereum)")
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
