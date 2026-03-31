from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('profile/verify-2fa/', views.verify_2fa, name='verify_2fa'),
    
    # Password Reset
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Referrals
    path('referrals/', views.referral_dashboard, name='referrals'),
    path('referral-leaderboard/', views.referral_leaderboard, name='referral_leaderboard'),
]
