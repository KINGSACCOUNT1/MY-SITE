from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investments', '0004_add_bank_withdrawal_support'),
    ]

    operations = [
        migrations.CreateModel(
            name='CryptoTicker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=20, unique=True, help_text='Trading symbol, e.g. BTC, ETH')),
                ('name', models.CharField(max_length=100, help_text='Display name, e.g. Bitcoin, Ethereum')),
                ('coingecko_id', models.CharField(max_length=100, help_text='CoinGecko coin ID used to fetch prices (e.g. bitcoin, ethereum, tether)')),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0, help_text='Lower numbers appear first')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Crypto Ticker',
                'verbose_name_plural': 'Crypto Tickers',
                'ordering': ['display_order', 'symbol'],
            },
        ),
    ]
