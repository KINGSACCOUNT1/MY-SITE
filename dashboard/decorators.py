"""
Security decorators for admin panel access control
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger('admin_actions')


def admin_only(view_func):
    """
    Decorator to restrict view access to admin/staff members only.
    Logs all admin access for security.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        
        if not request.user.is_staff:
            # Log unauthorized access attempt
            logger.warning(
                f'Unauthorized admin access attempt by {request.user.email} '
                f'from {request.META.get("REMOTE_ADDR")} to {request.path}'
            )
            raise PermissionDenied('You do not have permission to access this page.')
        
        # Log successful admin access
        logger.info(
            f'Admin access by {request.user.email} from {request.META.get("REMOTE_ADDR")} '
            f'to {request.path}'
        )
        
        return view_func(request, *args, **kwargs)
    return wrapper


def superuser_only(view_func):
    """
    Decorator to restrict view access to superusers only.
    More restrictive than admin_only - for sensitive operations.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        
        if not request.user.is_superuser:
            # Log unauthorized superuser access attempt
            logger.warning(
                f'Unauthorized superuser access attempt by {request.user.email} '
                f'(is_staff={request.user.is_staff}) from {request.META.get("REMOTE_ADDR")} '
                f'to {request.path}'
            )
            raise PermissionDenied('You do not have permission to access this page.')
        
        # Log successful superuser access
        logger.info(
            f'Superuser access by {request.user.email} from {request.META.get("REMOTE_ADDR")} '
            f'to {request.path}'
        )
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_admin_and_post(view_func):
    """
    Decorator combining admin check and POST method requirement.
    Useful for admin actions like approvals and rejections.
    """
    @wraps(view_func)
    @require_http_methods(["POST"])
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to perform this action.')
            return redirect('login')
        
        if not request.user.is_staff:
            logger.warning(
                f'Unauthorized admin POST attempt by {request.user.email} '
                f'from {request.META.get("REMOTE_ADDR")} to {request.path}'
            )
            raise PermissionDenied('You do not have permission to perform this action.')
        
        # Log admin action
        logger.info(
            f'Admin action by {request.user.email} (POST to {request.path}) '
            f'from {request.META.get("REMOTE_ADDR")}'
        )
        
        return view_func(request, *args, **kwargs)
    return wrapper


def log_admin_action(action_type, description=''):
    """
    Decorator to log admin actions with details.
    Usage: @log_admin_action('user_edit', 'Changed user role')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            result = view_func(request, *args, **kwargs)
            
            if request.user.is_authenticated and request.user.is_staff:
                logger.info(
                    f'Admin action: {action_type} | '
                    f'Admin: {request.user.email} | '
                    f'Description: {description} | '
                    f'Path: {request.path} | '
                    f'IP: {request.META.get("REMOTE_ADDR")}'
                )
            
            return result
        return wrapper
    return decorator
