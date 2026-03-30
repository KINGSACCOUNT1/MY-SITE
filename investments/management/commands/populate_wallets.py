"""
Management command to populate sample wallet addresses
Usage: python manage.py populate_wallets
"""
from django.core.management.base import BaseCommand
from investments.models import WalletAddress


class Command(BaseCommand):
    help = 'Populate sample cryptocurrency wallet addresses'

    def handle(self, *args, **options):
        wallets = [
            {
                'crypto_type': 'BTC',
                'address': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
                'label': 'Bitcoin Main Wallet',
                'network': 'Bitcoin Network',
                'is_active': True
            },
            {
                'crypto_type': 'ETH',
                'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8',
                'label': 'Ethereum Main Wallet',
                'network': 'ERC-20',
                'is_active': True
            },
            {
                'crypto_type': 'USDT',
                'address': 'TQjXhJ3X8e9YJp4hZvQ2nJZRWr8FnEyKzZ',
                'label': 'USDT TRC-20 Wallet',
                'network': 'TRC-20',
                'is_active': True
            },
            {
                'crypto_type': 'USDC',
                'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb8',
                'label': 'USDC Main Wallet',
                'network': 'ERC-20',
                'is_active': True
            },
            {
                'crypto_type': 'LTC',
                'address': 'ltc1qg6hpzwkgkg4p8qftygvwsj0f23zk5nkr5skhqd',
                'label': 'Litecoin Main Wallet',
                'network': 'Litecoin Network',
                'is_active': True
            },
            {
                'crypto_type': 'BNB',
                'address': 'bnb1grpf0955h0ykzq3ar5nmum7y6gdfl6lxfn46h2',
                'label': 'Binance Coin Wallet',
                'network': 'BEP-20',
                'is_active': True
            },
            {
                'crypto_type': 'BANK',
                'address': 'Contact Support via Chat',
                'label': 'Bank Transfer - Contact Support',
                'network': 'Bank Wire',
                'is_active': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for wallet_data in wallets:
            wallet, created = WalletAddress.objects.update_or_create(
                crypto_type=wallet_data['crypto_type'],
                defaults=wallet_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created {wallet_data["crypto_type"]} wallet')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated {wallet_data["crypto_type"]} wallet')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Wallet population complete!'
                f'\n  Created: {created_count}'
                f'\n  Updated: {updated_count}'
                f'\n  Total: {created_count + updated_count}'
            )
        )
