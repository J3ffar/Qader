from django.urls import path

from .views import (
    ApplySerialCodeView,
    CancelSubscriptionView,
    SubscriptionPlanListView,
    UserProfileView,
    PasswordChangeView,
)

app_name = "users"

urlpatterns = [
    # User Profile & Settings for logged-in user ('me')
    path("me/", UserProfileView.as_view(), name="me_profile"),  # GET, PATCH
    path(
        "me/change-password/", PasswordChangeView.as_view(), name="me_change_password"
    ),  # POST
    # New Subscription Management Endpoints under /users/
    path(
        "me/apply-serial-code/",
        ApplySerialCodeView.as_view(),
        name="me_apply_serial_code",
    ),  # POST
    path(
        "me/subscription/cancel/",
        CancelSubscriptionView.as_view(),
        name="me_cancel_subscription",
    ),  # POST
    # Subscription Plans (could be moved to a separate app's urls later)
    path(
        "subscription-plans/",
        SubscriptionPlanListView.as_view(),
        name="subscription_plans_list",
    ),
]
