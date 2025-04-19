import pytest
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.utils import translation, timezone  # Import translation
from django.utils.translation import gettext_lazy as _
from django.conf import settings  # Import settings

from ..models import SerialCode, UserProfile, SubscriptionTypeChoices, RoleChoices
from ..admin import SerialCodeAdmin, UserAdmin
from .factories import UserFactory, SerialCodeFactory

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# --- Fixtures remain the same ---
@pytest.fixture
def mock_request(admin_client):
    request = admin_client.get("/").wsgi_request
    return request


@pytest.fixture
def serial_code_admin_instance(mock_request):
    return SerialCodeAdmin(model=SerialCode, admin_site=AdminSite())


# --- Apply translation override to tests accessing admin URLs ---


def test_serial_code_admin_changelist_loads(admin_client):
    """Test that the SerialCode changelist page loads successfully."""
    language_code = settings.LANGUAGE_CODE  # Get default language ('en-us', 'en', etc.)
    with translation.override(language_code):  # Activate language context
        index_url = reverse("admin:index")
        changelist_url = reverse("admin:users_serialcode_changelist")

        # Optional: Add header to reinforce language preference for the request
        headers = {"HTTP_ACCEPT_LANGUAGE": language_code}

        index_response = admin_client.get(index_url, headers=headers)
        assert (
            index_response.status_code == 200
        ), f"Admin index page failed to load at {index_url}"

        response = admin_client.get(changelist_url, headers=headers)
        assert (
            response.status_code == 200
        ), f"Failed to load SerialCode changelist at {changelist_url}"


def test_serial_code_admin_subscription_type_in_list_display(admin_client):
    """Test that Subscription Type column appears in the changelist."""
    code_1m = SerialCodeFactory(type_1_month=True)
    code_custom = SerialCodeFactory(type_custom=True, duration_days=10)
    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        url = reverse("admin:users_serialcode_changelist")
        response = admin_client.get(url, HTTP_ACCEPT_LANGUAGE=language_code)

    assert response.status_code == 200
    content = response.content.decode()
    assert str(_("Subscription Type")) in content
    assert str(SubscriptionTypeChoices.MONTH_1.label) in content
    assert str(SubscriptionTypeChoices.CUSTOM.label) in content
    assert code_1m.code in content
    assert code_custom.code in content


def test_serial_code_admin_filter_by_subscription_type(admin_client):
    """Test filtering the changelist by subscription_type."""
    code_1m = SerialCodeFactory(type_1_month=True)
    code_6m = SerialCodeFactory(type_6_months=True)
    code_none = SerialCodeFactory(subscription_type=None)

    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        base_url = reverse("admin:users_serialcode_changelist")

        # Filter for 1 Month
        url_1m = (
            f"{base_url}?subscription_type__exact={SubscriptionTypeChoices.MONTH_1}"
        )
        response_1m = admin_client.get(url_1m, HTTP_ACCEPT_LANGUAGE=language_code)
        assert response_1m.status_code == 200
        content_1m = response_1m.content.decode()
        assert code_1m.code in content_1m
        assert code_6m.code not in content_1m
        assert code_none.code not in content_1m

        # Filter for 6 Months
        url_6m = (
            f"{base_url}?subscription_type__exact={SubscriptionTypeChoices.MONTH_6}"
        )
        response_6m = admin_client.get(url_6m, HTTP_ACCEPT_LANGUAGE=language_code)
        assert response_6m.status_code == 200
        content_6m = response_6m.content.decode()
        assert code_1m.code not in content_6m
        assert code_6m.code in content_6m
        assert code_none.code not in content_6m

        # Filter for 'empty' type
        url_none = f"{base_url}?subscription_type__isnull=True"
        response_none = admin_client.get(url_none, HTTP_ACCEPT_LANGUAGE=language_code)
        if (
            response_none.status_code != 200
            or code_none.code not in response_none.content.decode()
        ):
            url_none = f"{base_url}?subscription_type__exact="
            response_none = admin_client.get(
                url_none, HTTP_ACCEPT_LANGUAGE=language_code
            )

        assert response_none.status_code == 200
        content_none = response_none.content.decode()
        assert code_1m.code not in content_none
        assert code_6m.code not in content_none
        assert code_none.code in content_none


def test_serial_code_admin_add_view_loads(admin_client):
    """Test that the SerialCode add page loads and contains the type field."""
    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        url = reverse("admin:users_serialcode_add")
        response = admin_client.get(url, HTTP_ACCEPT_LANGUAGE=language_code)

    assert response.status_code == 200
    content = response.content.decode()
    assert 'name="subscription_type"' in content
    assert f'value="{SubscriptionTypeChoices.MONTH_1}"' in content


def test_serial_code_admin_add_new_code(admin_client, admin_user):
    """Test adding a new SerialCode via the admin interface."""
    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        add_url = reverse("admin:users_serialcode_add")
        changelist_url = reverse("admin:users_serialcode_changelist")

        data = {
            "code": "ADMIN-ADDED-CODE",
            "subscription_type": SubscriptionTypeChoices.MONTH_6,
            "duration_days": 183,
            "is_active": "on",
            "notes": "Added via admin test",
            "_save": "Save",
        }
        # POST requests generally don't need the language in the URL itself
        # but the redirect URL calculation might depend on the active language context
        response = admin_client.post(add_url, data, HTTP_ACCEPT_LANGUAGE=language_code)

        assert (
            response.status_code == 302
        ), f"Expected redirect, got {response.status_code}"
        # Ensure the expected redirect URL also has the prefix
        assert (
            response.url == changelist_url
        ), f"Expected redirect to {changelist_url}, got {response.url}"

    assert SerialCode.objects.filter(code="ADMIN-ADDED-CODE").exists()
    new_code = SerialCode.objects.get(code="ADMIN-ADDED-CODE")
    assert new_code.subscription_type == SubscriptionTypeChoices.MONTH_6
    assert new_code.duration_days == 183
    assert new_code.is_active is True
    assert new_code.notes == "Added via admin test"


def test_serial_code_admin_change_view_loads(admin_client):
    """Test loading the change view for an existing SerialCode."""
    code = SerialCodeFactory(type_1_month=True)
    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        url = reverse("admin:users_serialcode_change", args=[code.id])
        response = admin_client.get(url, HTTP_ACCEPT_LANGUAGE=language_code)

    assert response.status_code == 200
    content = response.content.decode()
    assert code.code in content
    assert 'name="subscription_type"' in content
    assert f'<option value="{SubscriptionTypeChoices.MONTH_1}" selected>' in content
    assert f'name="duration_days" value="{code.duration_days}"' in content


def test_serial_code_admin_change_code_type(admin_client):
    """Test changing the subscription_type of an existing code via admin."""
    code = SerialCodeFactory(type_1_month=True)
    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        change_url = reverse("admin:users_serialcode_change", args=[code.id])
        changelist_url = reverse("admin:users_serialcode_changelist")
        data = {
            "code": code.code,
            "subscription_type": SubscriptionTypeChoices.CUSTOM,
            "duration_days": 99,
            "is_active": "on",
            "notes": code.notes or "",
            "_save": "Save",
        }
        response = admin_client.post(
            change_url, data, HTTP_ACCEPT_LANGUAGE=language_code
        )

        assert (
            response.status_code == 302
        ), f"Expected redirect, got {response.status_code}"
        assert (
            response.url == changelist_url
        ), f"Expected redirect to {changelist_url}, got {response.url}"

    code.refresh_from_db()
    assert code.subscription_type == SubscriptionTypeChoices.CUSTOM
    assert code.duration_days == 99


# --- UserAdmin Tests ---


def test_user_admin_changelist_loads(admin_client):
    """Test that the User changelist page loads."""
    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        url = reverse("admin:auth_user_changelist")
        response = admin_client.get(url, HTTP_ACCEPT_LANGUAGE=language_code)
    assert response.status_code == 200


def test_user_admin_displays_role_and_subscription(
    admin_client, subscribed_user, unsubscribed_user
):
    """Test custom columns in UserAdmin list display."""
    subscribed_user.profile.role = RoleChoices.STUDENT
    subscribed_user.profile.subscription_expires_at = (
        timezone.now() + timezone.timedelta(days=5)
    )
    subscribed_user.profile.save()

    unsubscribed_user.profile.role = RoleChoices.STUDENT
    unsubscribed_user.profile.subscription_expires_at = (
        timezone.now() - timezone.timedelta(days=5)
    )
    unsubscribed_user.profile.save()

    language_code = settings.LANGUAGE_CODE
    with translation.override(language_code):
        url = reverse("admin:auth_user_changelist")
        response = admin_client.get(url, HTTP_ACCEPT_LANGUAGE=language_code)

    assert response.status_code == 200
    content = response.content.decode()
    assert str(_("Role")) in content
    assert str(_("Subscribed")) in content
    assert subscribed_user.username in content
    assert str(RoleChoices.STUDENT.label) in content
    assert 'alt="True"' in content or "icon-yes" in content
    assert unsubscribed_user.username in content
    assert 'alt="False"' in content or "icon-no" in content
