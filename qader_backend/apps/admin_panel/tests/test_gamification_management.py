import pytest
from django.urls import reverse
from rest_framework import status
from faker import Faker

# Use specific factory paths
from apps.gamification.tests.factories import BadgeFactory, RewardStoreItemFactory
from apps.gamification.models import Badge, RewardStoreItem


fake = Faker()

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

# --- Test AdminBadgeViewSet ---


class TestAdminBadgeViewSet:
    """Tests for the AdminBadgeViewSet endpoint."""

    list_url = reverse("api:v1:admin_panel:admin-badge-list")

    def detail_url(self, badge_id):
        return reverse("api:v1:admin_panel:admin-badge-detail", kwargs={"pk": badge_id})

    # --- Permission Tests ---
    def test_list_badges_unauthenticated(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_list_badges_standard_user(self, authenticated_client):
        response = authenticated_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_badge_standard_user(self, authenticated_client):
        data = {
            "name": "Test Badge",
            "slug": "test-badge",
            "criteria_type": Badge.BadgeCriteriaType.STUDY_STREAK,
            "target_value": 3,
        }
        response = authenticated_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # --- Admin CRUD Tests ---
    def test_list_badges_admin(self, admin_client):
        BadgeFactory.create_batch(3)
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert (
            len(response.data["results"]) >= 3
        )  # Check if created items are listed (consider pagination)

    def test_retrieve_badge_admin(self, admin_client):
        badge = BadgeFactory(
            criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK, target_value=5
        )
        url = self.detail_url(badge.id)
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == badge.id
        assert response.data["name"] == badge.name
        assert response.data["slug"] == badge.slug
        assert response.data["criteria_type"] == Badge.BadgeCriteriaType.STUDY_STREAK
        assert response.data["target_value"] == 5

    def test_retrieve_badge_not_found(self, admin_client):
        url = self.detail_url(9999)  # Non-existent ID
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_badge_admin_success(self, admin_client):
        badge_count = Badge.objects.count()
        data = {
            "name": "Super Streaker",
            "slug": "super-streaker-badge",
            "description": "Awarded for an amazing streak.",
            "criteria_description": "Maintain a 20-day streak.",
            "criteria_type": Badge.BadgeCriteriaType.STUDY_STREAK,
            "target_value": 20,
            "is_active": True,
        }
        response = admin_client.post(self.list_url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Badge.objects.count() == badge_count + 1
        created_badge = Badge.objects.get(slug=data["slug"])
        assert created_badge.name == data["name"]
        assert created_badge.criteria_type == data["criteria_type"]
        assert created_badge.target_value == data["target_value"]
        assert response.data["name"] == data["name"]

    def test_create_badge_admin_missing_required_field(self, admin_client):
        data = {  # Missing slug, name, criteria_type
            "description": "A badge.",
            "target_value": 10,
        }
        response = admin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data
        assert "slug" in response.data
        assert "criteria_type" in response.data

    def test_create_badge_admin_duplicate_slug(self, admin_client):
        existing_badge = BadgeFactory()
        data = {
            "name": "Another Badge Name",
            "slug": existing_badge.slug,  # Duplicate slug
            "criteria_type": Badge.BadgeCriteriaType.STUDY_STREAK,
            "target_value": 3,
        }
        response = admin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "slug" in response.data

    def test_update_badge_admin_success(self, admin_client):
        # Ensure the factory creates a badge suitable for update testing
        # Force a type that needs a target_value
        badge = BadgeFactory(
            name="Old Name",
            is_active=True,
            criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK,  # Create with this type directly
            target_value=5,
        )
        url = self.detail_url(badge.id)

        # Define the update payload
        update_data = {
            "name": "Updated Badge Name",
            "slug": badge.slug,
            "description": badge.description,
            "criteria_description": "Updated criteria.",
            "criteria_type": Badge.BadgeCriteriaType.STUDY_STREAK,
            "target_value": 10,  # Update target value
            "is_active": False,  # Update is_active
            # 'icon': None # Still omit for simplicity unless testing icon uploads
        }

        response = admin_client.put(url, data=update_data, format="json")

        assert response.status_code == status.HTTP_200_OK

        badge.refresh_from_db()
        assert badge.name == update_data["name"]
        assert not badge.is_active
        assert badge.target_value == update_data["target_value"]
        assert (
            badge.criteria_type == update_data["criteria_type"]
        )  # Verify type if needed
        assert response.data["name"] == update_data["name"]
        assert not response.data["is_active"]
        assert response.data["target_value"] == update_data["target_value"]

    def test_partial_update_badge_admin_success(self, admin_client):
        badge = BadgeFactory(is_active=True, target_value=7)
        url = self.detail_url(badge.id)
        data = {"is_active": False, "target_value": 8}  # Only update these
        response = admin_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        badge.refresh_from_db()
        assert badge.is_active == False
        assert badge.target_value == 8
        assert (
            badge.name == Badge.objects.get(id=badge.id).name
        )  # Check name is unchanged
        assert response.data["is_active"] == False
        assert response.data["target_value"] == 8

    def test_delete_badge_admin_success(self, admin_client):
        badge = BadgeFactory()
        badge_count = Badge.objects.count()
        url = self.detail_url(badge.id)
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Badge.objects.count() == badge_count - 1
        with pytest.raises(Badge.DoesNotExist):
            Badge.objects.get(id=badge.id)

    def test_delete_badge_not_found(self, admin_client):
        url = self.detail_url(9999)
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- Filtering/Ordering/Search Tests ---
    def test_list_badges_filter_by_criteria_type(self, admin_client):
        BadgeFactory.create_batch(2, criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK)
        BadgeFactory.create_batch(
            3, criteria_type=Badge.BadgeCriteriaType.QUESTIONS_SOLVED_CORRECTLY
        )
        url = f"{self.list_url}?criteria_type={Badge.BadgeCriteriaType.STUDY_STREAK}"
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Check results based on exact count or presence/absence
        results = response.data["results"]
        assert len(results) >= 2  # Should have at least the 2 created
        assert all(
            b["criteria_type"] == Badge.BadgeCriteriaType.STUDY_STREAK for b in results
        )

    def test_list_badges_search_by_name(self, admin_client):
        BadgeFactory(name="Super Special Badge Alpha")
        BadgeFactory(name="Another Boring Badge")
        url = f"{self.list_url}?search=Super Special"
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) >= 1
        assert results[0]["name"] == "Super Special Badge Alpha"

    def test_list_badges_order_by_target_value(self, admin_client):
        BadgeFactory(
            criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK, target_value=10
        )
        BadgeFactory(criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK, target_value=5)
        BadgeFactory(
            criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK, target_value=20
        )
        url = f"{self.list_url}?ordering=target_value"  # Ascending
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        values = [
            b["target_value"]
            for b in response.data["results"]
            if b["target_value"] is not None
        ]
        assert values == sorted(values)  # Check if sorted ascending

        url = f"{self.list_url}?ordering=-target_value"  # Descending
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        values = [
            b["target_value"]
            for b in response.data["results"]
            if b["target_value"] is not None
        ]
        assert values == sorted(values, reverse=True)  # Check if sorted descending


# --- Test AdminRewardStoreItemViewSet ---


class TestAdminRewardStoreItemViewSet:
    """Tests for the AdminRewardStoreItemViewSet endpoint."""

    list_url = reverse("api:v1:admin_panel:admin-reward-item-list")

    def detail_url(self, item_id):
        return reverse(
            "api:v1:admin_panel:admin-reward-item-detail", kwargs={"pk": item_id}
        )

    # --- Permission Tests ---
    def test_list_items_unauthenticated(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_list_items_standard_user(self, authenticated_client):
        response = authenticated_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # --- Admin CRUD Tests ---
    def test_list_items_admin(self, admin_client):
        RewardStoreItemFactory.create_batch(2)
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 2

    def test_retrieve_item_admin(self, admin_client):
        item = RewardStoreItemFactory(cost_points=150)
        url = self.detail_url(item.id)
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == item.id
        assert response.data["name"] == item.name
        assert response.data["cost_points"] == 150

    def test_create_item_admin_success(self, admin_client):
        item_count = RewardStoreItem.objects.count()
        data = {
            "name": "Special Avatar Pack",
            "description": "Unlock cool avatars.",
            "item_type": RewardStoreItem.ItemType.AVATAR,
            "cost_points": 500,
            "is_active": True,
        }
        response = admin_client.post(self.list_url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert RewardStoreItem.objects.count() == item_count + 1
        created_item = RewardStoreItem.objects.get(name=data["name"])
        assert created_item.cost_points == data["cost_points"]
        assert created_item.item_type == data["item_type"]

    def test_update_item_admin_success(self, admin_client):
        item = RewardStoreItemFactory(cost_points=100, is_active=True)
        url = self.detail_url(item.id)
        data = {
            "name": item.name,
            "description": "Updated description.",
            "item_type": item.item_type,
            "cost_points": 120,
            "is_active": False,
        }
        response = admin_client.put(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.cost_points == 120
        assert item.is_active == False
        assert item.description == "Updated description."

    def test_partial_update_item_admin_success(self, admin_client):
        item = RewardStoreItemFactory(cost_points=300)
        url = self.detail_url(item.id)
        data = {"cost_points": 350}
        response = admin_client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.cost_points == 350

    def test_delete_item_admin_success(self, admin_client):
        item = RewardStoreItemFactory()
        item_count = RewardStoreItem.objects.count()
        url = self.detail_url(item.id)
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert RewardStoreItem.objects.count() == item_count - 1
        with pytest.raises(RewardStoreItem.DoesNotExist):
            RewardStoreItem.objects.get(id=item.id)
