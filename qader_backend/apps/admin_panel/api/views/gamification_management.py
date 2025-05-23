from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.gamification.models import Badge, RewardStoreItem
from ..serializers.gamification_management import (
    AdminBadgeSerializer,
    AdminRewardStoreItemSerializer,
)
from ..permissions import (
    IsAdminUserOrSubAdminWithPermission,
)  # Import the custom permission


@extend_schema_view(
    list=extend_schema(
        summary="Admin: List Badges",
        description="List all Badge definitions (active and inactive). Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    create=extend_schema(
        summary="Admin: Create Badge",
        description="Create a new Badge definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    retrieve=extend_schema(
        summary="Admin: Retrieve Badge",
        description="Retrieve details of a specific Badge definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    update=extend_schema(
        summary="Admin: Update Badge",
        description="Update an existing Badge definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    partial_update=extend_schema(
        summary="Admin: Partially Update Badge",
        description="Partially update an existing Badge definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    destroy=extend_schema(
        summary="Admin: Delete Badge",
        description="Delete a Badge definition. Requires admin privileges. Note: Consider deactivating instead of deleting if badges have been earned.",
        tags=["Admin Panel - Gamification Management"],
    ),
)
class AdminBadgeViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing Badge definitions.
    Provides full CRUD operations for administrators, including criteria management.
    """

    queryset = Badge.objects.all().order_by("name")  # pylint: disable=no-member
    serializer_class = AdminBadgeSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "criteria_type"]
    search_fields = ["name", "slug", "description", "criteria_description"]
    ordering_fields = [
        "name",
        "slug",
        "created_at",
        "updated_at",
        "is_active",
        "criteria_type",
        "target_value",
    ]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_gamification"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_gamification"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(
        summary="Admin: List Reward Store Items",
        description="List all Reward Store Item definitions (active and inactive). Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    create=extend_schema(
        summary="Admin: Create Reward Store Item",
        description="Create a new Reward Store Item definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    retrieve=extend_schema(
        summary="Admin: Retrieve Reward Store Item",
        description="Retrieve details of a specific Reward Store Item definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    update=extend_schema(
        summary="Admin: Update Reward Store Item",
        description="Update an existing Reward Store Item definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    partial_update=extend_schema(
        summary="Admin: Partially Update Reward Store Item",
        description="Partially update an existing Reward Store Item definition. Requires admin privileges.",
        tags=["Admin Panel - Gamification Management"],
    ),
    destroy=extend_schema(
        summary="Admin: Delete Reward Store Item",
        description="Delete a Reward Store Item definition. Requires admin privileges. Note: Consider deactivating instead of deleting if items have been purchased.",
        tags=["Admin Panel - Gamification Management"],
    ),
)
class AdminRewardStoreItemViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing Reward Store Item definitions.
    Provides full CRUD operations for administrators.
    """

    queryset = RewardStoreItem.objects.all().order_by(  # pylint: disable=no-member
        "name"
    )
    serializer_class = AdminRewardStoreItemSerializer
    permission_classes = [
        IsAdminUserOrSubAdminWithPermission
    ]  # Or [IsAdminOrSubAdminWithPermission('manage_gamification')]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_active", "item_type"]
    search_fields = ["name", "description"]
    ordering_fields = [
        "name",
        "item_type",
        "cost_points",
        "created_at",
        "updated_at",
        "is_active",
    ]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_gamification"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_gamification"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]
