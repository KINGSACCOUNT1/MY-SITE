from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import (InvestmentPlan, Investment, Deposit, Withdrawal, WalletAddress,
                     Loan, LoanRepayment, VirtualCard, Coupon, AgentApplication)
from decimal import Decimal


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
        amount = Decimal(request.POST.get('amount', 0))
        
        # Validation
        if amount < plan.min_amount or amount > plan.max_amount:
            messages.error(request, f'Amount must be between ${plan.min_amount} and ${plan.max_amount}')
            return redirect('investments:invest', plan_id=plan_id)
        
        if amount > request.user.balance:
            messages.error(request, 'Insufficient balance. Please add funds first.')
            return redirect('investments:deposit')
        
        # Create investment
        investment = Investment.objects.create(
            user=request.user,
            plan=plan,
            amount=amount
        )
        
        # Deduct from user balance
        user = request.user
        user.balance -= amount
        user.invested_amount += amount
        user.save()
        
        messages.success(request, f'Investment of ${amount} created successfully!')
        return redirect('dashboard:dashboard')
    
    return render(request, 'investments/invest.html', {'plan': plan})


@login_required
@login_required
def my_investments(request):
    """User's investment portfolio"""
    # Auto-check and update investments (no Celery needed!)
    from investments.utils import check_and_update_investments
    check_and_update_investments(request.user)
    
    investments = Investment.objects.filter(user=request.user).order_by('-start_date')
    active_count = investments.filter(status='active').count()
    completed_count = investments.filter(status='completed').count()
    
    return render(request, 'investments/my_investments.html', {
        'investments': investments,
        'active_count': active_count,
        'completed_count': completed_count
    })


@login_required
def deposit_view(request):
    """Deposit funds"""
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        crypto_type = request.POST.get('crypto_type')
        tx_hash = request.POST.get('tx_hash', '')
        proof_image = request.FILES.get('proof_image')
        payment_method = request.POST.get('payment_method', 'crypto')
        
        if amount < 10:
            messages.error(request, 'Minimum deposit is $10')
            return redirect('investments:deposit')
        
        # Create deposit request
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            crypto_type=crypto_type if payment_method == 'crypto' else 'BANK',
            tx_hash=tx_hash,
            proof_image=proof_image,
            status='pending'
        )
        
        messages.success(request, f'Deposit request of ${amount} submitted successfully! Awaiting admin confirmation.')
        return redirect('investments:deposit')
    
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
def withdraw_view(request):
    """Withdraw funds"""
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        withdrawal_method = request.POST.get('withdrawal_method')
        crypto_type = request.POST.get('crypto_type', '')
        wallet_address = request.POST.get('wallet_address', '')
        
        # Validation
        if amount < 10:
            messages.error(request, 'Minimum withdrawal is $10')
            return redirect('withdraw')
        
        if not request.user.can_withdraw(amount):
            messages.error(request, 'Insufficient balance, KYC not verified, or amount too low.')
            return redirect('withdraw')
        
        # Create withdrawal request
        withdrawal = Withdrawal.objects.create(
            user=request.user,
            amount=amount,
            withdrawal_method=withdrawal_method,
            crypto_type=crypto_type,
            wallet_address=wallet_address,
            status='pending'
        )
        
        messages.success(request, 'Withdrawal request submitted.')
        return redirect('dashboard')
    
    return render(request, 'investments/withdraw.html')


@login_required
def loan_application(request):
    """Loan application and management"""
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        duration = int(request.POST.get('duration_days'))
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
        amount = Decimal(request.POST.get('amount'))
        
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
        expected_referrals = int(request.POST.get('expected_referrals', 0))
        social_media_links = request.POST.get('social_media_links', '')
        website = request.POST.get('website', '')
        id_document = request.FILES.get('id_document')
        
        AgentApplication.objects.create(
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
    
    # Get user's agent application if exists
    try:
        agent_application = AgentApplication.objects.filter(
            full_name__icontains=request.user.full_name
        ).first()
    except:
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

