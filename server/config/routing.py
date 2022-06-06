from django.core.asgi import get_asgi_application
from django.urls import path

from channels.routing import ProtocolTypeRouter, URLRouter

from config.middleware import TokenAuthMiddlewareStack
from core.consumers import DispatchConsumer


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': TokenAuthMiddlewareStack( # changed
        URLRouter([
            path('dispatch/', DispatchConsumer.as_asgi()),
        ])
    ),
})
