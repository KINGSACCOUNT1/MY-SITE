"""
URL Configuration for Elite Wealth Capital
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard import views as dashboard_views

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
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

# Custom error pages (will be implemented later)
# handler404 = 'accounts.views.custom_404'
# handler500 = 'accounts.views.custom_500'
