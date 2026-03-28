from celery import shared_task
from django.utils import timezone

@shared_task
def calculate_daily_profits():
    from investments.models import Investment
    active = Investment.objects.filter(status='active')
    for inv in active:
        profit = inv.amount * (inv.plan.daily_roi / 100)
        inv.actual_profit += profit
        inv.save()
        inv.user.balance += profit
        inv.user.total_profit += profit
        inv.user.save()
    return {'success': True}

@shared_task
def check_completed_investments():
    from investments.models import Investment
    now = timezone.now()
    matured = Investment.objects.filter(status='active', end_date__lte=now)
    for inv in matured:
        inv.user.balance += inv.amount
        inv.user.invested_amount -= inv.amount
        inv.user.save()
        inv.status = 'completed'
        inv.completed_at = now
        inv.save()
    return {'success': True}
