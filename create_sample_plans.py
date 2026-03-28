"""
Create sample investment plans for all sectors
Run: python manage.py shell < create_sample_plans.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')
django.setup()

from investments.models import InvestmentPlan
from decimal import Decimal

# Clear existing plans
InvestmentPlan.objects.all().delete()

plans = [
    # CRYPTO TRADING SECTOR
    {
        'name': 'Bitcoin Mining Pool',
        'category': 'crypto',
        'icon': 'fab fa-bitcoin',
        'description': 'Join our Bitcoin mining collective with state-of-the-art ASIC miners. Daily returns from block rewards and transaction fees.',
        'min_amount': Decimal('500'),
        'max_amount': Decimal('50000'),
        'daily_roi': Decimal('2.5'),
        'duration_days': 30,
        'is_featured': True,
    },
    {
        'name': 'DeFi Staking Portfolio',
        'category': 'crypto',
        'icon': 'fas fa-coins',
        'description': 'Diversified DeFi staking across Ethereum, Cardano, and Polkadot networks. Automated yield optimization.',
        'min_amount': Decimal('1000'),
        'max_amount': Decimal('100000'),
        'daily_roi': Decimal('3.2'),
        'duration_days': 60,
        'is_featured': True,
    },
    {
        'name': 'Altcoin Trading Bot',
        'category': 'crypto',
        'icon': 'fas fa-robot',
        'description': 'AI-powered trading bot executing high-frequency trades on 50+ altcoins. Proven algorithm with risk management.',
        'min_amount': Decimal('2000'),
        'max_amount': Decimal('200000'),
        'daily_roi': Decimal('4.5'),
        'duration_days': 45,
    },
    {
        'name': 'Crypto Index Fund',
        'category': 'crypto',
        'icon': 'fas fa-chart-area',
        'description': 'Balanced portfolio tracking top 20 cryptocurrencies by market cap. Lower risk, steady growth.',
        'min_amount': Decimal('250'),
        'max_amount': Decimal('25000'),
        'daily_roi': Decimal('1.8'),
        'duration_days': 90,
    },
    
    # REAL ESTATE SECTOR
    {
        'name': 'London Prime Properties',
        'category': 'real_estate',
        'icon': 'fas fa-building',
        'description': 'Tokenized shares in luxury London residential properties. Prime locations in Mayfair, Chelsea, and Kensington.',
        'min_amount': Decimal('5000'),
        'max_amount': Decimal('500000'),
        'daily_roi': Decimal('0.8'),
        'duration_days': 365,
        'is_featured': True,
    },
    {
        'name': 'US Commercial Real Estate',
        'category': 'real_estate',
        'icon': 'fas fa-city',
        'description': 'Office buildings and retail spaces in New York, Los Angeles, and Miami. Long-term rental income.',
        'min_amount': Decimal('10000'),
        'max_amount': Decimal('1000000'),
        'daily_roi': Decimal('0.6'),
        'duration_days': 730,
    },
    {
        'name': 'Property Development Fund',
        'category': 'real_estate',
        'icon': 'fas fa-hard-hat',
        'description': 'New construction projects across UK. Higher returns from property appreciation and sales.',
        'min_amount': Decimal('15000'),
        'max_amount': Decimal('750000'),
        'daily_roi': Decimal('1.2'),
        'duration_days': 540,
    },
    {
        'name': 'Vacation Rental Portfolio',
        'category': 'real_estate',
        'icon': 'fas fa-hotel',
        'description': 'Short-term rental properties in tourist hotspots. Airbnb and Booking.com managed.',
        'min_amount': Decimal('3000'),
        'max_amount': Decimal('100000'),
        'daily_roi': Decimal('1.5'),
        'duration_days': 180,
    },
    
    # OIL & GAS SECTOR
    {
        'name': 'North Sea Drilling Project',
        'category': 'oil_gas',
        'icon': 'fas fa-oil-can',
        'description': 'Investment in proven North Sea oil reserves. Partnership with major energy companies.',
        'min_amount': Decimal('25000'),
        'max_amount': Decimal('2000000'),
        'daily_roi': Decimal('1.1'),
        'duration_days': 1095,
        'is_featured': True,
    },
    {
        'name': 'Norwegian Gas Pipeline',
        'category': 'oil_gas',
        'icon': 'fas fa-industry',
        'description': 'Natural gas extraction and distribution infrastructure. Stable long-term returns from European demand.',
        'min_amount': Decimal('50000'),
        'max_amount': Decimal('5000000'),
        'daily_roi': Decimal('0.9'),
        'duration_days': 1825,
    },
    {
        'name': 'Oil Futures Trading',
        'category': 'oil_gas',
        'icon': 'fas fa-chart-line',
        'description': 'Commodities trading in crude oil futures. Professional traders managing positions.',
        'min_amount': Decimal('10000'),
        'max_amount': Decimal('500000'),
        'daily_roi': Decimal('2.3'),
        'duration_days': 90,
    },
    {
        'name': 'Energy Storage Fund',
        'category': 'oil_gas',
        'icon': 'fas fa-battery-full',
        'description': 'Strategic petroleum reserves and storage facilities. Profit from price arbitrage.',
        'min_amount': Decimal('20000'),
        'max_amount': Decimal('1000000'),
        'daily_roi': Decimal('1.4'),
        'duration_days': 365,
    },
    
    # AGRICULTURE SECTOR
    {
        'name': 'Organic Farm Co-operative',
        'category': 'agriculture',
        'icon': 'fas fa-seedling',
        'description': 'Sustainable organic farming across UK and Ireland. Direct farm-to-market distribution network.',
        'min_amount': Decimal('2000'),
        'max_amount': Decimal('100000'),
        'daily_roi': Decimal('1.3'),
        'duration_days': 180,
        'is_featured': True,
    },
    {
        'name': 'Livestock Trading Fund',
        'category': 'agriculture',
        'icon': 'fas fa-horse-head',
        'description': 'Cattle and livestock trading operations. Profit from breeding, raising, and market sales.',
        'min_amount': Decimal('5000'),
        'max_amount': Decimal('250000'),
        'daily_roi': Decimal('1.7'),
        'duration_days': 270,
    },
    {
        'name': 'AgriTech Ventures',
        'category': 'agriculture',
        'icon': 'fas fa-tractor',
        'description': 'Investment in agricultural technology startups. Precision farming, drones, and automation.',
        'min_amount': Decimal('10000'),
        'max_amount': Decimal('500000'),
        'daily_roi': Decimal('2.1'),
        'duration_days': 365,
    },
    {
        'name': 'Grain Commodity Trading',
        'category': 'agriculture',
        'icon': 'fas fa-wheat-awn',
        'description': 'Wheat, corn, and soybean futures trading. Global agricultural commodity markets.',
        'min_amount': Decimal('3000'),
        'max_amount': Decimal('150000'),
        'daily_roi': Decimal('1.9'),
        'duration_days': 120,
    },
    
    # SOLAR ENERGY SECTOR
    {
        'name': 'European Solar Farm Fund',
        'category': 'solar',
        'icon': 'fas fa-solar-panel',
        'description': 'Large-scale solar installations across Spain, Portugal, and Southern France. Government-backed feed-in tariffs.',
        'min_amount': Decimal('8000'),
        'max_amount': Decimal('400000'),
        'daily_roi': Decimal('1.0'),
        'duration_days': 730,
        'is_featured': True,
    },
    {
        'name': 'African Solar Initiative',
        'category': 'solar',
        'icon': 'fas fa-sun',
        'description': 'Renewable energy projects in Kenya, Ghana, and South Africa. High impact, high returns.',
        'min_amount': Decimal('5000'),
        'max_amount': Decimal('200000'),
        'daily_roi': Decimal('2.2'),
        'duration_days': 365,
    },
    {
        'name': 'Residential Solar Leasing',
        'category': 'solar',
        'icon': 'fas fa-home',
        'description': 'Install solar panels on residential properties. Income from energy sales and leasing agreements.',
        'min_amount': Decimal('3000'),
        'max_amount': Decimal('75000'),
        'daily_roi': Decimal('1.4'),
        'duration_days': 540,
    },
    {
        'name': 'Green Energy ETF',
        'category': 'solar',
        'icon': 'fas fa-leaf',
        'description': 'Diversified renewable energy portfolio. Solar, wind, and hydro investments worldwide.',
        'min_amount': Decimal('1000'),
        'max_amount': Decimal('50000'),
        'daily_roi': Decimal('1.1'),
        'duration_days': 365,
    },
    
    # GLOBAL SHARES SECTOR
    {
        'name': 'Tech Giants Portfolio',
        'category': 'stocks',
        'icon': 'fab fa-apple',
        'description': 'Blue-chip technology stocks: Apple, Microsoft, Google, Amazon. Long-term growth strategy.',
        'min_amount': Decimal('1000'),
        'max_amount': Decimal('100000'),
        'daily_roi': Decimal('0.9'),
        'duration_days': 365,
        'is_featured': True,
    },
    {
        'name': 'Emerging Markets Fund',
        'category': 'stocks',
        'icon': 'fas fa-globe-asia',
        'description': 'High-growth opportunities in Asian and African markets. Exposure to developing economies.',
        'min_amount': Decimal('2500'),
        'max_amount': Decimal('150000'),
        'daily_roi': Decimal('2.8'),
        'duration_days': 180,
    },
    {
        'name': 'Dividend Aristocrats',
        'category': 'stocks',
        'icon': 'fas fa-crown',
        'description': 'Companies with 25+ years of dividend increases. Reliable income from blue-chip stocks.',
        'min_amount': Decimal('5000'),
        'max_amount': Decimal('250000'),
        'daily_roi': Decimal('0.7'),
        'duration_days': 730,
    },
    {
        'name': 'Gold & Precious Metals',
        'category': 'stocks',
        'icon': 'fas fa-gem',
        'description': 'Physical gold, silver, and platinum holdings. Hedge against inflation and market volatility.',
        'min_amount': Decimal('2000'),
        'max_amount': Decimal('500000'),
        'daily_roi': Decimal('0.5'),
        'duration_days': 365,
    },
]

print("Creating investment plans...")
created = 0
for plan_data in plans:
    plan = InvestmentPlan.objects.create(**plan_data)
    created += 1
    print(f"✓ Created: {plan.name} ({plan.get_category_display()})")

print(f"\n✅ Successfully created {created} investment plans across 6 sectors!")
