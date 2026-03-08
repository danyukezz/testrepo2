"""
ASGI config for myproject project.

Includes the Django-Bolt ASGI app mounted at /bolt/.
Run:  uvicorn myproject.asgi:application --reload
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

# Standard Django ASGI app
django_asgi_app = get_asgi_application()

# Mount Bolt alongside Django
from core.bolt_api import bolt_app  # noqa: E402


async def application(scope, receive, send):
    """Route /bolt/* to Bolt, everything else to Django."""
    if scope["type"] == "http" and scope["path"].startswith("/bolt/"):
        # Strip /bolt prefix for the bolt router
        scope = dict(scope, path=scope["path"][5:])  # /bolt/ping → /ping
        await bolt_app(scope, receive, send)
    else:
        await django_asgi_app(scope, receive, send)

