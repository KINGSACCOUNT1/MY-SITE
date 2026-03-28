"""
Elite Wealth Capital - Email Notification Service
Handles all email notifications to users and admins.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

# Company Email Addresses (Cloudflare Email Routing)
COMPANY_EMAILS = {
    'admin': 'admin@elitewealthcapita.uk',
    'support': 'support@elitewealthcapita.uk',
    'noreply': 'noreply@elitewealthcapita.uk',
    'billing': 'billing@elitewealthcapita.uk',
    'kyc': 'kyc@elitewealthcapita.uk',
    'withdrawals': 'withdrawals@elitewealthcapita.uk',
    'deposits': 'deposits@elitewealthcapita.uk',
    'alerts': 'alerts@elitewealthcapita.uk',
    'notifications': 'notifications@elitewealthcapita.uk',
    'security': 'security@elitewealthcapita.uk',
}

# Admin notification recipient - use environment variable
ADMIN_EMAIL = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@elitewealthcapita.uk')


def send_admin_notification(subject, message, html_message=None, category='general'):
    """
    Send notification email to admin.
    Uses ADMIN_NOTIFICATION_EMAIL from environment.
    """
    from_email = COMPANY_EMAILS.get(category, COMPANY_EMAILS['admin'])
    
    try:
        if html_message:
            email = EmailMultiAlternatives(
                subject=f"[Elite Wealth Capital] {subject}",
                body=message,
                from_email=from_email,
                to=[ADMIN_EMAIL]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
        else:
            send_mail(
                subject=f"[Elite Wealth Capital] {subject}",
                message=message,
                from_email=from_email,
                recipient_list=[ADMIN_EMAIL],
                fail_silently=False
            )
        logger.info(f"Admin notification sent: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False


def send_user_notification(user, subject, message, html_message=None, category='notifications'):
    """
    Send notification email to a user.
    """
    from_email = COMPANY_EMAILS.get(category, COMPANY_EMAILS['noreply'])
    
    try:
        if html_message:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
        else:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False
            )
        logger.info(f"User notification sent to {user.email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send user notification to {user.email}: {e}")
        return False


def notify_admin_new_deposit(deposit):
    """
    Notify admin when a new deposit is submitted and needs verification.
    """
    subject = f"🔔 New Deposit Pending - ${deposit.amount:,.2f} {deposit.crypto_type}"
    
    message = f"""
NEW DEPOSIT REQUIRES VERIFICATION
================================

User: {deposit.user.full_name or deposit.user.email}
Email: {deposit.user.email}
Amount: ${deposit.amount:,.2f}
Crypto: {deposit.crypto_type}
Transaction Hash: {deposit.tx_hash or 'Not provided'}
Submitted: {deposit.created_at.strftime('%Y-%m-%d %H:%M UTC')}

Screenshot Attached: {'Yes' if deposit.proof_image else 'No'}

ACTION REQUIRED:
Please verify this deposit in the admin panel:
https://elitewealthcapita.uk/admin/investments/deposit/{deposit.id}/change/

---
Elite Wealth Capital Admin Alerts
    """
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0A1F44; color: #fff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e293b 0%, #0A1F44 100%); border-radius: 12px; padding: 30px; border: 1px solid #334155;">
            <h2 style="color: #FFD700; margin-top: 0;">🔔 New Deposit Pending Verification</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">User:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #fff;">{deposit.user.full_name or deposit.user.email}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">Email:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #fff;">{deposit.user.email}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">Amount:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #00A86B; font-weight: bold; font-size: 18px;">${deposit.amount:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">Crypto:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #fff;">{deposit.crypto_type}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">TX Hash:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #fff; font-family: monospace; font-size: 12px;">{deposit.tx_hash or 'Not provided'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">Screenshot:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: {'#00A86B' if deposit.proof_image else '#ef4444'};">{'✅ Attached' if deposit.proof_image else '❌ Not provided'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; color: #94a3b8;">Submitted:</td>
                    <td style="padding: 10px; color: #fff;">{deposit.created_at.strftime('%Y-%m-%d %H:%M UTC')}</td>
                </tr>
            </table>
            
            <a href="https://elitewealthcapita.uk/admin/investments/deposit/{deposit.id}/change/" 
               style="display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%); color: #000; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 20px;">
                ✓ Verify Deposit in Admin Panel
            </a>
            
            <hr style="border: none; border-top: 1px solid #334155; margin: 30px 0;">
            <p style="color: #64748b; font-size: 12px; margin: 0;">
                Elite Wealth Capital Admin Alerts<br>
                This is an automated notification.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_admin_notification(subject, message, html_message, category='deposits')


def notify_admin_new_withdrawal(withdrawal):
    """
    Notify admin when a new withdrawal is requested.
    """
    subject = f"💸 New Withdrawal Request - ${withdrawal.amount:,.2f}"
    
    message = f"""
NEW WITHDRAWAL REQUEST
======================

User: {withdrawal.user.full_name or withdrawal.user.email}
Email: {withdrawal.user.email}
Amount: ${withdrawal.amount:,.2f}
Method: {withdrawal.crypto_type}
Wallet: {withdrawal.wallet_address}
Submitted: {withdrawal.created_at.strftime('%Y-%m-%d %H:%M UTC')}

ACTION REQUIRED:
Please process this withdrawal in the admin panel:
https://elitewealthcapita.uk/admin/investments/withdrawal/{withdrawal.id}/change/

---
Elite Wealth Capital Admin Alerts
    """
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0A1F44; color: #fff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e293b 0%, #0A1F44 100%); border-radius: 12px; padding: 30px; border: 1px solid #334155;">
            <h2 style="color: #ef4444; margin-top: 0;">💸 New Withdrawal Request</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">User:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #fff;">{withdrawal.user.full_name or withdrawal.user.email}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">Email:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #fff;">{withdrawal.user.email}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">Amount:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #ef4444; font-weight: bold; font-size: 18px;">${withdrawal.amount:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #94a3b8;">Method:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #334155; color: #fff;">{withdrawal.crypto_type}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; color: #94a3b8;">Wallet:</td>
                    <td style="padding: 10px; color: #fff; font-family: monospace; font-size: 11px;">{withdrawal.wallet_address}</td>
                </tr>
            </table>
            
            <a href="https://elitewealthcapita.uk/admin/investments/withdrawal/{withdrawal.id}/change/" 
               style="display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%); color: #000; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 20px;">
                ✓ Process Withdrawal
            </a>
            
            <hr style="border: none; border-top: 1px solid #334155; margin: 30px 0;">
            <p style="color: #64748b; font-size: 12px; margin: 0;">
                Elite Wealth Capital Admin Alerts<br>
                This is an automated notification.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_admin_notification(subject, message, html_message, category='withdrawals')


def notify_admin_new_kyc(kyc_submission):
    """
    Notify admin when a new KYC document is submitted.
    """
    subject = f"📋 New KYC Submission - {kyc_submission.user.full_name or kyc_submission.user.email}"
    
    message = f"""
NEW KYC SUBMISSION
==================

User: {kyc_submission.user.full_name or kyc_submission.user.email}
Email: {kyc_submission.user.email}
Document Type: {kyc_submission.document_type}
Submitted: {kyc_submission.submitted_at.strftime('%Y-%m-%d %H:%M UTC') if kyc_submission.submitted_at else 'N/A'}

ACTION REQUIRED:
Please review this KYC submission in the admin panel:
https://elitewealthcapita.uk/admin/kyc/kycsubmission/{kyc_submission.id}/change/

---
Elite Wealth Capital Admin Alerts
    """
    
    return send_admin_notification(subject, message, category='kyc')


def notify_user_deposit_confirmed(deposit):
    """
    Notify user when their deposit has been confirmed.
    """
    subject = "✅ Your Deposit Has Been Confirmed - Elite Wealth Capital"
    
    message = f"""
Dear {deposit.user.full_name or 'Valued Investor'},

Great news! Your deposit has been confirmed and credited to your account.

DEPOSIT DETAILS:
- Amount: ${deposit.amount:,.2f}
- Crypto: {deposit.crypto_type}
- Status: Confirmed ✅
- New Balance: ${deposit.user.balance:,.2f}

You can now use these funds to invest in our high-yield investment plans.

Start investing: https://elitewealthcapita.uk/invest/

Best regards,
Elite Wealth Capital Team
    """
    
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0A1F44; color: #fff; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e293b 0%, #0A1F44 100%); border-radius: 12px; padding: 30px; border: 1px solid #334155;">
            <img src="https://elitewealthcapita.uk/static/images/logo.webp" alt="Elite Wealth Capital" style="height: 50px; margin-bottom: 20px;">
            
            <h2 style="color: #00A86B; margin-top: 0;">✅ Deposit Confirmed!</h2>
            
            <p style="color: #94a3b8;">Dear {deposit.user.full_name or 'Valued Investor'},</p>
            <p style="color: #fff;">Great news! Your deposit has been confirmed and credited to your account.</p>
            
            <div style="background: #0A1F44; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #334155;">
                <table style="width: 100%;">
                    <tr>
                        <td style="color: #94a3b8; padding: 5px 0;">Amount:</td>
                        <td style="color: #00A86B; font-weight: bold; text-align: right;">${deposit.amount:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="color: #94a3b8; padding: 5px 0;">Crypto:</td>
                        <td style="color: #fff; text-align: right;">{deposit.crypto_type}</td>
                    </tr>
                    <tr>
                        <td style="color: #94a3b8; padding: 5px 0;">New Balance:</td>
                        <td style="color: #FFD700; font-weight: bold; text-align: right;">${deposit.user.balance:,.2f}</td>
                    </tr>
                </table>
            </div>
            
            <a href="https://elitewealthcapita.uk/invest/" 
               style="display: inline-block; background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%); color: #000; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                Start Investing Now →
            </a>
            
            <hr style="border: none; border-top: 1px solid #334155; margin: 30px 0;">
            <p style="color: #64748b; font-size: 12px; margin: 0;">
                Elite Wealth Capital<br>
                support@elitewealthcapita.uk
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_user_notification(deposit.user, subject, message, html_message, category='deposits')


def notify_user_withdrawal_processed(withdrawal):
    """
    Notify user when their withdrawal has been processed.
    """
    status_emoji = "✅" if withdrawal.status == 'completed' else "❌"
    status_text = "Completed" if withdrawal.status == 'completed' else "Rejected"
    
    subject = f"{status_emoji} Your Withdrawal Has Been {status_text} - Elite Wealth Capital"
    
    message = f"""
Dear {withdrawal.user.full_name or 'Valued Investor'},

Your withdrawal request has been {status_text.lower()}.

WITHDRAWAL DETAILS:
- Amount: ${withdrawal.amount:,.2f}
- Wallet: {withdrawal.wallet_address}
- Status: {status_text}

{'Your funds have been sent to the provided wallet address.' if withdrawal.status == 'completed' else 'Please contact support if you have questions.'}

Best regards,
Elite Wealth Capital Team
    """
    
    return send_user_notification(withdrawal.user, subject, message, category='withdrawals')
