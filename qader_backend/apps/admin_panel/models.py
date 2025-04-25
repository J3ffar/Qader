from django.db import models
from django.utils.translation import gettext_lazy as _


class AdminPermission(models.Model):
    """
    Defines a specific permission that can be granted to a Sub-Admin.
    """

    # Use a slug for easier identification and use in code/API requests
    slug = models.SlugField(
        _("Slug"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_(
            "Unique identifier for the permission (e.g., 'view_users', 'manage_content')."
        ),
    )
    name = models.CharField(
        _("Name"),
        max_length=100,
        help_text=_("Human-readable name for the permission."),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Detailed explanation of what this permission allows."),
    )

    class Meta:
        verbose_name = _("Admin Permission")
        verbose_name_plural = _("Admin Permissions")
        ordering = ["name"]

    def __str__(self):
        return self.name
