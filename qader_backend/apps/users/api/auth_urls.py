from django.urls import path

from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    CustomTokenRefreshView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

app_name = "auth"

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Password Reset (considered auth-related)
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
