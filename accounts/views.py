from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
import logging
from .models import CustomUser, ActivityLog, Referral
from .forms import (
    SignupForm, LoginForm, ProfileForm, 
    ForgotPasswordForm, ResetPasswordForm, ChangePasswordForm
)
from notifications.models import Notification
from core.validators import validate_uploaded_file
from core.utils import get_client_ip

logger = logging.getLogger(__name__)

# Referral bonus amounts
NEW_USER_BONUS = Decimal('20.00')
REFERRER_BONUS = Decimal('30.00')



@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """User login with Django session authentication."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_panel')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                logger.info(f"Login attempt for user: {user.email}")
                
                # Handle "remember me" - set session expiry
                if form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
                else:
                    request.session.set_expiry(0)  # Browser close
                
                login(request, user, backend='accounts.backends.EmailBackend')
                logger.info(f"Login successful for: {user.email}")
                
                # Log activity
                try:
                    ActivityLog.objects.create(
                        user=user,
                        action='login',
                        description='User logged in',
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
                except Exception as e:
                    logger.error(f"ActivityLog error: {e}")
                
                messages.success(request, f'Welcome back, {user.full_name}!')
                
                # Redirect based on role, validating the next URL to prevent open redirects
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                if user.is_staff or user.is_superuser:
                    return redirect('admin_panel')
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Login view error: {type(e).__name__}: {e}")
                raise
        else:
            # Form errors are shown in template
            pass
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def logout_view(request):
    """User logout view - POST only for CSRF protection."""
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action='logout',
            description='User logged out',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@transaction.atomic
def signup_view(request):
    """User registration with referral bonus system."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Pre-fill referral code from URL
    initial_data = {}
    url_referral_code = request.GET.get('ref', '')
    if url_referral_code:
        initial_data['referral_code'] = url_referral_code.upper()
    
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)  # Include FILES for profile image
        if form.is_valid():
            # Validate profile image
            if 'profile_image' in request.FILES:
                try:
                    validate_uploaded_file(request.FILES['profile_image'], 'Profile Image')
                except ValidationError as e:
                    messages.error(request, str(e))
                    return render(request, 'signup.html', {'form': form})
            
            # Create user
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            
            # Handle profile image
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']
            
            # Handle referral
            referral_code = form.cleaned_data.get('referral_code', '').strip().upper()
            referrer = None
            bonus_awarded = False
            
            if referral_code:
                try:
                    referrer = CustomUser.objects.get(referral_code=referral_code)
                    user.referred_by = referrer
                except CustomUser.DoesNotExist:
                    pass
            
            user.save()
            
            # Create welcome notification for new user
            Notification.create_notification(
                user=user,
                title='🎉 Welcome to Elite Wealth Capital!',
                message='Your account has been successfully created. Start your investment journey today and build your wealth with us!',
                notification_type='success',
                category='general',
                priority='high',
                action_url='/dashboard/'
            )
            
            # Apply referral bonuses
            if referrer:
                # $20 to new user
                user.balance = NEW_USER_BONUS
                user.save()
                
                # $30 to referrer
                referrer.referral_bonus += REFERRER_BONUS
                referrer.balance += REFERRER_BONUS
                referrer.save()
                
                # Create referral record
                Referral.objects.create(
                    referrer=referrer,
                    referred=user,
                    bonus_amount=REFERRER_BONUS,
                    status='credited',
                    credited_at=timezone.now()
                )
                bonus_awarded = True
                
                # Create bonus notification for new user
                Notification.create_notification(
                    user=user,
                    title='💰 $20 Signup Bonus Credited!',
                    message=f'Congratulations! You received a $20 signup bonus for using referral code {referral_code}. Your balance has been updated.',
                    notification_type='success',
                    category='financial',
                    priority='high',
                    action_url='/dashboard/'
                )
                
                # Create referral notification for referrer
                Notification.create_notification(
                    user=referrer,
                    title='🎁 New Referral Bonus!',
                    message=f'{user.full_name} joined using your referral code! $30 bonus has been added to your account.',
                    notification_type='success',
                    category='financial',
                    priority='high',
                    action_url='/dashboard/'
                )
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='registration',
                description=f"New user registered. Referral bonus: {'$20' if bonus_awarded else 'No'}",
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if bonus_awarded:
                messages.success(request, 'Account created! $20 signup bonus added to your balance!')
            else:
                messages.success(request, 'Account created successfully! Please login.')
            
            return redirect('login')
    else:
        form = SignupForm(initial=initial_data)
    
    return render(request, 'signup.html', {'form': form})


@login_required
def profile_view(request):
    """User profile and account settings."""
    user = request.user
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=user)
    
    # Get referral stats
    referral_count = user.referrals.count()
    
    context = {
        'form': form,
        'user': user,
        'referral_count': referral_count,
    }
    return render(request, 'account-settings.html', context)


@login_required
def change_password_view(request):
    """Change password for logged-in user."""
    if request.method == 'POST':
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='password_change',
                description='Password changed successfully',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Password changed! Please login with your new password.')
            logout(request)
            return redirect('login')
    else:
        form = ChangePasswordForm(user=request.user)
    
    return render(request, 'change-password.html', {'form': form})


def verify_email(request, token=None):
    """Email verification view."""
    context = {'token': token, 'verified': False, 'error': None}
    
    if token:
        try:
            user = CustomUser.objects.get(email_verification_token=token)
            # Check if token is not expired (24 hours)
            if user.email_verification_sent_at:
                token_age = timezone.now() - user.email_verification_sent_at
                if token_age.total_seconds() > 86400:  # 24 hours
                    context['error'] = 'Verification link has expired. Please request a new one.'
                    return render(request, 'verify-email.html', context)
            
            # Verify the email
            user.email_verified = True
            user.email_verification_token = None
            user.save()
            
            context['verified'] = True
            messages.success(request, 'Email verified successfully! You can now login.')
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='email_verified',
                description='Email address verified',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except CustomUser.DoesNotExist:
            context['error'] = 'Invalid verification link.'
    
    return render(request, 'verify-email.html', context)


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def forgot_password(request):
    """Request password reset email."""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                
                # Generate reset token
                import secrets
                token = secrets.token_urlsafe(32)
                user.password_reset_token = token
                user.password_reset_sent_at = timezone.now()
                user.save()
                
                # Build reset URL
                reset_url = request.build_absolute_uri(
                    reverse('reset_password_token', kwargs={'token': token})
                )
                
                # Send email
                try:
                    send_mail(
                        subject='Password Reset - Elite Wealth Capital',
                        message=f'''Hello {user.full_name},

You requested a password reset for your Elite Wealth Capital account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this reset, please ignore this email.

Best regards,
Elite Wealth Capital Team''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        fail_silently=False,
                    )
                except Exception:
                    pass  # Silently fail to prevent email enumeration
                
                # Log activity
                ActivityLog.objects.create(
                    user=user,
                    action='password_reset_requested',
                    description='Password reset email requested',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except CustomUser.DoesNotExist:
                pass  # Silently fail to prevent email enumeration
            
            messages.success(request, 'If an account exists with this email, you will receive a password reset link.')
            return redirect('login')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'forgot-password.html', {'form': form})


def reset_password(request, token=None):
    """Reset password with token."""
    if not token:
        messages.error(request, 'Invalid reset link.')
        return redirect('forgot_password')
    
    # Verify token
    try:
        user = CustomUser.objects.get(password_reset_token=token)
        
        # Check if token is expired (1 hour)
        if user.password_reset_sent_at:
            token_age = timezone.now() - user.password_reset_sent_at
            if token_age.total_seconds() > 3600:  # 1 hour
                messages.error(request, 'Reset link has expired. Please request a new one.')
                return redirect('forgot_password')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid reset link.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            
            # Update password
            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_sent_at = None
            user.save()
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='password_reset_completed',
                description='Password was reset via email link',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Password reset successfully! Please login with your new password.')
            return redirect('login')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'reset-password.html', {'form': form, 'token': token})
