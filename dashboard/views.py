from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from datetime import timedelta
from decimal import Decimal
import csv
import logging

from investments.models import InvestmentPlan, Investment, Withdrawal, Deposit
from accounts.models import CustomUser, Referral, ActivityLog
from notifications.models import Notification

logger = logging.getLogger(__name__)


def process_user_mature_investments(user):
    """
    Process any mature investments for a user.
    Called when user views dashboard for immediate payout.
    Returns number of investments processed.
    """
    now = timezone.now()
    mature_investments = Investment.objects.filter(
        user=user,
        status='active',
        end_date__lte=now
    ).select_related('plan')
    
    processed = 0
    for investment in mature_investments:
        try:
            with transaction.atomic():
                # Lock user row for update
                user_locked = type(user).objects.select_for_update().get(pk=user.pk)
                
                # Recheck investment status to prevent double payout
                investment.refresh_from_db()
                if investment.status != 'active':
                    continue  # Already processed
                
                # Calculate total payout
                total_payout = investment.amount + investment.expected_profit
                
                # Credit user balance
                user_locked.balance = user_locked.balance + total_payout
                user_locked.total_profit = user_locked.total_profit + investment.expected_profit
                user_locked.save(update_fields=['balance', 'total_profit'])
                
                # Update investment status
                investment.status = 'completed'
                investment.actual_profit = investment.expected_profit
                investment.completed_at = now
                investment.save(update_fields=['status', 'actual_profit', 'completed_at'])
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    title='Investment Completed! 🎉',
                    message=(
                        f'Your investment of ${investment.amount:,.2f} in {investment.plan.name} has matured! '
                        f'${total_payout:,.2f} (including ${investment.expected_profit:,.2f} profit) '
                        f'has been credited to your account balance.'
                    ),
                    notification_type='investment'
                )
                processed += 1
        except Exception as e:
            logger.error(f'Error processing investment {investment.id}: {e}')
    
    return processed


def home(request):
    """Homepage with investment plans preview - CACHED for 1 hour."""
    # Try to get cached plans first
    plans = cache.get('home_featured_plans')
    if plans is None:
        # Cache miss - fetch from database
        plans = list(InvestmentPlan.objects.filter(is_active=True).order_by('sort_order')[:6])
        # Cache for 1 hour (3600 seconds)
        cache.set('home_featured_plans', plans, 3600)
    
    return render(request, 'index.html', {'plans': plans})


@login_required
def dashboard(request):
    """Main user dashboard with stats and recent activity."""
    user = request.user
    
    # Update last activity
    user.last_activity = timezone.now()
    user.save(update_fields=['last_activity'])
    
    # Process any mature investments first (auto-payout)
    matured_count = process_user_mature_investments(user)
    if matured_count > 0:
        # Refresh user data after processing
        user.refresh_from_db()
        messages.success(request, f'🎉 {matured_count} investment(s) have matured! Profits credited to your balance.')
    
    # Get user statistics with optimized queries
    active_investments = Investment.objects.filter(
        user=user, status='active'
    ).select_related('plan')
    
    active_investment_count = active_investments.count()
    total_invested = active_investments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    expected_profit = active_investments.aggregate(Sum('expected_profit'))['expected_profit__sum'] or Decimal('0')
    
    # Investment maturity alerts (maturing within 3 days)
    upcoming_maturities = active_investments.filter(
        end_date__lte=timezone.now() + timedelta(days=3)
    ).order_by('end_date')[:5]
    
    # Pending transactions
    pending_deposits = Deposit.objects.filter(user=user, status='pending').count()
    pending_withdrawals = Withdrawal.objects.filter(user=user, status='pending').count()
    
    # Recent transactions (last 5) with select_related for optimization
    recent_deposits = Deposit.objects.filter(user=user).select_related('confirmed_by').order_by('-created_at')[:5]
    recent_withdrawals = Withdrawal.objects.filter(user=user).select_related('processed_by').order_by('-created_at')[:5]
    recent_investments = Investment.objects.filter(user=user).select_related('plan').order_by('-start_date')[:5]
    
    # Referral stats
    referral_count = user.referrals.count()
    
    # Unread notifications count and recent notifications
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'balance': user.balance,
        'total_invested': total_invested,
        'total_profit': user.total_profit,
        'total_withdrawn': user.total_withdrawn,
        'referral_bonus': user.referral_bonus,
        'expected_profit': expected_profit,
        'active_investment_count': active_investment_count,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'recent_investments': recent_investments,
        'upcoming_maturities': upcoming_maturities,
        'referral_count': referral_count,
        'referral_code': user.referral_code,
        'unread_notifications': unread_notifications,
        'recent_notifications': recent_notifications,
        'kyc_status': user.kyc_status,
        'account_type': user.get_account_type_display(),
    }
    return render(request, 'dashboard.html', context)


@login_required
def referrals(request):
    """Referrals page showing user's referral stats and history."""
    user = request.user
    
    # Get referral stats
    referrals_list = Referral.objects.filter(referrer=user).select_related('referred').order_by('-created_at')
    total_referrals = referrals_list.count()
    
    context = {
        'referrals': referrals_list,
        'total_referrals': total_referrals,
        'referral_code': user.referral_code,
        'referral_bonus': user.referral_bonus,
    }
    return render(request, 'referrals.html', context)


@login_required
def transactions(request):
    """Transaction history page."""
    from django.core.paginator import Paginator
    
    user = request.user
    tx_type = request.GET.get('type', 'all')
    
    deposits = []
    withdrawals = []
    investments = []
    
    if tx_type in ['all', 'deposit']:
        deposits_qs = Deposit.objects.filter(user=user).select_related('confirmed_by').order_by('-created_at')
        deposit_paginator = Paginator(deposits_qs, 50)
        deposits = deposit_paginator.get_page(request.GET.get('deposit_page', 1))
    
    if tx_type in ['all', 'withdrawal']:
        withdrawals_qs = Withdrawal.objects.filter(user=user).select_related('processed_by').order_by('-created_at')
        withdrawal_paginator = Paginator(withdrawals_qs, 50)
        withdrawals = withdrawal_paginator.get_page(request.GET.get('withdrawal_page', 1))
    
    if tx_type in ['all', 'investment']:
        investments_qs = Investment.objects.filter(user=user).select_related('plan').order_by('-start_date')
        investment_paginator = Paginator(investments_qs, 50)
        investments = investment_paginator.get_page(request.GET.get('investment_page', 1))
    
    context = {
        'deposits': deposits,
        'withdrawals': withdrawals,
        'investments': investments,
        'tx_type': tx_type,
    }
    return render(request, 'transactions.html', context)


@login_required
def export_transactions(request):
    """Export user transactions to CSV."""
    user = request.user
    export_type = request.GET.get('type', 'all')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Description', 'Amount', 'Status'])
    
    # Deposits
    if export_type in ['all', 'deposit']:
        for deposit in Deposit.objects.filter(user=user).select_related('user', 'confirmed_by').order_by('-created_at'):
            writer.writerow([
                deposit.created_at.strftime('%Y-%m-%d %H:%M'),
                'Deposit',
                f'{deposit.crypto_type} deposit',
                f'${deposit.amount:,.2f}',
                deposit.get_status_display()
            ])
    
    # Withdrawals
    if export_type in ['all', 'withdrawal']:
        for withdrawal in Withdrawal.objects.filter(user=user).select_related('user', 'processed_by').order_by('-created_at'):
            writer.writerow([
                withdrawal.created_at.strftime('%Y-%m-%d %H:%M'),
                'Withdrawal',
                f'{withdrawal.crypto_type} to {withdrawal.wallet_address[:20]}...',
                f'-${withdrawal.amount:,.2f}',
                withdrawal.get_status_display()
            ])
    
    # Investments
    if export_type in ['all', 'investment']:
        for investment in Investment.objects.filter(user=user).select_related('plan').order_by('-start_date'):
            writer.writerow([
                investment.start_date.strftime('%Y-%m-%d %H:%M'),
                'Investment',
                f'{investment.plan.name} ({investment.plan.duration_days} days)',
                f'${investment.amount:,.2f}',
                investment.get_status_display()
            ])
    
    return response


@login_required
def activity_log(request):
    """Show user's activity log with pagination."""
    logs = ActivityLog.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'total_logs': logs.count(),
    }
    return render(request, 'activity-log.html', context)


@login_required
def referral_leaderboard(request):
    """Referral leaderboard showing top referrers."""
    top_referrers = CustomUser.objects.annotate(
        ref_count=Count('referrals_made', filter=Q(referrals_made__status='credited'))
    ).filter(ref_count__gt=0).order_by('-ref_count', '-referral_bonus')[:20]
    
    # User's own rank
    user_ref_count = Referral.objects.filter(
        referrer=request.user, status='credited'
    ).count()
    
    context = {
        'top_referrers': top_referrers,
        'user_ref_count': user_ref_count,
        'referral_code': request.user.referral_code,
        'referral_bonus': request.user.referral_bonus,
    }
    return render(request, 'referral-leaderboard.html', context)


# ============== PUBLIC PAGES ==============

def about(request):
    return render(request, 'about.html')

def team(request):
    return render(request, 'team.html')

def reviews(request):
    return render(request, 'reviews.html')

def contact(request):
    if request.method == 'POST':
        from .models import ContactMessage
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_body = request.POST.get('message', '').strip()
        if name and email and subject and message_body:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message_body,
            )
            # Notify admin by email (best-effort)
            try:
                admin_email = getattr(django_settings, 'ADMIN_NOTIFICATION_EMAIL', None)
                if admin_email:
                    send_mail(
                        subject=f'New Contact Message: {subject}',
                        message=(
                            f'From: {name} <{email}>\n\n'
                            f'Subject: {subject}\n\n'
                            f'{message_body}'
                        ),
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin_email],
                        fail_silently=True,
                    )
            except Exception as e:
                logger.warning(f'Failed to send contact notification: {e}')
        messages.success(request, 'Your message has been sent! We will respond within 24 hours.')
        return redirect('contact')
    return render(request, 'contact.html')

def faq(request):
    return render(request, 'faq.html')

def investment_plans(request):
    """All investment plans page - CACHED for 1 hour."""
    # Try to get cached plans first
    plans = cache.get('all_investment_plans')
    if plans is None:
        # Cache miss - fetch from database with optimized query
        plans = list(InvestmentPlan.objects.filter(is_active=True).order_by('sort_order'))
        # Cache for 1 hour (3600 seconds)
        cache.set('all_investment_plans', plans, 3600)
    
    return render(request, 'investment-plans.html', {'plans': plans})

def certificate(request):
    return render(request, 'certificate.html')

def partners(request):
    return render(request, 'partners.html')

def global_presence(request):
    """Global offices and presence page."""
    return render(request, 'global-presence.html')

def terms(request):
    return render(request, 'terms.html')

def privacy_policy(request):
    return render(request, 'privacy-policy.html')

def news(request):
    from .models import NewsArticle
    all_articles = NewsArticle.objects.filter(is_published=True).order_by('-published_at')
    featured = all_articles.filter(is_featured=True).first()
    if featured:
        regular = all_articles.exclude(pk=featured.pk)
    else:
        regular = all_articles
    context = {
        'featured_article': featured,
        'articles': regular,
    }
    return render(request, 'news.html', context)


def news_article(request, slug):
    from .models import NewsArticle
    article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
    related = NewsArticle.objects.filter(
        is_published=True, category=article.category
    ).exclude(pk=article.pk).order_by('-published_at')[:3]
    return render(request, 'news-article.html', {'article': article, 'related_articles': related})

def us_services(request):
    return render(request, 'us-services.html')

def dispute(request):
    from .models import Dispute
    if request.method == 'POST':
        # Get user (authenticated or guest)
        user = request.user if request.user.is_authenticated else None
        guest_name = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        appeal_type = request.POST.get('appeal_type', 'other')
        category = request.POST.get('category', '')
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        currency = request.POST.get('currency', 'USD')
        transaction_id = request.POST.get('transaction_id', '').strip()

        if subject and description:
            amount = None
            try:
                if amount_str:
                    amount = Decimal(amount_str)
            except (ValueError, TypeError):
                pass  # Invalid amount format, leave as None

            dispute_obj = Dispute.objects.create(
                user=user,
                guest_name=guest_name,
                guest_email=guest_email,
                appeal_type=appeal_type,
                category=category,
                subject=subject,
                description=description,
                amount=amount,
                currency=currency,
                transaction_id=transaction_id,
            )
            # Notify admin
            from django.core.mail import send_mail
            from django.conf import settings as django_settings
            try:
                admin_email = getattr(django_settings, 'ADMIN_NOTIFICATION_EMAIL', None)
                if admin_email:
                    send_mail(
                        subject=f'New Dispute/Appeal: {subject}',
                        message=(
                            f'Reference: {dispute_obj.reference}\n'
                            f'Type: {dispute_obj.get_appeal_type_display()}\n'
                            f'From: {user.email if user else guest_email}\n\n'
                            f'{description}'
                        ),
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin_email],
                        fail_silently=True,
                    )
            except Exception as e:
                logger.warning(f'Failed to send dispute notification: {e}')

            messages.success(
                request,
                f'Appeal {dispute_obj.reference} submitted successfully! '
                'Our team will review within 24-48 hours.'
            )
            return redirect('dispute')
        messages.error(request, 'Please fill in the required fields (subject and description).')
    # Load existing disputes for the current user
    user_disputes = []
    pending_dispute_count = 0
    if request.user.is_authenticated:
        user_disputes = list(Dispute.objects.filter(user=request.user).order_by('-created_at'))
        pending_dispute_count = sum(1 for dispute in user_disputes if dispute.status in ('pending', 'under_review'))
    return render(request, 'dispute.html', {
        'user_disputes': user_disputes,
        'pending_dispute_count': pending_dispute_count,
    })


# ============== NEWSLETTER ==============

def subscribe_newsletter(request):
    """Newsletter subscription endpoint (AJAX or form POST)."""
    from .models import NewsletterSubscription
    from django.http import JsonResponse
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            _, created = NewsletterSubscription.objects.get_or_create(email=email, defaults={'is_active': True})
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Successfully subscribed!' if created else 'Already subscribed.'})
            messages.success(request, 'Successfully subscribed to our newsletter!')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please provide a valid email address.'})
            messages.error(request, 'Please provide a valid email address.')
    return redirect('news')


# ============== ERROR PAGES ==============

def error_404(request, exception):
    """Custom 404 error page."""
    return render(request, '404.html', status=404)

def error_500(request):
    """Custom 500 error page."""
    return render(request, '500.html', status=500)


# ============== ADMIN PANEL ==============

from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from investments.models import Loan
from kyc.models import KYCDocument
from accounts.models import SiteSettings


@staff_member_required
def admin_panel(request):
    """Custom staff admin dashboard."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # ---- Overview Stats ----
    total_users = CustomUser.objects.filter(is_staff=False).count()
    new_users_7d = CustomUser.objects.filter(is_staff=False, date_joined__gte=seven_days_ago).count()
    active_users_30d = CustomUser.objects.filter(is_staff=False, last_activity__gte=thirty_days_ago).count()
    kyc_verified_count = CustomUser.objects.filter(kyc_status='verified').count()

    total_balance = CustomUser.objects.filter(is_staff=False).aggregate(t=Sum('balance'))['t'] or Decimal('0')
    total_invested = Investment.objects.filter(status='active').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    total_profit_paid = CustomUser.objects.filter(is_staff=False).aggregate(t=Sum('total_profit'))['t'] or Decimal('0')

    pending_withdrawals_qs = Withdrawal.objects.filter(status='pending').select_related('user').order_by('-created_at')[:50]
    pending_deposits_qs = Deposit.objects.filter(status='pending').select_related('user').order_by('-created_at')[:50]
    pending_loans_qs = Loan.objects.filter(status='pending').select_related('user').order_by('-created_at')[:50]
    pending_kyc_qs = KYCDocument.objects.filter(status='submitted').select_related('user').order_by('-submitted_at')[:50]

    pending_withdrawals_amount = pending_withdrawals_qs.aggregate(t=Sum('amount'))['t'] or Decimal('0')

    confirmed_deposits_30d = Deposit.objects.filter(
        status='confirmed', confirmed_at__gte=thirty_days_ago
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    completed_withdrawals_30d = Withdrawal.objects.filter(
        status='completed', processed_at__gte=thirty_days_ago
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    # ---- Recent Users ----
    recent_users = CustomUser.objects.filter(is_staff=False).order_by('-date_joined')[:10]

    # ---- Active Investments ----
    active_investments_qs = Investment.objects.filter(status='active').select_related('user', 'plan').order_by('-start_date')[:10]

    # ---- Referral stats ----
    top_referrers = CustomUser.objects.annotate(
        ref_count=Count('referrals_made')
    ).filter(ref_count__gt=0).order_by('-ref_count')[:5]

    context = {
        # User stats
        'total_users': total_users,
        'new_users_7d': new_users_7d,
        'active_users_30d': active_users_30d,
        'kyc_verified_count': kyc_verified_count,
        # Financial stats
        'total_balance': total_balance,
        'total_invested': total_invested,
        'total_profit_paid': total_profit_paid,
        'pending_withdrawals_amount': pending_withdrawals_amount,
        'confirmed_deposits_30d': confirmed_deposits_30d,
        'completed_withdrawals_30d': completed_withdrawals_30d,
        # Queues
        'pending_withdrawals': pending_withdrawals_qs,
        'pending_deposits': pending_deposits_qs,
        'pending_loans': pending_loans_qs,
        'pending_kyc': pending_kyc_qs,
        'pending_withdrawals_count': pending_withdrawals_qs.count(),
        'pending_deposits_count': pending_deposits_qs.count(),
        'pending_loans_count': pending_loans_qs.count(),
        'pending_kyc_count': pending_kyc_qs.count(),
        # Tables
        'recent_users': recent_users,
        'active_investments': active_investments_qs,
        'top_referrers': top_referrers,
        'now': now,
    }
    return render(request, 'admin-panel.html', context)


@staff_member_required
@require_POST
def admin_approve_withdrawal(request, pk):
    """Approve a pending withdrawal."""
    w = get_object_or_404(Withdrawal, pk=pk, status='pending')
    w.status = 'approved'
    w.processed_by = request.user
    w.processed_at = timezone.now()
    w.save()
    Notification.objects.create(
        user=w.user,
        notification_type='success',
        title='Withdrawal Approved',
        message=f'Your withdrawal of ${w.amount:,.2f} ({w.crypto_type}) has been approved and is being processed.',
    )
    messages.success(request, f'Withdrawal ${w.amount:,.2f} approved.')
    return redirect('admin_panel')


@staff_member_required
@require_POST
def admin_reject_withdrawal(request, pk):
    """Reject a withdrawal and refund the user."""
    w = get_object_or_404(Withdrawal, pk=pk, status__in=['pending', 'approved'])
    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(pk=w.user.pk)
        user.balance += w.amount
        user.save()
        w.status = 'rejected'
        w.processed_by = request.user
        w.processed_at = timezone.now()
        w.save()
    Notification.objects.create(
        user=w.user,
        notification_type='error',
        title='Withdrawal Rejected',
        message=f'Your withdrawal of ${w.amount:,.2f} has been rejected. ${w.amount:,.2f} has been refunded to your balance.',
    )
    messages.success(request, f'Withdrawal rejected and ${w.amount:,.2f} refunded.')
    return redirect('admin_panel')


@staff_member_required
@require_POST
def admin_confirm_deposit(request, pk):
    """Confirm a pending deposit and credit the user."""
    dep = get_object_or_404(Deposit, pk=pk, status='pending')
    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(pk=dep.user.pk)
        user.balance += dep.amount
        user.save()
        dep.status = 'confirmed'
        dep.confirmed_by = request.user
        dep.confirmed_at = timezone.now()
        dep.save()
    ActivityLog.objects.create(
        user=dep.user,
        action='deposit_confirmed',
        description=f'Deposit of ${dep.amount:,.2f} {dep.crypto_type} confirmed by admin.',
    )
    Notification.objects.create(
        user=dep.user,
        notification_type='success',
        title='Deposit Confirmed! 💰',
        message=f'Your deposit of ${dep.amount:,.2f} ({dep.crypto_type}) has been confirmed and added to your balance.',
    )
    messages.success(request, f'Deposit ${dep.amount:,.2f} confirmed.')
    return redirect('admin_panel')


@staff_member_required
@require_POST
def admin_reject_deposit(request, pk):
    """Reject a pending deposit."""
    dep = get_object_or_404(Deposit, pk=pk, status='pending')
    dep.status = 'rejected'
    dep.confirmed_by = request.user
    dep.confirmed_at = timezone.now()
    dep.save()
    Notification.objects.create(
        user=dep.user,
        notification_type='error',
        title='Deposit Rejected',
        message=f'Your deposit of ${dep.amount:,.2f} ({dep.crypto_type}) could not be verified. Please contact support.',
    )
    messages.success(request, f'Deposit ${dep.amount:,.2f} rejected.')
    return redirect('admin_panel')


@staff_member_required
@require_POST
def admin_approve_kyc(request, pk):
    """Approve KYC and unlock withdrawals for user."""
    kyc = get_object_or_404(KYCDocument, pk=pk, status='submitted')
    kyc.status = 'approved'
    kyc.reviewed_by = request.user
    kyc.reviewed_at = timezone.now()
    kyc.save()
    # Update user KYC status
    user = kyc.user
    user.kyc_status = 'verified'
    user.save()
    Notification.objects.create(
        user=user,
        notification_type='success',
        title='KYC Verified ✅',
        message='Your identity has been verified. You can now make withdrawals!',
    )
    messages.success(request, f'KYC approved for {user.email}.')
    return redirect('admin_panel')


@staff_member_required
@require_POST
def admin_reject_kyc(request, pk):
    """Reject KYC submission."""
    kyc = get_object_or_404(KYCDocument, pk=pk, status='submitted')
    reason = request.POST.get('reason', 'Documents could not be verified.')
    kyc.status = 'rejected'
    kyc.reviewed_by = request.user
    kyc.reviewed_at = timezone.now()
    kyc.rejection_reason = reason
    kyc.save()
    user = kyc.user
    user.kyc_status = 'rejected'
    user.save()
    Notification.objects.create(
        user=user,
        notification_type='error',
        title='KYC Rejected',
        message=f'Your KYC submission was rejected: {reason}. Please re-submit with clearer documents.',
    )
    messages.success(request, f'KYC rejected for {user.email}.')
    return redirect('admin_panel')


@staff_member_required
@require_POST
def admin_approve_loan(request, pk):
    """Approve a pending loan and disburse funds."""
    loan = get_object_or_404(Loan, pk=pk, status='pending')
    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(pk=loan.user.pk)
        user.balance += loan.amount
        user.save()
        loan.status = 'active'
        loan.approved_by = request.user
        loan.approved_at = timezone.now()
        loan.disbursed_at = timezone.now()
        loan.save()
    Notification.objects.create(
        user=loan.user,
        notification_type='success',
        title='Loan Approved! 🏦',
        message=f'Your loan of ${loan.amount:,.2f} has been approved and credited to your balance.',
    )
    messages.success(request, f'Loan ${loan.amount:,.2f} approved for {loan.user.email}.')
    return redirect('admin_panel')


@staff_member_required
@require_POST
def admin_reject_loan(request, pk):
    """Reject a pending loan."""
    loan = get_object_or_404(Loan, pk=pk, status='pending')
    loan.status = 'rejected'
    loan.approved_by = request.user
    loan.approved_at = timezone.now()
    loan.save()
    Notification.objects.create(
        user=loan.user,
        notification_type='error',
        title='Loan Application Rejected',
        message=f'Your loan application for ${loan.amount:,.2f} has been declined. Contact support for more info.',
    )
    messages.success(request, f'Loan rejected for {loan.user.email}.')
    return redirect('admin_panel')

