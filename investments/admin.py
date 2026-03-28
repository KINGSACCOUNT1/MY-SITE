from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import (InvestmentPlan, Investment, Deposit, Withdrawal, WalletAddress,
                     Loan, LoanRepayment, VirtualCard, Coupon, CouponUsage, 
                     AgentApplication, AccountUpgrade)


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
    list_display = ['user', 'amount_display', 'crypto_type', 'status', 'tx_hash', 'created_at']
    list_filter = ['status', 'crypto_type', 'created_at']
    search_fields = ['user__email', 'tx_hash']
    readonly_fields = ['user', 'created_at']
    actions = ['mark_confirmed', 'mark_rejected']
    
    def amount_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def mark_confirmed(self, request, queryset):
        for deposit in queryset.filter(status='pending'):
            user = deposit.user
            user.balance += deposit.amount
            user.save()
            
            deposit.status = 'confirmed'
            deposit.confirmed_by = request.user
            deposit.save()
        
        self.message_user(request, f'{queryset.count()} deposits confirmed.')
    mark_confirmed.short_description = 'Confirm selected deposits'
    
    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()} deposits rejected.')
    mark_rejected.short_description = 'Reject selected deposits'


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'withdrawal_method', 'crypto_type', 
                    'wallet_address_short', 'status', 'created_at']
    list_filter = ['status', 'withdrawal_method', 'crypto_type', 'created_at']
    search_fields = ['user__email', 'wallet_address']
    readonly_fields = ['user', 'created_at']
    actions = ['approve_withdrawal', 'reject_withdrawal', 'mark_completed']
    
    def amount_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def wallet_address_short(self, obj):
        if obj.wallet_address:
            return f'{obj.wallet_address[:10]}...'
        return '-'
    wallet_address_short.short_description = 'Wallet'
    
    def approve_withdrawal(self, request, queryset):
        queryset.filter(status='pending').update(status='approved', processed_by=request.user)
        self.message_user(request, f'{queryset.count()} withdrawals approved.')
    approve_withdrawal.short_description = 'Approve selected'
    
    def reject_withdrawal(self, request, queryset):
        for withdrawal in queryset.filter(status='pending'):
            user = withdrawal.user
            user.balance += withdrawal.amount
            user.save()
            
            withdrawal.status = 'rejected'
            withdrawal.processed_by = request.user
            withdrawal.save()
        
        self.message_user(request, f'{queryset.count()} withdrawals rejected.')
    reject_withdrawal.short_description = 'Reject selected'
    
    def mark_completed(self, request, queryset):
        queryset.update(status='completed', processed_by=request.user)
        self.message_user(request, f'{queryset.count()} withdrawals completed.')
    mark_completed.short_description = 'Mark as completed'


@admin.register(WalletAddress)
class WalletAddressAdmin(admin.ModelAdmin):
    list_display = ['crypto_type', 'address_short', 'label', 'is_active', 'created_at']
    list_filter = ['crypto_type', 'is_active']
    list_editable = ['is_active']
    
    def address_short(self, obj):
        return f'{obj.address[:20]}...'
    address_short.short_description = 'Address'


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
    search_fields = ['user__email', 'card_number']
    
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
    list_display = ['user', 'requested_tier', 'amount', 'status', 'created_at']
    list_filter = ['status', 'requested_tier']
    search_fields = ['user__email']


admin.site.register(LoanRepayment)
admin.site.register(CouponUsage)
