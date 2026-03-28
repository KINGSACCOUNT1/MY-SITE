from django.urls import path
from . import views, admin_views

app_name = 'dashboard'

urlpatterns = [
    # User dashboard
    path('', views.dashboard, name='dashboard'),
    path('overview/', views.user_dashboard, name='user_dashboard'),
    path('contact/', views.contact, name='contact'),
    path('export-transactions/', views.export_transactions_csv, name='export_transactions'),
    path('transactions/', views.transaction_history, name='transactions'),
    path('activity-log/', views.activity_log, name='activity_log'),
    
    # Dashboard subpages - Mobile optimized
    path('transactions-overview/', views.transactions_overview, name='transactions_overview'),
    path('certificates/', views.certificates_view, name='certificates_view'),
    path('upgrade/', views.upgrade_plans, name='upgrade_plans'),
    path('partners/', views.partner_integrations, name='partner_integrations'),
    path('testimonials/', views.testimonials_manage, name='testimonials_manage'),
    path('global/', views.global_presence_info, name='global_presence_info'),
    
    # Public pages
    path('about/', views.about, name='about'),
    path('faq/', views.faq, name='faq'),
    path('team/', views.team, name='team'),
    path('reviews/', views.reviews, name='reviews'),
    path('terms/', views.terms, name='terms'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('certificates-public/', views.certificates, name='certificates'),
    path('news/', views.news_list, name='news'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    
    # Admin panel - Dashboard
    path('admin-panel/', admin_views.admin_dashboard, name='admin_panel'),
    
    # Admin panel - User Management
    path('admin-panel/users/', admin_views.admin_users, name='admin_users'),
    path('admin-panel/users/<user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),
    
    # Admin panel - Content Management
    path('admin-panel/content/', admin_views.admin_content, name='admin_content'),
    path('admin-panel/content/edit/<int:article_id>/', admin_views.admin_content_edit, name='admin_content_edit'),
    path('admin-panel/content/new/', admin_views.admin_content_edit, name='admin_content_new'),
    
    # Admin panel - Analytics
    path('admin-panel/analytics/', admin_views.admin_analytics, name='admin_analytics'),
    path('admin-panel/analytics/data/', admin_views.analytics_data_json, name='analytics_data'),
    
    # Admin panel - Certificates
    path('admin-panel/certificates/', admin_views.admin_certificates, name='admin_certificates'),
    path('admin-panel/certificates/add/', admin_views.admin_certificate_add, name='admin_certificate_add'),
    path('admin-panel/certificates/<int:cert_id>/edit/', admin_views.admin_certificate_edit, name='admin_certificate_edit'),
    
    # Admin panel - Settings
    path('admin-panel/settings/', admin_views.admin_settings, name='admin_settings'),
    
    # Deposit management
    path('admin-panel/deposits/<int:pk>/confirm/', admin_views.confirm_deposit, name='confirm_deposit'),
    path('admin-panel/deposits/<int:pk>/reject/', admin_views.reject_deposit, name='reject_deposit'),
    
    # Withdrawal management
    path('admin-panel/withdrawals/<int:pk>/approve/', admin_views.approve_withdrawal, name='approve_withdrawal'),
    path('admin-panel/withdrawals/<int:pk>/reject/', admin_views.reject_withdrawal, name='reject_withdrawal'),
    
    # KYC management
    path('admin-panel/kyc/<int:pk>/approve/', admin_views.approve_kyc, name='approve_kyc'),
    path('admin-panel/kyc/<int:pk>/reject/', admin_views.reject_kyc, name='reject_kyc'),
    
    # Loan management
    path('admin-panel/loans/<int:pk>/approve/', admin_views.approve_loan, name='approve_loan'),
    path('admin-panel/loans/<int:pk>/reject/', admin_views.reject_loan, name='reject_loan'),
]
