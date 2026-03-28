from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import secrets
import json
from .models import CustomUser, ActivityLog, Referral
from investments.models import Investment, Deposit, Withdrawal


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower()
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check if account is locked
            if user.locked_until and user.locked_until > timezone.now():
                messages.error(request, 'Account is temporarily locked. Please try again later.')
                return redirect('accounts:login')
            
            login(request, user)
            user.failed_login_attempts = 0
            user.last_login = timezone.now()
            user.save(update_fields=['failed_login_attempts', 'last_login'])
            
            # Log activity
            ActivityLog.objects.create(user=user, action='login')
            
            messages.success(request, f'Welcome back, {user.full_name}!')
            return redirect('dashboard:dashboard')
        else:
            # Handle failed login
            try:
                user = CustomUser.objects.get(email=email)
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
                user.save()
            except CustomUser.DoesNotExist:
                pass
            
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').lower()
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        referral_code = request.POST.get('referral_code', '').upper()
        
        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('accounts:signup')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('accounts:signup')
        
        # Create user
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            full_name=full_name
        )
        
        # Generate email verification token
        user.email_verification_token = secrets.token_urlsafe(32)
        user.email_verification_sent_at = timezone.now()
        
        # Handle referral - New user gets $20 ONLY if using referral code
        if referral_code:
            try:
                referrer = CustomUser.objects.get(referral_code=referral_code)
                user.referred_by = referrer
                user.balance = 20.00  # New user gets $20 with referral code
                
                # Referrer gets $30 bonus
                referrer.referral_bonus += 30.00
                referrer.save()
                
                # Create referral record
                Referral.objects.create(
                    referrer=referrer,
                    referred=user,
                    bonus_amount=30.00,
                    status='completed'
                )
                
                # Create notification for referrer
                from notifications.models import Notification
                Notification.objects.create(
                    user=referrer,
                    title='Referral Bonus Earned',
                    message=f'You earned $30 for referring {user.full_name}!',
                    notification_type='referral'
                )
            except CustomUser.DoesNotExist:
                user.balance = 0.00  # Invalid referral code = $0
        else:
            # No referral code = $0 starting balance
            user.balance = 0.00
        
        user.save()
        
        # Log activity
        ActivityLog.objects.create(user=user, action='signup')
        
        # Auto-login
        login(request, user)
        
        messages.success(request, 'Account created successfully! Welcome bonus of $20 credited.')
        return redirect('dashboard:dashboard')
    
    return render(request, 'accounts/signup.html')


@login_required
def logout_view(request):
    ActivityLog.objects.create(user=request.user, action='logout')
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.full_name = request.POST.get('full_name', user.full_name)
        user.phone = request.POST.get('phone', user.phone)
        user.country = request.POST.get('country', user.country)
        user.save()
        
        ActivityLog.objects.create(user=user, action='profile_updated')
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html')


@login_required
def edit_profile(request):
    """Edit profile page with all tabs"""
    user = request.user
    active_tab = request.GET.get('tab', 'personal')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_personal':
            user.full_name = request.POST.get('full_name', user.full_name)
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            user.country = request.POST.get('country', user.country)
            user.save()
            ActivityLog.objects.create(user=user, action='profile_updated')
            messages.success(request, 'Personal details updated successfully.')
        
        elif action == 'update_preferences':
            # Store preferences as JSON
            preferences = {
                'risk_tolerance': request.POST.get('risk_tolerance', 'medium'),
                'preferred_assets': request.POST.getlist('preferred_assets'),
                'notifications_email': request.POST.get('notifications_email') == 'on',
                'notifications_sms': request.POST.get('notifications_sms') == 'on',
                'notifications_push': request.POST.get('notifications_push') == 'on',
            }
            # You would save this to a UserPreferences model if you create one
            messages.success(request, 'Investment preferences updated successfully.')
        
        elif action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                user.set_password(new_password)
                user.save()
                ActivityLog.objects.create(user=user, action='password_change')
                messages.success(request, 'Password changed successfully.')
                return redirect('accounts:login')
        
        return redirect(f'accounts:edit_profile?tab={active_tab}')
    
    # Get kyc status
    kyc_status = user.kyc_status
    
    context = {
        'user': user,
        'active_tab': active_tab,
        'kyc_status': kyc_status,
    }
    
    return render(request, 'accounts/edit_profile.html', context)


@login_required
@require_http_methods(["POST"])
def upload_avatar(request):
    """Handle profile picture upload with AJAX"""
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file provided'}, status=400)
        
        avatar_file = request.FILES['avatar']
        
        # Validate file size (max 5MB)
        if avatar_file.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size exceeds 5MB limit'}, status=400)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        if avatar_file.content_type not in allowed_types:
            return JsonResponse({'success': False, 'error': 'Invalid file type. Allowed: JPEG, PNG, WebP, GIF'}, status=400)
        
        user = request.user
        user.profile_image = avatar_file
        user.save()
        
        ActivityLog.objects.create(user=user, action='profile_updated', description='Profile picture updated')
        
        return JsonResponse({
            'success': True,
            'message': 'Profile picture updated successfully',
            'avatar_url': user.profile_image.url if user.profile_image else ''
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def enable_2fa(request):
    """Enable two-factor authentication"""
    if request.method == 'POST':
        import pyotp
        
        user = request.user
        secret = pyotp.random_base32()
        
        # Store secret temporarily for verification
        request.session['2fa_secret_temp'] = secret
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='Elite Wealth Capital'
        )
        
        context = {
            'qr_uri': qr_uri,
            'secret': secret,
        }
        
        return render(request, 'accounts/setup_2fa.html', context)
    
    return render(request, 'accounts/enable_2fa.html')


@login_required
def verify_2fa(request):
    """Verify and enable 2FA"""
    if request.method == 'POST':
        import pyotp
        
        user = request.user
        secret = request.session.get('2fa_secret_temp')
        code = request.POST.get('code')
        
        if not secret:
            messages.error(request, '2FA setup session expired. Please try again.')
            return redirect('accounts:enable_2fa')
        
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            user.two_fa_enabled = True
            user.two_fa_secret = secret
            user.save()
            
            del request.session['2fa_secret_temp']
            ActivityLog.objects.create(user=user, action='2fa_enabled')
            messages.success(request, 'Two-factor authentication enabled successfully.')
            return redirect('accounts:edit_profile?tab=security')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
            return redirect('accounts:enable_2fa')
    
    return render(request, 'accounts/verify_2fa.html')


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


@login_required
def referral_dashboard(request):
    """Referral dashboard"""
    user = request.user
    referrals = Referral.objects.filter(referrer=user).select_related('referred')
    total_earnings = referrals.filter(status='credited').aggregate(Sum('bonus_amount'))['bonus_amount__sum'] or 0
    
    context = {
        'referral_code': user.referral_code,
        'referrals': referrals,
        'total_referrals': referrals.count(),
        'total_earnings': total_earnings,
    }
    
    return render(request, 'accounts/referrals.html', context)


@login_required  
def referral_leaderboard(request):
    """Top referrers leaderboard"""
    from django.db.models import Count
    
    top_referrers = CustomUser.objects.annotate(
        referral_count=Count('referrals_made')
    ).filter(referral_count__gt=0).order_by('-referral_count')[:20]
    
    return render(request, 'accounts/referral_leaderboard.html', {'top_referrers': top_referrers})
