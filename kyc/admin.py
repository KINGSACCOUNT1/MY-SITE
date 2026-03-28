from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import KYCDocument


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    """Admin for KYC document verification with enhanced country-specific details."""

    list_display = [
        'user', 'document_type', 'document_number', 'issuing_country',
        'date_of_birth', 'expires_at', 'status_badge', 'submitted_at', 'reviewed_by',
    ]
    list_filter = ['status', 'document_type', 'issuing_country', 'submitted_at']
    search_fields = [
        'user__email', 'user__full_name', 'document_number',
        'issuing_country', 'issuing_authority', 'nationality',
    ]
    readonly_fields = ['id', 'submitted_at', 'updated_at']
    ordering = ['-submitted_at']

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Document Information', {
            'fields': (
                'document_type', 'document_number',
                'issuing_country', 'issuing_authority',
                'issue_date', 'expires_at',
            ),
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'nationality'),
        }),
        ('Document Images', {
            'fields': ('front_image', 'back_image', 'selfie_image'),
        }),
        ('Review', {
            'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at'),
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#FFD700',
            'submitted': '#3b82f6',
            'verified': '#00A86B',
            'rejected': '#ef4444',
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.status.upper(),
        )
    status_badge.short_description = 'Status'

    actions = ['approve_kyc', 'reject_kyc']

    @admin.action(description='✅ Approve selected KYC documents')
    def approve_kyc(self, request, queryset):
        count = 0
        for doc in queryset.exclude(status='verified'):
            doc.status = 'verified'
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save()
            count += 1
        self.message_user(request, f'Approved {count} KYC document(s).')

    @admin.action(description='❌ Reject selected KYC documents')
    def reject_kyc(self, request, queryset):
        count = 0
        for doc in queryset.exclude(status='rejected'):
            doc.status = 'rejected'
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save()
            count += 1
        self.message_user(request, f'Rejected {count} KYC document(s).')

