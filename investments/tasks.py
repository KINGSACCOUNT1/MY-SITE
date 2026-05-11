"""
Celery tasks for investment profit processing
Auto-credits profits to users on schedule
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=False)
def process_all_investments(self):
    """
    Process all active investments - credit daily profits and complete matured investments
    Called automatically every hour via Celery Beat
    """
    from investments.models import Investment
    from accounts.models import CustomUser
    from notifications.models import Notification
    
    stats = {
        'users_processed': 0,
        'investments_completed': 0,
        'investments_updated': 0,
        'total_profits_credited': Decimal('0'),
        'total_principal_returned': Decimal('0'),
    }
    
    try:
        # Get all active investments
        active_investments = Investment.objects.filter(
            status='active'
        ).select_related('user', 'plan')
        
        logger.info(f"Processing {active_investments.count()} active investments")
        
        # Group by user to minimize database transactions
        user_investments = {}
        for investment in active_investments:
            if investment.user_id not in user_investments:
                user_investments[investment.user_id] = []
            user_investments[investment.user_id].append(investment)
        
        # Process each user's investments
        for user_id, investments in user_investments.items():
            try:
                with transaction.atomic():
                    user = CustomUser.objects.select_for_update().get(id=user_id)
                    user_stats = process_user_investments(user, investments)
                    
                    stats['users_processed'] += 1
                    stats['investments_completed'] += user_stats['completed']
                    stats['investments_updated'] += user_stats['updated']
                    stats['total_profits_credited'] += user_stats['profits_credited']
                    stats['total_principal_returned'] += user_stats['principal_returned']
                    
            except Exception as e:
                logger.error(f"Error processing investments for user {user_id}: {e}")
                continue
        
        logger.info(f"Investment processing complete: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error in process_all_investments: {e}")
        raise


def process_user_investments(user, investments):
    """
    Process all investments for a specific user
    Credits profits and completes matured investments
    
    Args:
        user: CustomUser instance (must be locked with select_for_update)
        investments: List of Investment instances for this user
        
    Returns:
        dict with processing statistics
    """
    from notifications.models import Notification
    
    stats = {
        'completed': 0,
        'updated': 0,
        'profits_credited': Decimal('0'),
        'principal_returned': Decimal('0'),
    }
    
    now = timezone.now()
    
    for investment in investments:
        # Check if investment has matured
        if investment.is_matured():
            # COMPLETE MATURED INVESTMENT
            
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
                stats['profits_credited'] += remaining_profit
            
            # Return principal amount to user balance
            user.balance += investment.amount
            user.invested_amount -= investment.amount
            stats['principal_returned'] += investment.amount
            
            # Mark investment as completed
            investment.status = 'completed'
            investment.completed_at = now
            investment.profit_paid_at = now
            investment.save()
            
            # Create notification
            Notification.objects.create(
                user=user,
                title='Investment Completed! 🎉',
                message=f'Your {investment.plan.name} investment of ${investment.amount} has matured! '
                       f'Total profit earned: ${investment.actual_profit:.2f}. '
                       f'Principal + profits (${investment.amount + investment.actual_profit:.2f}) '
                       f'have been credited to your balance.',
                notification_type='success'
            )
            
            stats['completed'] += 1
            logger.info(f"Completed investment {investment.id} for user {user.email}: "
                       f"${investment.amount} principal + ${investment.actual_profit} profit")
        
        else:
            # ACTIVE INVESTMENT - CREDIT ACCUMULATED PROFITS
            
            days_elapsed = investment.days_elapsed
            expected_daily_profit = investment.amount * (investment.plan.daily_roi / Decimal('100'))
            expected_profit_so_far = expected_daily_profit * days_elapsed
            profit_to_add = expected_profit_so_far - investment.actual_profit
            
            if profit_to_add > Decimal('0.01'):  # Only process if at least $0.01 profit
                # Add accumulated profit
                user.balance += profit_to_add
                user.total_profit += profit_to_add
                investment.actual_profit = expected_profit_so_far
                investment.save()
                stats['profits_credited'] += profit_to_add
                stats['updated'] += 1
                
                logger.debug(f"Added ${profit_to_add:.2f} profit to investment {investment.id} "
                           f"for user {user.email}")
    
    # Save user changes if any updates were made
    if stats['completed'] > 0 or stats['profits_credited'] > 0:
        user.save()
        logger.info(f"Updated user {user.email}: "
                   f"+${stats['profits_credited']:.2f} profit, "
                   f"+${stats['principal_returned']:.2f} principal returned")
    
    return stats


@shared_task(bind=True)
def process_single_user_investments(self, user_id):
    """
    Process investments for a single user (can be called manually)
    
    Args:
        user_id: ID of the user to process
        
    Returns:
        dict with processing statistics
    """
    from investments.models import Investment
    from accounts.models import CustomUser
    
    try:
        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(id=user_id)
            investments = Investment.objects.filter(user=user, status='active').select_related('plan')
            stats = process_user_investments(user, list(investments))
            logger.info(f"Processed user {user.email}: {stats}")
            return stats
    except CustomUser.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error processing user {user_id}: {e}")
        raise
