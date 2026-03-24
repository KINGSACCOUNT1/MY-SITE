# Generated migration for bank withdrawal support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0002_coupon_accountupgrade_agentapplication_couponusage_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='withdrawal',
            name='withdrawal_method',
            field=models.CharField(
                choices=[('crypto', 'Cryptocurrency'), ('bank', 'Bank Transfer')],
                default='crypto',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='withdrawal',
            name='bank_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='withdrawal',
            name='account_number',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='withdrawal',
            name='account_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='withdrawal',
            name='crypto_type',
            field=models.CharField(blank=True, choices=[('BTC', 'Bitcoin'), ('ETH', 'Ethereum'), ('USDT', 'USDT (TRC20)'), ('USDC', 'USDC'), ('LTC', 'Litecoin')], max_length=10),
        ),
        migrations.AlterField(
            model_name='withdrawal',
            name='wallet_address',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
