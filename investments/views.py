from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import (InvestmentPlan, Investment, Deposit, Withdrawal, WalletAddress,
                     Loan, LoanRepayment, VirtualCard, Coupon, AgentApplication, CryptoTicker)
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from accounts.email_notifications import send_deposit_notification
import urllib.request
import json
import logging

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_uploaded_file(file_obj, field_name):
    """Validate uploaded file type and size."""
    if not file_obj:
        return
    
    # Check file size
    if file_obj.size > MAX_FILE_SIZE:
        raise ValidationError(f'{field_name} exceeds maximum size of 10MB')
    
    # Check file type
    if file_obj.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(f'{field_name} must be JPEG, PNG image or PDF')
    
    # Verify file by checking magic bytes
    file_obj.seek(0)
    header = file_obj.read(8)
    file_obj.seek(0)
    
    # JPEG starts with FF D8 FF, PNG starts with 89 50 4E 47, PDF starts with %PDF
    is_jpeg = header[:3] == b'\xff\xd8\xff'
    is_png = header[:8] == b'\x89PNG\r\n\x1a\n'
    is_pdf = header[:4] == b'%PDF'
    
    if not (is_jpeg or is_png or is_pdf):
        raise ValidationError(f'{field_name} is not a valid image or PDF file')


def plans_list(request):
    """List all investment plans"""
    plans = InvestmentPlan.objects.filter(is_active=True).order_by('sort_order')
    category = request.GET.get('category', None)
    if category:
        plans = plans.filter(category=category)
    return render(request, 'investments/plans.html', {'plans': plans, 'category': category})


def sector_page(request, sector):
    """Display sector-specific investment opportunities"""
    sector_map = {
        'crypto': 'crypto',
        'real-estate': 'real_estate',
        'oil-gas': 'oil_gas',
        'agriculture': 'agriculture',
        'solar': 'solar',
        'stocks': 'stocks',
    }
    
    category = sector_map.get(sector)
    if not category:
        messages.error(request, 'Invalid sector')
        return redirect('home')
    
    plans = InvestmentPlan.objects.filter(category=category, is_active=True).order_by('sort_order', 'min_amount')
    
    sector_info = {
        'crypto': {
            'title': 'Crypto Trading',
            'subtitle': 'Digital Asset Investment Opportunities',
            'description': 'Access our diversified cryptocurrency portfolio including Bitcoin mining, DeFi staking, and algorithmic trading strategies.',
            'icon': 'fab fa-bitcoin',
            'bg_image': 'crypto-bg.jpg',
        },
        'real_estate': {
            'title': 'Real Estate',
            'subtitle': 'Premium Property Investments',
            'description': 'Tokenized real estate opportunities in prime UK and US locations. From luxury residential to commercial developments.',
            'icon': 'fas fa-building',
            'bg_image': 'real-estate-luxury.jpg',
        },
        'oil_gas': {
            'title': 'Oil & Gas',
            'subtitle': 'Energy Sector Investments',
            'description': 'Strategic investments in North Sea drilling, Norwegian gas pipelines, and global energy commodities.',
            'icon': 'fas fa-oil-can',
            'bg_image': 'oil-rig.jpg',
        },
        'agriculture': {
            'title': 'Agriculture',
            'subtitle': 'Sustainable Farming & AgriTech',
            'description': 'Invest in organic farms, livestock operations, and cutting-edge agricultural technology ventures.',
            'icon': 'fas fa-seedling',
            'bg_image': 'land-o-lakes-inc-iFx1WMvjvpw-unsplash.jpg',
        },
        'solar': {
            'title': 'Solar Energy',
            'subtitle': 'Renewable Energy Projects',
            'description': 'Green investments in solar farms across Europe and Africa. Sustainable returns with environmental impact.',
            'icon': 'fas fa-solar-panel',
            'bg_image': 'solar-panels.jpg',
        },
        'stocks': {
            'title': 'Global Shares',
            'subtitle': 'International Stock Markets',
            'description': 'Diversified portfolio of blue-chip stocks, emerging markets, and precious metals across global exchanges.',
            'icon': 'fas fa-chart-line',
            'bg_image': 'stock-trading.jpg',
        },
    }
    
    context = {
        'sector': sector,
        'category': category,
        'plans': plans,
        'sector_info': sector_info.get(category, {}),
    }
    
    return render(request, 'investments/sector.html', context)



@login_required
def create_investment(request, plan_id):
    """Create new investment"""
    plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)
    
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str)
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero')
                return redirect('investments:invest', plan_id=plan_id)
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid amount entered')
            return redirect('investments:invest', plan_id=plan_id)
        
        # Validation
        if amount < plan.min_amount or amount > plan.max_amount:
            messages.error(request, f'Amount must be between ${plan.min_amount} and ${plan.max_amount}')
            return redirect('investments:invest', plan_id=plan_id)
        
        if amount > request.user.balance:
            messages.error(request, 'Insufficient balance. Please add funds first.')
            return redirect('investments:deposit')
        
        # Use atomic transaction for financial operations
        from django.db import transaction
        try:
            with transaction.atomic():
                # Lock the user row to prevent race conditions
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.select_for_update().get(pk=request.user.pk)
                
                # Double-check balance after lock
                if amount > user.balance:
                    messages.error(request, 'Insufficient balance.')
                    return redirect('investments:deposit')
                
                # Create investment
                investment = Investment.objects.create(
                    user=user,
                    plan=plan,
                    amount=amount
                )
                
                # Deduct from user balance
                user.balance -= amount
                user.invested_amount += amount
                user.save()
                
            messages.success(request, f'Investment of ${amount} created successfully!')
            return redirect('dashboard:dashboard')
        except Exception as e:
            logger.error(f'Investment creation error: {str(e)}')
            messages.error(request, 'An error occurred. Please try again.')
            return redirect('investments:invest', plan_id=plan_id)
    
    return render(request, 'investments/invest.html', {'plan': plan})


@login_required
def my_investments(request):
    """User's investment portfolio"""
    # Auto-check and update investments (no Celery needed!)
    from investments.utils import check_and_update_investments
    check_and_update_investments(request.user)
    
    investments = Investment.objects.filter(user=request.user).select_related('plan').order_by('-start_date')
    active_investments = investments.filter(status='active')
    completed_investments = investments.filter(status='completed')
    
    active_count = active_investments.count()
    completed_count = completed_investments.count()
    total_invested = sum(inv.amount for inv in active_investments)
    total_profit = sum(inv.actual_profit for inv in investments)
    
    return render(request, 'investments/my_investments.html', {
        'investments': investments,
        'active_count': active_count,
        'completed_count': completed_count,
        'total_invested': total_invested,
        'total_profit': total_profit,
    })


@login_required
def deposit_view(request):
    """Deposit funds"""
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str).quantize(Decimal('0.01'))
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero')
                return redirect('investments:deposit')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid amount entered')
            return redirect('investments:deposit')
        
        payment_method = request.POST.get('payment_method', 'crypto').lower()
        crypto_type = request.POST.get('crypto_type', '').upper()
        tx_hash = request.POST.get('transaction_hash', request.POST.get('tx_hash', ''))
        proof_image = request.FILES.get('proof_image', request.FILES.get('proof', None))
        
        if amount < 10:
            messages.error(request, 'Minimum deposit is $10')
            return redirect('investments:deposit')
        
        if amount > 1000000:
            messages.error(request, 'Maximum single deposit is $1,000,000')
            return redirect('investments:deposit')
        
        # Validate payment method
        if payment_method not in ['bank', 'crypto']:
            messages.error(request, 'Invalid payment method')
            return redirect('investments:deposit')
        
        # Validate crypto type if crypto payment
        valid_cryptos = ['BTC', 'ETH', 'USDT', 'USDC', 'LTC', 'BNB']
        if payment_method == 'crypto' and crypto_type not in valid_cryptos:
            messages.error(request, 'Please select a valid cryptocurrency')
            return redirect('investments:deposit')
        
        # Validate file upload if provided
        if proof_image:
            try:
                validate_uploaded_file(proof_image, 'Payment proof')
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('investments:deposit')
        
        # Create deposit request
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method,
            crypto_type=crypto_type if payment_method == 'crypto' else 'BANK',
            tx_hash=tx_hash,
            proof_image=proof_image,
            status='pending'
        )
        
        # Send admin notification email
        try:
            send_deposit_notification(deposit)
        except Exception as e:
            # Log error but don't stop deposit creation
            logger.error(f"Failed to send deposit notification: {str(e)}")
        
        messages.success(request, f'Deposit request of ${amount} submitted successfully! Awaiting admin confirmation.')
        return redirect('investments:deposit_status', deposit_id=deposit.id)
    
    # Get wallet addresses from database
    wallet_addresses = WalletAddress.objects.filter(is_active=True)
    wallets_dict = {wallet.crypto_type: wallet for wallet in wallet_addresses}
    
    # Get user's pending deposits
    pending_deposits = Deposit.objects.filter(user=request.user, status='pending').order_by('-created_at')
    recent_deposits = Deposit.objects.filter(user=request.user).exclude(status='pending').order_by('-created_at')[:5]
    
    return render(request, 'investments/deposit.html', {
        'wallets': wallets_dict,
        'pending_deposits': pending_deposits,
        'recent_deposits': recent_deposits
    })


@login_required
def deposit_status(request, deposit_id):
    """Display deposit status page with real-time updates"""
    deposit = get_object_or_404(Deposit, id=deposit_id, user=request.user)
    return render(request, 'investments/deposit_status.html', {'deposit': deposit})


@login_required
def pending_payment(request, deposit_id):
    """Display pending payment status page"""
    deposit = get_object_or_404(Deposit, id=deposit_id, user=request.user)
    return render(request, 'investments/pending_payment.html', {'deposit': deposit})


@login_required
def payment_confirmed(request, deposit_id):
    """Display payment confirmation success page"""
    deposit = get_object_or_404(Deposit, id=deposit_id, user=request.user)
    if deposit.status != 'CONFIRMED':
        return redirect('investments:pending_payment', deposit_id=deposit_id)
    return render(request, 'investments/payment_confirmed.html', {'deposit': deposit})


@login_required
def check_deposit_status_api(request, deposit_id):
    """API endpoint for checking deposit status via AJAX polling"""
    deposit = get_object_or_404(Deposit, id=deposit_id, user=request.user)
    return JsonResponse({
        'status': deposit.status,
        'confirmed': deposit.status == 'confirmed',
        'rejected': deposit.status == 'rejected',
    })


@login_required
@transaction.atomic
def withdraw_view(request):
    """Withdraw funds - atomic transaction to prevent race conditions"""
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str).quantize(Decimal('0.01'))
            if amount <= 0:
                messages.error(request, 'Amount must be greater than zero')
                return redirect('investments:withdraw')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid amount entered')
            return redirect('investments:withdraw')
        
        withdrawal_method = request.POST.get('withdrawal_method')
        crypto_type = request.POST.get('crypto_type', '')
        wallet_address = request.POST.get('wallet_address', '').strip()
        
        # Validation
        if amount < 10:
            messages.error(request, 'Minimum withdrawal is $10')
            return redirect('investments:withdraw')
        
        if amount > 100000:
            messages.error(request, 'Maximum single withdrawal is $100,000')
            return redirect('investments:withdraw')
        
        # Wallet address validation for crypto withdrawals
        if withdrawal_method == 'crypto' and wallet_address:
            import re
            # Basic crypto address validation patterns
            patterns = {
                'BTC': r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$',
                'ETH': r'^0x[a-fA-F0-9]{40}$',
                'USDT': r'^(0x[a-fA-F0-9]{40}|T[A-Za-z1-9]{33,34})$',  # ERC-20 or TRC-20
                'USDC': r'^0x[a-fA-F0-9]{40}$',
                'LTC': r'^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$',
                'BNB': r'^(0x[a-fA-F0-9]{40}|bnb[a-z0-9]{38,42})$',  # BEP-20 or BNB Beacon
            }
            pattern = patterns.get(crypto_type)
            # Only validate if we have a pattern for this crypto type
            if pattern and not re.match(pattern, wallet_address):
                messages.error(request, f'Invalid {crypto_type} wallet address format. Please check and try again.')
                return redirect('investments:withdraw')
        
        # Lock user row to prevent race conditions
        user = request.user.__class__.objects.select_for_update().get(pk=request.user.pk)
        
        if not user.can_withdraw(amount):
            messages.error(request, 'Insufficient balance, KYC not verified, or amount too low.')
            return redirect('investments:withdraw')
        
        # Deduct balance immediately when withdrawal is requested
        user.balance -= amount
        user.total_withdrawn += amount
        user.save()
        
        # Create withdrawal request
        withdrawal = Withdrawal.objects.create(
            user=user,
            amount=amount,
            withdrawal_method=withdrawal_method,
            crypto_type=crypto_type,
            wallet_address=wallet_address,
            status='pending'
        )
        
        messages.success(request, 'Withdrawal request submitted.')
        return redirect('dashboard:dashboard')
    
    return render(request, 'investments/withdraw.html')


@login_required
def loan_application(request):
    """Loan application and management"""
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str)
            if amount <= 0:
                messages.error(request, 'Loan amount must be greater than zero')
                return redirect('investments:loans')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid loan amount entered')
            return redirect('investments:loans')
        
        try:
            duration = int(request.POST.get('duration_days', 0))
            if duration <= 0:
                messages.error(request, 'Duration must be greater than zero')
                return redirect('investments:loans')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid duration entered')
            return redirect('investments:loans')
        
        purpose = request.POST.get('purpose')
        collateral = request.POST.get('collateral_description', '')
        
        Loan.objects.create(
            user=request.user,
            amount=amount,
            duration_days=duration,
            purpose=purpose,
            collateral_description=collateral,
            interest_rate=Decimal('4.5')
        )
        
        messages.success(request, 'Loan application submitted for review.')
        return redirect('investments:loans')
    
    loans = Loan.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'investments/loans.html', {'loans': loans})


@login_required
def loan_repay(request, loan_id):
    """Make loan repayment"""
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)
    
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount', '0')
            amount = Decimal(amount_str)
            if amount <= 0:
                messages.error(request, 'Repayment amount must be greater than zero')
                return redirect('investments:loans')
        except (InvalidOperation, ValueError):
            messages.error(request, 'Invalid repayment amount entered')
            return redirect('investments:loans')
        
        if amount > request.user.balance:
            messages.error(request, 'Insufficient balance.')
            return redirect('investments:loans')
        
        # Create repayment
        LoanRepayment.objects.create(loan=loan, amount=amount)
        
        # Deduct from user balance
        request.user.balance -= amount
        request.user.save()
        
        messages.success(request, f'Payment of ${amount} processed.')
        return redirect('investments:loans')
    
    return redirect('investments:loans')


@login_required
def virtual_cards(request):
    """Virtual card management"""
    if request.method == 'POST':
        card_type = request.POST.get('card_type', 'standard')
        billing_address = request.POST.get('billing_address', '')
        
        # Set limits based on card type
        limits = {
            'standard': {'daily': 1000, 'monthly': 10000},
            'premium': {'daily': 5000, 'monthly': 50000},
            'platinum': {'daily': 10000, 'monthly': 100000},
        }
        
        # Create new card
        VirtualCard.objects.create(
            user=request.user,
            card_type=card_type,
            card_holder_name=request.user.full_name,
            billing_address=billing_address or request.user.country,
            daily_limit=limits[card_type]['daily'],
            monthly_limit=limits[card_type]['monthly']
        )
        
        messages.success(request, 'Virtual card request submitted! Admin will review and activate shortly.')
        return redirect('investments:cards')
    
    cards = VirtualCard.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'investments/cards.html', {'cards': cards})


@login_required
def agent_page(request):
    """Agent recruitment and dashboard"""
    if request.method == 'POST':
        # Agent application submission
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        country = request.POST.get('country')
        city = request.POST.get('city')
        experience = request.POST.get('experience')
        marketing_plan = request.POST.get('marketing_plan')
        
        try:
            expected_referrals = int(request.POST.get('expected_referrals', 0))
            if expected_referrals < 0:
                expected_referrals = 0
        except (ValueError, TypeError):
            expected_referrals = 0
        
        social_media_links = request.POST.get('social_media_links', '')
        website = request.POST.get('website', '')
        id_document = request.FILES.get('id_document')
        
        # Validate uploaded file
        if id_document:
            try:
                validate_uploaded_file(id_document, 'ID document')
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('investments:agent')
        
        AgentApplication.objects.create(
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
        
        messages.success(request, 'Agent application submitted successfully! We will review and respond within 48 hours.')
        return redirect('investments:agent')
    
    # Get user's agent application if exists (secure lookup by user FK)
    try:
        agent_application = AgentApplication.objects.get(user=request.user)
    except AgentApplication.DoesNotExist:
        agent_application = None
    
    # Get referral stats for this user
    referral_count = request.user.referrals.count()
    total_referral_earnings = request.user.referral_bonus
    
    # Get referred users' investments total
    referred_users_total = 0
    for referral in request.user.referrals.all():
        referred_users_total += referral.invested_amount
    
    context = {
        'agent_application': agent_application,
        'referral_count': referral_count,
        'total_referral_earnings': total_referral_earnings,
        'referred_users_total': referred_users_total,
        'referral_code': request.user.referral_code
    }
    
    return render(request, 'investments/agent.html', context)


@ratelimit(key='ip', rate='60/m', method='GET', block=False)
def crypto_ticker_api(request):
    """
    JSON endpoint for live crypto price ticker.
    Fetches prices from CoinGecko API for cryptos configured in CryptoTicker model.
    Returns fallback data if no tickers configured or API fails.
    """
    # Handle rate limit exceeded gracefully (block=False means we check manually)
    if getattr(request, 'limited', False):
        return JsonResponse({'success': False, 'error': 'Rate limit exceeded. Please try again later.'}, status=429)
    
    tickers = CryptoTicker.objects.filter(is_active=True).order_by('display_order')

    # Default fallback tickers if none configured in database
    default_tickers = [
        {'symbol': 'BTC', 'name': 'Bitcoin', 'coingecko_id': 'bitcoin'},
        {'symbol': 'ETH', 'name': 'Ethereum', 'coingecko_id': 'ethereum'},
        {'symbol': 'USDT', 'name': 'Tether', 'coingecko_id': 'tether'},
        {'symbol': 'BNB', 'name': 'BNB', 'coingecko_id': 'binancecoin'},
        {'symbol': 'SOL', 'name': 'Solana', 'coingecko_id': 'solana'},
        {'symbol': 'XRP', 'name': 'XRP', 'coingecko_id': 'ripple'},
        {'symbol': 'ADA', 'name': 'Cardano', 'coingecko_id': 'cardano'},
        {'symbol': 'DOGE', 'name': 'Dogecoin', 'coingecko_id': 'dogecoin'},
    ]

    if not tickers.exists():
        # Use default tickers if none configured
        ticker_list = default_tickers
        coingecko_ids = ','.join([t['coingecko_id'] for t in ticker_list])
    else:
        ticker_list = [{'symbol': t.symbol, 'name': t.name, 'coingecko_id': t.coingecko_id} for t in tickers]
        coingecko_ids = ','.join([t.coingecko_id for t in tickers])

    # Fetch prices from CoinGecko public API
    try:
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={coingecko_ids}&vs_currencies=usd&include_24hr_change=true'
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')

        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Format response
        results = []
        for ticker in ticker_list:
            cg_id = ticker['coingecko_id'] if isinstance(ticker, dict) else ticker.coingecko_id
            symbol = ticker['symbol'] if isinstance(ticker, dict) else ticker.symbol
            name = ticker['name'] if isinstance(ticker, dict) else ticker.name
            
            coin_data = data.get(cg_id, {})
            results.append({
                'symbol': symbol,
                'name': name,
                'price': coin_data.get('usd', 0),
                'change_24h': coin_data.get('usd_24h_change', 0)
            })

        return JsonResponse({'success': True, 'tickers': results})

    except Exception as e:
        logger.warning(f'CoinGecko API error: {e}')
        # Return fallback static prices on error
        fallback_prices = {
            'BTC': 67500, 'ETH': 3450, 'USDT': 1.00, 'BNB': 580,
            'SOL': 145, 'XRP': 0.52, 'ADA': 0.45, 'DOGE': 0.12
        }
        fallback = []
        for ticker in ticker_list:
            symbol = ticker['symbol'] if isinstance(ticker, dict) else ticker.symbol
            name = ticker['name'] if isinstance(ticker, dict) else ticker.name
            fallback.append({
                'symbol': symbol,
                'name': name,
                'price': fallback_prices.get(symbol, 0),
                'change_24h': 0
            })
        return JsonResponse({'success': True, 'tickers': fallback, 'source': 'fallback'})