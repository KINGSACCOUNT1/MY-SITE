from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import KYCDocument
from accounts.email_notifications import send_kyc_notification

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_uploaded_file(file_obj, field_name):
    """Validate uploaded file type and size."""
    if not file_obj:
        return
    
    # Check file size
    if file_obj.size > MAX_FILE_SIZE:
        raise ValidationError(f'{field_name} exceeds maximum size of 10MB')
    
    # Check file type
    if file_obj.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(f'{field_name} must be JPEG or PNG image')
    
    # Verify it's actually an image by checking magic bytes
    file_obj.seek(0)
    header = file_obj.read(8)
    file_obj.seek(0)
    
    # JPEG starts with FF D8 FF, PNG starts with 89 50 4E 47
    is_jpeg = header[:3] == b'\xff\xd8\xff'
    is_png = header[:8] == b'\x89PNG\r\n\x1a\n'
    
    if not (is_jpeg or is_png):
        raise ValidationError(f'{field_name} is not a valid image file')


@login_required
def upload_kyc(request):
    """KYC document upload"""
    # Check if user already has KYC submitted
    try:
        kyc_doc = KYCDocument.objects.get(user=request.user)
        if kyc_doc.status in ['submitted', 'verified']:
            messages.info(request, 'You have already submitted KYC documents.')
            return redirect('kyc:status')
    except KYCDocument.DoesNotExist:
        kyc_doc = None
    
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        front_image = request.FILES.get('front_image')
        back_image = request.FILES.get('back_image')
        selfie_image = request.FILES.get('selfie_image')
        
        if not all([document_type, front_image, back_image, selfie_image]):
            messages.error(request, 'All fields are required.')
            return redirect('kyc:upload')
        
        # Validate uploaded files
        try:
            validate_uploaded_file(front_image, 'Front image')
            validate_uploaded_file(back_image, 'Back image')
            validate_uploaded_file(selfie_image, 'Selfie image')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('kyc:upload')
        
        # Create or update KYC document
        if kyc_doc:
            kyc_doc.document_type = document_type
            kyc_doc.front_image = front_image
            kyc_doc.back_image = back_image
            kyc_doc.selfie_image = selfie_image
            kyc_doc.status = 'submitted'
            kyc_doc.save()
        else:
            kyc_doc = KYCDocument.objects.create(
                user=request.user,
                document_type=document_type,
                front_image=front_image,
                back_image=back_image,
                selfie_image=selfie_image,
                status='submitted'
            )
        
        # Send admin notification
        send_kyc_notification(kyc_doc)
        
        messages.success(request, 'KYC documents uploaded successfully! We will review them within 24-48 hours.')
        return redirect('kyc:status')
    
    return render(request, 'kyc/upload.html')


@login_required
def kyc_status(request):
    """Display KYC verification status"""
    try:
        kyc_document = KYCDocument.objects.get(user=request.user)
    except KYCDocument.DoesNotExist:
        kyc_document = None
    
    return render(request, 'kyc/status.html', {
        'kyc_document': kyc_document
    })
