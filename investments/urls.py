from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('plans/', views.plans_list, name='plans'),
    path('sectors/<str:sector>/', views.sector_page, name='sector'),
    path('invest/<int:plan_id>/', views.create_investment, name='invest'),
    path('my-investments/', views.my_investments, name='my_investments'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('loans/', views.loan_application, name='loans'),
    path('loans/<int:loan_id>/repay/', views.loan_repay, name='loan_repay'),
    path('cards/', views.virtual_cards, name='cards'),
    path('agent/', views.agent_page, name='agent'),
]
