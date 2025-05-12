import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.users.models import SerialCode, SubscriptionTypeChoices
from apps.users.tests.factories import SerialCodeFactory
from apps.users.constants import SUBSCRIPTION_PLANS_CONFIG

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
        assert "code" in response.data["results"][0]

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
        assert response.data["notes"] == active_serial_code.notes

    def test_create_serial_code_admin(self, admin_client, admin_user):
        """Verify admin can create a single serial code."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        # Create a 3-month code
        plan_config = SUBSCRIPTION_PLANS_CONFIG[SubscriptionTypeChoices.MONTH_3]
        data = {
            "code": "ADMIN-CREATE-TEST-001",
            "subscription_type": plan_config["id"],  # Use value from config
            "duration_days": plan_config["duration_days"],  # Use duration from config
            "is_active": True,
            "notes": "Created via API test (3 Month)",
        }
        response = admin_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert SerialCode.objects.filter(code=data["code"]).exists()
        new_code = SerialCode.objects.get(code=data["code"])
        assert new_code.subscription_type == data["subscription_type"]
        assert new_code.duration_days == data["duration_days"]
        assert new_code.created_by == admin_user

    def test_create_serial_code_duplicate_admin(self, admin_client, active_serial_code):
        """Verify admin cannot create a code with an existing value (case-insensitive)."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        # Use the 12 month plan for variety, duration from config
        plan_config = SUBSCRIPTION_PLANS_CONFIG[SubscriptionTypeChoices.MONTH_12]
        data = {
            "code": active_serial_code.code.lower(),  # Use existing code
            "subscription_type": plan_config["id"],
            "duration_days": plan_config["duration_days"],
        }
        initial_count = SerialCode.objects.count()
        response = admin_client.post(url, data=data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data
        assert SerialCode.objects.count() == initial_count

    def test_create_serial_code_invalid_data_admin(self, admin_client):
        """Verify validation errors for invalid data during creation."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-list")
        data = {
            "subscription_type": SubscriptionTypeChoices.MONTH_1.value,
            "duration_days": "thirty",  # Invalid integer
        }
        response = admin_client.post(url, data=data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "code" in response.data  # Missing code
        assert "duration_days" in response.data

    def test_update_serial_code_admin(self, admin_client, active_serial_code):
        """Verify admin can update allowed fields (is_active, notes)."""
        url = reverse(
            f"{SERIAL_CODE_BASE_URL}-detail", kwargs={"pk": active_serial_code.pk}
        )
        data = {"is_active": False, "notes": "Deactivated."}
        response = admin_client.patch(url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False
        active_serial_code.refresh_from_db()
        assert active_serial_code.is_active is False

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
            SubscriptionTypeChoices.MONTH_3,
            SubscriptionTypeChoices.MONTH_12,
        ],
    )
    def test_generate_codes_admin(self, admin_client, admin_user, plan_type_enum):
        """Verify admin can generate a batch of codes for standard plan types."""
        url = reverse(
            f"{SERIAL_CODE_BASE_URL}-generate-codes"
        )  # This should correctly point to the generate-batch path due to router naming
        count = 5
        notes = f"Test batch for {plan_type_enum.label}"

        data = {
            "plan_type": plan_type_enum.value,  # CHANGED: Send plan_type
            "count": count,
            "notes": notes,
        }
        initial_code_count = SerialCode.objects.count()  # Renamed for clarity
        response = admin_client.post(url, data=data, format="json")

        assert (
            response.status_code == status.HTTP_201_CREATED
        ), response.data  # Include response.data for easier debugging
        assert SerialCode.objects.count() == initial_code_count + count
        # The response detail now includes the plan name, adjust assertion if needed or keep more generic
        assert f"{count} serial codes generated successfully" in response.data["detail"]

        # Verify one of the created codes
        last_code = (
            SerialCode.objects.filter(notes=notes).order_by("-created_at").first()
        )
        assert last_code is not None
        assert (
            last_code.subscription_type == plan_type_enum.value
        )  # Model field is subscription_type
        assert last_code.notes == notes
        assert last_code.created_by == admin_user
        expected_duration = SUBSCRIPTION_PLANS_CONFIG[plan_type_enum]["duration_days"]
        assert last_code.duration_days == expected_duration

    def test_generate_codes_invalid_plan_admin(self, admin_client):
        """Verify error when trying to generate batch with invalid plan type."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-generate-codes")

        # Test with an invalid plan string
        data_invalid_string = {
            "plan_type": "invalid-plan-string",
            "count": 10,
        }
        response_invalid = admin_client.post(  # <<< CORRECTED LINE
            url, data=data_invalid_string, format="json"  # Pass data only once
        )
        assert response_invalid.status_code == status.HTTP_400_BAD_REQUEST
        assert "plan_type" in response_invalid.data
        assert (
            '"invalid-plan-string" is not a valid choice.'
            in response_invalid.data["plan_type"][0]
        )

        # Test with 'custom' plan type which should be rejected by the serializer
        data_custom = {
            "plan_type": SubscriptionTypeChoices.CUSTOM.value,
            "count": 10,
        }
        response_custom = admin_client.post(
            url, data=data_custom, format="json"
        )  # Pass data only once
        assert response_custom.status_code == status.HTTP_400_BAD_REQUEST
        assert "plan_type" in response_custom.data
        # The error message might come from choices validation or custom validate_plan_type
        error_messages = response_custom.data["plan_type"]
        assert any(
            "not a valid choice" in msg or "not supported" in msg
            for msg in error_messages
        )

    def test_generate_codes_invalid_count_admin(self, admin_client):
        """Verify error when count is invalid during batch generation."""
        url = reverse(f"{SERIAL_CODE_BASE_URL}-generate-codes")
        # Test various invalid counts
        for count in [0, -5, 2000]:  # Assuming max 1000 in serializer
            data = {
                "subscription_type": SubscriptionTypeChoices.MONTH_1.value,
                "count": count,
            }
            response = admin_client.post(url, data=data, format="json")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "count" in response.data
