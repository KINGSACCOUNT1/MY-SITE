from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # User dashboard
    path('', views.dashboard, name='dashboard'),
    path('index/', views.dashboard, name='index'),
    path('overview/', views.user_dashboard, name='user_dashboard'),
    path('contact/', views.contact, name='contact'),
    path('dispute/', views.dispute, name='dispute'),
    path('settings/', views.settings_page, name='settings'),
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
    path('reviews-page/', views.reviews_page, name='reviews_page'),
    path('us-services/', views.us_services, name='us_services'),
    path('terms/', views.terms, name='terms'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('certificates-public/', views.certificates, name='certificates'),
    path('news/', views.news_list, name='news'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
]
