"""
Mini Shop – test suite.

Tests:
  1. Product creation + tagging
  2. Product filtering (django-filter)
  3. Authenticated /api/me/ endpoint (drf-auth-kit JWT)
  4. Order creation triggers Payment (django-lifecycle)
  5. Encrypted field round-trip (django-fernet-encrypted-fields)
  6. EAV attribute setting
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Product, Order, Payment, CustomerNote
from eav.models import Attribute

User = get_user_model()


class ProductTests(TestCase):
    """Product creation, tags, and filtering."""

    def setUp(self):
        self.client = APIClient()
        self.p1 = Product.objects.create(name="Widget", price=Decimal("12.50"))
        self.p1.tags.add("gadgets", "sale")
        self.p2 = Product.objects.create(name="Gizmo", price=Decimal("45.00"))
        self.p2.tags.add("gadgets")

    # 1 – basic creation
    def test_product_creation(self):
        self.assertEqual(Product.objects.count(), 2)
        self.assertIn("gadgets", [t.name for t in self.p1.tags.all()])

    # 2 – filtering by price
    def test_filter_by_price(self):
        resp = self.client.get("/api/products/", {"min_price": 20})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [p["name"] for p in resp.data["results"]]
        self.assertIn("Gizmo", names)
        self.assertNotIn("Widget", names)

    # 2b – filtering by tag
    def test_filter_by_tag(self):
        resp = self.client.get("/api/products/", {"tag": "sale"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [p["name"] for p in resp.data["results"]]
        self.assertIn("Widget", names)
        self.assertNotIn("Gizmo", names)


class AuthTests(TestCase):
    """Authenticated endpoint via JWT (drf-auth-kit / simplejwt)."""

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.client = APIClient()

    # 3 – /api/me/ requires auth
    def test_me_unauthenticated(self):
        resp = self.client.get("/api/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_authenticated(self):
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        resp = self.client.get("/api/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["username"], "tester")


class OrderLifecycleTests(TestCase):
    """Order creation triggers auto-Payment (django-lifecycle)."""

    def setUp(self):
        self.user = User.objects.create_user(username="buyer", password="pass1234")
        self.product = Product.objects.create(name="Book", price=Decimal("15.00"))

    # 4 – payment auto-created
    def test_order_creates_payment(self):
        order = Order.objects.create(user=self.user, product=self.product, quantity=3)
        self.assertEqual(order.payments.count(), 1)
        payment = order.payments.first()
        self.assertEqual(payment.total, Decimal("45.00"))
        self.assertEqual(payment.variant, "default")


class EncryptedFieldTests(TestCase):
    """CustomerNote encrypted field round-trip."""

    def setUp(self):
        self.user = User.objects.create_user(username="secretkeeper", password="pass1234")

    # 5 – write + read encrypted field
    def test_encrypted_note_round_trip(self):
        note = CustomerNote.objects.create(user=self.user, private_note="top secret 🔑")
        note.refresh_from_db()
        self.assertEqual(note.private_note, "top secret 🔑")


class EAVTests(TestCase):
    """EAV dynamic attributes on Product."""

    def setUp(self):
        import eav

        # Ensure Product is registered (may already be from apps.ready)
        try:
            eav.register(Product)
        except Exception:
            pass  # already registered

        Attribute.objects.get_or_create(
            slug="color",
            defaults={"name": "Color", "datatype": Attribute.TYPE_TEXT},
        )
        self.product = Product.objects.create(name="Hat", price=Decimal("8.00"))

    # 6 – set + read EAV attribute
    def test_eav_attribute(self):
        self.product.eav.color = "green"
        self.product.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.eav.color, "green")
