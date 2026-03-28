from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from accounts.models import CustomUser


@shared_task
def send_email_notification(user_email, subject, message):
    """Send email notification to user."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return f"Email sent to {user_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


@shared_task
def calculate_daily_profits():
    """Calculate and credit daily profits for active investments."""
    from investments.models import Investment
    from notifications.models import Notification
    
    active_investments = Investment.objects.filter(status='active').select_related('plan', 'user')
    credited_count = 0
    
    for investment in active_investments:
        daily_profit = investment.amount * (investment.plan.daily_roi / 100)
        with transaction.atomic():
            inv = Investment.objects.select_for_update().get(pk=investment.pk)
            user = CustomUser.objects.select_for_update().get(pk=inv.user_id)
            inv.actual_profit += daily_profit
            inv.save()
            user.total_profit += daily_profit
            user.balance += daily_profit
            user.save()
        credited_count += 1
        
        # Create notification
        Notification.create_notification(
            user=investment.user,
            title='Daily Profit Credited',
            message=f'${daily_profit:.2f} profit credited from your {investment.plan.name} investment.',
            notification_type='transaction'
        )
    
    return f"Credited profits for {credited_count} investments"


@shared_task
def check_completed_investments():
    """Check and complete investments that have reached their end date."""
    from investments.models import Investment
    from notifications.models import Notification
    
    now = timezone.now()
    completed = Investment.objects.filter(status='active', end_date__lte=now).select_related('plan', 'user')
    count = 0
    
    for investment in completed:
        with transaction.atomic():
            inv = Investment.objects.select_for_update().get(pk=investment.pk)
            if inv.status != 'active':
                continue  # Already processed by another task instance
            user = CustomUser.objects.select_for_update().get(pk=inv.user_id)
            inv.status = 'completed'
            inv.completed_at = now
            inv.save()
            user.balance += inv.amount  # Return principal
            user.invested_amount -= inv.amount
            user.save()
        count += 1
        
        # Notify user
        Notification.create_notification(
            user=investment.user,
            title='Investment Completed',
            message=f'Your {investment.plan.name} investment of ${investment.amount:.2f} has completed. Total profit: ${investment.actual_profit:.2f}',
            notification_type='success'
        )
    
    return f"Completed {count} investments"


@shared_task
def process_referral_bonus(referrer_id, amount):
    """Process referral bonus when a new user makes first deposit."""
    from accounts.models import CustomUser, Referral
    from notifications.models import Notification
    
    try:
        referrer = CustomUser.objects.get(id=referrer_id)
        bonus = amount * (settings.REFERRAL_BONUS_PERCENT / 100)
        
        referrer.referral_bonus += bonus
        referrer.balance += bonus
        referrer.save()
        
        # Create notification
        Notification.create_notification(
            user=referrer,
            title='Referral Bonus Credited',
            message=f'${bonus:.2f} referral bonus credited to your account!',
            notification_type='success'
        )
        
        return f"Credited ${bonus:.2f} bonus to {referrer.email}"
    except CustomUser.DoesNotExist:
        return "Referrer not found"


@shared_task
def send_withdrawal_notification(withdrawal_id, status):
    """Send notification when withdrawal status changes."""
    from investments.models import Withdrawal
    from notifications.models import Notification
    
    try:
        withdrawal = Withdrawal.objects.get(id=withdrawal_id)
        
        if status == 'approved':
            title = 'Withdrawal Approved'
            message = f'Your withdrawal of ${withdrawal.amount:.2f} has been approved and is being processed.'
            notif_type = 'success'
        elif status == 'completed':
            title = 'Withdrawal Completed'
            message = f'Your withdrawal of ${withdrawal.amount:.2f} to {withdrawal.wallet_address[:15]}... has been completed.'
            notif_type = 'success'
        elif status == 'rejected':
            title = 'Withdrawal Rejected'
            message = f'Your withdrawal of ${withdrawal.amount:.2f} was rejected. Funds returned to balance.'
            notif_type = 'error'
        else:
            return "Unknown status"
        
        Notification.create_notification(
            user=withdrawal.user,
            title=title,
            message=message,
            notification_type=notif_type
        )
        
        return f"Notification sent for withdrawal {withdrawal_id}"
    except Withdrawal.DoesNotExist:
        return "Withdrawal not found"


@shared_task
def send_deposit_notification(deposit_id, status):
    """Send notification when deposit status changes."""
    from investments.models import Deposit
    from notifications.models import Notification
    
    try:
        deposit = Deposit.objects.get(id=deposit_id)
        
        if status == 'confirmed':
            title = 'Deposit Confirmed'
            message = f'Your deposit of ${deposit.amount:.2f} has been confirmed and added to your balance.'
            notif_type = 'success'
        elif status == 'rejected':
            title = 'Deposit Rejected'
            message = f'Your deposit of ${deposit.amount:.2f} could not be verified. Please contact support.'
            notif_type = 'error'
        else:
            return "Unknown status"
        
        Notification.create_notification(
            user=deposit.user,
            title=title,
            message=message,
            notification_type=notif_type
        )
        
        return f"Notification sent for deposit {deposit_id}"
    except Deposit.DoesNotExist:
        return "Deposit not found"
