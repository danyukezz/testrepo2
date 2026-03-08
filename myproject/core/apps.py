from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Mini Shop Core"

    def ready(self):
        # Register Product with django-eav2
        import eav
        from .models import Product

        eav.register(Product)
