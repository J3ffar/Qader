import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from django.conf import settings
from django.utils.text import slugify
from django.core.files.base import ContentFile
from faker import Faker  # Needed for ImageField

# Import necessary factories from other apps
from apps.users.tests.factories import UserFactory

# Import models from the gamification app
from ..models import (
    PointLog,
    Badge,
    UserBadge,
    RewardStoreItem,
    UserRewardPurchase,
    PointReason,
)

fake = Faker()


class PointLogFactory(DjangoModelFactory):
    class Meta:
        model = PointLog

    user = factory.SubFactory(UserFactory)
    points_change = factory.Iterator([-10, -5, 1, 5, 10, 50])
    # Use PointReason enum for choices
    reason_code = factory.Iterator(
        [
            PointReason.QUESTION_SOLVED,
            PointReason.TEST_COMPLETED,
            PointReason.REWARD_PURCHASE,
            PointReason.ADMIN_ADJUSTMENT,
        ]
    )
    description = factory.LazyAttribute(lambda o: f"Log entry for {o}")
    timestamp = factory.LazyFunction(timezone.now)
    content_type = None
    object_id = None


class BadgeFactory(DjangoModelFactory):
    class Meta:
        model = Badge
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Awesome Badge {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.LazyAttribute(lambda o: f"Description for {o.name}")

    criteria_type = factory.Iterator(
        Badge.BadgeCriteriaType.choices, getter=lambda c: c[0]
    )

    @factory.lazy_attribute
    def target_value(self):
        """Ensure target_value is None if criteria_type is OTHER."""
        if self.criteria_type == Badge.BadgeCriteriaType.OTHER:
            return None
        # Provide a sensible default for other types
        return fake.random_int(min=1, max=50)

    icon = factory.django.ImageField(
        filename=factory.LazyAttribute(lambda o: f"{o}.png"),
        color="blue",  # Simple placeholder image
        icon=ContentFile(
            b"dummy image content",
            name=factory.LazyAttribute(lambda o: f"{o}.png"),
        ),
    )

    criteria_description = "Earn this by being awesome."
    is_active = True


class UserBadgeFactory(DjangoModelFactory):
    class Meta:
        model = UserBadge
        # Consider removing django_get_or_create from UserBadgeFactory unless
        # you specifically need that behavior and handle potential IntegrityErrors
        # in tests where duplicates might be created.
        # django_get_or_create = ("user", "badge")

    user = factory.SubFactory(UserFactory)
    badge = factory.SubFactory(BadgeFactory)
    earned_at = factory.LazyFunction(timezone.now)


class RewardStoreItemFactory(DjangoModelFactory):
    class Meta:
        model = RewardStoreItem

    name = factory.Sequence(lambda n: f"Reward Item {n}")
    description = factory.LazyAttribute(lambda o: f"Details about {o.name}")
    item_type = factory.Iterator(
        [
            RewardStoreItem.ItemType.AVATAR,
            RewardStoreItem.ItemType.MATERIAL,
            RewardStoreItem.ItemType.COMPETITION_ENTRY,
        ]
    )
    cost_points = factory.Iterator([100, 250, 500, 1000])
    image = factory.django.ImageField(
        filename=factory.LazyAttribute(lambda o: f"reward_{o}.jpg"),
        color="green",
    )
    asset_file = factory.django.FileField(
        filename=factory.LazyAttribute(lambda o: f"reward_asset_{o}.pdf"),
        data=b"Dummy file content for testing.",  # Provide some dummy data
    )
    is_active = True


class UserRewardPurchaseFactory(DjangoModelFactory):
    class Meta:
        model = UserRewardPurchase

    user = factory.SubFactory(UserFactory)
    item = factory.SubFactory(RewardStoreItemFactory)
    points_spent = factory.LazyAttribute(lambda o: o.item.cost_points)
    purchased_at = factory.LazyFunction(timezone.now)
