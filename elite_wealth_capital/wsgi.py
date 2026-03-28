"""
WSGI config for Elite Wealth Capital project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth_capital.settings')
application = get_wsgi_application()
