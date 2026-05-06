from django.db import models
from django.conf import settings
from django.utils import timezone


class KYCDocument(models.Model):
    """KYC Document verification model"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('passport', 'Passport'),
        ('drivers_license', "Driver's License"),
        ('national_id', 'National ID Card'),
        ('residence_permit', 'Residence Permit'),
        ('voter_id', 'Voter ID'),
        ('tax_id', 'Tax ID Card'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_document')
    
    # Document Information (optional - admin can fill during review)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=100, blank=True, default='')
    issuing_country = models.CharField(max_length=100, blank=True, default='')
    issuing_authority = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True, default='')
    issue_date = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    company_name = models.CharField(max_length=255, blank=True, default='', help_text='Company name for business accounts')
    
    # Document Images
    front_image = models.ImageField(upload_to='kyc/front/')
    back_image = models.ImageField(upload_to='kyc/back/', blank=True, null=True)
    selfie_image = models.ImageField(upload_to='kyc/selfie/')
    
    # Review Information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kyc_reviews'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'KYC Document'
        verbose_name_plural = 'KYC Documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.document_type} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-set submitted_at when status changes to submitted
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()
        
        # Sync status with user's kyc_status
        if self.user:
            self.user.kyc_status = self.status
            self.user.save(update_fields=['kyc_status'])
        
        super().save(*args, **kwargs)
