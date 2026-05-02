"""
Signals for investment app
Sends email notifications when deposit status changes
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from .models import Deposit
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Deposit)
def track_deposit_status_change(sender, instance, **kwargs):
    """Track old status before save"""
    if instance.pk:
        try:
            instance._old_status = Deposit.objects.get(pk=instance.pk).status
        except Deposit.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Deposit)
def notify_deposit_status_change(sender, instance, created, **kwargs):
    """Send notification when deposit status changes"""
    # Skip if just created (admin already got notification from deposit_view)
    if created:
        return
    
    # Check if status changed
    old_status = getattr(instance, '_old_status', None)
    if old_status == instance.status:
        return
    
    user = instance.user
    
    # Send email and in-app notification based on new status
    if instance.status == 'confirmed':
        # Update user balance
        user.balance += instance.amount
        user.save(update_fields=['balance'])
        
        # Update confirmation details
        if not instance.confirmed_at:
            instance.confirmed_at = timezone.now()
            Deposit.objects.filter(pk=instance.pk).update(confirmed_at=timezone.now())
        
        # Create in-app notification
        Notification.objects.create(
            user=user,
            title='Deposit Confirmed',
            message=f'Your deposit of ${instance.amount:,.2f} has been confirmed and credited to your balance.',
            notification_type='deposit'
        )
        
        # Send email to user
        send_deposit_confirmed_email(instance)
        logger.info(f"Deposit {instance.id} confirmed for user {user.email}")
        
    elif instance.status == 'rejected':
        # Create in-app notification
        Notification.objects.create(
            user=user,
            title='Deposit Rejected',
            message=f'Your deposit of ${instance.amount:,.2f} was rejected. {instance.admin_note or "Please contact support for more information."}',
            notification_type='deposit'
        )
        
        # Send email to user
        send_deposit_rejected_email(instance)
        logger.info(f"Deposit {instance.id} rejected for user {user.email}")


def send_deposit_confirmed_email(deposit):
    """Send email notification when deposit is confirmed"""
    try:
        user = deposit.user
        subject = f'✅ Deposit Confirmed - ${deposit.amount:,.2f} - Elite Wealth Capital'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="color-scheme" content="dark light">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: #0A0E1A;
                    color: #E5E7EB;
                    padding: 20px;
                    line-height: 1.6;
                }}
                .email-wrapper {{ 
                    max-width: 600px; 
                    margin: 0 auto;
                }}
                .container {{ 
                    background: linear-gradient(180deg, #0F1623 0%, #1A1F2E 100%);
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
                    border: 1px solid rgba(255, 215, 0, 0.1);
                }}
                .header {{ 
                    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                }}
                .logo {{ 
                    font-size: 28px;
                    font-weight: 800;
                    color: #000;
                    margin-bottom: 10px;
                    letter-spacing: -0.5px;
                }}
                .header-icon {{ 
                    font-size: 48px;
                    margin-bottom: 15px;
                    animation: bounce 1s ease;
                }}
                @keyframes bounce {{
                    0%, 100% {{ transform: translateY(0); }}
                    50% {{ transform: translateY(-10px); }}
                }}
                .header h1 {{ 
                    margin: 0;
                    font-size: 26px;
                    font-weight: 700;
                    color: #000;
                }}
                .amount {{ 
                    font-size: 42px;
                    font-weight: 900;
                    margin: 15px 0;
                    color: #000;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .content {{ 
                    padding: 40px 30px;
                }}
                .greeting {{ 
                    font-size: 18px;
                    color: #FFD700;
                    font-weight: 600;
                    margin-bottom: 15px;
                }}
                .message {{ 
                    font-size: 16px;
                    color: #D1D5DB;
                    margin-bottom: 30px;
                }}
                .info-card {{ 
                    background: rgba(255, 215, 0, 0.05);
                    border: 1px solid rgba(255, 215, 0, 0.2);
                    border-left: 4px solid #FFD700;
                    padding: 20px;
                    margin: 15px 0;
                    border-radius: 12px;
                }}
                .info-label {{ 
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    color: #9CA3AF;
                    margin-bottom: 8px;
                    font-weight: 600;
                }}
                .info-value {{ 
                    font-size: 18px;
                    color: #F3F4F6;
                    font-weight: 600;
                }}
                .info-value-large {{
                    font-size: 28px;
                    color: #FFD700;
                    font-weight: 800;
                }}
                .success-badge {{
                    display: inline-block;
                    background: rgba(34, 197, 94, 0.2);
                    color: #22C55E;
                    padding: 8px 20px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                    margin: 20px 0;
                    border: 1px solid rgba(34, 197, 94, 0.3);
                }}
                .button-wrapper {{ 
                    text-align: center;
                    margin: 35px 0;
                }}
                .btn {{ 
                    display: inline-block;
                    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                    color: #000;
                    padding: 16px 40px;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 700;
                    font-size: 16px;
                    box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
                    transition: transform 0.2s;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4);
                }}
                .divider {{
                    height: 1px;
                    background: linear-gradient(90deg, transparent, rgba(255,215,0,0.3), transparent);
                    margin: 30px 0;
                }}
                .footer {{ 
                    background: rgba(0, 0, 0, 0.3);
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid rgba(255, 215, 0, 0.1);
                }}
                .footer-logo {{
                    font-size: 20px;
                    font-weight: 800;
                    color: #FFD700;
                    margin-bottom: 10px;
                }}
                .footer-text {{ 
                    color: #9CA3AF;
                    font-size: 13px;
                    line-height: 1.8;
                }}
                .social-links {{
                    margin-top: 20px;
                }}
                .social-links a {{
                    color: #FFD700;
                    text-decoration: none;
                    margin: 0 10px;
                    font-size: 14px;
                }}
                @media only screen and (max-width: 600px) {{
                    body {{ padding: 10px; }}
                    .content {{ padding: 25px 20px; }}
                    .amount {{ font-size: 36px; }}
                    .header h1 {{ font-size: 22px; }}
                    .btn {{ padding: 14px 30px; font-size: 15px; }}
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="container">
                    <div class="header">
                        <div class="logo">ELITE WEALTH CAPITAL</div>
                        <div class="header-icon">✅</div>
                        <h1>Deposit Confirmed!</h1>
                        <div class="amount">${deposit.amount:,.2f}</div>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">Hello {user.full_name},</div>
                        
                        <div class="message">
                            Great news! Your deposit has been successfully confirmed and credited to your Elite Wealth Capital account. You're now ready to start building your wealth!
                        </div>
                        
                        <div class="success-badge">
                            ✨ SUCCESSFULLY PROCESSED
                        </div>
                        
                        <div class="info-card">
                            <div class="info-label">💵 Deposit Amount</div>
                            <div class="info-value-large">${deposit.amount:,.2f}</div>
                        </div>
                        
                        <div class="info-card">
                            <div class="info-label">💳 Payment Method</div>
                            <div class="info-value">{deposit.get_crypto_type_display()}</div>
                        </div>
                        
                        <div class="info-card">
                            <div class="info-label">📅 Confirmed On</div>
                            <div class="info-value">{timezone.now().strftime('%B %d, %Y at %H:%M UTC')}</div>
                        </div>
                        
                        <div class="info-card">
                            <div class="info-label">💰 Your New Balance</div>
                            <div class="info-value-large">${user.balance:,.2f}</div>
                        </div>
                        
                        <div class="divider"></div>
                        
                        <div class="message">
                            🚀 Ready to invest? Explore our premium investment plans and start growing your portfolio today!
                        </div>
                        
                        <div class="button-wrapper">
                            <a href="https://elitewealthcapita.uk/dashboard/" class="btn">
                                📊 Open Dashboard
                            </a>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <div class="footer-logo">ELITE WEALTH CAPITAL</div>
                        <div class="footer-text">
                            Your trusted partner in wealth management<br>
                            Need assistance? Email us at {settings.COMPANY_EMAIL}<br>
                            <br>
                            This is an automated message. Please do not reply to this email.
                        </div>
                        <div class="social-links">
                            <a href="https://elitewealthcapita.uk">Website</a> •
                            <a href="https://elitewealthcapita.uk/dashboard/contact/">Support</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        ELITE WEALTH CAPITAL
        ═══════════════════════════════════════════
        
        ✅ DEPOSIT CONFIRMED
        
        Hello {user.full_name},
        
        Great news! Your deposit has been successfully confirmed and credited to your account.
        
        Deposit Amount: ${deposit.amount:,.2f}
        Payment Method: {deposit.get_crypto_type_display()}
        Confirmed On: {timezone.now().strftime('%B %d, %Y at %H:%M UTC')}
        Your New Balance: ${user.balance:,.2f}
        
        Ready to invest? Visit your dashboard to explore our investment plans:
        https://elitewealthcapita.uk/dashboard/
        
        Need help? Contact us at {settings.COMPANY_EMAIL}
        
        ═══════════════════════════════════════════
        Elite Wealth Capital - Your Trusted Partner in Wealth Management
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Confirmation email sent for deposit {deposit.id}")
        
    except Exception as e:
        logger.error(f"Failed to send deposit confirmation email: {str(e)}")


def send_deposit_rejected_email(deposit):
    """Send email notification when deposit is rejected"""
    try:
        user = deposit.user
        subject = f'⚠️ Deposit Update - ${deposit.amount:,.2f} - Elite Wealth Capital'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="color-scheme" content="dark light">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: #0A0E1A;
                    color: #E5E7EB;
                    padding: 20px;
                    line-height: 1.6;
                }}
                .email-wrapper {{ 
                    max-width: 600px; 
                    margin: 0 auto;
                }}
                .container {{ 
                    background: linear-gradient(180deg, #0F1623 0%, #1A1F2E 100%);
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
                    border: 1px solid rgba(239, 68, 68, 0.1);
                }}
                .header {{ 
                    background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%);
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                }}
                .logo {{ 
                    font-size: 28px;
                    font-weight: 800;
                    color: #FFF;
                    margin-bottom: 10px;
                    letter-spacing: -0.5px;
                }}
                .header-icon {{ 
                    font-size: 48px;
                    margin-bottom: 15px;
                }}
                .header h1 {{ 
                    margin: 0;
                    font-size: 26px;
                    font-weight: 700;
                    color: #FFF;
                }}
                .amount {{ 
                    font-size: 42px;
                    font-weight: 900;
                    margin: 15px 0;
                    color: #FFF;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .content {{ 
                    padding: 40px 30px;
                }}
                .greeting {{ 
                    font-size: 18px;
                    color: #FFD700;
                    font-weight: 600;
                    margin-bottom: 15px;
                }}
                .message {{ 
                    font-size: 16px;
                    color: #D1D5DB;
                    margin-bottom: 30px;
                }}
                .info-card {{ 
                    background: rgba(239, 68, 68, 0.05);
                    border: 1px solid rgba(239, 68, 68, 0.2);
                    border-left: 4px solid #EF4444;
                    padding: 20px;
                    margin: 15px 0;
                    border-radius: 12px;
                }}
                .info-label {{ 
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    color: #9CA3AF;
                    margin-bottom: 8px;
                    font-weight: 600;
                }}
                .info-value {{ 
                    font-size: 18px;
                    color: #F3F4F6;
                    font-weight: 600;
                }}
                .info-value-large {{
                    font-size: 28px;
                    color: #F3F4F6;
                    font-weight: 800;
                }}
                .warning-badge {{
                    display: inline-block;
                    background: rgba(239, 68, 68, 0.2);
                    color: #EF4444;
                    padding: 8px 20px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                    margin: 20px 0;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }}
                .button-wrapper {{ 
                    text-align: center;
                    margin: 35px 0;
                }}
                .btn {{ 
                    display: inline-block;
                    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                    color: #000;
                    padding: 16px 40px;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 700;
                    font-size: 16px;
                    box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
                    transition: transform 0.2s;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(255, 215, 0, 0.4);
                }}
                .help-box {{
                    background: rgba(255, 215, 0, 0.05);
                    border: 1px solid rgba(255, 215, 0, 0.2);
                    padding: 25px;
                    border-radius: 12px;
                    margin: 30px 0;
                    text-align: center;
                }}
                .help-title {{
                    font-size: 20px;
                    color: #FFD700;
                    font-weight: 700;
                    margin-bottom: 15px;
                }}
                .contact-info {{
                    font-size: 15px;
                    color: #D1D5DB;
                    line-height: 2;
                }}
                .divider {{
                    height: 1px;
                    background: linear-gradient(90deg, transparent, rgba(239,68,68,0.3), transparent);
                    margin: 30px 0;
                }}
                .footer {{ 
                    background: rgba(0, 0, 0, 0.3);
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid rgba(239, 68, 68, 0.1);
                }}
                .footer-logo {{
                    font-size: 20px;
                    font-weight: 800;
                    color: #FFD700;
                    margin-bottom: 10px;
                }}
                .footer-text {{ 
                    color: #9CA3AF;
                    font-size: 13px;
                    line-height: 1.8;
                }}
                .social-links {{
                    margin-top: 20px;
                }}
                .social-links a {{
                    color: #FFD700;
                    text-decoration: none;
                    margin: 0 10px;
                    font-size: 14px;
                }}
                @media only screen and (max-width: 600px) {{
                    body {{ padding: 10px; }}
                    .content {{ padding: 25px 20px; }}
                    .amount {{ font-size: 36px; }}
                    .header h1 {{ font-size: 22px; }}
                    .btn {{ padding: 14px 30px; font-size: 15px; }}
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="container">
                    <div class="header">
                        <div class="logo">ELITE WEALTH CAPITAL</div>
                        <div class="header-icon">⚠️</div>
                        <h1>Deposit Requires Attention</h1>
                        <div class="amount">${deposit.amount:,.2f}</div>
                    </div>
                    
                    <div class="content">
                        <div class="greeting">Hello {user.full_name},</div>
                        
                        <div class="message">
                            We've reviewed your recent deposit submission and unfortunately we were unable to confirm the transaction at this time.
                        </div>
                        
                        <div class="warning-badge">
                            ⚠️ REQUIRES REVIEW
                        </div>
                        
                        <div class="info-card">
                            <div class="info-label">💵 Deposit Amount</div>
                            <div class="info-value-large">${deposit.amount:,.2f}</div>
                        </div>
                        
                        <div class="info-card">
                            <div class="info-label">💳 Payment Method</div>
                            <div class="info-value">{deposit.get_crypto_type_display()}</div>
                        </div>
                        
                        {f'''<div class="info-card">
                            <div class="info-label">📝 Note from Support Team</div>
                            <div class="info-value">{deposit.admin_note}</div>
                        </div>''' if deposit.admin_note else ''}
                        
                        <div class="divider"></div>
                        
                        <div class="help-box">
                            <div class="help-title">🆘 Need Help?</div>
                            <div class="message">
                                Our support team is here to assist you! If you believe this is an error or need clarification, please don't hesitate to reach out.
                            </div>
                            <div class="contact-info">
                                📧 Email: {settings.COMPANY_EMAIL}<br>
                                📞 Phone: {settings.COMPANY_PHONE}
                            </div>
                        </div>
                        
                        <div class="button-wrapper">
                            <a href="https://elitewealthcapita.uk/dashboard/contact/" class="btn">
                                💬 Contact Support
                            </a>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <div class="footer-logo">ELITE WEALTH CAPITAL</div>
                        <div class="footer-text">
                            Your trusted partner in wealth management<br>
                            Available 24/7 to assist you<br>
                            <br>
                            This is an automated message. Please do not reply to this email.
                        </div>
                        <div class="social-links">
                            <a href="https://elitewealthcapita.uk">Website</a> •
                            <a href="https://elitewealthcapita.uk/dashboard/">Dashboard</a> •
                            <a href="https://elitewealthcapita.uk/dashboard/contact/">Support</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        ELITE WEALTH CAPITAL
        ═══════════════════════════════════════════
        
        ⚠️ DEPOSIT REQUIRES ATTENTION
        
        Hello {user.full_name},
        
        We were unable to confirm your recent deposit submission.
        
        Deposit Amount: ${deposit.amount:,.2f}
        Payment Method: {deposit.get_crypto_type_display()}
        {'Note: ' + deposit.admin_note if deposit.admin_note else ''}
        
        Need assistance? Our support team is ready to help:
        
        Email: {settings.COMPANY_EMAIL}
        Phone: {settings.COMPANY_PHONE}
        
        Contact Support: https://elitewealthcapita.uk/dashboard/contact/
        
        ═══════════════════════════════════════════
        Elite Wealth Capital - Your Trusted Partner in Wealth Management
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"Rejection email sent for deposit {deposit.id}")
        
    except Exception as e:
        logger.error(f"Failed to send deposit rejection email: {str(e)}")
