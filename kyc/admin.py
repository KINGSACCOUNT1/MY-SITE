from django.contrib import admin
from django.utils.html import format_html
from .models import KYCDocument


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'document_number', 'status_badge', 
                    'submitted_at', 'reviewed_at']
    list_filter = ['status', 'document_type', 'submitted_at']
    search_fields = ['user__email', 'document_number']
    readonly_fields = ['user', 'submitted_at', 'front_image', 'back_image', 'selfie_image']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Document Information', {
            'fields': ('document_type', 'document_number', 'issuing_country', 
                      'issuing_authority', 'date_of_birth', 'nationality',
                      'issue_date', 'expires_at')
        }),
        ('Uploaded Images', {
            'fields': ('front_image', 'back_image', 'selfie_image')
        }),
        ('Review', {
            'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'submitted': 'blue',
            'verified': 'green',
            'rejected': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
