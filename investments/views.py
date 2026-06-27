from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta
import hashlib
import hmac
import json
import time
import logging
import urllib.request
import urllib.parse
from .models import (
    InvestmentPlan, Investment, Withdrawal, Deposit, WalletAddress,
    Loan, LoanRepayment, VirtualCard, Coupon, CouponUsage,
    AgentApplication, AccountUpgrade
)
from accounts.models import ActivityLog, CustomUser
from notifications.models import Notification
from core.validators import validate_uploaded_file
from core.utils import get_client_ip

logger = logging.getLogger(__name__)


# Bybit coin → chain type mapping for deposit addresses
_BYBIT_CHAIN_MAP = {
    'BTC':  ('BTC',  'BTC'),
    'ETH':  ('ETH',  'ERC20'),
    'USDT': ('USDT', 'TRC20'),
    'USDC': ('USDC', 'ERC20'),
    'LTC':  ('LTC',  'LTC'),
}


def _bybit_get_deposit_address(coin: str, chain_type: str) -> dict | None:
    """
    Fetch a deposit address from Bybit v5 API (authenticated).
    Returns the address dict or None if unavailable / not configured.
    """
    api_key = getattr(settings, 'BYBIT_API_KEY', '')
    api_secret = getattr(settings, 'BYBIT_API_SECRET', '')
    if not api_key or not api_secret:
        logger.debug('Bybit API credentials not configured — skipping deposit address fetch for %s/%s', coin, chain_type)
        return None

    recv_window = '5000'
    timestamp = str(int(time.time() * 1000))
    params = {'coin': coin, 'chainType': chain_type}
    query_string = urllib.parse.urlencode(params)

    # Signature: timestamp + api_key + recv_window + queryString
    sign_payload = f'{timestamp}{api_key}{recv_window}{query_string}'
    signature = hmac.new(
        api_secret.encode('utf-8'),
        sign_payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    url = f'https://api.bybit.com/v5/asset/deposit/query-address?{query_string}'
    bybit_request = urllib.request.Request(url)
    bybit_request.add_header('X-BAPI-API-KEY', api_key)
    bybit_request.add_header('X-BAPI-SIGN', signature)
    bybit_request.add_header('X-BAPI-TIMESTAMP', timestamp)
    bybit_request.add_header('X-BAPI-RECV-WINDOW', recv_window)
    bybit_request.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(bybit_request, timeout=10) as http_response:
            response_json = json.loads(http_response.read().decode('utf-8'))
        if response_json.get('retCode') == 0:
            return response_json.get('result', {})
    except Exception as exc:
        logger.warning('Bybit deposit address fetch failed for %s/%s: %s', coin, chain_type, exc)
    return None


@login_required
def wallet_addresses_api(request):
    """
    JSON endpoint that returns active deposit wallet addresses.
    Prefers live addresses fetched from Bybit; falls back to the
    WalletAddress records managed in the Django admin.
    """
    wallet_addresses = []
    for crypto_type, (coin, chain) in _BYBIT_CHAIN_MAP.items():
        bybit_data = _bybit_get_deposit_address(coin, chain)
        if bybit_data:
            # Try top-level 'address' first; fall back to depositAddressList
            address = bybit_data.get('address', '')
            if not address:
                deposit_list = bybit_data.get('depositAddressList', [])
                address = deposit_list[0].get('address', '') if deposit_list else ''
            if address:
                wallet_addresses.append({
                    'symbol': crypto_type,
                    'name': {'BTC': 'Bitcoin', 'ETH': 'Ethereum',
                              'USDT': 'Tether USDT', 'USDC': 'USD Coin',
                              'LTC': 'Litecoin'}.get(crypto_type, crypto_type),
                    'address': address,
                    'network': chain,
                    'qr_code_url': f'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={address}',
                    'source': 'bybit',
                })
                continue

        # Fallback: use the admin-managed WalletAddress records
        wallet = WalletAddress.objects.filter(crypto_type=crypto_type, is_active=True).first()
        if wallet:
            wallet_addresses.append({
                'symbol': crypto_type,
                'name': wallet.get_crypto_type_display(),
                'address': wallet.address,
                'network': chain,
                'qr_code_url': (
                    wallet.qr_code.url if wallet.qr_code
                    else f'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={wallet.address}'
                ),
                'source': 'db',
            })

    return JsonResponse({'success': True, 'wallets': wallet_addresses})


def plans_list(request):
    """Display all investment plans."""
    plans = InvestmentPlan.objects.filter(is_active=True).order_by('sort_order')
    return render(request, 'investment-plans.html', {'plans': plans})


@login_required
def invest_page(request):
    """Show investment page with all plans to choose from."""
    plans = InvestmentPlan.objects.filter(is_active=True).order_by('sort_order')
    return render(request, 'invest.html', {
        'plans': plans,
        'user': request.user
    })


@login_required
def create_investment(request):
    """Create investment from general invest page (handles form POST)."""
    if request.method != 'POST':
        return redirect('invest')
    
    plan_id = request.POST.get('plan')
    if not plan_id:
        messages.error(request, 'Please select an investment plan.')
        return redirect('invest')
    
    try:
        plan = InvestmentPlan.objects.get(id=plan_id, is_active=True)
    except InvestmentPlan.DoesNotExist:
        messages.error(request, 'Invalid investment plan selected.')
        return redirect('invest')
    
    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except (ValueError, TypeError, InvalidOperation):
        messages.error(request, 'Invalid amount.')
        return redirect('invest')
    
    # Validate amount
    if amount < plan.min_amount:
        messages.error(request, f'Minimum investment for {plan.name} is ${plan.min_amount:,.2f}')
        return redirect('invest')
    
    if amount > plan.max_amount:
        messages.error(request, f'Maximum investment for {plan.name} is ${plan.max_amount:,.2f}')
        return redirect('invest')
    
    if amount > request.user.balance:
        messages.error(request, f'Insufficient balance. Your balance is ${request.user.balance:,.2f}')
        return redirect('invest')
    
    # Create investment
    expected_profit = amount * (plan.daily_roi / 100) * plan.duration_days
    end_date = timezone.now() + timedelta(days=plan.duration_days)
    
    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
        # Re-check balance after acquiring lock
        if amount > user.balance:
            messages.error(request, f'Insufficient balance. Your balance is ${user.balance:,.2f}')
            return redirect('invest')
        investment = Investment.objects.create(
            user=user,
            plan=plan,
            amount=amount,
            expected_profit=expected_profit,
            end_date=end_date
        )
        user.balance -= amount
        user.invested_amount += amount
        user.save()
    request.user.refresh_from_db()
    
    # Log activity
    ActivityLog.objects.create(
        user=request.user,
        action='investment',
        description=f'Invested ${amount:,.2f} in {plan.name}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Create notification
    Notification.objects.create(
        user=request.user,
        notification_type='success',
        title='Investment Created',
        message=f'You invested ${amount:,.2f} in {plan.name}. Expected profit: ${expected_profit:,.2f}'
    )
    
    messages.success(request, f'Successfully invested ${amount:,.2f} in {plan.name}! Expected profit: ${expected_profit:,.2f}')
    return redirect('dashboard')


@login_required
def invest(request, plan_id):
    """Create new investment in a specific plan."""
    plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid amount.')
            return redirect('investments:invest', plan_id=plan_id)
        
        # Validate amount
        if amount < plan.min_amount:
            messages.error(request, f'Minimum investment is ${plan.min_amount:,.2f}')
            return redirect('investments:invest', plan_id=plan_id)
        
        if amount > plan.max_amount:
            messages.error(request, f'Maximum investment is ${plan.max_amount:,.2f}')
            return redirect('investments:invest', plan_id=plan_id)
        
        if amount > request.user.balance:
            messages.error(request, 'Insufficient balance. Please make a deposit first.')
            return redirect('add_funds')
        
        # Create investment
        expected_profit = amount * (plan.daily_roi / 100) * plan.duration_days
        end_date = timezone.now() + timedelta(days=plan.duration_days)
        
        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
            # Re-check balance after acquiring lock
            if amount > user.balance:
                messages.error(request, 'Insufficient balance. Please make a deposit first.')
                return redirect('add_funds')
            investment = Investment.objects.create(
                user=user,
                plan=plan,
                amount=amount,
                expected_profit=expected_profit,
                end_date=end_date
            )
            user.balance -= amount
            user.invested_amount += amount
            user.save()
        request.user.refresh_from_db()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='investment',
            description=f'Invested ${amount:,.2f} in {plan.name}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            notification_type='success',
            title='Investment Created',
            message=f'You invested ${amount:,.2f} in {plan.name}. Expected profit: ${expected_profit:,.2f}'
        )
        
        messages.success(request, f'Successfully invested ${amount:,.2f} in {plan.name}!')
        return redirect('dashboard')
    
    return render(request, 'invest.html', {
        'plan': plan,
        'plans': InvestmentPlan.objects.filter(is_active=True).order_by('sort_order'),
        'user': request.user
    })


@login_required
def my_investments(request):
    """Display user's investments."""
    investments = Investment.objects.filter(user=request.user).order_by('-start_date')
    active_investments = investments.filter(status='active')
    completed_investments = investments.filter(status='completed')
    
    context = {
        'investments': investments,
        'active_investments': active_investments,
        'completed_investments': completed_investments,
    }
    return render(request, 'investments/my_investments.html', context)


@login_required
def deposit(request):
    """Deposit funds page."""
    wallets = WalletAddress.objects.filter(is_active=True)
    
    # Group wallets by crypto type
    wallets_by_crypto = {}
    for wallet in wallets:
        wallets_by_crypto[wallet.crypto_type] = wallet
    
    # Get user's pending deposits to show status
    pending_deposits = Deposit.objects.filter(user=request.user, status='pending').order_by('-created_at')
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid amount.')
            return redirect('add_funds')
        
        crypto_type = request.POST.get('crypto_type')
        tx_hash = request.POST.get('tx_hash', '').strip()
        proof_image = request.FILES.get('proof_image')
        
        # Validate proof image
        if proof_image:
            try:
                proof_image = validate_uploaded_file(proof_image, 'Proof Image')
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('add_funds')
        
        min_dep = getattr(settings, 'MIN_DEPOSIT', 10)
        if amount < Decimal(str(min_dep)):
            messages.error(request, f'Minimum deposit is ${min_dep}')
            return redirect('add_funds')
        
        if crypto_type not in ['BTC', 'ETH', 'USDT', 'USDC', 'LTC']:
            messages.error(request, 'Invalid cryptocurrency selected.')
            return redirect('add_funds')
        
        deposit_obj = Deposit.objects.create(
            user=request.user,
            amount=amount,
            crypto_type=crypto_type,
            tx_hash=tx_hash,
            proof_image=proof_image
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='deposit_request',
            description=f'Deposit request of ${amount:,.2f} {crypto_type}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Notify user
        Notification.objects.create(
            user=request.user,
            notification_type='info',
            title='Deposit Submitted',
            message=f'Your deposit of ${amount:,.2f} {crypto_type} is pending confirmation. We will notify you once verified.'
        )
        
        # Send email notification to admin for verification
        try:
            from notifications.email_service import notify_admin_new_deposit
            notify_admin_new_deposit(deposit_obj)
        except Exception as e:
            # Log error but don't block user flow
            logger.error(f"Failed to send admin deposit notification: {e}")
        
        # Redirect to deposit status page
        return redirect('deposit_status', deposit_id=deposit_obj.id)
    
    context = {
        'wallets': wallets,
        'wallets_by_crypto': wallets_by_crypto,
        'crypto_choices': Deposit.CRYPTO_CHOICES,
        'pending_deposits': pending_deposits,
    }
    return render(request, 'add-funds.html', context)


@login_required
def deposit_status(request, deposit_id):
    """Show deposit status page with spinning animation until confirmed."""
    deposit = get_object_or_404(Deposit, id=deposit_id, user=request.user)
    return render(request, 'deposit-status.html', {'deposit': deposit})


@login_required
def check_deposit_status(request, deposit_id):
    """API endpoint to check deposit status (for AJAX polling)."""
    from django.http import JsonResponse
    deposit = get_object_or_404(Deposit, id=deposit_id, user=request.user)
    return JsonResponse({
        'status': deposit.status,
        'amount': float(deposit.amount),
        'confirmed': deposit.status == 'confirmed',
        'rejected': deposit.status == 'rejected',
    })


@login_required
def withdraw(request):
    """Request withdrawal. Requires verified KYC."""
    if request.method == 'POST':
        # KYC gate: only verified users can withdraw
        if request.user.kyc_status != 'verified':
            messages.error(
                request,
                'Identity verification (KYC) is required before you can withdraw. '
                'Please submit your documents and wait for approval.'
            )
            return redirect('kyc:upload')

        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid amount.')
            return redirect('withdraw')
        
        # Get withdrawal method (crypto or bank)
        withdrawal_method = request.POST.get('withdrawal_method', 'crypto').strip().lower()
        
        # Get method-specific fields
        if withdrawal_method == 'crypto':
            crypto_type = request.POST.get('crypto_type', '').strip()
            wallet_address = request.POST.get('wallet_address', '').strip()
            bank_name = ''
            account_number = ''
            account_name = ''
        else:  # bank transfer
            crypto_type = ''
            wallet_address = ''
            bank_name = request.POST.get('bank_name', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            account_name = request.POST.get('account_name', '').strip()
        
        min_with = getattr(settings, 'MIN_WITHDRAWAL', 10)
        if amount < Decimal(str(min_with)):
            messages.error(request, f'Minimum withdrawal is ${min_with}')
            return redirect('withdraw')
        
        if amount > request.user.balance:
            messages.error(request, f'Insufficient balance. Your balance is ${request.user.balance:,.2f}')
            return redirect('withdraw')
        
        # Validate based on withdrawal method
        if withdrawal_method == 'crypto':
            if crypto_type not in ['BTC', 'ETH', 'USDT', 'USDC', 'LTC']:
                messages.error(request, 'Invalid cryptocurrency selected.')
                return redirect('withdraw')
            
            if not wallet_address:
                messages.error(request, 'Please enter your wallet address.')
                return redirect('withdraw')
        elif withdrawal_method == 'bank':
            if not bank_name or not account_number or not account_name:
                messages.error(request, 'Please provide all bank account details.')
                return redirect('withdraw')
        else:
            messages.error(request, 'Invalid withdrawal method.')
            return redirect('withdraw')
        
        # Create withdrawal request and deduct from balance atomically
        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
            # Re-check balance after acquiring lock
            if amount > user.balance:
                messages.error(request, f'Insufficient balance. Your balance is ${user.balance:,.2f}')
                return redirect('withdraw')
            withdrawal = Withdrawal.objects.create(
                user=user,
                amount=amount,
                withdrawal_method=withdrawal_method,
                crypto_type=crypto_type,
                wallet_address=wallet_address,
                bank_name=bank_name,
                account_number=account_number,
                account_name=account_name
            )
            # Deduct from balance (will be refunded if rejected)
            user.balance -= amount
            user.save()
        request.user.refresh_from_db()
        
        # Log activity
        withdrawal_destination = wallet_address[:20] if withdrawal_method == 'crypto' else f'{bank_name} ({account_number[-4:]})'
        ActivityLog.objects.create(
            user=request.user,
            action='withdrawal_request',
            description=f'Withdrawal request of ${amount:,.2f} via {withdrawal_method.upper()}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Notify user
        if withdrawal_method == 'crypto':
            message = f'Your withdrawal of ${amount:,.2f} to {wallet_address[:20]}... is pending approval.'
        else:
            message = f'Your withdrawal of ${amount:,.2f} to {bank_name} account ending in {account_number[-4:]} is pending approval.'
            
        Notification.objects.create(
            user=request.user,
            notification_type='info',
            title='Withdrawal Requested',
            message=message
        )
        
        # Send email notification to admin for processing
        try:
            from notifications.email_service import notify_admin_new_withdrawal
            notify_admin_new_withdrawal(withdrawal)
        except Exception as e:
            logger.error(f"Failed to send admin withdrawal notification: {e}")
        
        messages.success(request, 'Withdrawal requested! Awaiting admin approval.')
        return redirect('dashboard')
    
    context = {
        'user': request.user,
        'crypto_choices': Withdrawal.CRYPTO_CHOICES,
        'kyc_verified': request.user.kyc_status == 'verified',
        'kyc_status': request.user.kyc_status,
    }
    return render(request, 'withdraw.html', context)


# ============== LOAN VIEWS ==============

@login_required
def loans_page(request):
    """Display loans page and apply for loan."""
    user_loans = Loan.objects.filter(user=request.user).order_by('-created_at')
    active_loan = user_loans.filter(status__in=['approved', 'disbursed', 'repaying']).first()
    
    if request.method == 'POST':
        # Check if user already has active loan
        if active_loan:
            messages.error(request, 'You already have an active loan. Please repay it first.')
            return redirect('loans')
        
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            duration_days = int(request.POST.get('duration', '30'))
        except (ValueError, TypeError, Exception) as e:
            messages.error(request, 'Invalid loan details.')
            return redirect('loans')
        
        purpose = request.POST.get('purpose', '').strip()
        
        # Validate
        if amount < Decimal('100'):
            messages.error(request, 'Minimum loan amount is $100')
            return redirect('loans')
        
        if amount > Decimal('50000'):
            messages.error(request, 'Maximum loan amount is $50,000')
            return redirect('loans')
        
        if duration_days not in [30, 60, 90, 180, 365]:
            messages.error(request, 'Invalid loan duration.')
            return redirect('loans')
        
        # Create loan application
        loan = Loan.objects.create(
            user=request.user,
            amount=amount,
            duration_days=duration_days,
            purpose=purpose,
            interest_rate=Decimal('5.0')  # 5% monthly
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='loan_application',
            description=f'Applied for ${amount:,.2f} loan for {duration_days} days',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Notify user
        Notification.objects.create(
            user=request.user,
            notification_type='info',
            title='Loan Application Submitted',
            message=f'Your loan application for ${amount:,.2f} is under review.'
        )
        
        messages.success(request, 'Loan application submitted! You will be notified once reviewed.')
        return redirect('loans')
    
    context = {
        'user': request.user,
        'loans': user_loans,
        'active_loan': active_loan,
        'duration_choices': Loan.DURATION_CHOICES,
    }
    return render(request, 'loans.html', context)


@login_required
def repay_loan(request, loan_id):
    """Repay loan from balance."""
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)
    
    if loan.status not in ['disbursed', 'repaying']:
        messages.error(request, 'This loan cannot be repaid.')
        return redirect('loans')
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid amount.')
            return redirect('loans')
        
        if amount <= 0:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('loans')
        
        if amount > request.user.balance:
            messages.error(request, 'Insufficient balance.')
            return redirect('loans')
        
        remaining_loan_balance = loan.remaining_balance
        if amount > remaining_loan_balance:
            amount = remaining_loan_balance  # Cap at remaining balance
        
        # Process repayment with proper locking
        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
            loan = Loan.objects.select_for_update().get(pk=loan_id, user=user)
            
            # Recheck balance after lock
            if amount > user.balance:
                messages.error(request, 'Insufficient balance.')
                return redirect('loans')
            
            user.balance -= amount
            user.save()
            
            loan.amount_repaid += amount
            if loan.is_fully_repaid:
                loan.status = 'completed'
            else:
                loan.status = 'repaying'
            loan.save()
        
        # Create repayment record
        LoanRepayment.objects.create(
            loan=loan,
            amount=amount,
            payment_method='balance'
        )
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='loan_repayment',
            description=f'Repaid ${amount:,.2f} on loan',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        if loan.is_fully_repaid:
            messages.success(request, 'Congratulations! Your loan has been fully repaid.')
            Notification.objects.create(
                user=request.user,
                notification_type='success',
                title='Loan Fully Repaid',
                message='Your loan has been completely repaid. Thank you!'
            )
        else:
            messages.success(request, f'Repayment of ${amount:,.2f} successful. Remaining: ${loan.remaining_balance:,.2f}')
        
        return redirect('loans')
    
    return redirect('loans')


# ============== VIRTUAL CARD VIEWS ==============

@login_required
def cards_page(request):
    """Display virtual cards page."""
    user_cards = VirtualCard.objects.filter(user=request.user).order_by('-created_at')
    active_card = user_cards.filter(status='active').first()
    pending_card = user_cards.filter(status='pending').first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'request_card':
            # Check if user already has pending or active card
            if pending_card:
                messages.info(request, 'You already have a card request pending approval.')
                return redirect('cards')
            
            if active_card:
                messages.info(request, 'You already have an active card.')
                return redirect('cards')
            
            card_type = request.POST.get('card_type', 'standard')
            card_holder_name = request.POST.get('card_holder_name', request.user.full_name)
            billing_address = request.POST.get('billing_address', '')
            
            # Create card request
            card = VirtualCard.objects.create(
                user=request.user,
                card_type=card_type,
                card_holder_name=card_holder_name,
                billing_address=billing_address
            )
            
            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='card_request',
                description=f'Requested {card_type} virtual card',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            Notification.objects.create(
                user=request.user,
                notification_type='info',
                title='Card Requested',
                message='Your virtual card request is being processed.'
            )
            
            messages.success(request, 'Virtual card requested! You will be notified once approved.')
            return redirect('cards')
        
        elif action == 'fund_card':
            if not active_card:
                messages.error(request, 'No active card to fund.')
                return redirect('cards')
            
            try:
                amount = Decimal(request.POST.get('amount', '0'))
            except (ValueError, TypeError, InvalidOperation):
                messages.error(request, 'Invalid amount.')
                return redirect('cards')
            
            if amount <= 0:
                messages.error(request, 'Please enter a valid amount.')
                return redirect('cards')
            
            if amount > request.user.balance:
                messages.error(request, 'Insufficient balance.')
                return redirect('cards')
            
            # Transfer from balance to card with proper locking
            with transaction.atomic():
                user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
                card = VirtualCard.objects.select_for_update().get(pk=active_card.pk)
                
                # Recheck balance after lock
                if amount > user.balance:
                    messages.error(request, 'Insufficient balance.')
                    return redirect('cards')
                
                user.balance -= amount
                user.save()
                card.balance += amount
                card.save()
                
                # Update active_card reference for activity log
                active_card = card
            
            ActivityLog.objects.create(
                user=request.user,
                action='card_funding',
                description=f'Funded card with ${amount:,.2f}',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Successfully added ${amount:,.2f} to your card.')
            return redirect('cards')
        
        elif action == 'freeze_card':
            card_id = request.POST.get('card_id')
            card = get_object_or_404(VirtualCard, id=card_id, user=request.user, status='active')
            card.status = 'frozen'
            card.save()
            messages.success(request, 'Card frozen successfully.')
            return redirect('cards')
        
        elif action == 'unfreeze_card':
            card_id = request.POST.get('card_id')
            card = get_object_or_404(VirtualCard, id=card_id, user=request.user, status='frozen')
            card.status = 'active'
            card.save()
            messages.success(request, 'Card unfrozen successfully.')
            return redirect('cards')
    
    context = {
        'user': request.user,
        'cards': user_cards,
        'active_card': active_card,
        'pending_card': pending_card,
        'card_type_choices': VirtualCard.CARD_TYPE_CHOICES,
    }
    return render(request, 'cards.html', context)


# ============== COUPON VIEWS ==============

@login_required
def apply_coupon(request):
    """Apply coupon code (AJAX endpoint)."""
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    code = request.POST.get('code', '').strip().upper()
    amount = Decimal(request.POST.get('amount', '0'))
    
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code'})
    
    if not coupon.is_valid:
        return JsonResponse({'success': False, 'message': 'Coupon is expired or no longer valid'})
    
    if amount < coupon.min_deposit:
        return JsonResponse({'success': False, 'message': f'Minimum deposit for this coupon is ${coupon.min_deposit}'})
    
    # Check user usage
    user_usage = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
    if user_usage >= coupon.uses_per_user:
        return JsonResponse({'success': False, 'message': 'You have already used this coupon'})
    
    # Calculate discount
    if coupon.discount_type == 'percentage':
        discount = amount * (coupon.discount_value / 100)
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
    elif coupon.discount_type == 'fixed':
        discount = coupon.discount_value
    else:  # bonus
        discount = coupon.discount_value
    
    return JsonResponse({
        'success': True,
        'discount': float(discount),
        'discount_type': coupon.discount_type,
        'message': f'Coupon applied! You get ${discount:.2f} {"bonus" if coupon.discount_type == "bonus" else "off"}'
    })


# ============== UPGRADE VIEWS ==============

@login_required
def upgrade_page(request):
    """Account upgrade page."""
    current_tier = request.user.account_type
    upgrade_history = AccountUpgrade.objects.filter(user=request.user).order_by('-created_at')
    pending_upgrade = upgrade_history.filter(status__in=['pending', 'paid']).first()
    
    # Define tier benefits
    tiers = {
        'beginner': {'price': 0, 'benefits': ['Basic ROI', 'Email support', 'Standard withdrawals']},
        'intermediate': {'price': 500, 'benefits': ['5% higher ROI', 'Priority support', 'Weekly market insights']},
        'advanced': {'price': 2000, 'benefits': ['10% higher ROI', '24/7 support', 'Daily insights', 'Lower fees']},
        'vip': {'price': 10000, 'benefits': ['15% higher ROI', 'Personal manager', 'Exclusive plans', 'Zero fees', 'VIP events']},
    }
    
    if request.method == 'POST':
        if pending_upgrade:
            messages.info(request, 'You already have a pending upgrade request.')
            return redirect('upgrade')
        
        requested_tier = request.POST.get('tier')
        payment_method = request.POST.get('payment_method', 'balance')
        
        if requested_tier not in ['intermediate', 'advanced', 'vip']:
            messages.error(request, 'Invalid tier selected.')
            return redirect('upgrade')
        
        tier_order = ['beginner', 'intermediate', 'advanced', 'vip']
        if tier_order.index(requested_tier) <= tier_order.index(current_tier):
            messages.error(request, 'You can only upgrade to a higher tier.')
            return redirect('upgrade')
        
        amount = Decimal(str(tiers[requested_tier]['price']))
        
        if payment_method == 'balance':
            # Deduct from balance with proper locking
            with transaction.atomic():
                user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
                
                # Recheck balance after lock
                if user.balance < amount:
                    messages.error(request, f'Insufficient balance. Need ${amount:,.2f}, have ${user.balance:,.2f}')
                    return redirect('upgrade')
                
                user.balance -= amount
                user.save()
            status = 'paid'
        else:
            status = 'pending'
        
        # Create upgrade request
        upgrade = AccountUpgrade.objects.create(
            user=request.user,
            current_tier=current_tier,
            requested_tier=requested_tier,
            amount=amount,
            payment_method=payment_method,
            status=status
        )
        
        ActivityLog.objects.create(
            user=request.user,
            action='upgrade_request',
            description=f'Requested upgrade to {requested_tier}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        Notification.objects.create(
            user=request.user,
            notification_type='info',
            title='Upgrade Requested',
            message=f'Your upgrade to {requested_tier.title()} is being processed.'
        )
        
        messages.success(request, 'Upgrade request submitted!')
        return redirect('upgrade')
    
    context = {
        'user': request.user,
        'current_tier': current_tier,
        'tiers': tiers,
        'upgrade_history': upgrade_history,
        'pending_upgrade': pending_upgrade,
    }
    return render(request, 'upgrade.html', context)


# ============== AGENT APPLICATION VIEWS ==============

@login_required
def agent_application_page(request):
    """Agent application page."""
    existing_application = AgentApplication.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        if existing_application:
            messages.info(request, 'You have already submitted an agent application.')
            return redirect('agent_application')
        
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        country = request.POST.get('country', '').strip()
        city = request.POST.get('city', '').strip()
        experience = request.POST.get('experience', '').strip()
        marketing_plan = request.POST.get('marketing_plan', '').strip()
        expected_referrals = request.POST.get('expected_referrals', '0')
        social_media_links = request.POST.get('social_media_links', '').strip()
        website = request.POST.get('website', '').strip()
        id_document = request.FILES.get('id_document')
        
        # Validate file upload
        if id_document:
            try:
                id_document = validate_uploaded_file(id_document, 'ID Document')
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('agent_application')
        
        # Validate required fields
        if not all([full_name, phone, country, city, experience, marketing_plan]):
            messages.error(request, 'Please fill all required fields.')
            return redirect('agent_application')
        
        try:
            expected_referrals = int(expected_referrals)
        except (ValueError, TypeError, Exception) as e:
            expected_referrals = 0
        
        # Create application
        application = AgentApplication.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            country=country,
            city=city,
            experience=experience,
            marketing_plan=marketing_plan,
            expected_referrals=expected_referrals,
            social_media_links=social_media_links,
            website=website,
            id_document=id_document
        )
        
        ActivityLog.objects.create(
            user=request.user,
            action='agent_application',
            description='Submitted agent application',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        Notification.objects.create(
            user=request.user,
            notification_type='info',
            title='Agent Application Submitted',
            message='Your agent application is under review. We will contact you soon.'
        )
        
        # Notify all admin users about new agent application
        admin_users = CustomUser.objects.filter(is_staff=True, is_active=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                notification_type='alert',
                title='New Agent Application',
                message=f'New agent application from {full_name} ({request.user.email}). Review at /admin/investments/agentapplication/',
                action_url='/admin/investments/agentapplication/'
            )
        
        messages.success(request, 'Agent application submitted successfully!')
        return redirect('agent_application')
    
    context = {
        'user': request.user,
        'existing_application': existing_application,
    }
    return render(request, 'agent-application.html', context)


# ============== RECEIPT VIEWS ==============

@login_required
def download_receipt(request, receipt_type, transaction_id):
    """Download PDF receipt for a transaction."""
    from django.http import HttpResponse
    from .receipt_generator import generate_deposit_receipt, generate_withdrawal_receipt, generate_investment_receipt
    
    try:
        if receipt_type == 'deposit':
            transaction = get_object_or_404(Deposit, id=transaction_id, user=request.user)
            pdf_buffer = generate_deposit_receipt(transaction)
            filename = f'deposit_receipt_{transaction_id}.pdf'
        elif receipt_type == 'withdrawal':
            transaction = get_object_or_404(Withdrawal, id=transaction_id, user=request.user)
            pdf_buffer = generate_withdrawal_receipt(transaction)
            filename = f'withdrawal_receipt_{transaction_id}.pdf'
        elif receipt_type == 'investment':
            transaction = get_object_or_404(Investment, id=transaction_id, user=request.user)
            pdf_buffer = generate_investment_receipt(transaction)
            filename = f'investment_receipt_{transaction_id}.pdf'
        else:
            messages.error(request, 'Invalid receipt type.')
            return redirect('transactions')
        
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        ActivityLog.objects.create(
            user=request.user,
            action='receipt_download',
            description=f'Downloaded {receipt_type} receipt #{transaction_id}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return response
        
    except Exception as e:
        messages.error(request, 'Could not generate receipt. Please try again.')
        return redirect('transactions')


# ===== PAYMENT GATEWAY VIEWS =====

@login_required
def process_stripe_payment(request):
    """Process Stripe payment for deposit."""
    from .payment_gateways import StripePaymentGateway
    from django.urls import reverse
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid amount.')
            return redirect('add_funds')
        
        min_dep = getattr(settings, 'MIN_DEPOSIT', 10)
        if amount < Decimal(str(min_dep)):
            messages.error(request, f'Minimum deposit is ${min_dep}')
            return redirect('add_funds')
        
        # Create payment intent
        success, result = StripePaymentGateway.create_payment_intent(
            amount=amount,
            currency='usd',
            metadata={
                'user_id': str(request.user.id),
                'user_email': request.user.email
            }
        )
        
        if success:
            # Store payment intent ID in session
            request.session['stripe_payment_intent_id'] = result['payment_intent_id']
            request.session['stripe_amount'] = str(amount)
            
            return render(request, 'payments/stripe_checkout.html', {
                'client_secret': result['client_secret'],
                'amount': amount,
                'stripe_public_key': os.getenv('STRIPE_PUBLIC_KEY')
            })
        else:
            messages.error(request, f"Payment failed: {result.get('error', 'Unknown error')}")
            return redirect('add_funds')
    
    return redirect('add_funds')


@login_required
def verify_stripe_payment(request):
    """Verify and confirm Stripe payment."""
    from .payment_gateways import StripePaymentGateway
    
    payment_intent_id = request.session.get('stripe_payment_intent_id')
    if not payment_intent_id:
        messages.error(request, 'Payment session expired.')
        return redirect('add_funds')
    
    success, result = StripePaymentGateway.verify_payment(payment_intent_id)
    
    if success and result['status'] == 'succeeded':
        amount = result['amount']
        
        # Create deposit record
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            crypto_type='USD',
            tx_hash=payment_intent_id,
            status='confirmed'
        )
        
        # Update user balance
        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
            user.balance += amount
            user.save()
        request.user.refresh_from_db()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='stripe_deposit',
            description=f'Stripe deposit of ${amount:,.2f}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Notify user
        Notification.objects.create(
            user=request.user,
            notification_type='success',
            title='Deposit Confirmed',
            message=f'Your Stripe deposit of ${amount:,.2f} has been confirmed.'
        )
        
        # Clear session
        del request.session['stripe_payment_intent_id']
        del request.session['stripe_amount']
        
        messages.success(request, f'Successfully deposited ${amount:,.2f} via Stripe!')
        return redirect('dashboard')
    else:
        messages.error(request, 'Payment verification failed.')
        return redirect('add_funds')


@login_required
def process_paypal_payment(request):
    """Initiate PayPal payment."""
    from .payment_gateways import PayPalPaymentGateway
    from django.urls import reverse
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, 'Invalid amount.')
            return redirect('add_funds')
        
        min_dep = getattr(settings, 'MIN_DEPOSIT', 10)
        if amount < Decimal(str(min_dep)):
            messages.error(request, f'Minimum deposit is ${min_dep}')
            return redirect('add_funds')
        
        # Create PayPal payment
        success, result = PayPalPaymentGateway.create_payment(
            amount=amount,
            currency='USD',
            return_url=request.build_absolute_uri(reverse('investments:execute_paypal_payment')),
            cancel_url=request.build_absolute_uri(reverse('add_funds')),
            description='Elite Wealth Capital - Investment Deposit'
        )
        
        if success and result.get('approval_url'):
            # Store payment ID in session
            request.session['paypal_payment_id'] = result['payment_id']
            request.session['paypal_amount'] = str(amount)
            
            # Redirect to PayPal for approval
            return redirect(result['approval_url'])
        else:
            messages.error(request, f"Payment failed: {result.get('error', 'Unknown error')}")
            return redirect('add_funds')
    
    return redirect('add_funds')


@login_required
def execute_paypal_payment(request):
    """Execute PayPal payment after user approval."""
    from .payment_gateways import PayPalPaymentGateway
    
    payment_id = request.session.get('paypal_payment_id')
    payer_id = request.GET.get('PayerID')
    
    if not payment_id or not payer_id:
        messages.error(request, 'Payment session expired or invalid.')
        return redirect('add_funds')
    
    success, result = PayPalPaymentGateway.execute_payment(payment_id, payer_id)
    
    if success and result['status'] == 'approved':
        amount = result['amount']
        
        # Create deposit record
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            crypto_type='USD',
            tx_hash=payment_id,
            status='confirmed'
        )
        
        # Update user balance
        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
            user.balance += amount
            user.save()
        request.user.refresh_from_db()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action='paypal_deposit',
            description=f'PayPal deposit of ${amount:,.2f}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Notify user
        Notification.objects.create(
            user=request.user,
            notification_type='success',
            title='Deposit Confirmed',
            message=f'Your PayPal deposit of ${amount:,.2f} has been confirmed.'
        )
        
        # Clear session
        del request.session['paypal_payment_id']
        del request.session['paypal_amount']
        
        messages.success(request, f'Successfully deposited ${amount:,.2f} via PayPal!')
        return redirect('dashboard')
    else:
        messages.error(request, 'Payment execution failed.')
        return redirect('add_funds')


@login_required
def verify_crypto_payment(request):
    """Verify cryptocurrency payment via Coinbase Commerce."""
    from .payment_gateways import CryptoPaymentGateway
    
    if request.method == 'POST':
        charge_id = request.POST.get('charge_id')
        
        if not charge_id:
            return JsonResponse({'success': False, 'error': 'Missing charge ID'})
        
        success, result = CryptoPaymentGateway.verify_charge(charge_id)
        
        if success:
            status = result['status']
            
            if status == 'COMPLETED':
                # Extract amount from pricing
                pricing = result.get('pricing', {})
                amount = Decimal(pricing.get('local', {}).get('amount', '0'))
                
                # Create deposit record
                deposit = Deposit.objects.create(
                    user=request.user,
                    amount=amount,
                    crypto_type='CRYPTO',
                    tx_hash=charge_id,
                    status='confirmed'
                )
                
                # Update user balance
                with transaction.atomic():
                    user = CustomUser.objects.select_for_update().get(pk=request.user.pk)
                    user.balance += amount
                    user.save()
                
                # Log activity
                ActivityLog.objects.create(
                    user=request.user,
                    action='crypto_deposit',
                    description=f'Crypto deposit of ${amount:,.2f}',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Notify user
                Notification.objects.create(
                    user=request.user,
                    notification_type='success',
                    title='Crypto Deposit Confirmed',
                    message=f'Your cryptocurrency deposit of ${amount:,.2f} has been confirmed.'
                )
                
                return JsonResponse({'success': True, 'status': 'confirmed', 'amount': float(amount)})
            else:
                return JsonResponse({'success': True, 'status': status.lower()})
        else:
            return JsonResponse({'success': False, 'error': result.get('error', 'Verification failed')})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
