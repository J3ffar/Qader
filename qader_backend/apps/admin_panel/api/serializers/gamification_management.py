from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.gamification.models import Badge, RewardStoreItem


class AdminBadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for Admin CRUD operations on Badge definitions.
    Allows modification of all relevant fields.
    """

    icon_url = serializers.ImageField(
        source="icon", read_only=True, use_url=True, allow_null=True
    )

    class Meta:
        model = Badge
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "icon",  # Allow upload/update
            "icon_url",  # Read-only URL for display
            "criteria_description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "icon_url",
            "created_at",
            "updated_at",
        )  # These are typically read-only


class AdminRewardStoreItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Admin CRUD operations on RewardStoreItem definitions.
    Allows modification of all relevant fields.
    """

    item_type_display = serializers.CharField(
        source="get_item_type_display", read_only=True
    )
    image_url = serializers.ImageField(
        source="image", read_only=True, use_url=True, allow_null=True
    )
    asset_file_url = serializers.FileField(
        source="asset_file", read_only=True, use_url=True, allow_null=True
    )

    class Meta:
        model = RewardStoreItem
        fields = (
            "id",
            "name",
            "description",
            "item_type",
            "item_type_display",
            "cost_points",
            "image",  # Allow upload/update
            "image_url",  # Read-only URL
            "asset_file",  # Allow upload/update
            "asset_file_url",  # Read-only URL
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "item_type_display",
            "image_url",
            "asset_file_url",
            "created_at",
            "updated_at",
        )
