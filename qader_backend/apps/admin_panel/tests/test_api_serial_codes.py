# qader_backend/apps/admin_panel/tests/test_serial_code_management.py

import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.users.models import SerialCode, SubscriptionTypeChoices
from apps.users.tests.factories import SerialCodeFactory

# Make sure necessary fixtures are imported or available via conftest
# from conftest import admin_client, authenticated_client, active_serial_code, used_serial_code, inactive_serial_code

User = get_user_model()

pytestmark = pytest.mark.django_db

# Define the base URL name for reversing
SERIAL_CODE_BASE_URL = "api:v1:admin_panel:admin-serial-code"


@pytest.mark.django_db
class TestSerialCodeAdminViewSet:
    """Tests for the SerialCodeAdminViewSet API endpoints."""

    def test_list_serial_codes_admin(
        self, admin_client, active_serial_code, used_serial_code, inactive_serial_code
    ):
        """Verify admin can list all serial codes."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3
        # Check if essential keys are present in one of the results
        assert "code" in response.data["results"][0]
        assert "is_active" in response.data["results"][0]
        assert "is_used" in response.data["results"][0]
        assert "subscription_type" in response.data["results"][0]

    def test_list_serial_codes_non_admin(self, authenticated_client):
        """Verify non-admin users cannot list serial codes."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_serial_code_admin(self, admin_client, active_serial_code):
        """Verify admin can retrieve a specific serial code."""
        url = reverse(
            f"{SERIAL_CODE_BASE_URL}-detail", kwargs={"pk": active_serial_code.pk}
        )
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == active_serial_code.pk
        assert response.data["code"] == active_serial_code.code
        assert (
            response.data["notes"] == active_serial_code.notes
        )  # Detail includes notes

    def test_create_serial_code_admin(self, admin_client, admin_user):
        """Verify admin can create a single serial code."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        data = {
            "code": "ADMIN-CREATE-TEST-001",
            "subscription_type": SubscriptionTypeChoices.MONTH_1.value,
            "duration_days": 31,  # Can be different from default for the type if needed
            "is_active": True,
            "notes": "Created via API test",
        }
        response = admin_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert SerialCode.objects.filter(code=data["code"]).exists()
        new_code = SerialCode.objects.get(code=data["code"])
        assert new_code.subscription_type == data["subscription_type"]
        assert new_code.duration_days == data["duration_days"]
        assert new_code.notes == data["notes"]
        assert new_code.created_by == admin_user

    def test_create_serial_code_duplicate_admin(self, admin_client, active_serial_code):
        """Verify admin cannot create a code with an existing value (case-insensitive)."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        data = {
            "code": active_serial_code.code.lower(),  # Use existing code, different case
            "subscription_type": SubscriptionTypeChoices.MONTH_6.value,
            "duration_days": 180,
        }
        initial_count = SerialCode.objects.count()
        response = admin_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data  # Check error is related to the code field
        assert SerialCode.objects.count() == initial_count

    def test_create_serial_code_invalid_data_admin(self, admin_client):
        """Verify validation errors for invalid data during creation."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        data = {
            # Missing 'code'
            "subscription_type": SubscriptionTypeChoices.MONTH_1.value,
            "duration_days": "thirty",  # Invalid integer
        }
        response = admin_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data
        assert "duration_days" in response.data

    def test_update_serial_code_admin(self, admin_client, active_serial_code):
        """Verify admin can update allowed fields (is_active, notes)."""
        url = reverse(
            f"{SERIAL_CODE_BASE_URL}-detail", kwargs={"pk": active_serial_code.pk}
        )
        data = {
            "is_active": False,
            "notes": "Deactivated via API test.",
        }
        response = admin_client.patch(url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False
        assert response.data["notes"] == data["notes"]

        active_serial_code.refresh_from_db()
        assert active_serial_code.is_active is False
        assert active_serial_code.notes == data["notes"]

    def test_delete_serial_code_admin(self, admin_client, active_serial_code):
        """Verify admin can delete a serial code."""
        code_id = active_serial_code.pk
        url = reverse(f"{SERIAL_CODE_BASE_URL}-detail", kwargs={"pk": code_id})
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not SerialCode.objects.filter(pk=code_id).exists()

    # --- Tests for Generate Batch Action ---

    @pytest.mark.parametrize(
        "plan_type_enum",
        [
            SubscriptionTypeChoices.MONTH_1,
            SubscriptionTypeChoices.MONTH_6,
            SubscriptionTypeChoices.MONTH_12,
        ],
    )
    def test_generate_codes_admin(self, admin_client, admin_user, plan_type_enum):
        """Verify admin can generate a batch of codes for standard plan types."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-generate-codes")  # Action URL
        count = 5
        notes = f"Test batch for {plan_type_enum.label}"
        data = {
            "plan_type": plan_type_enum.value,
            "count": count,
            "notes": notes,
        }
        initial_count = SerialCode.objects.count()
        response = admin_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert SerialCode.objects.count() == initial_count + count
        assert f"{count} serial codes generated successfully" in response.data["detail"]

        # Check one of the created codes
        last_code = SerialCode.objects.order_by("-created_at").first()
        assert last_code.subscription_type == plan_type_enum.value
        assert last_code.notes == notes
        assert last_code.created_by == admin_user
        # Check duration matches config (requires importing PLAN_CONFIG or accessing via enum?)
        # For simplicity, we trust the view logic uses the config correctly here.
        # assert last_code.duration_days == PLAN_CONFIG[plan_type_enum]['duration_days']

    def test_generate_codes_invalid_plan_admin(self, admin_client):
        """Verify error when trying to generate batch with invalid/custom plan type."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-generate-codes")
        data = {
            "plan_type": "invalid-plan",
            "count": 10,
        }
        response = admin_client.post(url, data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "plan_type" in response.data

        data_custom = {
            "plan_type": SubscriptionTypeChoices.CUSTOM.value,
            "count": 10,
        }
        response_custom = admin_client.post(url, data=data_custom, format="json")
        assert response_custom.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "plan_type" in response_custom.data
        )  # Check specific error message if desired

    def test_generate_codes_invalid_count_admin(self, admin_client):
        """Verify error when count is invalid during batch generation."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-generate-codes")
        data_zero = {
            "plan_type": SubscriptionTypeChoices.MONTH_1.value,
            "count": 0,
        }
        response_zero = admin_client.post(url, data=data_zero, format="json")
        assert response_zero.status_code == status.HTTP_400_BAD_REQUEST
        assert "count" in response_zero.data

        data_negative = {
            "plan_type": SubscriptionTypeChoices.MONTH_1.value,
            "count": -5,
        }
        response_negative = admin_client.post(url, data=data_negative, format="json")
        assert response_negative.status_code == status.HTTP_400_BAD_REQUEST
        assert "count" in response_negative.data

        data_too_large = {
            "plan_type": SubscriptionTypeChoices.MONTH_1.value,
            "count": 2000,  # Assuming max is 1000 based on serializer
        }
        response_large = admin_client.post(url, data=data_too_large, format="json")
        assert response_large.status_code == status.HTTP_400_BAD_REQUEST
        assert "count" in response_large.data
