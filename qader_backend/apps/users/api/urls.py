from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    CustomTokenObtainPairView,  # Use custom if defined, else TokenObtainPairView
    LogoutView,
    UserProfileView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    # ProfilePictureUploadView, # Add when implemented
)

app_name = "users_api"

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),  # POST -> gets tokens
    path(
        "token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
    ),  # POST -> refreshes access token
    path(
        "logout/", LogoutView.as_view(), name="logout"
    ),  # POST -> blacklists refresh token
    # User Profile
    path("me/", UserProfileView.as_view(), name="user_profile"),  # GET, PATCH
    # path('me/upload-picture/', ProfilePictureUploadView.as_view(), name='upload_picture'), # POST
    # Password Management
    path(
        "me/change-password/", PasswordChangeView.as_view(), name="change_password"
    ),  # POST
    path(
        "password/reset/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),  # POST
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),  # POST
]
