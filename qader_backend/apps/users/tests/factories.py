import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import (
    SubscriptionTypeChoices,
    UserProfile,
    SerialCode,
    RoleChoices,
    GenderChoices,
    DarkModePrefChoices,
)
from django.contrib.auth.hashers import make_password

import logging

logger = logging.getLogger(__name__)


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances, with helpers for roles and profiles."""

    class Meta:
        model = User
        django_get_or_create = ("username",)  # Keep this

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Sequence(lambda n: f"testuser_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@qader.test")
    is_active = True  # Default to active, override in fixtures/tests as needed
    password = make_password("defaultpassword")  # Set hashed password directly

    # Removed post_generation hook for password, set directly above

    # Role flags
    @factory.post_generation
    def make_staff(self, create, extracted, **kwargs):
        """Flag to make the user staff."""
        if create and extracted:
            self.is_staff = True
            self.save(update_fields=["is_staff"])

    @factory.post_generation
    def make_admin(self, create, extracted, **kwargs):
        """Flag to make the user superuser/admin."""
        if create and extracted:
            self.is_staff = True
            self.is_superuser = True
            self.save(update_fields=["is_staff", "is_superuser"])
            # Attempt to set profile role - profile SHOULD exist due to signal
            try:
                # Profile *should* exist from signal. Don't refresh self here.
                profile = self.profile  # Access via related manager/descriptor
                if profile.role != RoleChoices.ADMIN:
                    profile.role = RoleChoices.ADMIN
                    profile.save(update_fields=["role"])
            except UserProfile.DoesNotExist:
                logger.error(
                    f"UserProfile not found via signal for {self.username} in make_admin. Creating."
                )
                # If signal failed, create it (less ideal)
                UserProfile.objects.create(user=self, role=RoleChoices.ADMIN)
            except Exception as e:
                logger.error(
                    f"Error setting admin role on profile for {self.username}: {e}"
                )

    # Profile data convenience
    @factory.post_generation
    def profile_data(self, create, extracted: dict, **kwargs):
        """Allows passing profile data directly: UserFactory(profile_data={'full_name': '...'})"""
        if create and extracted and isinstance(extracted, dict):
            try:
                # Profile should exist due to signal. Use get_or_create defensively.
                profile, created = UserProfile.objects.get_or_create(user=self)
                if created:
                    logger.warning(
                        f"Profile created directly in profile_data hook for {self.username} (signal might have failed or run late)"
                    )
                for key, value in extracted.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                    else:
                        logger.warning(
                            f"UserProfile has no attribute '{key}' provided in profile_data factory arg."
                        )
                profile.save()  # Save all changes made here
            except Exception as e:
                logger.error(f"Error setting profile_data for {self.username}: {e}")


class SerialCodeFactory(DjangoModelFactory):
    """Factory for creating SerialCode instances, with traits for types."""

    class Meta:
        model = SerialCode

    code = factory.Sequence(lambda n: f"QADER-FACT-{n:06d}")  # Increased padding
    subscription_type = None
    duration_days = 30
    is_active = True
    is_used = False
    used_by = None
    used_at = None
    created_by = None  # TODO: Consider setting to an admin user fixture if needed
    notes = factory.Faker("sentence")

    # Traits for common subscription types
    class Params:
        type_1_month = factory.Trait(
            subscription_type=SubscriptionTypeChoices.MONTH_1, duration_days=30
        )
        type_6_months = factory.Trait(
            subscription_type=SubscriptionTypeChoices.MONTH_6, duration_days=183
        )
        type_12_months = factory.Trait(
            subscription_type=SubscriptionTypeChoices.MONTH_12, duration_days=365
        )
        type_custom = factory.Trait(
            subscription_type=SubscriptionTypeChoices.CUSTOM,
            # duration_days must be set explicitly when using this trait
        )
