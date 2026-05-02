"""
Email notification system for admin alerts
Sends notifications to admin@elitewealthcapita.uk for:
- New user registrations (with credentials)
- Deposit requests (with verification buttons)
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_new_user_notification(user, raw_password):
    """
    Send admin notification when new user registers
    
    Args:
        user: CustomUser instance
        raw_password: Plain text password (before hashing)
    """
    try:
        subject = f'🆕 New User Registration: {user.full_name}'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .content {{ padding: 30px; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #FFD700; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .credential {{ background: #fff3cd; border: 1px solid #ffc107; padding: 12px; margin: 10px 0; border-radius: 5px; font-family: 'Courier New', monospace; }}
                .label {{ font-weight: 600; color: #333; margin-bottom: 5px; }}
                .value {{ color: #555; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 New User Registration</h1>
                </div>
                <div class="content">
                    <p>A new user has registered on Elite Wealth Capital:</p>
                    
                    <div class="info-box">
                        <div class="label">👤 Full Name:</div>
                        <div class="value">{user.full_name}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">📧 Email:</div>
                        <div class="value">{user.email}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">🆔 User ID:</div>
                        <div class="value">{user.id}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">🎫 Referral Code:</div>
                        <div class="value">{user.referral_code}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">📅 Registration Date:</div>
                        <div class="value">{user.date_joined.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                    </div>
                    
                    <h3 style="color: #e74c3c; margin-top: 30px;">🔐 User Credentials (For Password Recovery)</h3>
                    <div class="warning">
                        <strong>⚠️ CONFIDENTIAL:</strong> Store these credentials securely. Use only for customer support when users forget their password.
                    </div>
                    
                    <div class="credential">
                        <div class="label">Email:</div>
                        <div style="font-size: 16px; color: #000;">{user.email}</div>
                    </div>
                    
                    <div class="credential">
                        <div class="label">Password:</div>
                        <div style="font-size: 16px; color: #000; font-weight: bold;">{raw_password}</div>
                    </div>
                    
                    <div class="warning">
                        <strong>🛡️ Security Note:</strong> This password is stored hashed in the database. This is the ONLY time you'll receive the plain text password.
                    </div>
                    
                    <p style="margin-top: 30px;">
                        <a href="https://elitewealthcapita.uk/admin/accounts/customuser/{user.id}/change/" 
                           style="background: #FFD700; color: #000; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: 600;">
                            👁️ View User in Admin Panel
                        </a>
                    </p>
                </div>
                <div class="footer">
                    Elite Wealth Capital Admin Notifications<br>
                    This email was sent automatically. Do not reply.
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        NEW USER REGISTRATION
        
        Full Name: {user.full_name}
        Email: {user.email}
        User ID: {user.id}
        Referral Code: {user.referral_code}
        Registration Date: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        USER CREDENTIALS (For Password Recovery):
        Email: {user.email}
        Password: {raw_password}
        
        ⚠️ CONFIDENTIAL - Store securely for customer support use only.
        
        View user: https://elitewealthcapita.uk/admin/accounts/customuser/{user.id}/change/
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Admin notification sent for new user: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send new user notification: {str(e)}")
        return False


def send_deposit_notification(deposit):
    """
    Send admin notification when user makes a deposit
    
    Args:
        deposit: Deposit instance
    """
    try:
        user = deposit.user
        subject = f'💰 New Deposit Request: ${deposit.amount:,.2f} from {user.full_name}'
        
        # Build proof image section
        proof_section = ''
        if deposit.proof_image:
            proof_section = f"""
            <div class="info-box">
                <div class="label">📸 Payment Screenshot:</div>
                <div style="margin-top: 10px;">
                    <img src="{deposit.proof_image.url}" 
                         style="max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #ddd;"
                         alt="Payment proof">
                </div>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #27ae60 0%, #229954 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .amount {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
                .content {{ padding: 30px; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #27ae60; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .label {{ font-weight: 600; color: #333; margin-bottom: 5px; }}
                .value {{ color: #555; }}
                .buttons {{ text-align: center; margin: 30px 0; }}
                .btn {{ display: inline-block; padding: 15px 40px; margin: 10px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; }}
                .btn-verify {{ background: #27ae60; color: white; }}
                .btn-reject {{ background: #e74c3c; color: white; }}
                .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; background: #ffc107; color: #000; font-weight: 600; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💰 New Deposit Request</h1>
                    <div class="amount">${deposit.amount:,.2f}</div>
                    <div class="status-badge">⏳ PENDING VERIFICATION</div>
                </div>
                <div class="content">
                    <h3 style="color: #333;">User Information:</h3>
                    
                    <div class="info-box">
                        <div class="label">👤 User:</div>
                        <div class="value">{user.full_name}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">📧 Email:</div>
                        <div class="value">{user.email}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">🆔 User ID:</div>
                        <div class="value">{user.id}</div>
                    </div>
                    
                    <h3 style="color: #333; margin-top: 30px;">Deposit Details:</h3>
                    
                    <div class="info-box">
                        <div class="label">💵 Amount:</div>
                        <div class="value" style="font-size: 20px; font-weight: bold; color: #27ae60;">${deposit.amount:,.2f}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">💳 Payment Method:</div>
                        <div class="value">{deposit.get_payment_method_display()} - {deposit.get_crypto_type_display()}</div>
                    </div>
                    
                    {f'''<div class="info-box">
                        <div class="label">🔗 Transaction Hash:</div>
                        <div class="value" style="word-break: break-all; font-family: 'Courier New', monospace;">{deposit.tx_hash}</div>
                    </div>''' if deposit.tx_hash else ''}
                    
                    <div class="info-box">
                        <div class="label">📅 Submitted:</div>
                        <div class="value">{deposit.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                    </div>
                    
                    {proof_section}
                    
                    <div class="buttons">
                        <a href="https://elitewealthcapita.uk/admin/investments/deposit/{deposit.id}/change/" class="btn btn-verify">
                            ✅ VERIFY & APPROVE
                        </a>
                        <a href="https://elitewealthcapita.uk/admin/investments/deposit/{deposit.id}/change/" class="btn btn-reject">
                            ❌ REJECT
                        </a>
                    </div>
                    
                    <p style="text-align: center; color: #666; font-size: 14px;">
                        Click the buttons above to go to the admin panel and change the deposit status.
                    </p>
                </div>
                <div class="footer">
                    Elite Wealth Capital Admin Notifications<br>
                    This email was sent automatically. Do not reply.
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        NEW DEPOSIT REQUEST
        
        Amount: ${deposit.amount:,.2f}
        Status: PENDING VERIFICATION
        
        USER INFORMATION:
        Name: {user.full_name}
        Email: {user.email}
        User ID: {user.id}
        
        DEPOSIT DETAILS:
        Amount: ${deposit.amount:,.2f}
        Payment Method: {deposit.get_payment_method_display()} - {deposit.get_crypto_type_display()}
        {'Transaction Hash: ' + deposit.tx_hash if deposit.tx_hash else ''}
        Submitted: {deposit.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        {'Screenshot: ' + deposit.proof_image.url if deposit.proof_image else 'No screenshot uploaded'}
        
        VERIFY OR REJECT:
        Go to: https://elitewealthcapita.uk/admin/investments/deposit/{deposit.id}/change/
        Change the status to "Confirmed" to approve or "Rejected" to decline.
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        
        # Attach screenshot if available
        if deposit.proof_image:
            try:
                email.attach(
                    f"payment_proof_{deposit.id}.jpg",
                    deposit.proof_image.read(),
                    'image/jpeg'
                )
            except Exception as e:
                logger.warning(f"Could not attach deposit screenshot: {str(e)}")
        
        email.send(fail_silently=False)
        
        logger.info(f"Admin notification sent for deposit ID: {deposit.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send deposit notification: {str(e)}")
        return False
