"""
Admin API endpoints for one-click deposit verification from email
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Deposit
from notifications.models import Notification
import hmac
import hashlib
from django.conf import settings

User = get_user_model()


def generate_verification_token(deposit_id, action):
    """Generate secure token for email verification links"""
    message = f"{deposit_id}:{action}:{settings.SECRET_KEY}"
    return hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_token(deposit_id, action, token):
    """Verify the security token"""
    expected_token = generate_verification_token(deposit_id, action)
    return hmac.compare_digest(token, expected_token)


@csrf_exempt
@require_http_methods(["GET"])
def verify_deposit_from_email(request, deposit_id, token):
    """
    One-click deposit verification endpoint for admin emails
    URL: /admin-api/deposits/<id>/verify/<token>/
    """
    try:
        # Verify token
        if not verify_token(deposit_id, 'verify', token):
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
                        <p>This link is invalid or has expired. Please use the admin panel to verify deposits.</p>
                    </div>
                </body>
                </html>
                """,
                status=403
            )
        
        # Get deposit
        deposit = get_object_or_404(Deposit, id=deposit_id)
        
        # Check if already verified
        if deposit.status == 'confirmed':
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
                        <p>This deposit of <strong>${deposit.amount:,.2f}</strong> from <strong>{deposit.user.full_name}</strong> has already been confirmed.</p>
                        <p style="color: #7f8c8d; margin-top: 20px;">User balance: ${deposit.user.balance:,.2f}</p>
                    </div>
                </body>
                </html>
                """
            )
        
        # Update deposit status
        deposit.status = 'confirmed'
        deposit.save()
        
        # Update user balance
        user = deposit.user
        user.balance += deposit.amount
        user.save()
        
        # Create notification for user
        Notification.objects.create(
            user=user,
            title='Deposit Confirmed',
            message=f'Your deposit of ${deposit.amount:,.2f} has been confirmed and added to your balance.',
            notification_type='deposit'
        )
        
        # Return success page
        return HttpResponse(
            f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="3;url=https://elitewealthcapita.uk/admin/investments/deposit/">
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }}
                    .box {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .success {{ color: #27ae60; font-size: 48px; animation: checkmark 0.5s ease; }}
                    @keyframes checkmark {{ 0% {{ transform: scale(0); }} 100% {{ transform: scale(1); }} }}
                    h2 {{ color: #27ae60; }}
                    .details {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                    .amount {{ font-size: 24px; color: #27ae60; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="box">
                    <div class="success">✅</div>
                    <h2>Deposit Verified Successfully!</h2>
                    <div class="details">
                        <p><strong>User:</strong> {user.full_name}</p>
                        <p><strong>Email:</strong> {user.email}</p>
                        <p class="amount">💰 ${deposit.amount:,.2f}</p>
                        <p style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd;">
                            <strong>New Balance:</strong> ${user.balance:,.2f}
                        </p>
                    </div>
                    <p style="color: #7f8c8d; font-size: 14px;">User has been notified via email ✉️</p>
                    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">Redirecting to admin panel...</p>
                </div>
            </body>
            </html>
            """
        )
        
    except Deposit.DoesNotExist:
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
                    <h2>Deposit Not Found</h2>
                    <p>The deposit you're trying to verify doesn't exist.</p>
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
def reject_deposit_from_email(request, deposit_id, token):
    """
    One-click deposit rejection endpoint for admin emails
    URL: /admin-api/deposits/<id>/reject/<token>/
    """
    try:
        # Verify token
        if not verify_token(deposit_id, 'reject', token):
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
                        <p>This link is invalid or has expired. Please use the admin panel to reject deposits.</p>
                    </div>
                </body>
                </html>
                """,
                status=403
            )
        
        # Get deposit
        deposit = get_object_or_404(Deposit, id=deposit_id)
        
        # Check if already processed
        if deposit.status in ['confirmed', 'rejected']:
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
                        <p>This deposit has already been {deposit.status}.</p>
                    </div>
                </body>
                </html>
                """
            )
        
        # Update deposit status
        deposit.status = 'rejected'
        deposit.save()
        
        # Create notification for user
        Notification.objects.create(
            user=deposit.user,
            title='Deposit Rejected',
            message=f'Your deposit of ${deposit.amount:,.2f} has been rejected. Please contact support for more information.',
            notification_type='deposit'
        )
        
        # Return success page
        return HttpResponse(
            f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="3;url=https://elitewealthcapita.uk/admin/investments/deposit/">
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
                    <h2>Deposit Rejected</h2>
                    <div class="details">
                        <p><strong>User:</strong> {deposit.user.full_name}</p>
                        <p><strong>Email:</strong> {deposit.user.email}</p>
                        <p><strong>Amount:</strong> ${deposit.amount:,.2f}</p>
                    </div>
                    <p style="color: #7f8c8d; font-size: 14px;">User has been notified via email ✉️</p>
                    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">Redirecting to admin panel...</p>
                </div>
            </body>
            </html>
            """
        )
        
    except Deposit.DoesNotExist:
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
                    <h2>Deposit Not Found</h2>
                    <p>The deposit you're trying to reject doesn't exist.</p>
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
