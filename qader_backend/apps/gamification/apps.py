from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GamificationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gamification"
    verbose_name = _("Gamification")

    def ready(self):
        try:
            import apps.gamification.signals  # noqa F401
        except ImportError:
            pass
