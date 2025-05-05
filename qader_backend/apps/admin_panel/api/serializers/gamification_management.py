from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.gamification.models import Badge, RewardStoreItem


class AdminBadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for Admin CRUD operations on Badge definitions.
    Allows modification of all relevant fields, including criteria.
    """

    icon_url = serializers.ImageField(
        source="icon", read_only=True, use_url=True, allow_null=True
    )
    criteria_type_display = serializers.CharField(
        source="get_criteria_type_display", read_only=True
    )

    class Meta:
        model = Badge
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "icon_url",
            "criteria_description",
            "criteria_type",
            "criteria_type_display",
            "target_value",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "icon_url",
            "criteria_type_display",
            "created_at",
            "updated_at",
        )
        # Add extra validation if needed (e.g., using serializer methods)
        # The model's clean() method handles the core logic for target_value requirement.

    # Optional: Add explicit serializer-level validation if needed,
    # although the model's clean() method provides good coverage.
    # def validate(self, data):
    #     criteria_type = data.get('criteria_type', getattr(self.instance, 'criteria_type', None))
    #     target_value = data.get('target_value', getattr(self.instance, 'target_value', None))
    #
    #     if criteria_type and criteria_type != Badge.BadgeCriteriaType.OTHER and target_value is None:
    #         raise serializers.ValidationError({
    #             'target_value': _('Target Value is required for the selected criteria type.')
    #         })
    #     if criteria_type == Badge.BadgeCriteriaType.OTHER and target_value is not None:
    #          # Decide if this is an error or if you just want to nullify it
    #          # raise serializers.ValidationError({'target_value': _('Target Value must be empty for criteria type "Other".')})
    #          data['target_value'] = None # Silently nullify if preferred
    #
    #     return data


class AdminRewardStoreItemSerializer(serializers.ModelSerializer):
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
            "image",
            "image_url",
            "asset_file",
            "asset_file_url",
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
