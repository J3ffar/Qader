from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

app_name = "v1"

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("apps.users.api.auth_urls"), name="auth"),
    path("users/", include("apps.users.api.users_urls"), name="users"),
    path(
        "notifications/",
        include("apps.notifications.api.urls", namespace="notifications"),
    ),
    path("chat/", include("apps.chat.api.urls", namespace="chat")),
    path("learning/", include("apps.learning.api.urls"), name="learning"),
    path("study/", include("apps.study.api.urls"), name="study"),
    path("gamification/", include("apps.gamification.api.urls"), name="gamification"),
    path("challenges/", include("apps.challenges.api.urls"), name="challenges"),
    path("content/", include("apps.content.api.urls"), name="content"),
    path("community/", include("apps.community.api.urls"), name="community"),
    path("blog/", include("apps.blog.api.urls"), name="blog"),
    path("support/", include("apps.support.api.urls"), name="support"),
    path("admin/", include("apps.admin_panel.api.urls"), name="admin_panel"),
]
