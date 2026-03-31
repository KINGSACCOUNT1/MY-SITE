from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import CustomUser, ActivityLog, Referral


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'full_name', 'balance_display', 'invested_display', 
                    'profit_display', 'account_badge', 'kyc_badge', 'status_badge', 
                    'referral_code', 'joined_date', 'quick_actions']
    list_filter = ['is_active', 'is_staff', 'account_type', 'kyc_status', 
                   'email_verified', 'two_fa_enabled', 'date_joined']
    search_fields = ['email', 'full_name', 'phone', 'referral_code', 'country']
    ordering = ['-date_joined']
    list_select_related = ['referred_by']
    
    fieldsets = (
        ('Login Credentials', {
            'fields': ('email',)
        }),
        ('Personal Information', {
            'fields': ('full_name', 'phone', 'country', 'profile_image')
        }),
        ('💰 FINANCIAL MANAGEMENT (EDIT HERE)', {
            'fields': ('balance', 'invested_amount', 'total_profit', 'total_withdrawn', 'referral_bonus'),
            'description': '<strong style="color: red;">⚠️ ADMIN CONTROLS: Manually adjust user balances, profits, and investments here</strong>'
        }),
        ('Referral System', {
            'fields': ('referral_code', 'referred_by')
        }),
        ('🔐 ACCOUNT STATUS & UPGRADES', {
            'fields': ('account_type', 'kyc_status', 'email_verified'),
            'description': '<strong style="color: blue;">✅ Change account type (Beginner → VIP) and verify KYC here</strong>'
        }),
        ('Security Settings', {
            'fields': ('two_fa_enabled', 'two_fa_secret', 
                      'failed_login_attempts', 'locked_until'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'fields': ('email', 'full_name', 'password1', 'password2')
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'referral_code', 'two_fa_secret', 
                       'last_activity', 'failed_login_attempts', 'locked_until']
    
    def balance_display(self, obj):
        balance = obj.balance or 0
        color = 'green' if balance >= 0 else 'red'
        return format_html('<strong style="color: {};">${:,.2f}</strong>', color, balance)
    balance_display.short_description = 'Balance'
    balance_display.admin_order_field = 'balance'
    
    def invested_display(self, obj):
        amount = obj.invested_amount or 0
        return format_html('<span style="color: blue;">${:,.2f}</span>', amount)
    invested_display.short_description = 'Invested'
    invested_display.admin_order_field = 'invested_amount'
    
    def profit_display(self, obj):
        profit = obj.total_profit or 0
        return format_html('<span style="color: green;">${:,.2f}</span>', profit)
    profit_display.short_description = 'Profit'
    profit_display.admin_order_field = 'total_profit'
    
    def account_badge(self, obj):
        colors = {
            'starter': '#6c757d',      # gray
            'advance': '#0d6efd',      # blue
            'intro': '#6f42c1',        # purple
            'region': '#20c997',       # teal
            'pro': '#fd7e14',          # orange
            'premium': '#dc3545',      # red
            'executive': '#198754',    # green
            'elite': '#ffc107',        # gold
            'platinum': '#0dcaf0',     # cyan
            'diamond': '#d63384',      # pink
        }
        color = colors.get(obj.account_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_account_type_display()
        )
    account_badge.short_description = 'Account Type'
    
    def kyc_badge(self, obj):
        colors = {
            'pending': 'orange',
            'submitted': 'blue',
            'verified': 'green',
            'rejected': 'red'
        }
        color = colors.get(obj.kyc_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_kyc_status_display()
        )
    kyc_badge.short_description = 'KYC Status'
    
    def status_badge(self, obj):
        color = 'green' if obj.is_active else 'red'
        status = 'Active' if obj.is_active else 'Inactive'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'
    
    def joined_date(self, obj):
        if obj.date_joined:
            return obj.date_joined.strftime('%Y-%m-%d')
        return '-'
    joined_date.short_description = 'Joined'
    joined_date.admin_order_field = 'date_joined'
    
    def quick_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit User</a>',
            reverse('admin:accounts_customuser_change', args=[obj.pk])
        )
    quick_actions.short_description = 'Actions'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'description', 'ip_address']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'user_agent', 'created_at']
    list_select_related = ['user']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred', 'bonus_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['referrer__email', 'referred__email']
    readonly_fields = ['referrer', 'referred', 'created_at']
    list_select_related = ['referrer', 'referred']
