"""
Custom Admin Panel Views for Elite Wealth Capital
Provides admin dashboard and approval workflows for deposits, withdrawals, KYC, and loans
Enhanced with user management, content management, analytics, and certificates
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import json
from datetime import timedelta, datetime

from investments.models import Deposit, Withdrawal, Loan, Investment
from kyc.models import KYCDocument
from accounts.models import CustomUser
from notifications.models import Notification
from .models import NewsArticle, Certificate, AdminActivityLog, SiteSettings, AdminSession
from .decorators import admin_only, superuser_only, log_admin_action


# ============================================================================
# DASHBOARD OVERVIEW
# ============================================================================

@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard with statistics and pending items"""
    
    # Statistics
    stats = {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True).count(),
        'total_deposits': Deposit.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_withdrawals': Withdrawal.objects.aggregate(Sum('amount'))['amount__sum'] or 0,
        'active_investments': Investment.objects.filter(status='active').count(),
        'total_invested': Investment.objects.filter(status='active').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    # Revenue stats (7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    stats['revenue_7d'] = Deposit.objects.filter(
        status='confirmed', 
        created_at__gte=seven_days_ago
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    stats['withdrawals_7d'] = Withdrawal.objects.filter(
        status='approved',
        created_at__gte=seven_days_ago
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Pending items that need admin action
    pending_deposits = Deposit.objects.filter(status='pending').order_by('-created_at')[:10]
    pending_withdrawals = Withdrawal.objects.filter(status='pending').order_by('-created_at')[:10]
    pending_kyc = KYCDocument.objects.filter(status__in=['pending', 'submitted']).order_by('-submitted_at')[:10]
    pending_loans = Loan.objects.filter(status='pending').order_by('-created_at')[:10]
    
    # Count pending items
    pending_counts = {
        'deposits': Deposit.objects.filter(status='pending').count(),
        'withdrawals': Withdrawal.objects.filter(status='pending').count(),
        'kyc': KYCDocument.objects.filter(status__in=['pending', 'submitted']).count(),
        'loans': Loan.objects.filter(status='pending').count(),
    }
    
    # Recent admin activity
    recent_activity = AdminActivityLog.objects.select_related('admin_user').order_by('-created_at')[:15]
    
    context = {
        'stats': stats,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'pending_kyc': pending_kyc,
        'pending_loans': pending_loans,
        'pending_counts': pending_counts,
        'recent_activity': recent_activity,
        'active_tab': 'overview',
    }
    
    return render(request, 'dashboard/admin_panel.html', context)


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@admin_only
def admin_users(request):
    """User management interface with search and filters"""
    
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Search
    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(
            Q(email__icontains=query) | 
            Q(full_name__icontains=query) |
            Q(phone__icontains=query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)
    
    # Filter by KYC status
    kyc_filter = request.GET.get('kyc', 'all')
    if kyc_filter != 'all':
        users = users.filter(kyc_status=kyc_filter)
    
    # Pagination
    paginator = Paginator(users, 50)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    context = {
        'users': users_page,
        'total_users': paginator.count,
        'query': query,
        'status_filter': status_filter,
        'kyc_filter': kyc_filter,
        'active_tab': 'users',
    }
    
    return render(request, 'dashboard/admin_users.html', context)


@admin_only
def admin_user_detail(request, user_id):
    """View and edit individual user details"""
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        # Update user information
        action_type = request.POST.get('action')
        changes_before = {
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'kyc_status': user.kyc_status,
        }
        
        if action_type == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            status = 'activated' if user.is_active else 'suspended'
            messages.success(request, f'User {status} successfully.')
            
        elif action_type == 'toggle_staff':
            user.is_staff = not user.is_staff
            user.save()
            role = 'promoted to staff' if user.is_staff else 'removed from staff'
            messages.success(request, f'User {role} successfully.')
            
        elif action_type == 'update_kyc':
            kyc_status = request.POST.get('kyc_status')
            user.kyc_status = kyc_status
            user.save()
            messages.success(request, 'KYC status updated.')
        
        # Log the admin action
        changes_after = {
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'kyc_status': user.kyc_status,
        }
        
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='user_edit',
            description=f'Edited user: {user.email}',
            target_user=user,
            target_id=str(user.id),
            target_type='User',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            changes_before=changes_before,
            changes_after=changes_after,
        )
        
        return redirect('dashboard:admin_user_detail', user_id=user.id)
    
    # Get user statistics
    user_stats = {
        'total_invested': Investment.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_deposits': Deposit.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_withdrawals': Withdrawal.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0,
        'active_investments': Investment.objects.filter(user=user, status='active').count(),
    }
    
    recent_deposits = Deposit.objects.filter(user=user).order_by('-created_at')[:5]
    recent_withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'user_stats': user_stats,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'active_tab': 'users',
    }
    
    return render(request, 'dashboard/admin_user_detail.html', context)


# ============================================================================
# CONTENT MANAGEMENT
# ============================================================================

@admin_only
def admin_content(request):
    """Content management for news articles and homepage"""
    
    articles = NewsArticle.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'published':
        articles = articles.filter(is_published=True)
    elif status_filter == 'draft':
        articles = articles.filter(is_published=False)
    elif status_filter == 'featured':
        articles = articles.filter(is_featured=True)
    
    # Filter by category
    category_filter = request.GET.get('category', 'all')
    if category_filter != 'all':
        articles = articles.filter(category=category_filter)
    
    # Pagination
    paginator = Paginator(articles, 20)
    page = request.GET.get('page', 1)
    articles_page = paginator.get_page(page)
    
    context = {
        'articles': articles_page,
        'total_articles': paginator.count,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'active_tab': 'content',
    }
    
    return render(request, 'dashboard/admin_content.html', context)


@admin_only
def admin_content_edit(request, article_id=None):
    """Create or edit news articles"""
    
    article = None
    if article_id:
        article = get_object_or_404(NewsArticle, id=article_id)
    
    if request.method == 'POST':
        changes_before = {}
        if article:
            changes_before = {
                'title': article.title,
                'is_published': article.is_published,
                'category': article.category,
            }
        
        article_data = {
            'title': request.POST.get('title'),
            'excerpt': request.POST.get('excerpt'),
            'content': request.POST.get('content'),
            'category': request.POST.get('category'),
            'image_url': request.POST.get('image_url'),
            'is_featured': request.POST.get('is_featured') == 'on',
            'is_published': request.POST.get('is_published') == 'on',
        }
        
        if article:
            for key, value in article_data.items():
                setattr(article, key, value)
            article.save()
            action_type = 'content_edit'
            message = 'Article updated successfully.'
        else:
            article = NewsArticle.objects.create(**article_data)
            action_type = 'content_create'
            message = 'Article created successfully.'
        
        # Log activity
        changes_after = {
            'title': article.title,
            'is_published': article.is_published,
            'category': article.category,
        }
        
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type=action_type,
            description=f'{action_type.replace("_", " ").title()}: {article.title}',
            target_id=str(article.id),
            target_type='NewsArticle',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            changes_before=changes_before,
            changes_after=changes_after,
        )
        
        messages.success(request, message)
        return redirect('dashboard:admin_content')
    
    context = {
        'article': article,
        'active_tab': 'content',
    }
    
    return render(request, 'dashboard/admin_content_edit.html', context)


# ============================================================================
# ANALYTICS
# ============================================================================

@admin_only
def admin_analytics(request):
    """Analytics dashboard with charts and data"""
    
    # Date range
    days = request.GET.get('days', '30')
    try:
        days = int(days)
    except:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # User growth
    user_data = []
    for i in range(days, -1, -1):
        date = timezone.now() - timedelta(days=i)
        count = CustomUser.objects.filter(date_joined__date__lte=date).count()
        user_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count,
        })
    
    # Daily revenue
    revenue_data = []
    for i in range(days, -1, -1):
        date = timezone.now() - timedelta(days=i)
        revenue = Deposit.objects.filter(
            status='confirmed',
            created_at__date=date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        revenue_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(revenue),
        })
    
    # Investment trends
    investment_data = []
    for i in range(days, -1, -1):
        date = timezone.now() - timedelta(days=i)
        total = Investment.objects.filter(
            created_at__date=date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        count = Investment.objects.filter(created_at__date=date).count()
        investment_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'total': float(total),
            'count': count,
        })
    
    # Summary stats
    stats = {
        'total_users': CustomUser.objects.count(),
        'new_users': CustomUser.objects.filter(date_joined__gte=start_date).count(),
        'active_investments': Investment.objects.filter(status='active').count(),
        'total_invested': float(Investment.objects.filter(status='active').aggregate(Sum('amount'))['amount__sum'] or 0),
        'pending_deposits': Deposit.objects.filter(status='pending').count(),
        'pending_withdrawals': Withdrawal.objects.filter(status='pending').count(),
    }
    
    context = {
        'stats': stats,
        'user_data': json.dumps(user_data),
        'revenue_data': json.dumps(revenue_data),
        'investment_data': json.dumps(investment_data),
        'days': days,
        'active_tab': 'analytics',
    }
    
    return render(request, 'dashboard/admin_analytics.html', context)


@admin_only
def analytics_data_json(request):
    """API endpoint for analytics data"""
    
    days = request.GET.get('days', '30')
    try:
        days = int(days)
    except:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Build data for different chart types
    metric = request.GET.get('metric', 'users')
    
    if metric == 'users':
        data = []
        for i in range(days, -1, -1):
            date = timezone.now() - timedelta(days=i)
            count = CustomUser.objects.filter(date_joined__date__lte=date).count()
            data.append([date.timestamp() * 1000, count])
    
    elif metric == 'revenue':
        data = []
        for i in range(days, -1, -1):
            date = timezone.now() - timedelta(days=i)
            revenue = Deposit.objects.filter(
                status='confirmed',
                created_at__date=date
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            data.append([date.timestamp() * 1000, float(revenue)])
    
    elif metric == 'investments':
        data = []
        for i in range(days, -1, -1):
            date = timezone.now() - timedelta(days=i)
            total = Investment.objects.filter(
                created_at__date=date
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            data.append([date.timestamp() * 1000, float(total)])
    
    else:
        data = []
    
    return JsonResponse({'data': data})


# ============================================================================
# CERTIFICATES & LICENSES
# ============================================================================

@admin_only
def admin_certificates(request):
    """Certificate and license management"""
    
    certificates = Certificate.objects.all().order_by('order', '-issue_date')
    
    context = {
        'certificates': certificates,
        'active_tab': 'certificates',
    }
    
    return render(request, 'dashboard/admin_certificates.html', context)


@admin_only
def admin_certificate_add(request):
    """Add new certificate"""
    
    if request.method == 'POST':
        try:
            cert = Certificate.objects.create(
                name=request.POST.get('name'),
                certificate_type=request.POST.get('certificate_type'),
                description=request.POST.get('description'),
                issuer=request.POST.get('issuer'),
                certificate_number=request.POST.get('certificate_number'),
                issue_date=request.POST.get('issue_date'),
                expiry_date=request.POST.get('expiry_date') or None,
                display_on_site=request.POST.get('display_on_site') == 'on',
                order=int(request.POST.get('order', 0)),
            )
            
            # Handle file upload
            if 'document' in request.FILES:
                cert.document = request.FILES['document']
                cert.save()
            
            # Log activity
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action_type='certificate_upload',
                description=f'Uploaded certificate: {cert.name}',
                target_id=str(cert.id),
                target_type='Certificate',
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            messages.success(request, 'Certificate uploaded successfully.')
            return redirect('dashboard:admin_certificates')
        
        except Exception as e:
            messages.error(request, f'Error uploading certificate: {str(e)}')
    
    context = {
        'active_tab': 'certificates',
    }
    
    return render(request, 'dashboard/admin_certificate_add.html', context)


@admin_only
def admin_certificate_edit(request, cert_id):
    """Edit existing certificate"""
    
    cert = get_object_or_404(Certificate, id=cert_id)
    
    if request.method == 'POST':
        changes_before = {
            'name': cert.name,
            'expiry_date': str(cert.expiry_date) if cert.expiry_date else None,
        }
        
        cert.name = request.POST.get('name')
        cert.certificate_type = request.POST.get('certificate_type')
        cert.description = request.POST.get('description')
        cert.issuer = request.POST.get('issuer')
        cert.certificate_number = request.POST.get('certificate_number')
        cert.issue_date = request.POST.get('issue_date')
        cert.expiry_date = request.POST.get('expiry_date') or None
        cert.display_on_site = request.POST.get('display_on_site') == 'on'
        cert.order = int(request.POST.get('order', 0))
        
        if 'document' in request.FILES:
            cert.document = request.FILES['document']
        
        cert.save()
        
        changes_after = {
            'name': cert.name,
            'expiry_date': str(cert.expiry_date) if cert.expiry_date else None,
        }
        
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='certificate_update',
            description=f'Updated certificate: {cert.name}',
            target_id=str(cert.id),
            target_type='Certificate',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            changes_before=changes_before,
            changes_after=changes_after,
        )
        
        messages.success(request, 'Certificate updated successfully.')
        return redirect('dashboard:admin_certificates')
    
    context = {
        'cert': cert,
        'active_tab': 'certificates',
    }
    
    return render(request, 'dashboard/admin_certificate_edit.html', context)


# ============================================================================
# SETTINGS
# ============================================================================

@superuser_only
def admin_settings(request):
    """Site settings management"""
    
    settings_obj = SiteSettings.get_settings()
    
    if request.method == 'POST':
        changes_before = {
            'maintenance_mode': settings_obj.maintenance_mode,
            'enable_registrations': settings_obj.enable_registrations,
            'enable_deposits': settings_obj.enable_deposits,
        }
        
        settings_obj.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        settings_obj.enable_registrations = request.POST.get('enable_registrations') == 'on'
        settings_obj.enable_deposits = request.POST.get('enable_deposits') == 'on'
        settings_obj.enable_withdrawals = request.POST.get('enable_withdrawals') == 'on'
        settings_obj.enable_two_factor = request.POST.get('enable_two_factor') == 'on'
        settings_obj.session_timeout_minutes = int(request.POST.get('session_timeout_minutes', 30))
        settings_obj.kyc_required = request.POST.get('kyc_required') == 'on'
        settings_obj.minimum_deposit = request.POST.get('minimum_deposit')
        settings_obj.maximum_withdrawal = request.POST.get('maximum_withdrawal')
        
        settings_obj.save()
        
        changes_after = {
            'maintenance_mode': settings_obj.maintenance_mode,
            'enable_registrations': settings_obj.enable_registrations,
            'enable_deposits': settings_obj.enable_deposits,
        }
        
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='settings_change',
            description='Updated site settings',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            changes_before=changes_before,
            changes_after=changes_after,
        )
        
        messages.success(request, 'Settings updated successfully.')
        return redirect('dashboard:admin_settings')
    
    context = {
        'settings': settings_obj,
        'active_tab': 'settings',
    }
    
    return render(request, 'dashboard/admin_settings.html', context)


# ============================================================================
# EXISTING DEPOSIT/WITHDRAWAL/KYC/LOAN MANAGEMENT (unchanged)
# ============================================================================

@staff_member_required
def confirm_deposit(request, pk):
    """Confirm a pending deposit and credit user's balance"""
    deposit = get_object_or_404(Deposit, pk=pk)
    
    if deposit.status != 'pending':
        messages.warning(request, 'This deposit has already been processed.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Credit user's balance
        user = deposit.user
        user.balance += deposit.amount
        user.save()
        
        # Update deposit status
        deposit.status = 'confirmed'
        deposit.confirmed_by = request.user
        deposit.admin_notes = request.POST.get('admin_notes', '')
        deposit.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='deposit_approve',
            description=f'Approved deposit of ${deposit.amount} from {user.email}',
            target_user=user,
            target_id=str(deposit.id),
            target_type='Deposit',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=user,
            title='Deposit Confirmed',
            message=f'Your deposit of ${deposit.amount} has been confirmed and credited to your account.',
            category='transaction',
            notification_type='success',
            action_url='/transactions/'
        )
        
        messages.success(request, f'Deposit of ${deposit.amount} confirmed successfully.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/confirm_deposit.html', {'deposit': deposit})


@staff_member_required
def reject_deposit(request, pk):
    """Reject a pending deposit"""
    deposit = get_object_or_404(Deposit, pk=pk)
    
    if deposit.status != 'pending':
        messages.warning(request, 'This deposit has already been processed.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Update deposit status
        deposit.status = 'rejected'
        deposit.confirmed_by = request.user
        deposit.admin_notes = request.POST.get('admin_notes', '')
        deposit.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='deposit_approve',  # Changed from deposit_approve context
            description=f'Rejected deposit of ${deposit.amount} from {deposit.user.email}',
            target_user=deposit.user,
            target_id=str(deposit.id),
            target_type='Deposit',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=deposit.user,
            title='Deposit Rejected',
            message=f'Your deposit of ${deposit.amount} was rejected. Please contact support for more information.',
            category='transaction',
            notification_type='error',
            action_url='/dashboard/contact/'
        )
        
        messages.success(request, 'Deposit rejected.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/reject_deposit.html', {'deposit': deposit})


# WITHDRAWAL MANAGEMENT
@staff_member_required
def approve_withdrawal(request, pk):
    """Approve a pending withdrawal"""
    withdrawal = get_object_or_404(Withdrawal, pk=pk)
    
    if withdrawal.status != 'pending':
        messages.warning(request, 'This withdrawal has already been processed.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Update withdrawal status
        withdrawal.status = 'approved'
        withdrawal.processed_by = request.user
        withdrawal.admin_notes = request.POST.get('admin_notes', '')
        withdrawal.tx_hash = request.POST.get('tx_hash', '')
        withdrawal.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='withdrawal_approve',
            description=f'Approved withdrawal of ${withdrawal.amount} for {withdrawal.user.email}',
            target_user=withdrawal.user,
            target_id=str(withdrawal.id),
            target_type='Withdrawal',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=withdrawal.user,
            title='Withdrawal Approved',
            message=f'Your withdrawal of ${withdrawal.amount} has been approved and is being processed.',
            category='transaction',
            notification_type='success'
        )
        
        messages.success(request, f'Withdrawal of ${withdrawal.amount} approved.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/approve_withdrawal.html', {'withdrawal': withdrawal})


@staff_member_required
def reject_withdrawal(request, pk):
    """Reject a pending withdrawal and refund user's balance"""
    withdrawal = get_object_or_404(Withdrawal, pk=pk)
    
    if withdrawal.status != 'pending':
        messages.warning(request, 'This withdrawal has already been processed.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Refund user's balance
        user = withdrawal.user
        user.balance += withdrawal.amount
        user.save()
        
        # Update withdrawal status
        withdrawal.status = 'rejected'
        withdrawal.processed_by = request.user
        withdrawal.admin_notes = request.POST.get('admin_notes', '')
        withdrawal.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='withdrawal_reject',
            description=f'Rejected withdrawal of ${withdrawal.amount} for {user.email}',
            target_user=user,
            target_id=str(withdrawal.id),
            target_type='Withdrawal',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=user,
            title='Withdrawal Rejected',
            message=f'Your withdrawal of ${withdrawal.amount} was rejected and the funds have been returned to your balance.',
            category='transaction',
            notification_type='warning',
            action_url='/transactions/'
        )
        
        messages.success(request, 'Withdrawal rejected and funds refunded.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/reject_withdrawal.html', {'withdrawal': withdrawal})


# KYC MANAGEMENT
@staff_member_required
def approve_kyc(request, pk):
    """Approve a KYC verification"""
    kyc = get_object_or_404(KYCDocument, pk=pk)
    
    if kyc.status == 'verified':
        messages.warning(request, 'This KYC is already verified.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Update KYC status
        kyc.status = 'verified'
        kyc.reviewed_by = request.user
        kyc.reviewed_at = timezone.now()
        kyc.save()
        
        # Update user's KYC status
        user = kyc.user
        user.kyc_status = 'verified'
        user.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='kyc_approve',
            description=f'Approved KYC for {user.email}',
            target_user=user,
            target_id=str(kyc.id),
            target_type='KYCDocument',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=user,
            title='KYC Verified',
            message='Your KYC verification has been approved. You now have full access to all platform features.',
            category='system',
            notification_type='success'
        )
        
        messages.success(request, f'KYC for {user.email} verified successfully.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/approve_kyc.html', {'kyc': kyc})


@staff_member_required
def reject_kyc(request, pk):
    """Reject a KYC verification"""
    kyc = get_object_or_404(KYCDocument, pk=pk)
    
    if kyc.status == 'rejected':
        messages.warning(request, 'This KYC is already rejected.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Update KYC status
        kyc.status = 'rejected'
        kyc.reviewed_by = request.user
        kyc.reviewed_at = timezone.now()
        kyc.rejection_reason = request.POST.get('rejection_reason', '')
        kyc.save()
        
        # Update user's KYC status
        user = kyc.user
        user.kyc_status = 'rejected'
        user.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='kyc_reject',
            description=f'Rejected KYC for {user.email}',
            target_user=user,
            target_id=str(kyc.id),
            target_type='KYCDocument',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=user,
            title='KYC Rejected',
            message=f'Your KYC verification was rejected. Reason: {kyc.rejection_reason}',
            category='system',
            notification_type='error',
            action_url='/kyc/upload/'
        )
        
        messages.success(request, 'KYC rejected.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/reject_kyc.html', {'kyc': kyc})


# LOAN MANAGEMENT
@staff_member_required
def approve_loan(request, pk):
    """Approve a loan application and disburse funds"""
    loan = get_object_or_404(Loan, pk=pk)
    
    if loan.status != 'pending':
        messages.warning(request, 'This loan has already been processed.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Update loan status
        loan.status = 'approved'
        loan.approved_by = request.user
        loan.approved_at = timezone.now()
        loan.admin_notes = request.POST.get('admin_notes', '')
        loan.save()
        
        # Credit user's balance
        user = loan.user
        user.balance += loan.amount
        user.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='loan_approve',
            description=f'Approved loan of ${loan.amount} for {user.email}',
            target_user=user,
            target_id=str(loan.id),
            target_type='Loan',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=user,
            title='Loan Approved',
            message=f'Your loan application for ${loan.amount} has been approved and credited to your account.',
            category='transaction',
            notification_type='success',
            action_url='/loans/'
        )
        
        messages.success(request, f'Loan of ${loan.amount} approved and disbursed.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/approve_loan.html', {'loan': loan})


@staff_member_required
def reject_loan(request, pk):
    """Reject a loan application"""
    loan = get_object_or_404(Loan, pk=pk)
    
    if loan.status != 'pending':
        messages.warning(request, 'This loan has already been processed.')
        return redirect('dashboard:admin_panel')
    
    if request.method == 'POST':
        # Update loan status
        loan.status = 'rejected'
        loan.approved_by = request.user
        loan.admin_notes = request.POST.get('admin_notes', '')
        loan.save()
        
        # Log activity
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action_type='loan_reject',
            description=f'Rejected loan of ${loan.amount} for {loan.user.email}',
            target_user=loan.user,
            target_id=str(loan.id),
            target_type='Loan',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        # Create notification
        Notification.create_notification(
            user=loan.user,
            title='Loan Rejected',
            message=f'Your loan application for ${loan.amount} was rejected. Please contact support for more information.',
            category='system',
            notification_type='error',
            action_url='/dashboard/contact/'
        )
        
        messages.success(request, 'Loan rejected.')
        return redirect('dashboard:admin_panel')
    
    return render(request, 'dashboard/reject_loan.html', {'loan': loan})
