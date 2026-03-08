"""
Mini Shop models.

Demonstrates:
  - django-model-utils  (TimeStampedModel, StatusField)
  - django-taggit        (TaggableManager on Product)
  - django-eav2          (registered in apps.py)
  - django-lifecycle     (hook on Order creation)
  - django-fernet-encrypted-fields (EncryptedTextField on CustomerNote)
  - django-payments      (BasePayment → Payment)
"""

from decimal import Decimal

from django.conf import settings
from django.db import models

from model_utils.models import TimeStampedModel
from model_utils.fields import StatusField
from model_utils import Choices

from django_lifecycle import LifecycleModelMixin, hook, AFTER_CREATE

from taggit.managers import TaggableManager

from encrypted_fields.fields import EncryptedTextField

from payments import PurchasedItem
from payments.models import BasePayment


# ─── Product ────────────────────────────────────────────────────────────────
class Product(TimeStampedModel):
    """
    A shop product.

    • TimeStampedModel  → auto ``created`` / ``modified`` fields  (django-model-utils)
    • TaggableManager   → ``tags`` many-to-many              (django-taggit)
    • EAV registered in apps.py → dynamic attrs like *color*, *size*  (django-eav2)
    """

    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, default="")

    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─── Order ──────────────────────────────────────────────────────────────────
class Order(LifecycleModelMixin, TimeStampedModel):
    """
    A simple order referencing one product.

    • StatusField keeps an order-status with predefined choices  (django-model-utils)
    • Lifecycle hook auto-creates a Payment record on creation   (django-lifecycle)
    """

    STATUS = Choices("new", "paid", "shipped", "cancelled")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    status = StatusField()

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Order #{self.pk} – {self.product.name}"

    # ── django-lifecycle hook ───────────────────────────────────────────────
    @hook(AFTER_CREATE)
    def create_payment_record(self):
        """Automatically create a Payment when a new Order is saved."""
        total = Decimal(str(self.product.price)) * self.quantity
        Payment.objects.create(
            order=self,
            variant="default",           # maps to PAYMENT_VARIANTS["default"]
            currency="USD",
            total=total,
            description=f"Payment for Order #{self.pk}",
        )


# ─── Payment (django-payments) ─────────────────────────────────────────────
class Payment(BasePayment):
    """
    Concrete payment model.

    Inherits everything from ``payments.models.BasePayment`` and adds
    a foreign-key back to our Order.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")

    def get_failure_url(self) -> str:
        return f"http://{settings.PAYMENT_HOST}/api/orders/{self.order_id}/"

    def get_success_url(self) -> str:
        return f"http://{settings.PAYMENT_HOST}/api/orders/{self.order_id}/"

    def get_purchased_items(self):
        order = self.order
        yield PurchasedItem(
            name=order.product.name,
            sku=str(order.product.pk),
            quantity=order.quantity,
            price=order.product.price,
            currency="USD",
        )


# ─── CustomerNote (encrypted field demo) ───────────────────────────────────
class CustomerNote(TimeStampedModel):
    """
    Stores a private note for a user.

    ``private_note`` is encrypted at rest via django-fernet-encrypted-fields.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_note",
    )
    private_note = EncryptedTextField(
        blank=True,
        default="",
        help_text="This field is Fernet-encrypted at rest.",
    )

    def __str__(self):
        return f"Note for {self.user}"
