from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SupportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.support"
    verbose_name = _("Support Management")

    def ready(self):
        # Import signals here to ensure they are connected when the app is ready.
        import apps.support.signals  # noqa: F401 (prevents unused import warning)
