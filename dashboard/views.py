from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from investments.models import Investment, Deposit, Withdrawal, InvestmentPlan
from notifications.models import Notification
from django.db.models import Sum, Count, Q
from decimal import Decimal


def home(request):
    """Homepage view"""
    plans = InvestmentPlan.objects.filter(is_active=True, is_featured=True)[:3]
    return render(request, 'home.html', {'plans': plans})


@login_required
def dashboard(request):
    """Main dashboard view"""
    user = request.user
    
    # Auto-check and update investments (no Celery needed!)
    from investments.utils import check_and_update_investments
    check_and_update_investments(user)
    
    # Get active investments
    active_investments = Investment.objects.filter(user=user, status='active')
    
    # Get recent transactions
    recent_deposits = Deposit.objects.filter(user=user).order_by('-created_at')[:5]
    recent_withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get notifications count and list
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    
    # Calculate stats
    total_invested = user.invested_amount
    total_profit = user.total_profit
    total_withdrawn = user.total_withdrawn
    
    context = {
        'user': user,
        'active_investments': active_investments,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
        'total_invested': total_invested,
        'total_profit': total_profit,
        'total_withdrawn': total_withdrawn,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def user_dashboard(request):
    """Enhanced user dashboard with portfolio overview"""
    user = request.user
    
    # Auto-check and update investments (no Celery needed!)
    from investments.utils import check_and_update_investments
    check_and_update_investments(user)
    
    # Portfolio calculations
    active_investments = Investment.objects.filter(user=user, status='active')
    completed_investments = Investment.objects.filter(user=user, status='completed')
    
    total_invested = active_investments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    active_count = active_investments.count()
    
    # Calculate ROI
    total_earnings = user.total_profit
    roi_percentage = ((total_earnings / total_invested) * 100) if total_invested > 0 else 0
    
    # Get asset breakdown
    investments_by_type = active_investments.values('plan__name').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')
    
    # Recent transactions (last 10)
    recent_deposits = Deposit.objects.filter(user=user).order_by('-created_at')[:10]
    recent_withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Pending withdrawals
    pending_withdrawals = Withdrawal.objects.filter(
        user=user,
        status='pending'
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    # Featured investment plans for carousel
    featured_plans = InvestmentPlan.objects.filter(
        is_active=True,
        is_featured=True
    )[:6]
    
    # Get notifications
    notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Quick stats
    total_balance = user.balance
    total_earnings_lifetime = user.total_earnings
    referral_earnings = user.referral_bonus
    
    context = {
        'user': user,
        'total_invested': total_invested,
        'total_balance': total_balance,
        'total_earnings': total_earnings,
        'total_earnings_lifetime': total_earnings_lifetime,
        'referral_earnings': referral_earnings,
        'roi_percentage': round(roi_percentage, 2),
        'active_count': active_count,
        'pending_withdrawals': pending_withdrawals,
        'active_investments': active_investments,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'investments_by_type': investments_by_type,
        'featured_plans': featured_plans,
        'notifications': notifications,
    }
    
    return render(request, 'dashboard/user_dashboard.html', context)


def contact(request):
    """Contact form view"""
    if request.method == 'POST':
        from .models import ContactMessage
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact')
    
    return render(request, 'dashboard/contact.html')


@login_required
def dispute(request):
    """Dispute and support page"""
    if request.method == 'POST':
        from .models import ContactMessage
        
        subject = request.POST.get('subject', 'Support Request')
        message = request.POST.get('message')
        dispute_type = request.POST.get('dispute_type', 'general')
        
        # Create support ticket
        ContactMessage.objects.create(
            name=request.user.full_name or request.user.email,
            email=request.user.email,
            subject=f"[{dispute_type.upper()}] {subject}",
            message=message
        )
        
        messages.success(request, 'Your support request has been submitted. We will respond within 24 hours.')
        return redirect('dashboard:dispute')
    
    return render(request, 'dashboard/dispute.html')


def about(request):
    """About page view"""
    return render(request, 'dashboard/about.html')


def faq(request):
    """FAQ page view"""
    return render(request, 'dashboard/faq.html')


def team(request):
    """Team page view"""
    return render(request, 'dashboard/team.html')


def reviews(request):
    """Reviews/Testimonials page view"""
    return render(request, 'dashboard/reviews.html')


def terms(request):
    """Terms & Conditions page view"""
    return render(request, 'dashboard/terms.html')


def privacy_policy(request):
    """Privacy Policy page view"""
    return render(request, 'dashboard/privacy.html')


def certificates(request):
    """Company Certificates page view"""
    return render(request, 'dashboard/certificates.html')


def news_list(request):
    """News listing page view"""
    from .models import NewsArticle
    from django.core.paginator import Paginator
    
    # Get published articles
    articles = NewsArticle.objects.filter(is_published=True)
    
    # Filter by category if provided
    category = request.GET.get('category')
    if category:
        articles = articles.filter(category=category)
    
    # Pagination
    paginator = Paginator(articles, 9)  # 9 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = NewsArticle.CATEGORY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category,
    }
    
    return render(request, 'dashboard/news.html', context)


def news_detail(request, slug):
    """News article detail view"""
    from .models import NewsArticle
    from django.shortcuts import get_object_or_404
    
    article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
    
    # Get related articles (same category, exclude current)
    related_articles = NewsArticle.objects.filter(
        category=article.category,
        is_published=True
    ).exclude(id=article.id)[:3]
    
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    
    return render(request, 'dashboard/news_detail.html', context)


@login_required
def export_transactions_csv(request):
    """Export user transactions to CSV"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    user = request.user
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transactions_{user.id}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Amount', 'Status', 'Details'])
    
    # Get all deposits
    for deposit in Deposit.objects.filter(user=user).order_by('-created_at'):
        writer.writerow([
            deposit.created_at.strftime('%Y-%m-%d %H:%M'),
            'Deposit',
            f'${deposit.amount}',
            deposit.status,
            f'{deposit.crypto_type} - {deposit.tx_hash[:20] if deposit.tx_hash else "N/A"}'
        ])
    
    # Get all withdrawals
    for withdrawal in Withdrawal.objects.filter(user=user).order_by('-created_at'):
        writer.writerow([
            withdrawal.created_at.strftime('%Y-%m-%d %H:%M'),
            'Withdrawal',
            f'${withdrawal.amount}',
            withdrawal.status,
            f'{withdrawal.withdrawal_method} - {withdrawal.crypto_type or withdrawal.bank_name}'
        ])
    
    # Get all investments
    for investment in Investment.objects.filter(user=user).order_by('-start_date'):
        writer.writerow([
            investment.start_date.strftime('%Y-%m-%d %H:%M'),
            'Investment',
            f'${investment.amount}',
            investment.status,
            f'{investment.plan.name} - {investment.expected_profit} profit'
        ])
    
    return response


@login_required
def transaction_history(request):
    """Transaction history page"""
    user = request.user
    filter_type = request.GET.get('type', 'all')
    
    deposits = []
    withdrawals = []
    investments = []
    
    if filter_type in ['all', 'deposits']:
        deposits = Deposit.objects.filter(user=user).order_by('-created_at')
    if filter_type in ['all', 'withdrawals']:
        withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
    if filter_type in ['all', 'investments']:
        investments = Investment.objects.filter(user=user).order_by('-start_date')
    
    context = {
        'deposits': deposits,
        'withdrawals': withdrawals,
        'investments': investments,
        'filter_type': filter_type,
    }
    
    return render(request, 'dashboard/transactions.html', context)


@login_required
def activity_log(request):
    """Activity log page"""
    from accounts.models import ActivityLog
    user = request.user
    activities = ActivityLog.objects.filter(user=user).order_by('-created_at')[:50]
    
    return render(request, 'dashboard/activity_log.html', {'activities': activities})


@login_required
def transactions_overview(request):
    """Transactions overview page with filtering"""
    user = request.user
    
    # Get all transactions
    deposits = Deposit.objects.filter(user=user).order_by('-created_at')
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
    investments = Investment.objects.filter(user=user).order_by('-start_date')
    
    # Combine and sort
    from itertools import chain
    all_transactions = list(chain(deposits, withdrawals, investments))
    
    # Calculate statistics
    total_deposited = sum(d.amount for d in deposits)
    total_withdrawn = sum(w.amount for w in withdrawals)
    total_invested = sum(i.amount for i in investments)
    
    context = {
        'user': user,
        'transactions': all_transactions[:20],  # Show latest 20
        'total_deposited': total_deposited,
        'total_withdrawn': total_withdrawn,
        'total_invested': total_invested,
    }
    
    return render(request, 'dashboard/transactions_overview.html', context)


@login_required
def certificates_view(request):
    """Certificates and achievements page"""
    user = request.user
    
    # Get user statistics for certificates
    active_investments = Investment.objects.filter(user=user, status='active').count()
    completed_investments = Investment.objects.filter(user=user, status='completed').count()
    
    context = {
        'user': user,
        'certificates_count': completed_investments,
        'total_investments': active_investments + completed_investments,
        'total_profit': user.total_profit,
        'achievement_level': 'Gold' if completed_investments >= 5 else 'Silver' if completed_investments >= 3 else 'Bronze',
        'certificates': [],  # Add certificate model later if needed
    }
    
    return render(request, 'dashboard/certificates_view.html', context)


@login_required
def upgrade_plans(request):
    """Upgrade plans page"""
    user = request.user
    from investments.models import InvestmentPlan
    
    # Get current plan info
    current_investment = Investment.objects.filter(user=user, status='active').first()
    current_plan = current_investment.plan if current_investment else None
    
    # Get all active plans
    plans = InvestmentPlan.objects.filter(is_active=True)
    
    context = {
        'user': user,
        'current_plan': current_plan,
        'plans': plans,
    }
    
    return render(request, 'dashboard/upgrade_plans.html', context)


@login_required
def partner_integrations(request):
    """Partner integrations page"""
    user = request.user
    
    context = {
        'user': user,
        'connected_partners_count': 2,  # Bank Transfer and Credit Card
        'available_partners_count': 4,
        'total_transactions': Deposit.objects.filter(user=user).count() + Withdrawal.objects.filter(user=user).count(),
        'total_volume': sum(d.amount for d in Deposit.objects.filter(user=user)) + sum(w.amount for w in Withdrawal.objects.filter(user=user)),
    }
    
    return render(request, 'dashboard/partner_integrations.html', context)


@login_required
def testimonials_manage(request):
    """Manage testimonials page"""
    user = request.user
    
    if request.method == 'POST':
        # Handle testimonial submission
        from dashboard.models import Testimonial
        
        testimonial = Testimonial(
            user=user,
            name=request.POST.get('name'),
            investment_amount=float(request.POST.get('investment_amount', 0)),
            investment_duration=request.POST.get('investment_duration'),
            rating=int(request.POST.get('rating', 5)),
            testimonial=request.POST.get('testimonial'),
            display_publicly=request.POST.get('allow_display') == 'on',
        )
        testimonial.save()
        messages.success(request, 'Your testimonial has been submitted for review!')
        return redirect('dashboard:testimonials_manage')
    
    # Get user's testimonials (if model exists)
    user_testimonials = []
    try:
        from dashboard.models import Testimonial
        user_testimonials = Testimonial.objects.filter(user=user).order_by('-created_at')
    except (ImportError, Exception):
        user_testimonials = []
    
    context = {
        'user': user,
        'testimonials': user_testimonials,
        'total_testimonials': len(user_testimonials),
        'approved_testimonials': sum(1 for t in user_testimonials if t.status == 'approved') if user_testimonials else 0,
        'pending_testimonials': sum(1 for t in user_testimonials if t.status == 'pending') if user_testimonials else 0,
        'average_rating': 4.8,
    }
    
    return render(request, 'dashboard/testimonials_manage.html', context)


@login_required
def global_presence_info(request):
    """Global presence and office locations page"""
    user = request.user
    
    context = {
        'user': user,
        'total_offices': 15,
        'total_countries': 25,
        'team_members': '500+',
        'support_languages': 18,
    }
    
    return render(request, 'dashboard/global_presence_info.html', context)


def us_services(request):
    """US Services page"""
    return render(request, 'us-services.html')


def reviews_page(request):
    """Reviews page with popup functionality"""
    return render(request, 'dashboard/reviews.html')


@login_required
def settings_page(request):
    """User settings page"""
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            # Update profile info
            user.full_name = request.POST.get('full_name', user.full_name)
            user.phone = request.POST.get('phone', user.phone)
            user.country = request.POST.get('country', user.country)
            user.save()
            messages.success(request, 'Profile updated successfully.')
        
        elif action == 'update_security':
            # Handle 2FA toggle
            enable_2fa = request.POST.get('enable_2fa') == 'on'
            if enable_2fa and not user.two_fa_enabled:
                # Would redirect to enable 2FA setup
                messages.info(request, '2FA setup is coming soon.')
            elif not enable_2fa and user.two_fa_enabled:
                user.two_fa_enabled = False
                user.save()
                messages.success(request, '2FA has been disabled.')
        
        return redirect('dashboard:settings')
    
    context = {
        'user': user,
    }
    return render(request, 'dashboard/settings.html', context)


def install_app(request):
    """Install App page with instructions for iOS and Android"""
    return render(request, 'dashboard/install_app.html')

