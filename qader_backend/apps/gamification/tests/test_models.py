import pytest
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType

# Import factories and models
from .factories import (
    PointLogFactory,
    BadgeFactory,
    UserBadgeFactory,
    RewardStoreItemFactory,
    UserRewardPurchaseFactory,
)
from ..models import (
    PointLog,
    Badge,
    PointReason,
    UserBadge,
    RewardStoreItem,
    UserRewardPurchase,
)
from apps.users.tests.factories import UserFactory
from apps.learning.tests.factories import QuestionFactory  # Example for related object

pytestmark = pytest.mark.django_db


# --- Test PointLog Model ---
def test_point_log_creation():
    log = PointLogFactory(reason_code=PointReason.TEST_COMPLETED)
    assert PointLog.objects.count() == 1
    reason_display = log.get_reason_code_display()
    expected_str = (
        f"{log.user.username}: {log.points_change:+} points "
        f"({reason_display}) at {log.timestamp}"
    )
    # --- END FIXED ---

    assert str(log) == expected_str


def test_point_log_generic_relation():
    user = UserFactory()
    question = QuestionFactory()
    log = PointLogFactory(
        user=user,
        points_change=1,
        reason_code="QUESTION_SOLVED",
        related_object=question,
    )
    assert log.content_type == ContentType.objects.get_for_model(question)
    assert log.object_id == question.pk
    assert log.related_object == question


# --- Test Badge Model ---
def test_badge_creation():
    badge = BadgeFactory(name="Super Learner")
    assert Badge.objects.count() == 1
    assert badge.slug == "super-learner"
    assert badge.icon is not None
    assert str(badge) == "Super Learner"


# --- Test UserBadge Model ---
def test_user_badge_creation():
    user_badge = UserBadgeFactory()
    assert UserBadge.objects.count() == 1
    assert (
        str(user_badge) == f"{user_badge.user.username} earned {user_badge.badge.name}"
    )


def test_user_badge_uniqueness():
    """Test that a user cannot earn the same badge twice."""
    user_badge = UserBadgeFactory()
    # Verify the initial badge exists
    assert UserBadge.objects.filter(
        user=user_badge.user, badge=user_badge.badge
    ).exists()
    assert UserBadge.objects.count() == 1  # Verify starting count

    # Expect an IntegrityError when trying to create a duplicate
    with pytest.raises(IntegrityError):
        UserBadgeFactory(user=user_badge.user, badge=user_badge.badge)


# --- Test RewardStoreItem Model ---
def test_reward_store_item_creation():
    item = RewardStoreItemFactory(name="Cool Avatar", cost_points=500)
    assert RewardStoreItem.objects.count() == 1
    assert item.name == "Cool Avatar"
    assert item.cost_points == 500
    assert str(item) == "Cool Avatar (500 points)"


# --- Test UserRewardPurchase Model ---
def test_user_reward_purchase_creation():
    purchase = UserRewardPurchaseFactory()
    assert UserRewardPurchase.objects.count() == 1
    assert purchase.points_spent == purchase.item.cost_points
    assert (
        str(purchase)
        == f"{purchase.user.username} purchased {purchase.item.name} at {purchase.purchased_at}"
    )
