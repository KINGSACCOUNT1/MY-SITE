"""
Custom authentication backend to allow login with email OR username
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with either
    their email address or a username field (if it exists).
    
    For admin users, also checks if input matches 'admin' as a shortcut.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        # Normalize input
        username = username.strip().lower()
        
        try:
            # Try to find user by email first
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # If not found by email, check if it's 'admin' shortcut for superuser
            if username == 'admin':
                try:
                    user = User.objects.get(is_superuser=True, email__icontains='admin')
                except User.DoesNotExist:
                    return None
                except User.MultipleObjectsReturned:
                    # Multiple admin accounts, try the first one
                    user = User.objects.filter(is_superuser=True, email__icontains='admin').first()
            else:
                # No user found
                return None
        
        # Check password and if user can authenticate
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
