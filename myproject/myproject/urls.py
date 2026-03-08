"""
Mini Shop – URL configuration.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # DRF browsable-API login
    path("api-auth/", include("rest_framework.urls")),
    # allauth HTML pages (register / login / etc.)
    path("accounts/", include("allauth.urls")),
    # drf-auth-kit REST endpoints (JWT login, register, user, …)
    path("api/auth/", include("auth_kit.urls")),
    # Core app API
    path("api/", include("core.urls")),
    # django-payments callback URLs
    path("payments/", include("payments.urls")),
]
