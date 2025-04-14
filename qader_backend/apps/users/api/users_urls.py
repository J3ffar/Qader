from django.urls import path

from .views import (
    UserProfileView,
    PasswordChangeView,
    ProfilePictureUploadView,
)

app_name = "users"

urlpatterns = [
    # User Profile & Settings for logged-in user ('me')
    path("me/", UserProfileView.as_view(), name="user-profile"),  # GET, PATCH
    path(
        "me/upload-picture/", ProfilePictureUploadView.as_view(), name="upload-picture"
    ),  # POST
    path(
        "me/change-password/", PasswordChangeView.as_view(), name="change-password"
    ),  # POST
]
