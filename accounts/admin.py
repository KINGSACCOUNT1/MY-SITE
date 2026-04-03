from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from decimal import Decimal
from .models import CustomUser, ActivityLog, Referral


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'full_name', 'balance_display', 'account_type', 
                    'kyc_status', 'is_active', 'referral_code', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'account_type', 'kyc_status', 'date_joined']
    search_fields = ['email', 'full_name', 'phone', 'referral_code']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Login Credentials', {
            'fields': ('email',)
        }),
        ('Personal Information', {
            'fields': ('full_name', 'phone', 'country', 'profile_image')
        }),
        ('💰 FINANCIAL MANAGEMENT', {
            'fields': ('balance', 'invested_amount', 'total_profit', 'total_withdrawn', 'referral_bonus'),
            'description': '<strong style="color: green;">⚠️ When you change the balance, the user will receive a notification!</strong>'
        }),
        ('Referral System', {
            'fields': ('referral_code', 'referred_by')
        }),
        ('Account Status', {
            'fields': ('account_type', 'kyc_status', 'email_verified'),
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
        try:
            balance = float(obj.balance or 0)
            return f'${balance:,.2f}'
        except:
            return '$0.00'
    balance_display.short_description = 'Balance'
    
    def save_model(self, request, obj, form, change):
        """Track balance changes and notify user"""
        if change:
            try:
                old_user = CustomUser.objects.get(pk=obj.pk)
                old_balance = Decimal(str(old_user.balance or 0))
                new_balance = Decimal(str(obj.balance or 0))
                
                # Check if balance changed
                if old_balance != new_balance:
                    difference = new_balance - old_balance
                    
                    # Create notification for balance change
                    from notifications.models import Notification
                    
                    if difference > 0:
                        # Amount added
                        Notification.objects.create(
                            user=obj,
                            title='Funds Added to Account',
                            message=f'${difference:,.2f} has been added to your account. Your new balance is ${new_balance:,.2f}.',
                            notification_type='deposit'
                        )
                    else:
                        # Amount deducted
                        Notification.objects.create(
                            user=obj,
                            title='Balance Adjustment',
                            message=f'${abs(difference):,.2f} has been deducted from your account. Your new balance is ${new_balance:,.2f}.',
                            notification_type='withdrawal'
                        )
            except CustomUser.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)


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
