from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import CustomUser


class LoginForm(forms.Form):
    """User login form with account lockout protection."""
    email = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'autocomplete': 'email',
            'id': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'id': 'password'
        })
    )
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        password = self.cleaned_data.get('password')
        
        if email and password:
            # Check if account is locked
            try:
                user = CustomUser.objects.get(email=email)
                if user.locked_until and user.locked_until > timezone.now():
                    remaining = (user.locked_until - timezone.now()).seconds // 60
                    raise forms.ValidationError(
                        f'Account is locked. Try again in {remaining} minutes.'
                    )
            except CustomUser.DoesNotExist:
                pass
            
            # Authenticate
            self.user_cache = authenticate(self.request, email=email, password=password)
            
            if self.user_cache is None:
                # Track failed attempts
                try:
                    user = CustomUser.objects.get(email=email)
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
                    user.save()
                except CustomUser.DoesNotExist:
                    pass
                raise forms.ValidationError('Invalid email or password.')
            
            if not self.user_cache.is_active:
                raise forms.ValidationError('This account has been disabled.')
            
            # Reset failed attempts on successful login
            self.user_cache.failed_login_attempts = 0
            self.user_cache.locked_until = None
            self.user_cache.save()
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class SignupForm(forms.ModelForm):
    """User registration form with profile image upload."""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'new-password'
        }),
        validators=[validate_password]
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'autocomplete': 'new-password'
        })
    )
    referral_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Referral Code (Optional)'
        })
    )
    profile_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'phone', 'country', 'profile_image']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class ProfileForm(forms.ModelForm):
    """User profile update form."""
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone', 'country', 'profile_image']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


class ForgotPasswordForm(forms.Form):
    """Request password reset email."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'id': 'email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        # Don't reveal if email exists - return silently for security
        return email


class ResetPasswordForm(forms.Form):
    """Set new password after reset."""
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password',
            'id': 'password'
        }),
        validators=[validate_password]
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'id': 'confirmPassword'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data


class ChangePasswordForm(forms.Form):
    """Change password for logged-in user."""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Password'
        }),
        validators=[validate_password]
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current = self.cleaned_data.get('current_password')
        if self.user and not self.user.check_password(current):
            raise forms.ValidationError('Current password is incorrect.')
        return current
    
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('New passwords do not match.')
        
        return cleaned_data
