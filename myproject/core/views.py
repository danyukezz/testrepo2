"""
Views for the Mini Shop API.

Demonstrates:
  - DRF ViewSets (Product, Order)
  - django-filter integration
  - Protected /api/me/ endpoint
  - CustomerNote CRUD
  - EAV attribute setter endpoint
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Product, Order, CustomerNote
from .serializers import (
    ProductSerializer,
    OrderSerializer,
    CustomerNoteSerializer,
    UserMeSerializer,
)
from .filters import ProductFilter


# ─── Product ViewSet ────────────────────────────────────────────────────────
class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD for Products.

    Supports filtering via django-filter:
        ?min_price=10&max_price=100&tag=electronics
    """

    queryset = Product.objects.prefetch_related("tags").all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filterset_class = ProductFilter

    @action(detail=True, methods=["post"], url_path="set-eav")
    def set_eav(self, request, pk=None):
        """
        Set EAV attributes on a product.

        POST /api/products/<id>/set-eav/
        Body: {"color": "red", "size": "XL"}

        Each key becomes an EAV attribute (auto-created if needed).
        """
        import eav
        from eav.models import Attribute

        product = self.get_object()
        for key, value in request.data.items():
            # Ensure the EAV attribute exists
            attr, _ = Attribute.objects.get_or_create(
                slug=key,
                defaults={"name": key.title(), "datatype": Attribute.TYPE_TEXT},
            )
            setattr(product.eav, key, str(value))
        product.save()
        return Response(
            ProductSerializer(product, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


# ─── Order ViewSet ──────────────────────────────────────────────────────────
class OrderViewSet(viewsets.ModelViewSet):
    """
    List / create orders.  Creating an order triggers a lifecycle hook
    that auto-creates a Payment record.
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("product")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ─── CustomerNote (encrypted field demo) ───────────────────────────────────
class CustomerNoteViewSet(viewsets.ModelViewSet):
    """
    Read / write an encrypted private note for the logged-in user.
    """

    serializer_class = CustomerNoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomerNote.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ─── /api/me/ ───────────────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Protected endpoint – returns the current user's info."""
    serializer = UserMeSerializer(request.user)
    return Response(serializer.data)
