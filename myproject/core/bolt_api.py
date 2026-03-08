"""
Django-Bolt demo endpoint.

Django-Bolt provides a high-performance ASGI layer.  Here we expose a single
tiny Bolt endpoint at /bolt/ping that returns JSON without touching DRF.

Run with:  bolt run   (or  uvicorn myproject.asgi:application)
"""
from django_bolt import BoltAPI, Request, Response

bolt_app = BoltAPI()


@bolt_app.get("/ping")
async def ping(request: Request) -> Response:
    """Lightweight health-check served by django-bolt."""
    return Response({"message": "pong from django-bolt 🚀"})
