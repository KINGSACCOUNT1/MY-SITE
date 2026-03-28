from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import KYCDocument


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
        
        # Create or update KYC document
        if kyc_doc:
            kyc_doc.document_type = document_type
            kyc_doc.front_image = front_image
            kyc_doc.back_image = back_image
            kyc_doc.selfie_image = selfie_image
            kyc_doc.status = 'submitted'
            kyc_doc.save()
        else:
            KYCDocument.objects.create(
                user=request.user,
                document_type=document_type,
                front_image=front_image,
                back_image=back_image,
                selfie_image=selfie_image,
                status='submitted'
            )
        
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
