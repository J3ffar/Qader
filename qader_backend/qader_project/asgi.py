import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qader_project.settings.production")
django.setup()  # Ensure Django settings and apps are loaded

# Import your WebSocket routing *after* django.setup()
from apps.challenges.routing import websocket_urlpatterns as challenge_ws_urlpatterns
from apps.chat.routing import websocket_urlpatterns as chat_ws_urlpatterns

# Get the standard Django ASGI app for HTTP requests
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        # WebSocket chat handler
        "websocket": AllowedHostsOriginValidator(  # Basic security
            AuthMiddlewareStack(  # Handle authentication
                URLRouter(
                    challenge_ws_urlpatterns  # Add challenge WebSocket routes
                    + chat_ws_urlpatterns  # Add chat WebSocket routes
                )
            )
        ),
    }
)
