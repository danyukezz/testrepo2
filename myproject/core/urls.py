"""
URL routing for core app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"products", views.ProductViewSet, basename="product")
router.register(r"orders", views.OrderViewSet, basename="order")
router.register(r"notes", views.CustomerNoteViewSet, basename="customernote")

urlpatterns = [
    path("me/", views.me_view, name="me"),
    path("", include(router.urls)),
]
