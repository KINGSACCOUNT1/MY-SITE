"""
ASGI config for Elite Wealth Capital project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')
application = get_asgi_application()
