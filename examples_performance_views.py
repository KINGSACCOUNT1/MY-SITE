"""
Example views with performance optimizations for Elite Wealth Capital.

This file demonstrates best practices for:
- View-level caching
- Query optimization
- User-specific caching

Copy these patterns to your actual views.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.db.models import Sum, Count, Prefetch
from investments.models import Investment, InvestmentPlan
from accounts.models import CustomUser


# Example 1: Cache public page for all users (15 minutes)
@cache_page(60 * 15)  # 15 minutes
def investment_plans_cached(request):
    """
    Investment plans page with full page caching.
    Perfect for pages that don't change often and are same for all users.
    """
    plans = InvestmentPlan.objects.filter(is_active=True).order_by('sort_order')
    return render(request, 'investment-plans.html', {'plans': plans})


# Example 2: Manual caching with cache key
def investment_plans_manual_cache(request):
    """
    Investment plans with manual cache control.
    More flexible than @cache_page decorator.
    """
    # Try to get cached plans
    plans = cache.get('all_investment_plans')
    
    if plans is None:
        # Cache miss - fetch from database
        plans = list(InvestmentPlan.objects.filter(is_active=True).order_by('sort_order'))
        # Cache for 1 hour
        cache.set('all_investment_plans', plans, 3600)
    
    return render(request, 'investment-plans.html', {'plans': plans})


# Example 3: User-specific caching
@login_required
def user_portfolio(request):
    """
    User portfolio with user-specific caching.
    Each user gets their own cached data.
    """
    cache_key = f'portfolio_{request.user.id}'
    portfolio = cache.get(cache_key)
    
    if portfolio is None:
        # Optimized query with select_related and aggregation
        stats = Investment.objects.filter(
            user=request.user,
            status='active'
        ).select_related('plan').aggregate(
            total_invested=Sum('amount'),
            investment_count=Count('id'),
            total_returns=Sum('total_return')
        )
        
        portfolio = {
            'balance': request.user.balance,
            'total_invested': stats['total_invested'] or 0,
            'investment_count': stats['investment_count'] or 0,
            'total_returns': stats['total_returns'] or 0,
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, portfolio, 300)
    
    return render(request, 'portfolio.html', {'portfolio': portfolio})


# Example 4: Query optimization with select_related
@login_required
def my_investments_optimized(request):
    """
    User investments with optimized database queries.
    Uses select_related to avoid N+1 queries.
    """
    # BAD: This causes N+1 queries
    # investments = Investment.objects.filter(user=request.user)
    # for inv in investments:
    #     print(inv.plan.name)  # Additional query for each plan!
    
    # GOOD: Single query with JOIN
    investments = Investment.objects.filter(
        user=request.user
    ).select_related('plan').order_by('-created_at')
    
    return render(request, 'my_investments.html', {'investments': investments})


# Example 5: Complex query optimization with prefetch_related
def admin_dashboard_optimized(request):
    """
    Admin dashboard with complex query optimization.
    Uses both select_related and prefetch_related.
    """
    # Get users with their investments in optimized way
    users = CustomUser.objects.prefetch_related(
        Prefetch(
            'investments',
            queryset=Investment.objects.select_related('plan').filter(status='active')
        )
    ).annotate(
        total_invested=Sum('investments__amount'),
        investment_count=Count('investments')
    ).order_by('-total_invested')[:10]  # Top 10 investors
    
    return render(request, 'admin_dashboard.html', {'top_investors': users})


# Example 6: Cache invalidation
@login_required
def create_investment(request):
    """
    Create investment and invalidate relevant caches.
    """
    # ... investment creation logic ...
    
    # After creating investment, invalidate user's cache
    cache.delete(f'portfolio_{request.user.id}')
    cache.delete(f'user_data_{request.user.id}_my_investments')
    
    # Also invalidate general stats cache if needed
    cache.delete('site_statistics')
    
    return redirect('dashboard')


# Example 7: Database indexes (add to models.py)
"""
# Add to investments/models.py Investment model:

class Investment(models.Model):
    # ... existing fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),  # For filtering user's active investments
            models.Index(fields=['status', 'end_date']),  # For finding mature investments
            models.Index(fields=['-created_at']),  # For ordering by date
        ]
        ordering = ['-created_at']


# Add to accounts/models.py CustomUser model:

class CustomUser(AbstractUser):
    # ... existing fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),  # For login queries
            models.Index(fields=['referral_code']),  # For referral lookups
            models.Index(fields=['kyc_status']),  # For filtering verified users
        ]
"""
