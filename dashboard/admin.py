from django.contrib import admin
from .models import NewsArticle, NewsletterSubscription, ContactMessage, Dispute, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'company_email', 'company_phone', 'maintenance_mode']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'company_email', 'support_email', 'company_phone', 'company_address', 'company_website'),
            'description': 'Public company contact information displayed on the website'
        }),
        ('Email Configuration', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email'),
            'classes': ('collapse',),
            'description': 'SMTP settings for outgoing emails'
        }),
        ('API Configuration', {
            'fields': ('stripe_api_key', 'stripe_publishable_key', 'paypal_client_id', 'paypal_client_secret'),
            'classes': ('collapse',),
            'description': 'Payment gateway API credentials'
        }),
        ('Site Configuration', {
            'fields': ('maintenance_mode', 'enable_registrations', 'enable_deposits', 'enable_withdrawals'),
            'description': 'Site-wide feature toggles'
        }),
        ('Security & Compliance', {
            'fields': ('enable_two_factor', 'enable_ip_whitelist', 'session_timeout_minutes', 'kyc_required', 'minimum_deposit', 'maximum_withdrawal'),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one SiteSettings instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of SiteSettings
        return False


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'is_featured', 'published_at']
    list_filter = ['category', 'is_published', 'is_featured']
    search_fields = ['title', 'content']
    list_editable = ['is_published', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['reference', 'user', 'appeal_type', 'subject', 'status', 'created_at']
    list_filter = ['status', 'appeal_type', 'created_at']
    search_fields = ['subject', 'description', 'user__email']
    readonly_fields = ['user', 'created_at']
