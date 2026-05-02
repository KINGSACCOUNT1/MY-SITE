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
        subject = f'✅ Deposit Confirmed - ${deposit.amount:,.2f}'
        
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
                .button {{ text-align: center; margin: 30px 0; }}
                .btn {{ background: #FFD700; color: #000; padding: 15px 40px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 600; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Deposit Confirmed!</h1>
                    <div class="amount">${deposit.amount:,.2f}</div>
                </div>
                <div class="content">
                    <p>Dear {user.full_name},</p>
                    <p>Great news! Your deposit has been confirmed and credited to your account.</p>
                    
                    <div class="info-box">
                        <div class="label">💵 Deposit Amount:</div>
                        <div class="value" style="font-size: 20px; font-weight: bold; color: #27ae60;">${deposit.amount:,.2f}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">💳 Payment Method:</div>
                        <div class="value">{deposit.get_crypto_type_display()}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">📅 Confirmed:</div>
                        <div class="value">{timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">💰 New Balance:</div>
                        <div class="value" style="font-size: 18px; font-weight: bold; color: #27ae60;">${user.balance:,.2f}</div>
                    </div>
                    
                    <p>You can now start investing in our various plans to grow your portfolio.</p>
                    
                    <div class="button">
                        <a href="https://elitewealthcapita.uk/dashboard/" class="btn">
                            📊 View Dashboard
                        </a>
                    </div>
                </div>
                <div class="footer">
                    Elite Wealth Capital<br>
                    Need help? Contact us at {settings.COMPANY_EMAIL}
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        DEPOSIT CONFIRMED
        
        Dear {user.full_name},
        
        Your deposit has been confirmed and credited to your account.
        
        Deposit Amount: ${deposit.amount:,.2f}
        Payment Method: {deposit.get_crypto_type_display()}
        Confirmed: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        New Balance: ${user.balance:,.2f}
        
        You can now start investing. Visit your dashboard:
        https://elitewealthcapita.uk/dashboard/
        
        Elite Wealth Capital
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
        subject = f'❌ Deposit Rejected - ${deposit.amount:,.2f}'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .amount {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
                .content {{ padding: 30px; }}
                .info-box {{ background: #f8f9fa; border-left: 4px solid #e74c3c; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .label {{ font-weight: 600; color: #333; margin-bottom: 5px; }}
                .value {{ color: #555; }}
                .button {{ text-align: center; margin: 30px 0; }}
                .btn {{ background: #FFD700; color: #000; padding: 15px 40px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: 600; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>❌ Deposit Rejected</h1>
                    <div class="amount">${deposit.amount:,.2f}</div>
                </div>
                <div class="content">
                    <p>Dear {user.full_name},</p>
                    <p>We regret to inform you that your deposit could not be confirmed.</p>
                    
                    <div class="info-box">
                        <div class="label">💵 Deposit Amount:</div>
                        <div class="value" style="font-size: 20px; font-weight: bold;">${deposit.amount:,.2f}</div>
                    </div>
                    
                    <div class="info-box">
                        <div class="label">💳 Payment Method:</div>
                        <div class="value">{deposit.get_crypto_type_display()}</div>
                    </div>
                    
                    {f'''<div class="info-box">
                        <div class="label">📝 Reason:</div>
                        <div class="value">{deposit.admin_note}</div>
                    </div>''' if deposit.admin_note else ''}
                    
                    <p>If you believe this is an error or need assistance, please contact our support team immediately.</p>
                    
                    <div class="button">
                        <a href="https://elitewealthcapita.uk/dashboard/contact/" class="btn">
                            💬 Contact Support
                        </a>
                    </div>
                </div>
                <div class="footer">
                    Elite Wealth Capital<br>
                    Email: {settings.COMPANY_EMAIL}<br>
                    Phone: {settings.COMPANY_PHONE}
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        DEPOSIT REJECTED
        
        Dear {user.full_name},
        
        Your deposit could not be confirmed.
        
        Deposit Amount: ${deposit.amount:,.2f}
        Payment Method: {deposit.get_crypto_type_display()}
        {'Reason: ' + deposit.admin_note if deposit.admin_note else ''}
        
        If you believe this is an error, please contact our support team:
        Email: {settings.COMPANY_EMAIL}
        Phone: {settings.COMPANY_PHONE}
        
        Elite Wealth Capital
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
