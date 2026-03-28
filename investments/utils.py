"""
Investment management utilities
Handles automatic investment status updates and profit calculations
"""
from django.utils import timezone
from decimal import Decimal


def check_and_update_investments(user):
    """
    Check and update user's investments when they access the dashboard
    This runs automatically without needing Celery/Redis
    
    Returns: dict with update statistics
    """
    from investments.models import Investment
    
    stats = {
        'completed': 0,
        'profits_added': Decimal('0'),
        'principal_returned': Decimal('0'),
    }
    
    # Get all active investments for this user
    active_investments = Investment.objects.filter(user=user, status='active')
    
    for investment in active_investments:
        # Check if investment has matured
        if investment.is_matured():
            # Calculate any remaining profit
            days_elapsed = investment.days_elapsed
            expected_daily_profit = investment.amount * (investment.plan.daily_roi / Decimal('100'))
            total_expected = expected_daily_profit * days_elapsed
            remaining_profit = total_expected - investment.actual_profit
            
            if remaining_profit > 0:
                # Add remaining profit to user balance
                user.balance += remaining_profit
                user.total_profit += remaining_profit
                investment.actual_profit = total_expected
                stats['profits_added'] += remaining_profit
            
            # Return principal amount to user balance
            user.balance += investment.amount
            user.invested_amount -= investment.amount
            stats['principal_returned'] += investment.amount
            
            # Mark investment as completed
            investment.status = 'completed'
            investment.completed_at = timezone.now()
            investment.save()
            
            # Create notification
            from notifications.models import Notification
            Notification.objects.create(
                user=user,
                title='Investment Completed! 🎉',
                message=f'Your {investment.plan.name} investment of ${investment.amount} has matured! '
                       f'Total profit earned: ${investment.actual_profit}. '
                       f'Principal amount has been returned to your balance.',
                notification_type='success'
            )
            
            stats['completed'] += 1
        
        else:
            # Investment still active - calculate daily profits
            days_elapsed = investment.days_elapsed
            expected_daily_profit = investment.amount * (investment.plan.daily_roi / Decimal('100'))
            expected_profit_so_far = expected_daily_profit * days_elapsed
            profit_to_add = expected_profit_so_far - investment.actual_profit
            
            if profit_to_add > 0:
                # Add accumulated profit
                user.balance += profit_to_add
                user.total_profit += profit_to_add
                investment.actual_profit = expected_profit_so_far
                investment.save()
                stats['profits_added'] += profit_to_add
    
    # Save user changes if any updates were made
    if stats['completed'] > 0 or stats['profits_added'] > 0:
        user.save()
    
    return stats


def calculate_daily_profits_for_user(user):
    """
    Calculate and add daily profits for a specific user
    Called automatically when user accesses dashboard
    """
    from investments.models import Investment
    
    active_investments = Investment.objects.filter(user=user, status='active')
    total_profit_added = Decimal('0')
    
    for investment in active_investments:
        # Don't add profit if already matured
        if investment.is_matured():
            continue
            
        # Calculate expected profit based on days elapsed
        days_elapsed = investment.days_elapsed
        daily_profit = investment.amount * (investment.plan.daily_roi / Decimal('100'))
        expected_total_profit = daily_profit * days_elapsed
        
        # Calculate profit to add (difference between expected and actual)
        profit_to_add = expected_total_profit - investment.actual_profit
        
        if profit_to_add > 0:
            investment.actual_profit = expected_total_profit
            investment.save()
            
            user.balance += profit_to_add
            user.total_profit += profit_to_add
            total_profit_added += profit_to_add
    
    if total_profit_added > 0:
        user.save()
    
    return total_profit_added
