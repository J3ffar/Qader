from django.db import models


class BaseModel(models.Model):
    """
    An abstract base class model that provides self-updating
    `created_at` and `updated_at` fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
