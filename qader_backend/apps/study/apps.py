from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StudyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.study"
    verbose_name = _("Study & Progress")

    def ready(self):
        try:
            import apps.study.signals  # noqa F401
        except ImportError:
            pass
