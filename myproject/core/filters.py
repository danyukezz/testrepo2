"""
Filters for the Mini Shop API.  (django-filter)
"""
import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Filter products by price range and tag name.

    Query examples:
        /api/products/?min_price=5&max_price=50
        /api/products/?tag=electronics
    """

    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    tag = django_filters.CharFilter(field_name="tags__name", lookup_expr="iexact")

    class Meta:
        model = Product
        fields = ["min_price", "max_price", "tag"]
