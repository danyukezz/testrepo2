"""
Management command to load tiny sample data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from eav.models import Attribute

from core.models import Product, Order, CustomerNote

User = get_user_model()


class Command(BaseCommand):
    help = "Load sample products, EAV attributes, an order, and a customer note."

    def handle(self, *args, **options):
        # ── User ───────────────────────────────────────────────────────────
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com", "is_staff": False},
        )
        if created:
            user.set_password("demo1234")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created user 'demo' (password: demo1234)"))

        # ── EAV attributes ────────────────────────────────────────────────
        color_attr, _ = Attribute.objects.get_or_create(
            slug="color",
            defaults={"name": "Color", "datatype": Attribute.TYPE_TEXT},
        )
        size_attr, _ = Attribute.objects.get_or_create(
            slug="size",
            defaults={"name": "Size", "datatype": Attribute.TYPE_TEXT},
        )

        # ── Products ──────────────────────────────────────────────────────
        p1, _ = Product.objects.get_or_create(
            name="T-Shirt",
            defaults={"price": "19.99", "description": "A comfy cotton T-Shirt."},
        )
        p1.tags.add("clothing", "cotton")
        p1.eav.color = "blue"
        p1.eav.size = "M"
        p1.save()

        p2, _ = Product.objects.get_or_create(
            name="USB-C Cable",
            defaults={"price": "9.50", "description": "1 m braided cable."},
        )
        p2.tags.add("electronics", "accessories")
        p2.eav.color = "black"
        p2.save()

        p3, _ = Product.objects.get_or_create(
            name="Notebook",
            defaults={"price": "4.99", "description": "Ruled, 100 pages."},
        )
        p3.tags.add("stationery")
        p3.save()

        self.stdout.write(self.style.SUCCESS(f"Products: {Product.objects.count()}"))

        # ── Order (triggers lifecycle → creates Payment) ─────────────────
        if not Order.objects.filter(user=user, product=p1).exists():
            order = Order.objects.create(user=user, product=p1, quantity=2)
            self.stdout.write(self.style.SUCCESS(
                f"Created Order #{order.pk} with auto-Payment "
                f"(total={order.payments.first().total})"
            ))

        # ── CustomerNote (encrypted) ─────────────────────────────────────
        note, created = CustomerNote.objects.get_or_create(
            user=user,
            defaults={"private_note": "This note is Fernet-encrypted at rest! 🔐"},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created encrypted CustomerNote"))

        self.stdout.write(self.style.SUCCESS("✅  Sample data loaded."))
