from django.urls import path, include

app_name = "api_v1"

urlpatterns = [
    path("auth/", include("apps.users.api.auth_urls"), name="auth"),
    path("users/", include("apps.users.api.users_urls"), name="users"),
]
