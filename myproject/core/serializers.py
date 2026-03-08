"""
Serializers for the Mini Shop API.
"""
from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer

from .models import Product, Order, Payment, CustomerNote


class ProductSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Product with tags (django-taggit)."""

    tags = TagListSerializerField()

    # Expose EAV attributes as read-only dict
    eav_attrs = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "description", "tags", "eav_attrs", "created", "modified"]

    def get_eav_attrs(self, obj):
        """Return dynamic EAV attributes as a simple dict."""
        try:
            return {
                attr.attribute.slug: attr.value_text or attr.value_float or attr.value_int
                for attr in obj.eav_values.all()
            }
        except Exception:
            return {}


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "variant", "status", "currency", "total", "description", "created"]


class OrderSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "user", "product", "product_name",
            "quantity", "status", "payments", "created", "modified",
        ]
        read_only_fields = ["user", "status"]


class CustomerNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerNote
        fields = ["id", "private_note", "created", "modified"]
        read_only_fields = ["id"]


class UserMeSerializer(serializers.Serializer):
    """Minimal 'who am I' response."""
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
