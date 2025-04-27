from django.urls import path

from .views import (
    UserProfileView,
    PasswordChangeView,
    CompleteProfileView,  # New
    ApplySerialCodeView,  # Keep this if users can apply more codes later
    CancelSubscriptionView,
    SubscriptionPlanListView,
    UserRedeemedCodesListView,
)

app_name = "users"

urlpatterns = [
    # User Profile & Settings for logged-in user ('me')
    path(
        "me/", UserProfileView.as_view(), name="me_profile"
    ),  # GET, PATCH (for general updates)
    path(
        "me/complete-profile/",
        CompleteProfileView.as_view(),
        name="me_complete_profile",
    ),  # New endpoint for initial completion
    path(
        "me/change-password/", PasswordChangeView.as_view(), name="me_change_password"
    ),
    # Subscription Management
    path(
        "me/apply-serial-code/",
        ApplySerialCodeView.as_view(),
        name="me_apply_serial_code",
    ),  # Apply subsequent codes
    path(
        "me/subscription/cancel/",
        CancelSubscriptionView.as_view(),
        name="me_cancel_subscription",
    ),
    path(
        "me/redeemed-codes/",
        UserRedeemedCodesListView.as_view(),
        name="user-redeemed-codes",
    ),
    path(
        "subscription-plans/",
        SubscriptionPlanListView.as_view(),
        name="subscription_plans_list",
    ),
]
