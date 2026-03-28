"""
Context processors for global template variables
"""
import os
from django.conf import settings


def site_settings(request):
    """
    Company and site settings available in all templates
    Pulls from SiteSettings model if available, fallback to settings.py
    """
    from dashboard.models import SiteSettings
    
    try:
        site_config = SiteSettings.get_settings()
        return {
            'SITE_NAME': site_config.company_name or 'Elite Wealth Capital',
            'COMPANY_NAME': site_config.company_name or 'Elite Wealth Capital',
            'COMPANY_EMAIL': site_config.company_email or getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapital.uk'),
            'COMPANY_PHONE': site_config.company_phone or getattr(settings, 'COMPANY_PHONE', '+44-XXX-XXXX-XXX'),
            'COMPANY_ADDRESS': site_config.company_address or getattr(settings, 'COMPANY_ADDRESS', 'London, United Kingdom'),
            'COMPANY_WEBSITE': site_config.company_website or getattr(settings, 'COMPANY_WEBSITE', 'https://elitewealthcapital.uk'),
            'SUPPORT_EMAIL': site_config.support_email or getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapital.uk'),
            'COMPANY_DESCRIPTION': 'Your trusted partner in wealth management and investment solutions',
        }
    except Exception:
        # Fallback to settings.py constants
        return {
            'SITE_NAME': 'Elite Wealth Capital',
            'COMPANY_NAME': 'Elite Wealth Capital',
            'COMPANY_EMAIL': getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapital.uk'),
            'COMPANY_PHONE': getattr(settings, 'COMPANY_PHONE', '+44-XXX-XXXX-XXX'),
            'COMPANY_ADDRESS': getattr(settings, 'COMPANY_ADDRESS', 'London, United Kingdom'),
            'COMPANY_WEBSITE': getattr(settings, 'COMPANY_WEBSITE', 'https://elitewealthcapital.uk'),
            'SUPPORT_EMAIL': getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapital.uk'),
            'COMPANY_DESCRIPTION': 'Your trusted partner in wealth management and investment solutions',
        }


def tawk_settings(request):
    """
    Tawk.to chat widget configuration
    """
    return {
        'TAWK_PROPERTY_ID': getattr(settings, 'TAWK_PROPERTY_ID', ''),
        'TAWK_WIDGET_ID': getattr(settings, 'TAWK_WIDGET_ID', ''),
        'TAWK_API_KEY': getattr(settings, 'TAWK_API_KEY', ''),
        'TAWK_ENABLED': bool(getattr(settings, 'TAWK_PROPERTY_ID', '')),
    }


def notification_context(request):
    """
    Unread notification count for authenticated users
    """
    unread_count = 0
    
    if request.user.is_authenticated:
        try:
            from notifications.models import Notification
            unread_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
        except Exception:
            pass
    
    return {
        'unread_notifications_count': unread_count,
    }


def user_stats(request):
    """
    User financial stats for authenticated users
    """
    stats = {
        'user_balance': 0,
        'user_invested': 0,
        'user_profit': 0,
        'user_referral_bonus': 0,
        'user_available_balance': 0,
        'user_kyc_verified': False,
        'user_account_type': 'beginner',
    }
    
    if request.user.is_authenticated:
        user = request.user
        stats.update({
            'user_balance': user.balance,
            'user_invested': user.invested_amount,
            'user_profit': user.total_profit,
            'user_referral_bonus': user.referral_bonus,
            'user_available_balance': user.get_available_balance(),
            'user_kyc_verified': user.kyc_status == 'verified',
            'user_account_type': user.account_type,
        })
    
    return stats
