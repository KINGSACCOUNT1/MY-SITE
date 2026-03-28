from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import (
    InvestmentPlan, Investment, Withdrawal, Deposit, WalletAddress,
    Loan, LoanRepayment, VirtualCard, Coupon, CouponUsage,
    AgentApplication, AccountUpgrade, CryptoTicker
)


# Inline models for user admin
class InvestmentInline(admin.TabularInline):
    model = Investment
    extra = 0
    readonly_fields = ['plan', 'amount', 'expected_profit', 'status', 'start_date', 'end_date']
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False


class DepositInline(admin.TabularInline):
    model = Deposit
    extra = 0
    readonly_fields = ['amount', 'crypto_type', 'status', 'created_at']
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False


class WithdrawalInline(admin.TabularInline):
    model = Withdrawal
    extra = 0
    readonly_fields = ['amount', 'crypto_type', 'wallet_address', 'status', 'created_at']
    can_delete = False
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    """Admin for InvestmentPlan model."""
    
    list_display = ['name', 'min_amount', 'max_amount', 'daily_roi', 'duration_days', 'is_active', 'is_featured', 'sort_order']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'is_featured', 'sort_order']
    ordering = ['sort_order']
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'icon')}),
        ('Investment Details', {'fields': ('min_amount', 'max_amount', 'daily_roi', 'duration_days')}),
        ('Display', {'fields': ('is_active', 'is_featured', 'sort_order')}),
    )


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """Admin for Investment model."""
    
    list_display = ['user', 'plan', 'amount_display', 'expected_profit_display', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'plan', 'start_date']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['id', 'expected_profit', 'start_date']
    ordering = ['-start_date']
    
    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def expected_profit_display(self, obj):
        return f"${obj.expected_profit:,.2f}"
    expected_profit_display.short_description = 'Expected Profit'
    
    actions = ['mark_completed', 'cancel_investments', 'export_investments_csv']
    
    @admin.action(description='Mark as completed')
    def mark_completed(self, request, queryset):
        for inv in queryset.filter(status='active'):
            inv.status = 'completed'
            inv.completed_at = timezone.now()
            inv.actual_profit = inv.expected_profit
            inv.user.balance += inv.amount + inv.actual_profit
            inv.user.total_profit += inv.actual_profit
            inv.user.save()
            inv.save()
        self.message_user(request, 'Investments marked as completed.')
    
    @admin.action(description='Cancel investments')
    def cancel_investments(self, request, queryset):
        queryset.filter(status='active').update(status='cancelled')
        self.message_user(request, 'Investments cancelled.')
    
    @admin.action(description='Export to CSV')
    def export_investments_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="investments_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Plan', 'Amount', 'Expected Profit', 'Status', 'Start Date', 'End Date'])
        for inv in queryset:
            writer.writerow([inv.user.email, inv.plan.name, f'${inv.amount:,.2f}', f'${inv.expected_profit:,.2f}', 
                           inv.status, inv.start_date.strftime('%Y-%m-%d'), inv.end_date.strftime('%Y-%m-%d')])
        return response


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    """Admin for Withdrawal model."""
    
    list_display = ['user', 'amount_display', 'crypto_type', 'wallet_short', 'status_badge', 'created_at']
    list_filter = ['status', 'crypto_type', 'created_at']
    search_fields = ['user__email', 'wallet_address', 'tx_hash']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Info', {'fields': ('user', 'amount', 'crypto_type', 'wallet_address')}),
        ('Status', {'fields': ('status', 'admin_note', 'tx_hash')}),
        ('Processing', {'fields': ('processed_by', 'processed_at')}),
    )
    
    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def wallet_short(self, obj):
        return f"{obj.wallet_address[:15]}...{obj.wallet_address[-8:]}" if len(obj.wallet_address) > 25 else obj.wallet_address
    wallet_short.short_description = 'Wallet'
    
    def status_badge(self, obj):
        colors = {'pending': 'orange', 'approved': 'blue', 'completed': 'green', 'rejected': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.status, 'gray'), obj.status.upper())
    status_badge.short_description = 'Status'
    
    actions = ['approve_withdrawals', 'reject_withdrawals', 'mark_completed']
    
    @admin.action(description='Approve selected withdrawals')
    def approve_withdrawals(self, request, queryset):
        queryset.filter(status='pending').update(status='approved', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, 'Withdrawals approved.')
    
    @admin.action(description='Reject selected withdrawals')
    def reject_withdrawals(self, request, queryset):
        for w in queryset.filter(status='pending'):
            w.user.balance += w.amount  # Refund
            w.user.save()
            w.status = 'rejected'
            w.processed_by = request.user
            w.processed_at = timezone.now()
            w.save()
        self.message_user(request, 'Withdrawals rejected and funds refunded.')
    
    @admin.action(description='Mark as completed')
    def mark_completed(self, request, queryset):
        queryset.filter(status='approved').update(status='completed')
        self.message_user(request, 'Withdrawals marked as completed.')


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    """Admin for Deposit model."""
    
    list_display = ['user', 'amount_display', 'crypto_type', 'has_proof', 'status_badge', 'created_at']
    list_filter = ['status', 'crypto_type', 'created_at']
    search_fields = ['user__email', 'tx_hash']
    readonly_fields = ['id', 'created_at', 'proof_image_preview']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Deposit Info', {'fields': ('user', 'amount', 'crypto_type', 'wallet_address', 'tx_hash')}),
        ('Payment Proof', {'fields': ('proof_image', 'proof_image_preview')}),
        ('Status', {'fields': ('status', 'admin_note')}),
        ('Processing', {'fields': ('confirmed_by', 'confirmed_at')}),
    )
    
    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def has_proof(self, obj):
        if obj.proof_image:
            return format_html('<span style="color: green; font-weight: bold;">✓ Yes</span>')
        return format_html('<span style="color: gray;">✗ No</span>')
    has_proof.short_description = 'Receipt'
    
    def proof_image_preview(self, obj):
        if obj.proof_image:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 400px; max-height: 300px; border-radius: 8px; border: 2px solid #334155;" />'
                '</a><br><small>Click to view full size</small>',
                obj.proof_image.url, obj.proof_image.url
            )
        return format_html('<span style="color: gray;">No payment proof uploaded</span>')
    proof_image_preview.short_description = 'Payment Proof Preview'
    
    def status_badge(self, obj):
        colors = {'pending': 'orange', 'confirmed': 'green', 'rejected': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.status, 'gray'), obj.status.upper())
    status_badge.short_description = 'Status'
    
    actions = ['confirm_deposits', 'reject_deposits']
    
    @admin.action(description='Confirm selected deposits')
    def confirm_deposits(self, request, queryset):
        from notifications.models import Notification
        count = 0
        for dep in queryset.filter(status='pending'):
            dep.user.balance += dep.amount
            dep.user.save()
            dep.status = 'confirmed'
            dep.confirmed_by = request.user
            dep.confirmed_at = timezone.now()
            dep.save()
            
            # Create notification for user
            Notification.objects.create(
                user=dep.user,
                notification_type='success',
                title='Deposit Confirmed! 💰',
                message=f'Your deposit of ${dep.amount:,.2f} ({dep.crypto_type}) has been confirmed and credited to your account.'
            )
            count += 1
        self.message_user(request, f'{count} deposit(s) confirmed and funds added.')
    
    @admin.action(description='Reject selected deposits')
    def reject_deposits(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected', confirmed_by=request.user, confirmed_at=timezone.now())
        self.message_user(request, 'Deposits rejected.')


@admin.register(WalletAddress)
class WalletAddressAdmin(admin.ModelAdmin):
    """Admin for WalletAddress model."""
    
    list_display = ['crypto_type', 'address_short', 'label', 'is_active']
    list_filter = ['crypto_type', 'is_active']
    search_fields = ['address', 'label']
    list_editable = ['is_active']
    
    def address_short(self, obj):
        return f"{obj.address[:20]}...{obj.address[-10:]}" if len(obj.address) > 35 else obj.address
    address_short.short_description = 'Address'


# ============== LOAN ADMIN ==============

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Admin for Loan model."""
    
    list_display = ['user', 'amount_display', 'interest_rate', 'duration_days', 'total_repayment_display', 'status_badge', 'created_at']
    list_filter = ['status', 'duration_days', 'created_at']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['id', 'total_repayment', 'amount_repaid', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Loan Info', {'fields': ('user', 'amount', 'interest_rate', 'duration_days', 'total_repayment')}),
        ('Purpose', {'fields': ('purpose', 'collateral_description')}),
        ('Repayment', {'fields': ('amount_repaid',)}),
        ('Status', {'fields': ('status', 'admin_note')}),
        ('Processing', {'fields': ('approved_by', 'approved_at', 'disbursed_at', 'due_date')}),
    )
    
    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def total_repayment_display(self, obj):
        return f"${obj.total_repayment:,.2f}"
    total_repayment_display.short_description = 'Total Due'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange', 'approved': 'blue', 'rejected': 'red',
            'disbursed': 'purple', 'repaying': 'teal', 'completed': 'green', 'defaulted': 'darkred'
        }
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.status, 'gray'), obj.status.upper())
    status_badge.short_description = 'Status'
    
    actions = ['approve_loans', 'reject_loans', 'disburse_loans']
    
    @admin.action(description='Approve selected loans')
    def approve_loans(self, request, queryset):
        from datetime import timedelta
        for loan in queryset.filter(status='pending'):
            loan.status = 'approved'
            loan.approved_by = request.user
            loan.approved_at = timezone.now()
            loan.save()
        self.message_user(request, 'Loans approved.')
    
    @admin.action(description='Reject selected loans')
    def reject_loans(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, 'Loans rejected.')
    
    @admin.action(description='Disburse approved loans')
    def disburse_loans(self, request, queryset):
        from datetime import timedelta
        for loan in queryset.filter(status='approved'):
            loan.user.balance += loan.amount
            loan.user.save()
            loan.status = 'disbursed'
            loan.disbursed_at = timezone.now()
            loan.due_date = timezone.now() + timedelta(days=loan.duration_days)
            loan.save()
        self.message_user(request, 'Loans disbursed to user accounts.')


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    """Admin for LoanRepayment model."""
    
    list_display = ['loan', 'amount_display', 'payment_method', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['loan__user__email']
    readonly_fields = ['id', 'created_at']
    
    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'


# ============== VIRTUAL CARD ADMIN ==============

@admin.register(VirtualCard)
class VirtualCardAdmin(admin.ModelAdmin):
    """Admin for VirtualCard model."""
    
    list_display = ['user', 'card_type', 'masked_number', 'balance_display', 'status_badge', 'created_at']
    list_filter = ['status', 'card_type', 'created_at']
    search_fields = ['user__email', 'card_holder_name']
    readonly_fields = ['id', 'card_number', 'created_at']  # CVV removed per PCI-DSS
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Card Details', {'fields': ('card_type', 'card_holder_name', 'card_number', 'expiry_month', 'expiry_year')}),
        ('Limits', {'fields': ('balance', 'daily_limit', 'monthly_limit')}),
        ('Settings', {'fields': ('is_online_enabled', 'is_international_enabled')}),
        ('Status', {'fields': ('status', 'billing_address', 'activated_at')}),
    )
    
    def balance_display(self, obj):
        return f"${obj.balance:,.2f}"
    balance_display.short_description = 'Balance'
    
    def status_badge(self, obj):
        colors = {'pending': 'orange', 'active': 'green', 'frozen': 'blue', 'expired': 'gray', 'cancelled': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.status, 'gray'), obj.status.upper())
    status_badge.short_description = 'Status'
    
    actions = ['activate_cards', 'freeze_cards', 'unfreeze_cards']
    
    @admin.action(description='Activate selected cards')
    def activate_cards(self, request, queryset):
        queryset.filter(status='pending').update(status='active', activated_at=timezone.now())
        self.message_user(request, 'Cards activated.')
    
    @admin.action(description='Freeze selected cards')
    def freeze_cards(self, request, queryset):
        queryset.filter(status='active').update(status='frozen')
        self.message_user(request, 'Cards frozen.')
    
    @admin.action(description='Unfreeze selected cards')
    def unfreeze_cards(self, request, queryset):
        queryset.filter(status='frozen').update(status='active')
        self.message_user(request, 'Cards unfrozen.')


# ============== COUPON ADMIN ==============

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin for Coupon model."""
    
    list_display = ['code', 'discount_type', 'discount_value', 'uses_count', 'uses_limit', 'is_active', 'expires_at']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'description']
    list_editable = ['is_active']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Code', {'fields': ('code', 'description')}),
        ('Discount', {'fields': ('discount_type', 'discount_value', 'min_deposit', 'max_discount')}),
        ('Limits', {'fields': ('uses_limit', 'uses_count', 'uses_per_user')}),
        ('Validity', {'fields': ('is_active', 'starts_at', 'expires_at')}),
    )


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    """Admin for CouponUsage model."""
    
    list_display = ['coupon', 'user', 'discount_amount', 'used_at']
    list_filter = ['coupon', 'used_at']
    search_fields = ['user__email', 'coupon__code']
    readonly_fields = ['id', 'used_at']


# ============== AGENT APPLICATION ADMIN ==============

@admin.register(AgentApplication)
class AgentApplicationAdmin(admin.ModelAdmin):
    """Admin for AgentApplication model."""
    
    list_display = ['user', 'full_name', 'country', 'expected_referrals', 'status_badge', 'created_at']
    list_filter = ['status', 'country', 'created_at']
    search_fields = ['user__email', 'full_name', 'phone']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Applicant', {'fields': ('user', 'full_name', 'phone', 'country', 'city')}),
        ('Application', {'fields': ('experience', 'marketing_plan', 'expected_referrals')}),
        ('Online Presence', {'fields': ('social_media_links', 'website')}),
        ('Documents', {'fields': ('id_document',)}),
        ('Status', {'fields': ('status', 'admin_note', 'commission_rate')}),
        ('Review', {'fields': ('reviewed_by', 'reviewed_at')}),
    )
    
    def status_badge(self, obj):
        colors = {'pending': 'orange', 'approved': 'green', 'rejected': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.status, 'gray'), obj.status.upper())
    status_badge.short_description = 'Status'
    
    actions = ['approve_applications', 'reject_applications']
    
    @admin.action(description='Approve selected applications')
    def approve_applications(self, request, queryset):
        queryset.filter(status='pending').update(
            status='approved', 
            reviewed_by=request.user, 
            reviewed_at=timezone.now()
        )
        self.message_user(request, 'Agent applications approved.')
    
    @admin.action(description='Reject selected applications')
    def reject_applications(self, request, queryset):
        queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, 'Agent applications rejected.')


# ============== ACCOUNT UPGRADE ADMIN ==============

@admin.register(AccountUpgrade)
class AccountUpgradeAdmin(admin.ModelAdmin):
    """Admin for AccountUpgrade model."""
    
    list_display = ['user', 'current_tier', 'requested_tier', 'amount_display', 'status_badge', 'created_at']
    list_filter = ['status', 'requested_tier', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    
    def amount_display(self, obj):
        return f"${obj.amount:,.2f}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {'pending': 'orange', 'paid': 'blue', 'confirmed': 'green', 'rejected': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.status, 'gray'), obj.status.upper())
    status_badge.short_description = 'Status'
    
    actions = ['confirm_upgrades', 'reject_upgrades']
    
    @admin.action(description='Confirm selected upgrades')
    def confirm_upgrades(self, request, queryset):
        for upgrade in queryset.filter(status='paid'):
            upgrade.user.account_type = upgrade.requested_tier
            upgrade.user.save()
            upgrade.status = 'confirmed'
            upgrade.processed_by = request.user
            upgrade.processed_at = timezone.now()
            upgrade.save()
        self.message_user(request, 'Account upgrades confirmed.')
    
    @admin.action(description='Reject selected upgrades')
    def reject_upgrades(self, request, queryset):
        for upgrade in queryset.filter(status__in=['pending', 'paid']):
            # Refund if paid from balance
            if upgrade.payment_method == 'balance':
                upgrade.user.balance += upgrade.amount
                upgrade.user.save()
            upgrade.status = 'rejected'
            upgrade.processed_by = request.user
            upgrade.processed_at = timezone.now()
            upgrade.save()
        self.message_user(request, 'Upgrades rejected and refunded.')


# ============== CRYPTO TICKER ADMIN ==============

@admin.register(CryptoTicker)
class CryptoTickerAdmin(admin.ModelAdmin):
    """
    Manage which cryptocurrencies appear in the live price ticker shown
    on every page.  Prices are fetched live from the CoinGecko public API
    using the coingecko_id you set here.

    Common coingecko_id values:
      BTC  → bitcoin          ETH  → ethereum
      USDT → tether           USDC → usd-coin
      LTC  → litecoin         BNB  → binancecoin
      SOL  → solana           XRP  → ripple
      ADA  → cardano          DOGE → dogecoin
    """

    list_display = ['symbol', 'name', 'coingecko_id', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['symbol', 'name', 'coingecko_id']
    ordering = ['display_order', 'symbol']
