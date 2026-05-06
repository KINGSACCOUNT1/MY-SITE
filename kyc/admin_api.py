"""
Admin API endpoints for one-click KYC verification from email
"""
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import KYCDocument
from notifications.models import Notification
import hmac
import hashlib
from django.conf import settings

User = get_user_model()


def generate_kyc_verification_token(kyc_id, action):
    """Generate secure token for KYC verification links"""
    message = f"{kyc_id}:{action}:{settings.SECRET_KEY}"
    return hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_kyc_token(kyc_id, action, token):
    """Verify the security token"""
    expected_token = generate_kyc_verification_token(kyc_id, action)
    return hmac.compare_digest(token, expected_token)


@csrf_exempt
@require_http_methods(["GET"])
def verify_kyc_from_email(request, kyc_id, token):
    """
    One-click KYC verification endpoint for admin emails
    URL: /admin-api/kyc/<id>/verify/<token>/
    """
    try:
        # Verify token
        if not verify_kyc_token(kyc_id, 'verify', token):
            return HttpResponse(
                """
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                        .box { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .error { color: #e74c3c; font-size: 48px; }
                        h2 { color: #e74c3c; }
                    </style>
                </head>
                <body>
                    <div class="box">
                        <div class="error">❌</div>
                        <h2>Invalid Verification Link</h2>
                        <p>This link is invalid or has expired. Please use the admin panel to verify KYC.</p>
                    </div>
                </body>
                </html>
                """,
                status=403
            )
        
        # Get KYC document
        kyc = get_object_or_404(KYCDocument, id=kyc_id)
        user = kyc.user
        
        # Check if already verified
        if kyc.status == 'verified':
            return HttpResponse(
                f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                        .box {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .icon {{ color: #3498db; font-size: 48px; }}
                        h2 {{ color: #3498db; }}
                    </style>
                </head>
                <body>
                    <div class="box">
                        <div class="icon">ℹ️</div>
                        <h2>Already Verified</h2>
                        <p>KYC for <strong>{user.full_name}</strong> has already been verified.</p>
                        <p style="color: #7f8c8d; margin-top: 20px;">Account Balance: ${user.balance:,.2f}</p>
                    </div>
                </body>
                </html>
                """
            )
        
        # Update KYC status
        kyc.status = 'verified'
        kyc.reviewed_by = None  # Email verification doesn't have a specific admin
        kyc.reviewed_at = timezone.now()
        kyc.save()
        
        # Update user KYC status
        user.kyc_status = 'verified'
        user.save()
        
        # Create in-app notification for user
        Notification.objects.create(
            user=user,
            title='KYC Verification Approved ✓',
            message='Congratulations! Your identity has been verified successfully. You can now make withdrawals and access all platform features.',
            notification_type='success'
        )
        
        # Return success page
        return HttpResponse(
            f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="3;url=https://elitewealthcapita.uk/admin/kyc/kycdocument/">
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                    .box {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .success {{ color: #27ae60; font-size: 48px; animation: checkmark 0.5s ease; }}
                    @keyframes checkmark {{ 0% {{ transform: scale(0); }} 100% {{ transform: scale(1); }} }}
                    h2 {{ color: #27ae60; }}
                    .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .doc-type {{ font-size: 18px; color: #27ae60; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <div class="success">✅</div>
                    <h2>KYC Verified Successfully!</h2>
                    <div class="details">
                        <p><strong>User:</strong> {user.full_name}</p>
                        <p><strong>Email:</strong> {user.email}</p>
                        <p class="doc-type">📄 {kyc.get_document_type_display()}</p>
                        <p style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd;">
                            <strong>Account Balance:</strong> ${user.balance:,.2f}
                        </p>
                    </div>
                    <p style="color: #7f8c8d; font-size: 14px;">User has been notified ✉️</p>
                    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">Redirecting to KYC admin panel...</p>
                </div>
            </body>
            </html>
            """
        )
        
    except KYCDocument.DoesNotExist:
        return HttpResponse(
            """
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                    .box { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .error { color: #e74c3c; font-size: 48px; }
                    h2 { color: #e74c3c; }
                </style>
            </head>
            <body>
                <div class="box">
                    <div class="error">❌</div>
                    <h2>KYC Document Not Found</h2>
                    <p>The KYC document you're trying to verify doesn't exist.</p>
                </div>
            </body>
            </html>
            """,
            status=404
        )
    
    except Exception as e:
        return HttpResponse(
            f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                    .box {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error {{ color: #e74c3c; font-size: 48px; }}
                    h2 {{ color: #e74c3c; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <div class="error">⚠️</div>
                    <h2>Verification Failed</h2>
                    <p>An error occurred: {str(e)}</p>
                    <p style="color: #7f8c8d; margin-top: 20px;">Please verify manually in the admin panel.</p>
                </div>
            </body>
            </html>
            """,
            status=500
        )


@csrf_exempt
@require_http_methods(["GET"])
def reject_kyc_from_email(request, kyc_id, token, reason=''):
    """
    One-click KYC rejection endpoint for admin emails
    URL: /admin-api/kyc/<id>/reject/<token>/
    """
    try:
        # Verify token
        if not verify_kyc_token(kyc_id, 'reject', token):
            return HttpResponse(
                """
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                        .box { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .error { color: #e74c3c; font-size: 48px; }
                        h2 { color: #e74c3c; }
                    </style>
                </head>
                <body>
                    <div class="box">
                        <div class="error">❌</div>
                        <h2>Invalid Rejection Link</h2>
                        <p>This link is invalid or has expired. Please use the admin panel to reject KYC.</p>
                    </div>
                </body>
                </html>
                """,
                status=403
            )
        
        # Get KYC document
        kyc = get_object_or_404(KYCDocument, id=kyc_id)
        user = kyc.user
        
        # Check if already processed
        if kyc.status in ['verified', 'rejected']:
            return HttpResponse(
                f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                        .box {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .icon {{ color: #3498db; font-size: 48px; }}
                        h2 {{ color: #3498db; }}
                    </style>
                </head>
                <body>
                    <div class="box">
                        <div class="icon">ℹ️</div>
                        <h2>Already Processed</h2>
                        <p>This KYC has already been {kyc.status}.</p>
                    </div>
                </body>
                </html>
                """
            )
        
        # Update KYC status
        kyc.status = 'rejected'
        kyc.rejection_reason = reason or 'Documents could not be verified. Please resubmit clear, valid documents.'
        kyc.reviewed_by = None  # Email verification doesn't have a specific admin
        kyc.reviewed_at = timezone.now()
        kyc.save()
        
        # Update user KYC status
        user.kyc_status = 'rejected'
        user.save()
        
        # Create in-app notification for user
        Notification.objects.create(
            user=user,
            title='KYC Verification Rejected',
            message=f'Your KYC verification was rejected. Reason: {kyc.rejection_reason}. Please upload new documents.',
            notification_type='warning'
        )
        
        # Return success page
        return HttpResponse(
            f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="3;url=https://elitewealthcapita.uk/admin/kyc/kycdocument/">
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                    .box {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .warning {{ color: #e74c3c; font-size: 48px; }}
                    h2 {{ color: #e74c3c; }}
                    .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <div class="warning">🚫</div>
                    <h2>KYC Rejected</h2>
                    <div class="details">
                        <p><strong>User:</strong> {user.full_name}</p>
                        <p><strong>Email:</strong> {user.email}</p>
                        <p><strong>Document:</strong> {kyc.get_document_type_display()}</p>
                    </div>
                    <p style="color: #7f8c8d; font-size: 14px;">User has been notified ✉️</p>
                    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">Redirecting to KYC admin panel...</p>
                </div>
            </body>
            </html>
            """
        )
        
    except KYCDocument.DoesNotExist:
        return HttpResponse(
            """
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
                    .box { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .error { color: #e74c3c; font-size: 48px; }
                    h2 { color: #e74c3c; }
                </style>
            </head>
            <body>
                <div class="box">
                    <div class="error">❌</div>
                    <h2>KYC Document Not Found</h2>
                    <p>The KYC document you're trying to reject doesn't exist.</p>
                </div>
            </body>
            </html>
            """,
            status=404
        )
    
    except Exception as e:
        return HttpResponse(
            f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                    .box {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error {{ color: #e74c3c; font-size: 48px; }}
                    h2 {{ color: #e74c3c; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <div class="error">⚠️</div>
                    <h2>Rejection Failed</h2>
                    <p>An error occurred: {str(e)}</p>
                    <p style="color: #7f8c8d; margin-top: 20px;">Please reject manually in the admin panel.</p>
                </div>
            </body>
            </html>
            """,
            status=500
        )
