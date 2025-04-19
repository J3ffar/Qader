import pytest
from django.urls import reverse

from apps.users.tests.factories import UserFactory

from .factories import (
    BadgeFactory,
    PointLogFactory,
    UserBadgeFactory,
    RewardStoreItemFactory,
)
from ..models import UserRewardPurchase, PointLog
from apps.users.models import UserProfile  # For checking points update

pytestmark = pytest.mark.django_db


# --- Test GamificationSummaryView ---
def test_get_gamification_summary_unauthenticated(api_client):
    url = reverse("api:v1:gamification:summary")
    response = api_client.get(url)
    assert response.status_code == 401  # Use 401 for JWT


def test_get_gamification_summary_authenticated(authenticated_client):
    user = authenticated_client.user
    profile = user.profile
    profile.points = 550
    profile.current_streak_days = 5
    profile.longest_streak_days = 10
    profile.save()

    url = reverse("api:v1:gamification:summary")
    response = authenticated_client.get(url)

    assert response.status_code == 200
    expected_data = {
        "points": 550,
        "current_streak": 5,
        "longest_streak": 10,
    }
    assert response.data == expected_data


# --- Test BadgeListView ---
def test_list_badges_unauthenticated(api_client):
    url = reverse("api:v1:gamification:badge-list")
    response = api_client.get(url)
    assert response.status_code == 401


def test_list_badges_authenticated(authenticated_client):
    user = authenticated_client.user
    badge1 = BadgeFactory(is_active=True)
    badge2 = BadgeFactory(is_active=True)
    badge3 = BadgeFactory(is_active=True)
    BadgeFactory(is_active=False)  # Inactive badge

    # User has earned badge1 and badge3
    UserBadgeFactory(user=user, badge=badge1)
    UserBadgeFactory(user=user, badge=badge3)

    url = reverse("api:v1:gamification:badge-list")
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 3  # Only active badges

    results_map = {item["slug"]: item for item in response.data}

    assert results_map[badge1.slug]["is_earned"] is True
    assert results_map[badge1.slug]["earned_at"] is not None

    assert results_map[badge2.slug]["is_earned"] is False
    assert results_map[badge2.slug]["earned_at"] is None

    assert results_map[badge3.slug]["is_earned"] is True
    assert results_map[badge3.slug]["earned_at"] is not None


# --- Test RewardStoreItemViewSet ---
def test_list_rewards_unauthenticated(api_client):
    url = reverse("api:v1:gamification:reward-store-list")
    response = api_client.get(url)
    assert response.status_code == 401


def test_list_rewards_authenticated(authenticated_client):
    item1 = RewardStoreItemFactory(is_active=True)
    item2 = RewardStoreItemFactory(is_active=True)
    RewardStoreItemFactory(is_active=False)  # Inactive

    url = reverse("api:v1:gamification:reward-store-list")
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 2  # Only active items
    slugs = [item["name"] for item in response.data]
    assert item1.name in slugs
    assert item2.name in slugs


# --- Test RewardPurchaseView ---
def test_purchase_reward_unauthenticated(api_client):
    item = RewardStoreItemFactory(cost_points=100)
    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = api_client.post(url)
    assert response.status_code == 401


def test_purchase_reward_unsubscribed_user(authenticated_client):
    """Authenticated but not subscribed users cannot purchase."""
    item = RewardStoreItemFactory(cost_points=100)
    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = authenticated_client.post(url)
    # Expecting 403 Forbidden based on IsSubscribed permission
    assert response.status_code == 403


def test_purchase_reward_success(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    profile.points = 500
    profile.save()
    item = RewardStoreItemFactory(cost_points=200, is_active=True)

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = subscribed_client.post(url)

    assert response.status_code == 200
    assert response.data["item_id"] == item.id
    assert response.data["item_name"] == item.name
    assert response.data["points_spent"] == 200
    assert response.data["remaining_points"] == 300
    assert response.data["message"] == "Purchase successful!"

    profile.refresh_from_db()
    assert profile.points == 300
    assert UserRewardPurchase.objects.filter(user=user, item=item).exists()
    assert PointLog.objects.filter(user=user, points_change=-200).exists()


def test_purchase_reward_insufficient_points(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    profile.points = 100
    profile.save()
    item = RewardStoreItemFactory(cost_points=200, is_active=True)

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = subscribed_client.post(url)

    assert response.status_code == 400
    assert "Insufficient points" in response.data["detail"]
    profile.refresh_from_db()
    assert profile.points == 100  # Unchanged


def test_purchase_reward_inactive_item(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    profile.points = 500
    profile.save()
    item = RewardStoreItemFactory(cost_points=200, is_active=False)

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = subscribed_client.post(url)

    assert (
        response.status_code == 404
    )  # Not found because inactive item is filtered by service


def test_purchase_reward_non_existent_item(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    profile.points = 500
    profile.save()

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": 999})
    response = subscribed_client.post(url)

    assert response.status_code == 404


# --- Test PointLogViewSet ---
def test_list_point_log_unauthenticated(api_client):
    url = reverse("api:v1:gamification:point-log-list")
    response = api_client.get(url)
    assert response.status_code == 401


def test_list_point_log_authenticated(authenticated_client):
    user = authenticated_client.user
    other_user = UserFactory()

    # Create logs for both users
    log1_user = PointLogFactory(user=user, points_change=10)
    PointLogFactory(user=other_user, points_change=5)  # Log for other user
    log2_user = PointLogFactory(user=user, points_change=-5)

    url = reverse("api:v1:gamification:point-log-list")
    response = authenticated_client.get(url)

    assert response.status_code == 200
    assert response.data["count"] == 2  # Only logs for the authenticated user
    results = response.data["results"]
    result_ids = {item["id"] for item in results}

    assert log1_user.id in result_ids
    assert log2_user.id in result_ids
    assert "points_change" in results[0]
    assert "reason_code" in results[0]
    assert "timestamp" in results[0]
