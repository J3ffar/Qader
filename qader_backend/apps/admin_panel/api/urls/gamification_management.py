from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import gamification_management as views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(
    r"badges", views.AdminBadgeViewSet, basename="admin-badge"
)  # e.g., /api/v1/admin/gamification/badges/
router.register(
    r"reward-items", views.AdminRewardStoreItemViewSet, basename="admin-reward-item"
)  # e.g., /api/v1/admin/gamification/reward-items/

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
