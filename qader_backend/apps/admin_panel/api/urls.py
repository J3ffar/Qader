from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import user_management as views  # Alias for clarity

router = DefaultRouter()
router.register(r"users", views.AdminUserViewSet, basename="admin-user")
router.register(r"sub-admins", views.AdminSubAdminViewSet, basename="admin-sub-admin")

app_name = "admin_panel_api"

urlpatterns = [
    path("", include(router.urls)),
    # Custom action routes
    path(
        "users/<int:user_id>/reset-password/",
        views.AdminPasswordResetView.as_view(),
        name="admin-user-reset-password",
    ),
    path(
        "users/<int:user_id>/adjust-points/",
        views.AdminPointAdjustmentView.as_view(),
        name="admin-user-adjust-points",
    ),
    # TODO: Add endpoint to list available permissions for sub-admins when model is updated
    # path("permissions/", views.PermissionListView.as_view(), name="admin-permission-list"),
]
