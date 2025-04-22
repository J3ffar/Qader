from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.community.api import views

app_name = "community"

router = DefaultRouter()
router.register(r"posts", views.CommunityPostViewSet, basename="communitypost")
# Replies are handled by the specific view below, not the main router

urlpatterns = [
    path("", include(router.urls)),
    path(
        "posts/<int:post_pk>/replies/",
        views.CommunityReplyListCreateView.as_view(),
        name="post-replies",
    ),
    path("tags/", views.TagListView.as_view(), name="tag-list"),
]
