import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from apps.users.models import UserProfile, SerialCode, RoleChoices  # Adjust import


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    # password = factory.PostGenerationMethodCall('set_password', 'defaultpassword') # Set password post-generation

    # Create profile automatically via signal, but allow overrides
    # profile = factory.RelatedFactory(UserProfileFactory, factory_related_name='user')

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        # Usage: UserFactory(password='...')
        if not create:
            # Simple build, do nothing.
            return
        # Use the default password if one wasn't provided.
        self.set_password(extracted or "defaultpassword")

    @factory.post_generation
    def make_staff(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:  # Usage: UserFactory(make_staff=True)
            self.is_staff = True
            self.save()

    @factory.post_generation
    def make_admin(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:  # Usage: UserFactory(make_admin=True)
            self.is_staff = True
            self.is_superuser = True
            profile = self.profile
            profile.role = RoleChoices.ADMIN
            profile.save()
            self.save()


class SerialCodeFactory(DjangoModelFactory):
    class Meta:
        model = SerialCode

    code = factory.Sequence(lambda n: f"CODE-{n:05d}")
    duration_days = 30
    is_active = True
    is_used = False
    used_by = None
    used_at = None
    created_by = None  # Optional: Link to an admin UserFactory instance


# Optional: UserProfileFactory if you need direct profile creation/overrides
# class UserProfileFactory(DjangoModelFactory):
#     class Meta:
#         model = UserProfile
#     user = factory.SubFactory(UserFactory, profile=None) # Avoid recursion
#     full_name = factory.Faker('name')
#     # ... other profile fields ...
