# qader_backend/apps/users/constants.py

from django.db import models
from django.utils.translation import gettext_lazy as _


class AccountTypeChoices(models.TextChoices):
    """Defines the types of user accounts regarding subscription status."""

    FREE_TRIAL = "FREE_TRIAL", _("Free Trial")  # Limited access, short duration
    SUBSCRIBED = "SUBSCRIBED", _("Subscribed")  # Standard paid subscription
    # Add other potential types later, e.g.:
    # PREMIUM = 'PREMIUM', _('Premium')
    # ENTERPRISE = 'ENTERPRISE', _('Enterprise')
    # PERMANENT = 'PERMANENT', _('Permanent Access') # If needed


# --- Subscription Plan Choices ---
class SubscriptionTypeChoices(models.TextChoices):
    """Defines the distinct types of subscription plans or codes."""

    MONTH_1 = "1_month", _("1 Month")
    MONTH_3 = "3_months", _("3 Months")
    MONTH_12 = "12_months", _("12 Months")
    CUSTOM = "custom", _("Custom Duration")  # For codes not tied to a standard plan


# --- Centralized Plan Configuration ---
# Maps the enum value to its properties. Used by serializers, views, commands.
SUBSCRIPTION_PLANS_CONFIG = {
    SubscriptionTypeChoices.MONTH_1: {
        "id": SubscriptionTypeChoices.MONTH_1.value,
        "name": _("1 Month Access"),
        "description": _("Full access to all platform features for 30 days."),
        "duration_days": 30,
        "prefix": "QDR1M",  # For code generation
        "cli_name": "1m",  # For management command argument
    },
    SubscriptionTypeChoices.MONTH_3: {
        "id": SubscriptionTypeChoices.MONTH_3.value,
        "name": _("3 Months Access"),
        "description": _(
            "Full access to all platform features for 91 days (approx. 3 months)."
        ),
        "duration_days": 91,
        "prefix": "QDR3M",
        "cli_name": "3m",
    },
    SubscriptionTypeChoices.MONTH_12: {
        "id": SubscriptionTypeChoices.MONTH_12.value,
        "name": _("12 Months Access"),
        "description": _("Full access to all platform features for 365 days (1 year)."),
        "duration_days": 365,
        "prefix": "QDR12M",
        "cli_name": "12m",
    },
    # NOTE: 'CUSTOM' is a type, but not typically listed as a purchasable 'plan'.
    # It might be included if needed for displaying custom codes, but usually excluded
    # from views listing standard plans.
    SubscriptionTypeChoices.CUSTOM: {
        "id": SubscriptionTypeChoices.CUSTOM.value,
        "name": _("Custom Duration"),
        "description": _(
            "Subscription duration determined by the specific serial code."
        ),
        "duration_days": None,  # Duration varies
        "prefix": "QDRCST",
        "cli_name": "custom",  # Less likely needed for generation command arg
    },
}

# --- Other Enums (Moved here for consistency, if desired) ---


class GenderChoices(models.TextChoices):
    MALE = "male", _("Male")
    FEMALE = "female", _("Female")


class RoleChoices(models.TextChoices):
    STUDENT = "student", _("Student")
    ADMIN = "admin", _("Admin")
    SUB_ADMIN = "sub_admin", _("Sub-Admin")


class DarkModePrefChoices(models.TextChoices):
    LIGHT = "light", _("Light")
    DARK = "dark", _("Dark")
    SYSTEM = "system", _("System")
