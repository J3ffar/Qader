import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from django.conf import settings
from django.utils.text import slugify

# Import necessary factories from other apps
from apps.users.tests.factories import UserFactory

# from apps.learning.tests.factories import QuestionFactory  # If needed for PointLog related_object
# from apps.study.tests.factories import UserTestAttemptFactory # If needed for PointLog related_object

# Import models from the gamification app
from ..models import PointLog, Badge, UserBadge, RewardStoreItem, UserRewardPurchase


class PointLogFactory(DjangoModelFactory):
    class Meta:
        model = PointLog

    user = factory.SubFactory(UserFactory)
    points_change = factory.Iterator([-10, -5, 1, 5, 10, 50])
    reason_code = factory.Iterator(
        ["QUESTION_SOLVED", "TEST_COMPLETED", "REWARD_PURCHASE", "ADMIN_ADJUSTMENT"]
    )
    description = factory.LazyAttribute(lambda o: f"Log entry for {o.reason_code}")
    timestamp = factory.LazyFunction(timezone.now)
    # related_object can be set explicitly in tests if needed
    content_type = None
    object_id = None


class BadgeFactory(DjangoModelFactory):
    class Meta:
        model = Badge
        django_get_or_create = ("slug",)  # Ensure unique slugs

    name = factory.Sequence(lambda n: f"Awesome Badge {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    description = factory.LazyAttribute(lambda o: f"Description for {o.name}")
    icon_class_or_image = factory.LazyAttribute(lambda o: f"icon-{o.slug}")
    criteria_description = "Earn this by being awesome."
    is_active = True


class UserBadgeFactory(DjangoModelFactory):
    class Meta:
        model = UserBadge
        # django_get_or_create = ("user", "badge")  # Prevent duplicates

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
    asset_url_or_data = factory.LazyAttribute(
        lambda o: f"/rewards/{slugify(o.name)}.png"
    )
    is_active = True


class UserRewardPurchaseFactory(DjangoModelFactory):
    class Meta:
        model = UserRewardPurchase

    user = factory.SubFactory(UserFactory)
    item = factory.SubFactory(RewardStoreItemFactory)
    points_spent = factory.LazyAttribute(lambda o: o.item.cost_points)
    purchased_at = factory.LazyFunction(timezone.now)
