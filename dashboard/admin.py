from django.contrib import admin
from django.utils.html import format_html
from .models import NewsArticle, NewsletterSubscription, ContactMessage, Dispute


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'is_featured', 'published_at']
    list_filter = ['is_published', 'is_featured', 'category']
    search_fields = ['title', 'excerpt', 'content']
    list_editable = ['is_published', 'is_featured']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-published_at']
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'category', 'is_published', 'is_featured', 'published_at')}),
        ('Content', {'fields': ('excerpt', 'content', 'image_url')}),
    )


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['reference_display', 'subject', 'appeal_type', 'status_badge', 'created_at']
    list_filter = ['status', 'appeal_type', 'created_at']
    search_fields = ['subject', 'description', 'user__email', 'guest_email', 'transaction_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Submission Info', {'fields': ('id', 'user', 'guest_name', 'guest_email', 'created_at')}),
        ('Appeal Details', {'fields': ('appeal_type', 'category', 'subject', 'description', 'amount', 'currency', 'transaction_id')}),
        ('Resolution', {'fields': ('status', 'admin_response', 'resolved_at')}),
    )

    def reference_display(self, obj):
        return obj.reference
    reference_display.short_description = 'Reference'

    def status_badge(self, obj):
        colors = {
            'pending': '#FFD700',
            'under_review': '#3b82f6',
            'resolved': '#00A86B',
            'closed': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.8rem;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        return False
