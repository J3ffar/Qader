from django.urls import path, include

app_name = "api_v1"

urlpatterns = [
    path("auth/", include("apps.users.api.urls", namespace="auth")),
    path("users/", include("apps.users.api.urls", namespace="users")),
]
