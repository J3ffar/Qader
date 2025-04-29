from django.urls import path
from .views import (
    InitialSignupView,  # New
    ConfirmEmailView,  # New
    CustomTokenObtainPairView,
    LogoutView,
    CustomTokenRefreshView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

app_name = "auth"

urlpatterns = [
    # Authentication & New Signup Flow
    path(
        "signup/", InitialSignupView.as_view(), name="initial_signup"
    ),  # New signup endpoint
    # Changed path to match common patterns, ensure frontend uses this
    path(
        "confirm-email/<str:uidb64>/<str:token>/",
        ConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),  # New confirmation endpoint
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Password Reset
    path(
        "password/reset/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
