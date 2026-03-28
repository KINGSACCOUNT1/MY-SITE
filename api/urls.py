"""
URL Configuration for REST API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'investment-plans', views.InvestmentPlanViewSet, basename='investmentplan')
router.register(r'investments', views.InvestmentViewSet, basename='investment')
router.register(r'deposits', views.DepositViewSet, basename='deposit')
router.register(r'withdrawals', views.WithdrawalViewSet, basename='withdrawal')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

app_name = 'api'

urlpatterns = [
    # JWT Authentication endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Balance and Stats endpoints
    path('balance/', views.BalanceView.as_view(), name='balance'),
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    
    # Router URLs
    path('', include(router.urls)),
]
