"""
ASGI config for elite_wealth project.
Standard ASGI application without WebSocket support.
For WebSocket support, uncomment Channels code and add channels to requirements.txt
"""

import os
from django.core.asgi import get_asgi_application

# Set default settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elite_wealth.settings')

# Initialize Django ASGI application
application = get_asgi_application()

# WebSocket support (Channels) - Commented out
# Uncomment the code below and install channels/channels-redis/daphne when needed
# 
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from channels.security.websocket import AllowedHostsOriginValidator
# from elite_wealth.routing import websocket_urlpatterns
# 
# application = ProtocolTypeRouter({
#     "http": application,
#     "websocket": AllowedHostsOriginValidator(
#         AuthMiddlewareStack(
#             URLRouter(websocket_urlpatterns)
#         )
#     ),
# })

