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
            'COMPANY_EMAIL': site_config.company_email or getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapita.uk'),
            'COMPANY_PHONE': site_config.company_phone or getattr(settings, 'COMPANY_PHONE', '+44-XXX-XXXX-XXX'),
            'COMPANY_ADDRESS': site_config.company_address or getattr(settings, 'COMPANY_ADDRESS', 'London, United Kingdom'),
            'COMPANY_WEBSITE': site_config.company_website or getattr(settings, 'COMPANY_WEBSITE', 'https://elitewealthcapita.uk'),
            'SUPPORT_EMAIL': site_config.support_email or getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapita.uk'),
            'COMPANY_DESCRIPTION': 'Your trusted partner in wealth management and investment solutions',
        }
    except Exception:
        # Fallback to settings.py constants
        return {
            'SITE_NAME': 'Elite Wealth Capital',
            'COMPANY_NAME': 'Elite Wealth Capital',
            'COMPANY_EMAIL': getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapita.uk'),
            'COMPANY_PHONE': getattr(settings, 'COMPANY_PHONE', '+44-XXX-XXXX-XXX'),
            'COMPANY_ADDRESS': getattr(settings, 'COMPANY_ADDRESS', 'London, United Kingdom'),
            'COMPANY_WEBSITE': getattr(settings, 'COMPANY_WEBSITE', 'https://elitewealthcapita.uk'),
            'SUPPORT_EMAIL': getattr(settings, 'COMPANY_EMAIL', 'admin@elitewealthcapita.uk'),
            'COMPANY_DESCRIPTION': 'Your trusted partner in wealth management and investment solutions',
        }


def tawk_settings(request):
    """
    Tawk.to chat widget configuration
    Uses hardcoded defaults if environment variables are not set
    """
    # Default Tawk.to credentials (fallback if env vars empty)
    # From: https://tawk.to/chat/69c1f2a729e9681c3d64de5d/1jkepnodo
    DEFAULT_PROPERTY_ID = '69c1f2a729e9681c3d64de5d'
    DEFAULT_WIDGET_ID = '1jkepnodo'
    
    property_id = getattr(settings, 'TAWK_PROPERTY_ID', '') or DEFAULT_PROPERTY_ID
    widget_id = getattr(settings, 'TAWK_WIDGET_ID', '') or DEFAULT_WIDGET_ID
    
    return {
        'TAWK_PROPERTY_ID': property_id,
        'TAWK_WIDGET_ID': widget_id,
        'TAWK_ENABLED': bool(property_id),
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


def page_type(request):
    """
    Detect page type based on URL path for conditional rendering
    Dashboard and admin pages get is_dashboard=True to hide landing page elements
    """
    path = request.path.lower()
    is_dashboard = path.startswith('/dashboard/') or path.startswith('/investments/') or path.startswith('/kyc/')
    is_admin_page = path.startswith('/dashboard/admin/')
    
    return {
        'is_dashboard': is_dashboard,
        'is_admin_page': is_admin_page,
    }
