from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

app_name = "v1"

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("apps.users.api.auth_urls"), name="auth"),
    path("users/", include("apps.users.api.users_urls"), name="users"),
    path("learning/", include("apps.learning.api.urls"), name="learning"),
    path("study/", include("apps.study.api.urls"), name="study"),
    path("gamification/", include("apps.gamification.api.urls"), name="gamification"),
]
