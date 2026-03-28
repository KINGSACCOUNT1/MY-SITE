"""Elite Wealth Capital URL Configuration."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.static import serve
import os
from accounts import views as accounts_views

# Admin customization
admin.site.site_header = 'Elite Wealth Capital Admin'
admin.site.site_title = 'Elite Wealth Capital'
admin.site.index_title = 'Admin Dashboard'


def serve_google_verification(request):
    """Serve Google Search Console verification file."""
    content = "google-site-verification: google7e9d2dd92a8559d2.html"
    return HttpResponse(content, content_type='text/html')


def serve_robots_txt(request):
    """Serve robots.txt from static folder."""
    robots_path = os.path.join(settings.BASE_DIR, 'static', 'robots.txt')
    with open(robots_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/plain')


def serve_sitemap_xml(request):
    """Serve sitemap.xml from static folder."""
    sitemap_path = os.path.join(settings.BASE_DIR, 'static', 'sitemap.xml')
    with open(sitemap_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/xml')


urlpatterns = [
    # Google Search Console verification
    path('google7e9d2dd92a8559d2.html', serve_google_verification, name='google_verification'),
    
    # SEO files at root
    path('robots.txt', serve_robots_txt, name='robots_txt'),
    path('sitemap.xml', serve_sitemap_xml, name='sitemap_xml'),
    
    # Django Admin (for staff/superusers)
    path('admin/', admin.site.urls),
    
    # Authentication URLs (at root level for convenience)
    path('login/', accounts_views.login_view, name='login'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('signup/', accounts_views.signup_view, name='signup'),
    path('forgot-password/', accounts_views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', accounts_views.reset_password, name='reset_password_token'),
    path('verify-email/', accounts_views.verify_email, name='verify_email'),
    path('verify-email/<str:token>/', accounts_views.verify_email, name='verify_email_token'),
    
    # Apps (includes /accounts/ routes)
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('investments/', include('investments.urls')),
    path('kyc/', include('kyc.urls')),
    path('notifications/', include('notifications.urls')),
    # path('messaging/', include('messaging.urls')),  # Commented out - messaging app not configured
    
    # REST API - commented out until rest_framework is installed
    # path('api/v1/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Custom error handlers
handler404 = 'dashboard.views.error_404'
handler500 = 'dashboard.views.error_500'

