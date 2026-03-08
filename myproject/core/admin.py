"""
Admin registration for Mini Shop models.
"""
from django.contrib import admin
from .models import Product, Order, Payment, CustomerNote


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "created"]
    search_fields = ["name"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "quantity", "status", "created"]
    list_filter = ["status"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "variant", "status", "total", "currency", "created"]
    list_filter = ["status"]


@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = ["user", "created"]
