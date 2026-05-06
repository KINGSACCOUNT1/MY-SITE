from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import KYCDocument
from notifications.models import Notification


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'document_number', 'status_badge', 
                    'submitted_at', 'reviewed_at', 'quick_verify']
    list_filter = ['status', 'document_type', 'submitted_at']
    search_fields = ['user__email', 'document_number']
    readonly_fields = ['user', 'submitted_at', 'front_image_preview', 'back_image_preview', 
                       'selfie_image_preview', 'reviewed_by', 'reviewed_at']
    list_select_related = ['user', 'reviewed_by']
    actions = ['verify_kyc', 'reject_kyc']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Document Information', {
            'fields': ('document_type', 'document_number', 'issuing_country', 
                      'issuing_authority', 'date_of_birth', 'nationality',
                      'issue_date', 'expires_at', 'company_name')
        }),
        ('📷 Uploaded Images', {
            'fields': ('front_image_preview', 'back_image_preview', 'selfie_image_preview')
        }),
        ('✅ REVIEW & VERIFY', {
            'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at'),
            'description': '<strong style="color: blue;">Change status to "Verified" to approve KYC</strong>'
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
    
    def quick_verify(self, obj):
        if obj.status == 'pending' or obj.status == 'submitted':
            return format_html(
                '<a class="button" style="background-color: green; color: white;" href="#" onclick="return false;">Click "Verify KYC" action above</a>'
            )
        return '-'
    quick_verify.short_description = 'Quick Action'
    
    def front_image_preview(self, obj):
        if obj.front_image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px;" />', obj.front_image.url)
        return 'No image'
    front_image_preview.short_description = 'Front Image'
    
    def back_image_preview(self, obj):
        if obj.back_image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px;" />', obj.back_image.url)
        return 'No image'
    back_image_preview.short_description = 'Back Image'
    
    def selfie_image_preview(self, obj):
        if obj.selfie_image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px;" />', obj.selfie_image.url)
        return 'No image'
    selfie_image_preview.short_description = 'Selfie'
    
    def verify_kyc(self, request, queryset):
        """Bulk verify KYC documents"""
        count = 0
        for kyc in queryset:
            if kyc.status != 'verified':
                kyc.status = 'verified'
                kyc.reviewed_by = request.user
                kyc.reviewed_at = timezone.now()
                kyc.save()
                
                # Update user KYC status
                user = kyc.user
                user.kyc_status = 'verified'
                user.save()
                
                # Send notification to user
                Notification.objects.create(
                    user=user,
                    title='KYC Verification Approved ✓',
                    message='Congratulations! Your identity has been verified successfully. You can now make withdrawals and access all platform features.',
                    notification_type='success'
                )
                count += 1
        
        self.message_user(request, f'{count} KYC documents verified successfully!')
    verify_kyc.short_description = '✅ Verify selected KYC documents'
    
    def reject_kyc(self, request, queryset):
        """Bulk reject KYC documents"""
        count = 0
        for kyc in queryset:
            if kyc.status != 'rejected':
                kyc.status = 'rejected'
                kyc.reviewed_by = request.user
                kyc.reviewed_at = timezone.now()
                kyc.rejection_reason = kyc.rejection_reason or 'Documents could not be verified. Please resubmit clear, valid documents.'
                kyc.save()
                
                # Update user KYC status
                user = kyc.user
                user.kyc_status = 'rejected'
                user.save()
                
                # Send notification to user
                Notification.objects.create(
                    user=user,
                    title='KYC Verification Rejected',
                    message=f'Your KYC verification was rejected. Reason: {kyc.rejection_reason}. Please upload new documents.',
                    notification_type='warning'
                )
                count += 1
        
        self.message_user(request, f'{count} KYC documents rejected.')
    reject_kyc.short_description = '❌ Reject selected KYC documents'
    
    def save_model(self, request, obj, form, change):
        """Auto-update user KYC status when admin changes KYC document status"""
        if change:
            old_obj = KYCDocument.objects.get(pk=obj.pk)
            old_status = old_obj.status
            if old_status != obj.status:
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
                
                # Update user's KYC status
                user = obj.user
                user.kyc_status = obj.status
                user.save()
                
                # Send notification based on new status
                if obj.status == 'verified':
                    Notification.objects.create(
                        user=user,
                        title='KYC Verification Approved ✓',
                        message='Congratulations! Your identity has been verified successfully.',
                        notification_type='success'
                    )
                elif obj.status == 'rejected':
                    Notification.objects.create(
                        user=user,
                        title='KYC Verification Rejected',
                        message=f'Your KYC was rejected. Reason: {obj.rejection_reason or "Please resubmit documents."}',
                        notification_type='warning'
                    )
        
        super().save_model(request, obj, form, change)
