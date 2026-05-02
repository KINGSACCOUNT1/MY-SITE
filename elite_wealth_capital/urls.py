"""
URL Configuration for Elite Wealth Capital
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from dashboard import views as dashboard_views
from investments.admin_api import verify_deposit_from_email, reject_deposit_from_email
import os

# PWA file serving views
def serve_manifest(request):
    """Serve manifest.json from root for PWA"""
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    with open(manifest_path, 'r') as f:
        return HttpResponse(f.read(), content_type='application/manifest+json')

def serve_service_worker(request):
    """Serve service worker from root for proper scope"""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    with open(sw_path, 'r') as f:
        return HttpResponse(f.read(), content_type='application/javascript')

def offline_view(request):
    """Offline fallback page"""
    return HttpResponse('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline - Elite Wealth Capital</title>
        <style>
            body { font-family: 'Inter', sans-serif; background: #050B1A; color: white; 
                   display: flex; align-items: center; justify-content: center; 
                   min-height: 100vh; margin: 0; text-align: center; }
            .container { padding: 40px; }
            h1 { color: #FFD700; margin-bottom: 20px; }
            p { color: rgba(255,255,255,0.7); }
            button { background: #FFD700; color: #000; border: none; padding: 12px 30px;
                     border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>You're Offline</h1>
            <p>Please check your internet connection and try again.</p>
            <button onclick="location.reload()">Retry</button>
        </div>
    </body>
    </html>
    ''', content_type='text/html')

urlpatterns = [
    # PWA files (must be at root for iOS/Android)
    path('manifest.json', serve_manifest, name='manifest'),
    path('sw.js', serve_service_worker, name='service_worker'),
    path('offline/', offline_view, name='offline'),
    
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Admin API endpoints (for email one-click actions)
    path('admin-api/deposits/<int:deposit_id>/verify/<str:token>/', 
         verify_deposit_from_email, name='verify_deposit_email'),
    path('admin-api/deposits/<int:deposit_id>/reject/<str:token>/', 
         reject_deposit_from_email, name='reject_deposit_email'),
    
    # Homepage
    path('', dashboard_views.home, name='home'),
    
    # Authentication
    path('', include('accounts.urls')),
    
    # Dashboard
    path('dashboard/', include('dashboard.urls')),
    
    # Investments
    path('investments/', include('investments.urls')),
    
    # KYC
    path('kyc/', include('kyc.urls')),
    
    # Notifications
    path('notifications/', include('notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers (enabled for production)
handler404 = 'accounts.views.custom_404'
handler500 = 'accounts.views.custom_500'
