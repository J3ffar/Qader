from django.urls import path

from .views import (
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
]
