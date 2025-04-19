import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from ..models import (
    SubscriptionTypeChoices,
    UserProfile,
    SerialCode,
    RoleChoices,
)  # Relative import within the app


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        # If using signals to create profile, prevent recursion:
        django_get_or_create = ("username",)  # Use if needed
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    is_active = True  # Default active users for tests

    # Handle password setting robustly
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or "defaultpassword"  # Use provided password or default
        self.set_password(password)
        if create:
            self.save()  # Save after setting password

    # Helper flags for creating different user types easily
    @factory.post_generation
    def make_staff(self, create, extracted, **kwargs):
        if create and extracted:
            self.is_staff = True
            self.save(update_fields=["is_staff"])

    @factory.post_generation
    def make_admin(self, create, extracted, **kwargs):
        if create and extracted:
            self.is_staff = True
            self.is_superuser = True
            self.save(update_fields=["is_staff", "is_superuser"])
            # Ensure profile role reflects admin status (profile created by signal)
            try:
                profile = self.profile
                profile.role = RoleChoices.ADMIN
                profile.save(update_fields=["role"])
            except UserProfile.DoesNotExist:
                # Handle case where signal might not have run yet in rare test scenarios
                UserProfile.objects.create(user=self, role=RoleChoices.ADMIN)
            except Exception as e:
                print(
                    f"Warning: Could not set admin role on profile for {self.username}: {e}"
                )


class SerialCodeFactory(DjangoModelFactory):
    class Meta:
        model = SerialCode

    code = factory.Sequence(lambda n: f"QADER-TEST-{n:05d}")
    subscription_type = None  # Default to None unless specified
    duration_days = 30
    is_active = True
    is_used = False
    used_by = None
    used_at = None
    created_by = None

    # Optional: Add traits for common types
    class Params:
        type_1_month = factory.Trait(
            subscription_type=SubscriptionTypeChoices.MONTH_1,
            duration_days=30,  # Set corresponding duration
        )
        type_6_months = factory.Trait(
            subscription_type=SubscriptionTypeChoices.MONTH_6,
            duration_days=183,  # Set corresponding duration
        )
        type_12_months = factory.Trait(
            subscription_type=SubscriptionTypeChoices.MONTH_12,
            duration_days=365,  # Set corresponding duration
        )
        type_custom = factory.Trait(
            subscription_type=SubscriptionTypeChoices.CUSTOM,
            # duration_days should be set manually for custom
        )


# Optional: UserProfileFactory - generally not needed if signal works reliably
# class UserProfileFactory(DjangoModelFactory):
#     class Meta:
#         model = UserProfile
#
#     # Ensure user is created without triggering recursion if UserFactory calls this
#     user = factory.SubFactory(UserFactory, profile=None)
#     full_name = factory.Faker('name')
#     role = RoleChoices.STUDENT
#     # ... other default profile fields ...
