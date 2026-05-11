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
import hmac
import hashlib

logger = logging.getLogger(__name__)


def generate_verification_token(deposit_id, action):
    """Generate secure token for email verification links"""
    message = f"{deposit_id}:{action}:{settings.SECRET_KEY}"
    return hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

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


def send_welcome_email(user):
    """
    Send welcome email to new user after registration
    
    Args:
        user: CustomUser instance
    """
    try:
        subject = f'Welcome to Elite Wealth Capital, {user.full_name}! 🎉'
        
        # Get referral bonus info
        bonus_message = ''
        if user.balance > 0:
            bonus_message = f"""
            <div class="bonus-box">
                <h3 style="color: #27ae60; margin: 0;">🎁 Welcome Bonus Credited!</h3>
                <p style="font-size: 20px; font-weight: bold; color: #27ae60; margin: 10px 0;">${user.balance:.2f}</p>
                <p style="margin: 0;">Your referral bonus has been added to your account balance.</p>
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
                .header {{ background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000; padding: 40px 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; }}
                .content {{ padding: 30px; }}
                .welcome-text {{ font-size: 16px; line-height: 1.6; color: #333; }}
                .bonus-box {{ background: #d4edda; border: 2px solid #27ae60; padding: 20px; margin: 20px 0; border-radius: 10px; text-align: center; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #FFD700; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .feature-list {{ list-style: none; padding: 0; }}
                .feature-list li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                .feature-list li:last-child {{ border-bottom: none; }}
                .cta-button {{ display: inline-block; background: #FFD700; color: #000; padding: 15px 35px; text-decoration: none; border-radius: 5px; font-weight: 600; margin: 20px 0; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
                .footer a {{ color: #FFD700; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to Elite Wealth Capital!</h1>
                    <p>Your journey to financial freedom starts here</p>
                </div>
                <div class="content">
                    <div class="welcome-text">
                        <p>Dear <strong>{user.full_name}</strong>,</p>
                        <p>Thank you for creating an account with Elite Wealth Capital. We're thrilled to have you join our community of smart investors!</p>
                    </div>
                    
                    {bonus_message}
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0; color: #333;">📧 Your Account Details</h3>
                        <p style="margin: 5px 0;"><strong>Email:</strong> {user.email}</p>
                        <p style="margin: 5px 0;"><strong>Referral Code:</strong> {user.referral_code}</p>
                        <p style="margin: 5px 0; font-size: 12px; color: #666;">Share your referral code and earn $30 for each person who signs up!</p>
                    </div>
                    
                    <h3 style="color: #333;">🚀 Get Started in 3 Easy Steps:</h3>
                    <ul class="feature-list">
                        <li>
                            <strong>1. Complete Your Profile</strong><br>
                            <span style="color: #666; font-size: 14px;">Add your personal information and verify your KYC documents</span>
                        </li>
                        <li>
                            <strong>2. Make Your First Deposit</strong><br>
                            <span style="color: #666; font-size: 14px;">Fund your account via crypto or bank transfer</span>
                        </li>
                        <li>
                            <strong>3. Start Investing</strong><br>
                            <span style="color: #666; font-size: 14px;">Choose from Crypto, Real Estate, Oil & Gas, and more!</span>
                        </li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="https://elitewealthcapita.uk/dashboard/" class="cta-button">
                            🎯 Go to Dashboard
                        </a>
                    </div>
                    
                    <div class="info-box" style="margin-top: 30px;">
                        <h3 style="margin-top: 0; color: #333;">💎 Why Elite Wealth Capital?</h3>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #555;">
                            <li>Multiple investment sectors (Crypto, Real Estate, Oil & Gas, Agriculture)</li>
                            <li>Daily ROI paid automatically</li>
                            <li>Secure and transparent platform</li>
                            <li>24/7 customer support</li>
                            <li>Referral rewards program</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        Need help? Contact us at <a href="mailto:support@elitewealthcapita.uk" style="color: #FFD700;">support@elitewealthcapita.uk</a>
                    </p>
                </div>
                <div class="footer">
                    <p><strong>Elite Wealth Capital</strong></p>
                    <p>London, United Kingdom | Norway</p>
                    <p><a href="https://elitewealthcapita.uk">elitewealthcapita.uk</a></p>
                    <p style="margin-top: 20px; font-size: 12px; color: #999;">
                        This email was sent to {user.email} because you created an account with Elite Wealth Capital.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Welcome to Elite Wealth Capital!
        
        Dear {user.full_name},
        
        Thank you for creating an account with Elite Wealth Capital. We're thrilled to have you join our community!
        
        YOUR ACCOUNT DETAILS:
        Email: {user.email}
        Referral Code: {user.referral_code}
        {"Current Balance: $" + str(user.balance) if user.balance > 0 else ""}
        
        GET STARTED:
        1. Complete your profile and KYC verification
        2. Make your first deposit
        3. Start investing in Crypto, Real Estate, Oil & Gas, and more!
        
        Visit your dashboard: https://elitewealthcapita.uk/dashboard/
        
        Need help? Contact us at support@elitewealthcapita.uk
        
        Best regards,
        Elite Wealth Capital Team
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Welcome email sent to: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
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
                        <a href="https://elitewealthcapita.uk/admin-api/deposits/{deposit.id}/verify/{generate_verification_token(deposit.id, 'verify')}/" class="btn btn-verify">
                            ✅ VERIFY & APPROVE
                        </a>
                        <a href="https://elitewealthcapita.uk/admin-api/deposits/{deposit.id}/reject/{generate_verification_token(deposit.id, 'reject')}/" class="btn btn-reject">
                            ❌ REJECT DEPOSIT
                        </a>
                    </div>
                    
                    <p style="color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;">
                        💡 Click the buttons above to instantly verify or reject this deposit without logging into the admin panel.
                    </p>
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


def send_kyc_notification(kyc_document):
    """
    Send admin notification when user submits KYC documents with direct action buttons
    
    Args:
        kyc_document: KYCDocument instance
    """
    try:
        from kyc.admin_api import generate_kyc_verification_token
        
        user = kyc_document.user
        subject = f'📋 New KYC Submission: {user.full_name} ({kyc_document.get_document_type_display()})'
        
        # Generate secure tokens for action links
        verify_token = generate_kyc_verification_token(kyc_document.id, 'verify')
        reject_token = generate_kyc_verification_token(kyc_document.id, 'reject')
        
        # Build document images section
        images_section = ''
        if kyc_document.front_image:
            images_section += f"""
            <div class="info-box">
                <div class="label">📷 Front Image:</div>
                <div style="margin-top: 10px;">
                    <img src="{kyc_document.front_image.url}" 
                         style="max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #ddd;"
                         alt="Document front">
                </div>
            </div>
            """
        
        if kyc_document.back_image:
            images_section += f"""
            <div class="info-box">
                <div class="label">📷 Back Image:</div>
                <div style="margin-top: 10px;">
                    <img src="{kyc_document.back_image.url}" 
                         style="max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #ddd;"
                         alt="Document back">
                </div>
            </div>
            """
        
        if kyc_document.selfie_image:
            images_section += f"""
            <div class="info-box">
                <div class="label">🤳 Selfie Image:</div>
                <div style="margin-top: 10px;">
                    <img src="{kyc_document.selfie_image.url}" 
                         style="max-width: 100%; height: auto; border-radius: 8px; border: 2px solid #ddd;"
                         alt="Selfie">
                </div>
            </div>
            """
        
        company_section = ''
        if kyc_document.company_name:
            company_section = f"""
            <div class="info-box">
                <div class="label">🏢 Company Name:</div>
                <div class="value" style="font-size: 18px; font-weight: 600; color: #2c3e50;">{kyc_document.company_name}</div>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 700px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .content {{ padding: 30px; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .label {{ font-weight: 600; color: #333; margin-bottom: 5px; }}
                .value {{ color: #555; }}
                .status-badge {{ display: inline-block; padding: 8px 15px; border-radius: 20px; background: #f39c12; color: #fff; font-weight: 600; font-size: 14px; }}
                .balance-box {{ background: #e8f5e9; border: 2px solid #27ae60; padding: 15px; margin: 15px 0; border-radius: 8px; text-align: center; }}
                .balance-amount {{ font-size: 28px; color: #27ae60; font-weight: bold; margin: 10px 0; }}
                .balance-label {{ color: #555; font-weight: 600; }}
                .buttons {{ text-align: center; margin: 30px 0; }}
                .btn {{ display: inline-block; padding: 15px 40px; margin: 8px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; transition: all 0.3s; border: none; cursor: pointer; }}
                .btn-verify {{ background: #27ae60; color: white; }}
                .btn-verify:hover {{ background: #229954; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(39,174,96,0.3); }}
                .btn-reject {{ background: #e74c3c; color: white; }}
                .btn-reject:hover {{ background: #c0392b; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(231,76,60,0.3); }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .section-title {{ color: #2c3e50; margin-top: 25px; margin-bottom: 15px; font-weight: 600; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📋 New KYC Submission</h1>
                    <div class="status-badge" style="margin-top: 15px;">⏳ PENDING VERIFICATION</div>
                </div>
                <div class="content">
                    <p style="font-size: 16px; color: #555;">A user has submitted their KYC documents for verification.</p>
                    
                    <div class="section-title">👤 User Information</div>
                    
                    <div class="info-box">
                        <div class="label">Full Name:</div>
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
                        <div class="label">📱 Phone:</div>
                        <div class="value">{user.phone or 'Not provided'}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">🌍 Country:</div>
                        <div class="value">{user.country or 'Not provided'}</div>
                    </div>
                    
                    {company_section}
                    
                    <div class="balance-box">
                        <div class="balance-label">💰 Account Balance</div>
                        <div class="balance-amount">${user.balance:,.2f}</div>
                    </div>
                    
                    <div class="section-title">📄 Document Information</div>
                    
                    <div class="info-box">
                        <div class="label">Document Type:</div>
                        <div class="value">{kyc_document.get_document_type_display()}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">Document Number:</div>
                        <div class="value">{kyc_document.document_number or 'Not provided'}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">Issuing Country:</div>
                        <div class="value">{kyc_document.issuing_country or 'Not provided'}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">Date of Birth:</div>
                        <div class="value">{kyc_document.date_of_birth or 'Not provided'}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">Nationality:</div>
                        <div class="value">{kyc_document.nationality or 'Not provided'}</div>
                    </div>
                    
                    <div class="section-title">📷 Document Images</div>
                    {images_section}
                    
                    <div class="buttons">
                        <a href="https://elitewealthcapita.uk/admin-api/kyc/{kyc_document.id}/verify/{verify_token}/" class="btn btn-verify">
                            ✅ VERIFY & APPROVE
                        </a>
                        <a href="https://elitewealthcapita.uk/admin-api/kyc/{kyc_document.id}/reject/{reject_token}/" class="btn btn-reject">
                            ❌ REJECT
                        </a>
                    </div>
                    
                    <p style="color: #7f8c8d; font-size: 12px; text-align: center; margin-top: 20px;">
                        💡 Click the buttons above to instantly verify or reject without logging into the admin panel.
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
        NEW KYC SUBMISSION
        
        Status: PENDING VERIFICATION
        
        USER INFORMATION:
        Name: {user.full_name}
        Email: {user.email}
        User ID: {user.id}
        Phone: {user.phone or 'Not provided'}
        Country: {user.country or 'Not provided'}
        Company: {kyc_document.company_name or 'Not provided'}
        Account Balance: ${user.balance:,.2f}
        
        DOCUMENT INFORMATION:
        Type: {kyc_document.get_document_type_display()}
        Number: {kyc_document.document_number or 'Not provided'}
        Issuing Country: {kyc_document.issuing_country or 'Not provided'}
        Date of Birth: {kyc_document.date_of_birth or 'Not provided'}
        Nationality: {kyc_document.nationality or 'Not provided'}
        
        Submitted: {kyc_document.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC') if kyc_document.submitted_at else 'Unknown'}
        
        QUICK ACTIONS:
        Verify: https://elitewealthcapita.uk/admin-api/kyc/{kyc_document.id}/verify/{verify_token}/
        Reject: https://elitewealthcapita.uk/admin-api/kyc/{kyc_document.id}/reject/{reject_token}/
        
        Or visit admin panel: https://elitewealthcapita.uk/admin/kyc/kycdocument/{kyc_document.id}/change/
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        
        email.send(fail_silently=False)
        
        logger.info(f"Admin KYC notification sent for user: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send KYC notification: {str(e)}")
        return False
