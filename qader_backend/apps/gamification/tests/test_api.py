# qader_backend/apps/gamification/tests/test_api.py

import pytest
from django.urls import reverse
from unittest.mock import patch  # For potentially mocking service calls if needed

from apps.users.tests.factories import UserFactory
from ..services import PurchaseError  # Import the specific exception
from ..models import (
    UserRewardPurchase,
    PointLog,
    RewardStoreItem,  # Import model for DoesNotExist check
    UserBadge,  # Import for badge tests
)
from apps.users.models import UserProfile

from .factories import (
    BadgeFactory,
    PointLogFactory,
    UserBadgeFactory,
    RewardStoreItemFactory,
)

pytestmark = pytest.mark.django_db


# --- Test GamificationSummaryView (No change needed) ---
def test_get_gamification_summary_unauthenticated(api_client):
    url = reverse("api:v1:gamification:summary")
    response = api_client.get(url)
    assert response.status_code == 401


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


# --- Test BadgeListView (No change needed) ---
def test_list_badges_unauthenticated(api_client):
    url = reverse("api:v1:gamification:badge-list")
    response = api_client.get(url)
    assert response.status_code == 401


def test_list_badges_authenticated(authenticated_client):
    user = authenticated_client.user
    # Use specific names/slugs for easier assertion
    badge_earned_1 = BadgeFactory(name="Earned Badge 1", is_active=True)
    badge_not_earned = BadgeFactory(name="Not Earned Badge", is_active=True)
    badge_earned_2 = BadgeFactory(name="Earned Badge 2", is_active=True)
    BadgeFactory(name="Inactive Badge", is_active=False)  # Inactive badge

    # User has earned badge1 and badge3
    UserBadgeFactory(user=user, badge=badge_earned_1)
    UserBadgeFactory(user=user, badge=badge_earned_2)

    url = reverse("api:v1:gamification:badge-list")
    response = authenticated_client.get(url)

    assert response.status_code == 200
    # Should return only the 3 *active* badges
    assert isinstance(response.data, list), "Response data should be a list"
    assert len(response.data) == 3, "Should only list active badges"

    # Create a map for easier lookup by slug
    results_map = {item["slug"]: item for item in response.data}

    # Verify badge 1 (earned)
    assert badge_earned_1.slug in results_map
    assert results_map[badge_earned_1.slug]["is_earned"] is True
    assert results_map[badge_earned_1.slug]["earned_at"] is not None
    assert "icon_url" in results_map[badge_earned_1.slug]
    assert results_map[badge_earned_1.slug]["icon_url"].endswith(
        ".png"
    )  # Or appropriate extension

    # Verify badge 2 (not earned)
    assert badge_not_earned.slug in results_map
    assert results_map[badge_not_earned.slug]["is_earned"] is False
    assert results_map[badge_not_earned.slug]["earned_at"] is None
    assert "icon_url" in results_map[badge_not_earned.slug]

    # Verify badge 3 (earned)
    assert badge_earned_2.slug in results_map
    assert results_map[badge_earned_2.slug]["is_earned"] is True
    assert results_map[badge_earned_2.slug]["earned_at"] is not None
    assert "icon_url" in results_map[badge_earned_2.slug]

    # Verify inactive badge is NOT present
    assert "inactive-badge" not in results_map


# --- Test RewardStoreItemViewSet (No change needed) ---
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

    # --- FIXED: Handle potential pagination ---
    if isinstance(response.data, dict) and "results" in response.data:
        results = response.data["results"]
        # Check count if pagination is active
        assert response.data["count"] == 2, "Count should reflect only active items"
    elif isinstance(response.data, list):
        results = response.data
        assert len(results) == 2, "Should list only active items"
    else:
        pytest.fail(f"Unexpected response data format: {type(response.data)}")
    # --- END FIXED ---

    assert len(results) == 2  # Double check length of results list
    names = [item["name"] for item in results]  # Access items from results list
    assert item1.name in names
    assert item2.name in names


# --- Test RewardPurchaseView (Adjusted for service behavior) ---
def test_purchase_reward_unauthenticated(api_client):
    item = RewardStoreItemFactory(cost_points=100)
    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = api_client.post(url)
    assert response.status_code == 401


def test_purchase_reward_unsubscribed_user(authenticated_client):
    item = RewardStoreItemFactory(cost_points=100)
    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = authenticated_client.post(url)
    assert response.status_code == 403


def test_purchase_reward_success(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    initial_points = 500
    item_cost = 200
    profile.points = initial_points
    profile.save()
    item = RewardStoreItemFactory(cost_points=item_cost, is_active=True)

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = subscribed_client.post(url)

    assert response.status_code == 200
    # Check response structure matches RewardPurchaseResponseSerializer
    assert response.data["item_id"] == item.id
    assert response.data["item_name"] == item.name
    assert response.data["points_spent"] == item_cost
    assert response.data["remaining_points"] == initial_points - item_cost
    # assert "message" in response.data # Message is optional

    profile.refresh_from_db()
    assert profile.points == initial_points - item_cost
    assert UserRewardPurchase.objects.filter(user=user, item=item).exists()
    assert PointLog.objects.filter(
        user=user, points_change=-item_cost, reason_code="REWARD_PURCHASE"
    ).exists()


def test_purchase_reward_insufficient_points(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    profile.points = 100
    profile.save()
    item = RewardStoreItemFactory(cost_points=200, is_active=True)

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = subscribed_client.post(url)

    assert response.status_code == 400  # Service raises PurchaseError -> 400
    assert "Insufficient points" in response.data["detail"]
    profile.refresh_from_db()
    assert profile.points == 100


def test_purchase_reward_inactive_item(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    profile.points = 500
    profile.save()
    item = RewardStoreItemFactory(cost_points=200, is_active=False)

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": item.id})
    response = subscribed_client.post(url)

    # Service raises RewardStoreItem.DoesNotExist -> View returns 404
    assert response.status_code == 404
    assert "not found" in response.data["detail"]  # Check error message


def test_purchase_reward_non_existent_item(subscribed_client):
    user = subscribed_client.user
    profile = user.profile
    profile.points = 500
    profile.save()

    url = reverse("api:v1:gamification:reward-purchase", kwargs={"item_id": 999})
    response = subscribed_client.post(url)

    # Service raises RewardStoreItem.DoesNotExist -> View returns 404
    assert response.status_code == 404
    assert "not found" in response.data["detail"]  # Check error message


# --- Test PointLogViewSet (No change needed) ---
def test_list_point_log_unauthenticated(api_client):
    url = reverse("api:v1:gamification:point-log-list")
    response = api_client.get(url)
    assert response.status_code == 401


def test_list_point_log_authenticated(authenticated_client):
    user = authenticated_client.user
    other_user = UserFactory()

    # Create logs for both users
    log1_user = PointLogFactory(user=user, points_change=10)
    PointLogFactory(user=other_user, points_change=5)
    log2_user = PointLogFactory(user=user, points_change=-5)

    url = reverse("api:v1:gamification:point-log-list")
    response = authenticated_client.get(url)

    assert response.status_code == 200
    # Assuming default pagination is active for ListAPIView unless set otherwise
    # Check structure assuming pagination. If no pagination, check list length directly.
    if "results" in response.data:  # Check if paginated
        assert response.data["count"] == 2
        results = response.data["results"]
    else:  # Not paginated
        assert len(response.data) == 2
        results = response.data

    result_ids = {item["id"] for item in results}
    assert log1_user.id in result_ids
    assert log2_user.id in result_ids
    assert "points_change" in results[0]
    assert "reason_code" in results[0]
    assert "timestamp" in results[0]
