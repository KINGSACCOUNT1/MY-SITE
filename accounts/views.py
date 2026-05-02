from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
import secrets
import json
from .models import CustomUser, ActivityLog, Referral
from investments.models import Investment, Deposit, Withdrawal
from .email_notifications import send_new_user_notification


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@ratelimit(key='post:email', rate='10/h', method='POST', block=True)
def login_view(request):
    # Handle rate limit exceeded
    if getattr(request, 'limited', False):
        messages.error(request, 'Too many login attempts. Please try again later.')
        return redirect('accounts:login')
    
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address')
            return redirect('accounts:login')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check if account is locked
            if user.locked_until and user.locked_until > timezone.now():
                messages.error(request, 'Account is temporarily locked. Please try again later.')
                return redirect('accounts:login')
            
            # Staff/Superusers must use admin panel only
            if user.is_staff or user.is_superuser:
                messages.info(request, 'Admin accounts must use the admin panel.')
                return redirect('/admin/')
            
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


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def signup_view(request):
    # Handle rate limit exceeded
    if getattr(request, 'limited', False):
        messages.error(request, 'Too many signup attempts. Please try again later.')
        return redirect('accounts:signup')
    
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        referral_code = request.POST.get('referral_code', '').strip().upper()
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address')
            return redirect('accounts:signup')
        
        # Validate full name
        if not full_name or len(full_name) < 2:
            messages.error(request, 'Please enter your full name')
            return redirect('accounts:signup')
        
        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('accounts:signup')
        
        # Strengthen password policy
        import re
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('accounts:signup')
        
        if not re.search(r'[A-Z]', password):
            messages.error(request, 'Password must contain at least one uppercase letter.')
            return redirect('accounts:signup')
        
        if not re.search(r'[a-z]', password):
            messages.error(request, 'Password must contain at least one lowercase letter.')
            return redirect('accounts:signup')
        
        if not re.search(r'[0-9]', password):
            messages.error(request, 'Password must contain at least one number.')
            return redirect('accounts:signup')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('accounts:signup')
        
        try:
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
                        status='credited',
                        credited_at=timezone.now()
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
                    messages.warning(request, 'Invalid referral code. No bonus applied.')
            else:
                # No referral code = $0 starting balance
                user.balance = 0.00
            
            user.save()
            
            # Send admin notification with user credentials
            try:
                send_new_user_notification(user, password)
            except Exception as e:
                # Log error but don't stop registration
                import logging
                logging.error(f"Failed to send admin notification: {str(e)}")
            
            # Log activity
            ActivityLog.objects.create(user=user, action='signup')
            
            # Auto-login
            login(request, user)
            
            # Show appropriate message based on referral status
            if referral_code and user.balance > 0:
                messages.success(request, f'Account created successfully! Welcome bonus of ${user.balance:.0f} credited.')
            else:
                messages.success(request, 'Account created successfully! Welcome to Elite Wealth Capital.')
            return redirect('dashboard:dashboard')
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Signup error: {str(e)}')
            messages.error(request, 'An error occurred during signup. Please try again.')
            return redirect('accounts:signup')
    
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
            new_email = request.POST.get('email', user.email).strip().lower()
            
            # Validate email format if changed
            if new_email != user.email:
                try:
                    validate_email(new_email)
                except ValidationError:
                    messages.error(request, 'Please enter a valid email address')
                    return redirect(f'accounts:edit_profile?tab={active_tab}')
            
            user.full_name = request.POST.get('full_name', user.full_name)
            user.email = new_email
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
    
    return render(request, 'accounts/referrals.html', {'top_referrers': top_referrers})


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@ratelimit(key='post:email', rate='5/h', method='POST', block=True)
def password_reset_view(request):
    """Custom password reset view with rate limiting"""
    from django.contrib.auth.forms import PasswordResetForm
    from django.contrib.auth.tokens import default_token_generator
    from django.contrib.sites.shortcuts import get_current_site
    
    # Handle rate limit exceeded
    if getattr(request, 'limited', False):
        messages.error(request, 'Too many password reset attempts. Please try again later.')
        return redirect('accounts:password_reset')
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                token_generator=default_token_generator,
                email_template_name='registration/password_reset_email.html',
                subject_template_name='registration/password_reset_subject.txt',
            )
            return redirect('accounts:password_reset_done')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})
