from django.urls import path
from . import views
from investments import views as inv_views

# Note: No app_name since dashboard URLs are included at root level
# This allows templates to use {% url 'terms' %} instead of {% url 'dashboard:terms' %}

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),
    path('reviews/', views.reviews, name='reviews'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('investment-plans/', views.investment_plans, name='investment_plans'),
    path('certificate/', views.certificate, name='certificate'),
    path('partners/', views.partners, name='partners'),
    path('global-presence/', views.global_presence, name='global_presence'),
    path('terms/', views.terms, name='terms'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('news/', views.news, name='news'),
    path('news/<slug:slug>/', views.news_article, name='news_article'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('us-services/', views.us_services, name='us_services'),
    path('dispute/', views.dispute, name='dispute'),
    
    # Authenticated user pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('referrals/', views.referrals, name='referrals'),
    path('referral-leaderboard/', views.referral_leaderboard, name='referral_leaderboard'),
    path('activity-log/', views.activity_log, name='activity_log'),
    path('transactions/', views.transactions, name='transactions'),
    path('export-transactions/', views.export_transactions, name='export_transactions'),
    
    # Admin panel
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/withdrawals/<uuid:pk>/approve/', views.admin_approve_withdrawal, name='admin_approve_withdrawal'),
    path('admin-panel/withdrawals/<uuid:pk>/reject/', views.admin_reject_withdrawal, name='admin_reject_withdrawal'),
    path('admin-panel/deposits/<uuid:pk>/confirm/', views.admin_confirm_deposit, name='admin_confirm_deposit'),
    path('admin-panel/deposits/<uuid:pk>/reject/', views.admin_reject_deposit, name='admin_reject_deposit'),
    path('admin-panel/kyc/<uuid:pk>/approve/', views.admin_approve_kyc, name='admin_approve_kyc'),
    path('admin-panel/kyc/<uuid:pk>/reject/', views.admin_reject_kyc, name='admin_reject_kyc'),
    path('admin-panel/loans/<uuid:pk>/approve/', views.admin_approve_loan, name='admin_approve_loan'),
    path('admin-panel/loans/<uuid:pk>/reject/', views.admin_reject_loan, name='admin_reject_loan'),
    
    # User financial pages (convenient short URLs)
    path('add-funds/', inv_views.deposit, name='add_funds'),
    path('deposit-status/<uuid:deposit_id>/', inv_views.deposit_status, name='deposit_status'),
    path('api/deposit-status/<uuid:deposit_id>/', inv_views.check_deposit_status, name='check_deposit_status'),
    path('withdraw/', inv_views.withdraw, name='withdraw'),
    path('invest/', inv_views.invest_page, name='invest'),
    path('loans/', inv_views.loans_page, name='loans'),
    path('cards/', inv_views.cards_page, name='cards'),
    path('upgrade/', inv_views.upgrade_page, name='upgrade'),
    path('agent-application/', inv_views.agent_application_page, name='agent_application'),
    
    # Receipt downloads
    path('receipt/<str:receipt_type>/<uuid:transaction_id>/', inv_views.download_receipt, name='download_receipt'),
]
