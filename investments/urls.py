from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    # Investment plans listing
    path('plans/', views.plans_list, name='plans'),

    # Investment actions (API-style endpoints)
    path('invest/create/', views.create_investment, name='create_investment'),
    path('invest/<uuid:plan_id>/', views.invest, name='invest'),
    path('my-investments/', views.my_investments, name='my_investments'),

    # Wallet addresses API (admin-managed via Django admin)
    path('api/wallets/', views.wallet_addresses_api, name='wallet_addresses_api'),

    # Live crypto price ticker API (sourced from CoinGecko public API)
    path('api/ticker/', views.crypto_ticker_api, name='crypto_ticker_api'),

    # Loan repayment
    path('loans/<uuid:loan_id>/repay/', views.repay_loan, name='repay_loan'),

    # Coupons
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
]
