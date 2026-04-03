from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import F
import csv
from .models import (InvestmentPlan, Investment, Deposit, Withdrawal, WalletAddress,
                     Loan, LoanRepayment, VirtualCard, Coupon, CouponUsage, 
                     AgentApplication, AccountUpgrade, CryptoTicker)


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_amount', 'max_amount', 'daily_roi', 'duration_days', 
                    'total_roi_display', 'is_active', 'is_featured', 'sort_order']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'is_featured', 'sort_order']
    
    def total_roi_display(self, obj):
        return f'{obj.total_roi}%'
    total_roi_display.short_description = 'Total ROI'


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount_display', 'expected_profit_display', 
                    'actual_profit_display', 'status', 'progress', 'start_date', 'end_date']
    list_filter = ['status', 'plan', 'start_date']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['start_date', 'expected_profit']
    list_select_related = ['user', 'plan']
    actions = ['mark_completed', 'cancel_investments', 'export_to_csv']
    
    def amount_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def expected_profit_display(self, obj):
        return format_html('<span style="color: blue;">${:,.2f}</span>', obj.expected_profit)
    expected_profit_display.short_description = 'Expected Profit'
    
    def actual_profit_display(self, obj):
        return format_html('<span style="color: green;">${:,.2f}</span>', obj.actual_profit)
    actual_profit_display.short_description = 'Actual Profit'
    
    def progress(self, obj):
        return f'{obj.progress_percentage}%'
    progress.short_description = 'Progress'
    
    def mark_completed(self, request, queryset):
        for investment in queryset.filter(status='active'):
            user = investment.user
            user.balance += investment.amount + investment.actual_profit
            user.invested_amount -= investment.amount
            user.save()
            
            investment.status = 'completed'
            investment.save()
        
        self.message_user(request, f'{queryset.count()} investments marked as completed.')
    mark_completed.short_description = 'Mark selected as completed'
    
    def cancel_investments(self, request, queryset):
        for investment in queryset.filter(status='active'):
            user = investment.user
            user.balance += investment.amount
            user.invested_amount -= investment.amount
            user.save()
            
            investment.status = 'cancelled'
            investment.save()
        
        self.message_user(request, f'{queryset.count()} investments cancelled.')
    cancel_investments.short_description = 'Cancel selected investments'
    
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="investments.csv"'
        writer = csv.writer(response)
        writer.writerow(['User', 'Plan', 'Amount', 'Status', 'Start Date', 'End Date'])
        
        for inv in queryset:
            writer.writerow([inv.user.email, inv.plan.name, inv.amount, inv.status, 
                           inv.start_date, inv.end_date])
        
        return response
    export_to_csv.short_description = 'Export to CSV'


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'crypto_type', 'payment_method_display', 
                    'status_badge', 'proof_preview', 'created_at', 'quick_actions']
    list_filter = ['status', 'crypto_type', 'created_at']
    search_fields = ['user__email', 'tx_hash']
    readonly_fields = ['user', 'created_at', 'confirmed_by', 'proof_image_large']
    list_select_related = ['user', 'confirmed_by']
    actions = ['mark_confirmed', 'mark_rejected']
    
    fieldsets = (
        ('💰 Deposit Details', {
            'fields': ('user', 'amount', 'crypto_type', 'tx_hash')
        }),
        ('📸 Payment Proof', {
            'fields': ('proof_image_large',),
            'description': '<strong style="color: blue;">⚠️ REVIEW THE PAYMENT SCREENSHOT BEFORE CONFIRMING</strong>'
        }),
        ('✅ Status & Approval', {
            'fields': ('status', 'admin_note', 'confirmed_by', 'created_at'),
            'description': '<strong style="color: green;">Change status to "Confirmed" to credit user balance</strong>'
        }),
    )
    
    def amount_display(self, obj):
        return format_html('<strong style="color: green;">${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def payment_method_display(self, obj):
        if obj.crypto_type == 'BANK':
            return format_html('<span style="background: #3498db; color: white; padding: 2px 8px; border-radius: 3px;">🏦 Bank</span>')
        return format_html('<span style="background: #f39c12; color: white; padding: 2px 8px; border-radius: 3px;">🪙 {}</span>', obj.crypto_type)
    payment_method_display.short_description = 'Payment'
    
    def status_badge(self, obj):
        colors = {'pending': 'orange', 'confirmed': 'green', 'rejected': 'red'}
        icons = {'pending': '⏳', 'confirmed': '✅', 'rejected': '❌'}
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 15px;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def proof_preview(self, obj):
        if obj.proof_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px; border: 2px solid #ddd;" title="Click to view full size"/></a>',
                obj.proof_image.url, obj.proof_image.url
            )
        return format_html('<span style="color: #999;">No proof</span>')
    proof_preview.short_description = '📸 Proof'
    
    def proof_image_large(self, obj):
        if obj.proof_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 400px; max-height: 300px; border: 3px solid #ddd; border-radius: 8px;" /></a><br><small>Click to view full size</small>',
                obj.proof_image.url, obj.proof_image.url
            )
        return 'No payment proof uploaded'
    proof_image_large.short_description = 'Payment Screenshot'
    
    def quick_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ WAITING FOR REVIEW</span>'
            )
        elif obj.status == 'confirmed':
            return format_html('<span style="color: green;">✅ Released</span>')
        return format_html('<span style="color: red;">❌ Rejected</span>')
    quick_actions.short_description = 'Action'
    
    @transaction.atomic
    def mark_confirmed(self, request, queryset):
        count = 0
        from accounts.models import CustomUser
        for deposit in queryset.filter(status='pending').select_for_update():
            # Lock the user row to prevent race conditions
            user = CustomUser.objects.select_for_update().get(pk=deposit.user.pk)
            user.balance = F('balance') + deposit.amount
            user.save(update_fields=['balance'])
            
            deposit.status = 'confirmed'
            deposit.confirmed_by = request.user
            deposit.confirmed_at = timezone.now()
            deposit.save()
            
            # Refresh user to get actual balance for notification
            user.refresh_from_db()
            
            # Create notification for user
            from notifications.models import Notification
            Notification.objects.create(
                user=user,
                title='Deposit Confirmed',
                message=f'Your deposit of ${deposit.amount:,.2f} has been confirmed and credited to your account.',
                notification_type='deposit'
            )
            count += 1
        
        self.message_user(request, f'✅ {count} deposit(s) confirmed and users notified!')
    mark_confirmed.short_description = '✅ Confirm & Credit Balance'
    
    def mark_rejected(self, request, queryset):
        count = 0
        for deposit in queryset.filter(status='pending'):
            deposit.status = 'rejected'
            deposit.save()
            
            # Create notification for user
            from notifications.models import Notification
            Notification.objects.create(
                user=deposit.user,
                title='Deposit Rejected',
                message=f'Your deposit of ${deposit.amount:,.2f} was rejected. Please contact support for assistance.',
                notification_type='deposit'
            )
            count += 1
        
        self.message_user(request, f'❌ {count} deposit(s) rejected.')
    mark_rejected.short_description = '❌ Reject Selected'
    
    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """Auto-credit user when admin confirms deposit"""
        if change:
            try:
                old_deposit = Deposit.objects.get(pk=obj.pk)
                # If status changed from pending to confirmed
                if old_deposit.status == 'pending' and obj.status == 'confirmed':
                    user = obj.user
                    user.balance += obj.amount
                    user.save()
                    
                    obj.confirmed_by = request.user
                    obj.confirmed_at = timezone.now()
                    
                    # Create notification
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=user,
                        title='Deposit Confirmed',
                        message=f'Your deposit of ${obj.amount:,.2f} has been confirmed!',
                        notification_type='deposit'
                    )
            except Deposit.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'user_balance_display', 'withdrawal_method', 'crypto_type', 
                    'wallet_address_short', 'status_badge', 'created_at', 'quick_actions']
    list_filter = ['status', 'withdrawal_method', 'crypto_type', 'created_at']
    search_fields = ['user__email', 'wallet_address', 'user__full_name']
    readonly_fields = ['user', 'amount', 'withdrawal_method', 'crypto_type', 'wallet_address', 
                       'bank_name', 'account_number', 'account_name',
                       'created_at', 'processed_by', 'processed_at']
    list_select_related = ['user', 'processed_by']
    actions = ['approve_and_complete_withdrawal', 'cancel_withdrawal']
    ordering = ['-created_at']
    
    fieldsets = (
        ('👤 User Information', {
            'fields': ('user',),
        }),
        ('💰 Withdrawal Details', {
            'fields': ('amount', 'withdrawal_method', 'crypto_type', 'wallet_address'),
            'description': '<strong style="color: blue;">Amount has already been deducted from user balance when they requested</strong>'
        }),
        ('🏦 Bank Details (if bank transfer)', {
            'fields': ('bank_name', 'account_number', 'account_name'),
            'classes': ('collapse',)
        }),
        ('✅ Status & Processing', {
            'fields': ('status', 'tx_hash', 'admin_note', 'processed_by', 'processed_at'),
            'description': '<strong style="color: green;">Use actions below to Approve/Complete or Cancel withdrawal</strong>'
        }),
    )
    
    def amount_display(self, obj):
        return format_html('<strong style="color: green;">${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def user_balance_display(self, obj):
        return format_html('<span style="color: blue;">${:,.2f}</span>', obj.user.balance)
    user_balance_display.short_description = 'User Balance'
    
    def wallet_address_short(self, obj):
        if obj.wallet_address:
            return format_html('<code>{}</code>', f'{obj.wallet_address[:15]}...')
        elif obj.bank_name:
            return format_html('<span>🏦 {}</span>', obj.bank_name[:15])
        return '-'
    wallet_address_short.short_description = 'Destination'
    
    def status_badge(self, obj):
        colors = {'pending': '#f39c12', 'approved': '#3498db', 'completed': '#27ae60', 'rejected': '#e74c3c'}
        icons = {'pending': '⏳', 'approved': '✅', 'completed': '💸', 'rejected': '❌'}
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 15px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def quick_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ NEEDS REVIEW</span>'
            )
        elif obj.status == 'completed':
            return format_html('<span style="color: green;">💸 Sent to user</span>')
        elif obj.status == 'rejected':
            return format_html('<span style="color: red;">❌ Cancelled - funds returned</span>')
        return format_html('<span style="color: blue;">✅ Approved</span>')
    quick_actions.short_description = 'Action Needed'
    
    @transaction.atomic
    def approve_and_complete_withdrawal(self, request, queryset):
        """Approve withdrawal and mark as completed - funds already deducted"""
        from notifications.models import Notification
        count = 0
        for withdrawal in queryset.filter(status='pending'):
            withdrawal.status = 'completed'
            withdrawal.processed_by = request.user
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            
            # Send success notification to user
            Notification.objects.create(
                user=withdrawal.user,
                title='Withdrawal Successful',
                message=f'Your withdrawal of ${withdrawal.amount:,.2f} has been processed successfully and sent to your wallet/account!',
                notification_type='withdrawal'
            )
            count += 1
        
        self.message_user(request, f'💸 {count} withdrawal(s) approved and completed! Users notified.')
    approve_and_complete_withdrawal.short_description = '✅ Approve & Complete (Send to User)'
    
    @transaction.atomic
    def cancel_withdrawal(self, request, queryset):
        """Cancel/Reject withdrawal and return funds to user"""
        from notifications.models import Notification
        count = 0
        for withdrawal in queryset.filter(status='pending').select_for_update():
            # Return funds to user balance
            withdrawal.user.__class__.objects.filter(pk=withdrawal.user.pk).update(
                balance=F('balance') + withdrawal.amount,
                total_withdrawn=F('total_withdrawn') - withdrawal.amount
            )
            
            withdrawal.status = 'rejected'
            withdrawal.processed_by = request.user
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            
            # Refresh user to get updated balance
            withdrawal.user.refresh_from_db()
            
            # Send notification - funds credited back
            Notification.objects.create(
                user=withdrawal.user,
                title='Withdrawal Cancelled',
                message=f'Your withdrawal request of ${withdrawal.amount:,.2f} has been cancelled. The funds have been credited back to your account. New balance: ${withdrawal.user.balance:,.2f}',
                notification_type='withdrawal'
            )
            count += 1
        
        self.message_user(request, f'❌ {count} withdrawal(s) cancelled. Funds returned to users!')
    cancel_withdrawal.short_description = '❌ Cancel & Return Funds to User'


@admin.register(WalletAddress)
class WalletAddressAdmin(admin.ModelAdmin):
    list_display = ['crypto_type', 'address_short', 'qr_preview', 'label', 'is_active', 'created_at']
    list_filter = ['crypto_type', 'is_active']
    list_editable = ['is_active']
    search_fields = ['address', 'label']
    
    fieldsets = (
        ('💰 Wallet Configuration', {
            'fields': ('crypto_type', 'address', 'label', 'network'),
            'description': '<strong style="color: blue;">⚠️ ADD WALLET ADDRESSES HERE - Users will see these on the deposit page</strong>'
        }),
        ('QR Code (Optional)', {
            'fields': ('qr_code_image',),
            'description': 'Upload QR code image for this wallet address (optional)'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Only active wallets are shown to users'
        }),
    )
    
    def address_short(self, obj):
        return format_html('<code>{}</code>', f'{obj.address[:20]}...' if len(obj.address) > 20 else obj.address)
    address_short.short_description = 'Wallet Address'
    
    def qr_preview(self, obj):
        if obj.qr_code_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px;" />', obj.qr_code_image.url)
        return '❌'
    qr_preview.short_description = 'QR Code'


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'interest_rate', 'duration_days', 
                    'status', 'due_date', 'remaining_display']
    list_filter = ['status', 'duration_days']
    search_fields = ['user__email']
    
    def amount_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def remaining_display(self, obj):
        return format_html('${:,.2f}', obj.remaining_balance)
    remaining_display.short_description = 'Remaining'


@admin.register(VirtualCard)
class VirtualCardAdmin(admin.ModelAdmin):
    list_display = ['user', 'masked_number', 'card_type', 'balance_display', 'status']
    list_filter = ['status', 'card_type']
    search_fields = ['user__email']  # Removed card_number for security
    readonly_fields = ['card_number', 'cvv']  # Protect sensitive card data
    list_select_related = ['user']
    
    def balance_display(self, obj):
        return format_html('${:,.2f}', obj.balance)
    balance_display.short_description = 'Balance'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'uses_count', 
                    'uses_limit', 'is_active', 'expires_at']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code']
    list_editable = ['is_active']


@admin.register(AgentApplication)
class AgentApplicationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'country', 'expected_referrals', 'commission_rate', 
                    'status', 'created_at']
    list_filter = ['status', 'country']
    search_fields = ['full_name', 'phone']


@admin.register(AccountUpgrade)
class AccountUpgradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_tier_display', 'requested_tier', 'amount', 'status_badge', 'created_at', 'actions_display']
    list_filter = ['status', 'requested_tier']
    search_fields = ['user__email']
    actions = ['approve_upgrades', 'reject_upgrades']
    
    fieldsets = (
        ('User & Request', {
            'fields': ('user', 'requested_tier', 'amount')
        }),
        ('✅ APPROVAL', {
            'fields': ('status', 'rejection_reason', 'processed_by', 'processed_at'),
            'description': '<strong style="color: green;">Change status to "Approved" to upgrade user account</strong>'
        }),
    )
    
    readonly_fields = ['user', 'created_at']
    
    def current_tier_display(self, obj):
        return obj.user.get_account_type_display()
    current_tier_display.short_description = 'Current Tier'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def actions_display(self, obj):
        if obj.status == 'pending':
            return format_html('<span style="color: orange;">⏳ Waiting for approval</span>')
        return '-'
    actions_display.short_description = 'Quick Action'
    
    def approve_upgrades(self, request, queryset):
        """Approve account upgrades and update user tier"""
        count = 0
        for upgrade in queryset.filter(status='pending'):
            # Update user account type
            user = upgrade.user
            user.account_type = upgrade.requested_tier
            user.save()
            
            # Mark upgrade as approved
            upgrade.status = 'approved'
            upgrade.processed_by = request.user
            upgrade.processed_at = timezone.now()
            upgrade.save()
            count += 1
        
        self.message_user(request, f'{count} account upgrades approved!')
    approve_upgrades.short_description = '✅ Approve selected upgrades'
    
    def reject_upgrades(self, request, queryset):
        """Reject account upgrades"""
        count = 0
        for upgrade in queryset.filter(status='pending'):
            upgrade.status = 'rejected'
            upgrade.processed_by = request.user
            upgrade.processed_at = timezone.now()
            upgrade.rejection_reason = 'Rejected by admin'
            upgrade.save()
            count += 1
        
        self.message_user(request, f'{count} account upgrades rejected.')
    reject_upgrades.short_description = '❌ Reject selected upgrades'
    
    def save_model(self, request, obj, form, change):
        """Auto-upgrade user account when admin approves"""
        if change:
            old_status = AccountUpgrade.objects.get(pk=obj.pk).status
            if old_status != obj.status and obj.status == 'approved':
                # Upgrade the user's account
                user = obj.user
                user.account_type = obj.requested_tier
                user.save()
                
                obj.processed_by = request.user
                obj.processed_at = timezone.now()
        
        super().save_model(request, obj, form, change)


@admin.register(CryptoTicker)
class CryptoTickerAdmin(admin.ModelAdmin):
    """
    Manage which cryptocurrencies appear in the live price ticker shown
    on every page. Prices are fetched live from the CoinGecko public API
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


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount', 'payment_method', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['loan__user__email']
    readonly_fields = ['loan', 'created_at']
    list_select_related = ['loan', 'loan__user']


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'used_at']
    list_filter = ['used_at']
    search_fields = ['user__email', 'coupon__code']
    readonly_fields = ['coupon', 'user', 'used_at']
    list_select_related = ['coupon', 'user']
