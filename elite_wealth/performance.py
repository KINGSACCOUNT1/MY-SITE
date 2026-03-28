"""Performance optimization utilities for Elite Wealth Capital."""
from functools import wraps
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import hashlib
import json


def cache_user_data(timeout=300):
    """
    Cache decorator for user-specific data.
    
    Usage:
        @cache_user_data(timeout=600)
        def get_user_portfolio(request):
            # Expensive calculation
            return portfolio_data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return func(request, *args, **kwargs)
            
            # Create cache key with user ID
            cache_key = f'user_data_{request.user.id}_{func.__name__}'
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Calculate and cache
            result = func(request, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cache_query_result(key_prefix, timeout=300):
    """
    Cache decorator for database queries.
    
    Usage:
        @cache_query_result('investment_plans', timeout=600)
        def get_all_plans():
            return InvestmentPlan.objects.all()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f'{key_prefix}_{func.__name__}'
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Calculate and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def invalidate_user_cache(user_id):
    """
    Invalidate all cache entries for a specific user.
    
    Usage:
        # After updating user investment
        invalidate_user_cache(request.user.id)
    """
    pattern = f'user_data_{user_id}_*'
    cache.delete_pattern(pattern)


def invalidate_cache_key(key_prefix):
    """
    Invalidate specific cache key.
    
    Usage:
        # After updating investment plans
        invalidate_cache_key('investment_plans')
    """
    cache.delete(key_prefix)


class CachedViewMixin:
    """
    Mixin for class-based views with caching.
    
    Usage:
        class InvestmentPlansView(CachedViewMixin, ListView):
            cache_timeout = 600  # 10 minutes
            cache_key_prefix = 'investment_plans'
    """
    cache_timeout = 300  # 5 minutes default
    cache_key_prefix = None
    
    @method_decorator(cache_page(cache_timeout))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# Example: Query optimization with caching
def get_user_portfolio(user):
    """
    Get user portfolio with caching and optimized queries.
    
    This function demonstrates:
    1. Caching expensive calculations
    2. Query optimization with select_related/prefetch_related
    3. Aggregation in database
    """
    from investments.models import Investment
    from django.db.models import Sum, Count
    
    cache_key = f'portfolio_{user.id}'
    portfolio = cache.get(cache_key)
    
    if not portfolio:
        # Optimized query with aggregation
        stats = Investment.objects.filter(
            user=user,
            status='active'
        ).select_related('plan').aggregate(
            total_invested=Sum('amount'),
            investment_count=Count('id'),
            total_returns=Sum('total_return')
        )
        
        portfolio = {
            'balance': user.balance,
            'total_invested': stats['total_invested'] or 0,
            'investment_count': stats['investment_count'] or 0,
            'total_returns': stats['total_returns'] or 0,
            'profit': (stats['total_returns'] or 0) - (stats['total_invested'] or 0)
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, portfolio, 300)
    
    return portfolio


def warm_cache():
    """
    Pre-warm cache with frequently accessed data.
    
    Usage:
        # Run after deployment
        python manage.py shell
        >>> from elite_wealth.performance import warm_cache
        >>> warm_cache()
    """
    from investments.models import InvestmentPlan
    from accounts.models import CustomUser
    
    print("Warming cache...")
    
    # Cache investment plans
    plans = list(InvestmentPlan.objects.filter(is_active=True))
    cache.set('active_investment_plans', plans, 3600)  # 1 hour
    print(f"Cached {len(plans)} investment plans")
    
    # Cache site statistics
    stats = {
        'total_users': CustomUser.objects.count(),
        'verified_users': CustomUser.objects.filter(kyc_status='verified').count(),
    }
    cache.set('site_statistics', stats, 600)  # 10 minutes
    print(f"Cached site statistics")
    
    print("Cache warming complete!")


# Example: Clear all cache
def clear_all_cache():
    """Clear all cached data."""
    cache.clear()
    print("All cache cleared!")
