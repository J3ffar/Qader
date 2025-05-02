# qader_backend/apps/admin_panel/api/urls/community_management.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.admin_panel.api.views import community_management as views

# Use a router for the admin viewsets
router = DefaultRouter()
router.register(
    r"posts",
    views.AdminCommunityPostViewSet,
    basename="admin-communitypost",
)
router.register(
    r"replies",
    views.AdminCommunityReplyViewSet,
    basename="admin-communityreply",
)


urlpatterns = [
    path("", include(router.urls)),
    # Add any other specific admin community management URLs here if needed
]
