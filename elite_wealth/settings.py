"""
Django settings for Elite Wealth Capital project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        # Only allow fallback in DEBUG mode for development
        import secrets
        SECRET_KEY = secrets.token_urlsafe(50)
        print("WARNING: Using random SECRET_KEY for development")
    else:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            'SECRET_KEY environment variable must be set in production. '
            'Add SECRET_KEY to your .env file or environment variables.'
        )

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,elite-wealth-capita.com,www.elite-wealth-capita.com,.railway.app,.onrender.com,elitewealthcapita.uk,www.elitewealthcapita.uk').split(',')
CSRF_TRUSTED_ORIGINS = ['https://*.railway.app', 'https://*.onrender.com', 'https://elite-wealth-capita.com', 'https://www.elite-wealth-capita.com', 'https://elitewealthcapita.uk', 'https://www.elitewealthcapita.uk']


# Application definition
INSTALLED_APPS = [
    # Modern Admin UI - MUST be before django.contrib.admin
    'jazzmin',
    
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third Party
    'corsheaders',
    # 'rest_framework',  # Commented out - add djangorestframework to requirements.txt if needed
    # 'rest_framework_simplejwt',  # Commented out - add djangorestframework-simplejwt to requirements.txt if needed
    # 'drf_yasg',  # Commented out - add drf-yasg to requirements.txt if needed
    # 'channels',  # Commented out - add channels to requirements.txt if needed
    
    # Local Apps
    'core.apps.CoreConfig',  # Core utilities and performance tools
    'accounts.apps.AccountsConfig',
    'investments.apps.InvestmentsConfig',
    'dashboard.apps.DashboardConfig',
    'tasks.apps.TasksConfig',
    'kyc.apps.KycConfig',
    'notifications.apps.NotificationsConfig',
    'messaging.apps.MessagingConfig',
    'api.apps.ApiConfig',
]

# Jazzmin Admin Settings
JAZZMIN_SETTINGS = {
    # Title & Branding
    "site_title": "Elite Wealth Capital",
    "site_header": "Elite Wealth Capital",
    "site_brand": "Elite Wealth",
    "site_logo": "images/logo.webp",
    "site_logo_classes": "img-circle",
    "site_icon": "images/logo.webp",
    "welcome_sign": "Welcome to Elite Wealth Capital Admin",
    "copyright": "Elite Wealth Capital Ltd.",
    
    # Search & User
    "search_model": ["accounts.CustomUser", "investments.Investment", "investments.Deposit"],
    "user_avatar": None,
    
    # Top Menu Links
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
        {"model": "accounts.CustomUser"},
        {"app": "investments"},
    ],
    
    # User Menu Links
    "usermenu_links": [
        {"name": "View Site", "url": "/", "new_window": True, "icon": "fas fa-globe"},
        {"model": "accounts.customuser"},
    ],
    
    # Side Menu - Custom Ordering
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "accounts",
        "accounts.CustomUser",
        "accounts.ActivityLog", 
        "accounts.Referral",
        "kyc",
        "kyc.KYCDocument",
        "investments",
        "investments.InvestmentPlan",
        "investments.Investment",
        "investments.Deposit",
        "investments.Withdrawal",
        "investments.Loan",
        "investments.LoanRepayment",
        "investments.VirtualCard",
        "investments.Coupon",
        "investments.AgentApplication",
        "investments.AccountUpgrade",
        "investments.WalletAddress",
        "dashboard",
        "dashboard.NewsArticle",
        "dashboard.NewsletterSubscription",
        "dashboard.ContactMessage",
        "dashboard.Dispute",
        "notifications",
    ],
    
    # Custom Icons for Apps/Models
    "icons": {
        # Accounts
        "accounts": "fas fa-users-cog",
        "accounts.CustomUser": "fas fa-users",
        "accounts.ActivityLog": "fas fa-history",
        "accounts.Referral": "fas fa-share-alt",
        "accounts.SiteSettings": "fas fa-cogs",
        # KYC
        "kyc": "fas fa-id-card",
        "kyc.KYCDocument": "fas fa-file-alt",
        # Investments
        "investments": "fas fa-chart-line",
        "investments.InvestmentPlan": "fas fa-layer-group",
        "investments.Investment": "fas fa-hand-holding-usd",
        "investments.Deposit": "fas fa-plus-circle",
        "investments.Withdrawal": "fas fa-minus-circle",
        "investments.Loan": "fas fa-money-check-alt",
        "investments.LoanRepayment": "fas fa-receipt",
        "investments.VirtualCard": "fas fa-credit-card",
        "investments.Coupon": "fas fa-tags",
        "investments.AgentApplication": "fas fa-user-tie",
        "investments.AccountUpgrade": "fas fa-arrow-up",
        "investments.WalletAddress": "fas fa-wallet",
        # Dashboard
        "dashboard": "fas fa-tachometer-alt",
        "dashboard.NewsArticle": "fas fa-newspaper",
        "dashboard.NewsletterSubscription": "fas fa-envelope",
        "dashboard.ContactMessage": "fas fa-comment-dots",
        "dashboard.Dispute": "fas fa-gavel",
        # Notifications
        "notifications": "fas fa-bell",
        "notifications.Notification": "fas fa-bell",
        # Auth
        "auth": "fas fa-lock",
        "auth.Group": "fas fa-users",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    
    # Related Modal
    "related_modal_active": True,
    
    # Custom CSS/JS
    "custom_css": "css/admin-jazzmin.css",
    "custom_js": None,
    
    # UI Tweaks
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "accounts.CustomUser": "collapsible",
        "investments.Investment": "horizontal_tabs",
    },
    
    # Language chooser
    "language_chooser": False,
}

# Jazzmin UI Tweaks
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-warning",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

def environment_callback(request):
    """Show environment badge in admin"""
    if DEBUG:
        return ["Development", "warning"]
    return ["Production", "success"]

def user_count_badge(request):
    from accounts.models import CustomUser
    count = CustomUser.objects.count()
    return f"{count}"

def pending_deposits_badge(request):
    from investments.models import Deposit
    count = Deposit.objects.filter(status='pending').count()
    if count > 0:
        return f"{count}"
    return None

def pending_withdrawals_badge(request):
    from investments.models import Withdrawal
    count = Withdrawal.objects.filter(status='pending').count()
    if count > 0:
        return f"{count}"
    return None

def unread_contacts_badge(request):
    from dashboard.models import ContactMessage
    count = ContactMessage.objects.filter(is_read=False).count()
    if count > 0:
        return f"{count}"
    return None

def pending_disputes_badge(request):
    from dashboard.models import Dispute
    count = Dispute.objects.filter(status='pending').count()
    if count > 0:
        return f"{count}"
    return None

def dashboard_callback(request, context):
    """Add statistics to admin dashboard."""
    from accounts.models import CustomUser
    from investments.models import Investment, Deposit, Withdrawal, Loan, AgentApplication
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User stats
    total_users = CustomUser.objects.count()
    new_users_week = CustomUser.objects.filter(date_joined__date__gte=week_ago).count()
    verified_users = CustomUser.objects.filter(kyc_status='verified').count()
    
    # Financial stats
    total_balance = CustomUser.objects.aggregate(total=Sum('balance'))['total'] or 0
    total_invested = Investment.objects.filter(status='active').aggregate(total=Sum('amount'))['total'] or 0
    total_deposits = Deposit.objects.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0
    total_withdrawals = Withdrawal.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    
    # Pending items
    pending_deposits = Deposit.objects.filter(status='pending').count()
    pending_withdrawals = Withdrawal.objects.filter(status='pending').count()
    pending_kyc = CustomUser.objects.filter(kyc_status='submitted').count()
    pending_loans = Loan.objects.filter(status='pending').count()
    pending_agents = AgentApplication.objects.filter(status='pending').count()
    
    # Active investments count
    active_investments = Investment.objects.filter(status='active').count()
    
    context.update({
        # User metrics
        'total_users': total_users,
        'new_users_week': new_users_week,
        'verified_users': verified_users,
        # Financial metrics
        'total_balance': f"${total_balance:,.2f}",
        'total_invested': f"${total_invested:,.2f}",
        'total_deposits': f"${total_deposits:,.2f}",
        'total_withdrawals': f"${total_withdrawals:,.2f}",
        # Pending actions
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'pending_kyc': pending_kyc,
        'pending_loans': pending_loans,
        'pending_agents': pending_agents,
        'active_investments': active_investments,
    })
    return context

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # GZip compression for performance
    'django.middleware.cache.UpdateCacheMiddleware',  # Cache middleware (must be first after GZip)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # Cache middleware (must be after Common)
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'elite_wealth.security_headers.SecurityHeadersMiddleware',  # Custom security headers
]

ROOT_URLCONF = 'elite_wealth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'elite_wealth.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'elite_wealth.wsgi.application'
ASGI_APPLICATION = 'elite_wealth.asgi.application'


# Database
import dj_database_url

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
            'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
            'USER': os.getenv('DB_USER', ''),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', ''),
            'PORT': os.getenv('DB_PORT', ''),
        }
    }


# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Custom Authentication Backend (email-based login)
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
]


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# Support CDN for static files if configured
STATIC_URL = os.getenv('CDN_URL', '/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Use CompressedStaticFilesStorage instead of Manifest version to avoid source map issues
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files (uploads)
# Support CDN for media files if configured
MEDIA_URL = os.getenv('CDN_MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / 'media'


# CORS Settings (for any external integrations)
CORS_ALLOWED_ORIGINS = [
    'https://elite-wealth-capita.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]


# Celery Configuration
CELERY_BROKER_URL = os.getenv(
    'CELERY_BROKER_URL',
    'redis://:changeme@localhost:6379/0'  # Default with password placeholder
)
CELERY_RESULT_BACKEND = os.getenv(
    'CELERY_RESULT_BACKEND', 
    'redis://:changeme@localhost:6379/0'
)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE


# Cache Configuration
# Use Redis when REDIS_URL is provided; fall back to local memory cache otherwise
REDIS_URL = os.getenv('REDIS_URL', '').strip()
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_CLASS_KWARGS': {
                    'max_connections': 50,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            },
            'KEY_PREFIX': 'ewc',
            'TIMEOUT': 300,  # 5 minutes default
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'ewc-default',
            'TIMEOUT': 300,
        }
    }

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes for page caching
CACHE_MIDDLEWARE_KEY_PREFIX = 'ewc_page'


# Email Configuration (Zoho Mail SMTP)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.zoho.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'admin@elitewealthcapita.uk')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'admin@elitewealthcapita.uk')

# Company Email Addresses
COMPANY_EMAILS = {
    'admin': 'admin@elitewealthcapita.uk',
    'support': 'support@elitewealthcapita.uk',
    'noreply': 'noreply@elitewealthcapita.uk',
    'billing': 'billing@elitewealthcapita.uk',
    'kyc': 'kyc@elitewealthcapita.uk',
    'withdrawals': 'withdrawals@elitewealthcapita.uk',
    'deposits': 'deposits@elitewealthcapita.uk',
    'alerts': 'alerts@elitewealthcapita.uk',
}
# Admin notification email - set via environment variable
ADMIN_NOTIFICATION_EMAIL = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@elitewealthcapita.uk')


# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days
SESSION_SAVE_EVERY_REQUEST = True


# Security Settings (Production)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # Render handles SSL at load balancer
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'Strict'  # Allow CSRF cookie for same-site requests
    SESSION_COOKIE_SAMESITE = 'Strict'  # Allow session cookie for same-site requests
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Additional CSP setting
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Site Configuration
SITE_NAME = 'Elite Wealth Capital'
SITE_DOMAIN = 'elite-wealth-capita.com'


# Investment Settings
MIN_DEPOSIT = 30
MIN_WITHDRAWAL = 50
REFERRAL_BONUS_PERCENT = 5

# Bybit API credentials for deposit address retrieval (set in environment)
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')


# ===== REST Framework Configuration =====
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Swagger/OpenAPI Configuration
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SHOW_REQUEST_HEADERS': True,
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
}


# ===== Django Channels Configuration =====
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/2')],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}


# ===== Payment Gateway Configuration =====
# Stripe
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# PayPal
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')  # sandbox or live
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', '')

# Coinbase Commerce
COINBASE_COMMERCE_API_KEY = os.getenv('COINBASE_COMMERCE_API_KEY', '')
COINBASE_COMMERCE_WEBHOOK_SECRET = os.getenv('COINBASE_COMMERCE_WEBHOOK_SECRET', '')
