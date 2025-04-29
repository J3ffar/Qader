from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

# from django.contrib.auth import get_user_model # Not needed directly
from django.conf import settings  # If using settings.AUTH_USER_MODEL

from ..models import Badge, UserBadge, RewardStoreItem, PointLog, PointReason

# from apps.users.models import UserProfile # Not needed directly if getting from request.user.profile

# User = settings.AUTH_USER_MODEL # If needed


class GamificationSummarySerializer(serializers.Serializer):
    """Serializer for the gamification summary endpoint."""

    points = serializers.IntegerField(
        read_only=True, help_text=_("User's current point balance.")
    )
    current_streak = serializers.IntegerField(
        source="current_streak_days",
        read_only=True,
        help_text=_("Number of consecutive study days."),
    )
    longest_streak = serializers.IntegerField(
        source="longest_streak_days",
        read_only=True,
        help_text=_("User's longest ever study streak."),
    )

    class Meta:
        # Define fields for clarity, even though not a ModelSerializer
        fields = ("points", "current_streak", "longest_streak")
        # Source object is expected to be UserProfile instance


class BadgeSerializer(serializers.ModelSerializer):
    """
    Serializer for Badge definitions.
    Includes user-specific 'is_earned' and 'earned_at' fields, which rely on
    annotations provided by the BadgeListView queryset for efficiency.
    """

    is_earned = serializers.SerializerMethodField(
        help_text=_("Whether the current authenticated user has earned this badge.")
    )
    earned_at = serializers.DateTimeField(
        read_only=True,
        source="user_earned_at",  # Rely on annotation name from view
        allow_null=True,
        help_text=_(
            "Timestamp when the current user earned this badge (null if not earned)."
        ),
    )
    icon_url = serializers.ImageField(
        source="icon",  # Get data from the 'icon' model field
        read_only=True,
        use_url=True,  # Ensure it outputs the URL
        help_text=_("URL of the badge icon image."),
    )

    class Meta:
        model = Badge
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "icon_url",
            "criteria_description",
            "is_earned",
            "earned_at",
        )
        read_only_fields = fields  # Badges are defined by admin

    def get_is_earned(self, obj):
        """
        Check if the badge is earned based on the annotation from the view's queryset.
        """
        # 'user_earned_at' annotation will be the timestamp if earned, None otherwise.
        # Accessing it directly via source='user_earned_at' in the field definition is cleaner.
        # This method relies on the view providing an annotation like 'user_earned_at'
        # (which could be the UserBadge.earned_at timestamp or null).
        return getattr(obj, "user_earned_at", None) is not None


class RewardStoreItemSerializer(serializers.ModelSerializer):
    """Serializer for items available in the reward store."""

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
            "item_type_display",  # Add human-readable type
            "cost_points",
            "image_url",
            "asset_file_url",
        )
        read_only_fields = fields  # Store items defined by admin


class RewardPurchaseResponseSerializer(serializers.Serializer):
    """Serializer for the successful reward purchase response."""

    item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    points_spent = serializers.IntegerField()
    remaining_points = serializers.IntegerField()
    message = serializers.CharField(default=_("Purchase successful!"))


class PointLogSerializer(serializers.ModelSerializer):
    """Serializer for the user's point transaction history."""

    reason_code_display = serializers.CharField(
        source="get_reason_code_display", read_only=True
    )
    # Optionally represent the related object if needed
    # related_object_str = serializers.StringRelatedField(source='related_object', read_only=True)

    class Meta:
        model = PointLog
        fields = (
            "id",
            "points_change",
            "reason_code",
            "reason_code_display",  # Add human-readable reason
            "description",
            "timestamp",
            # 'related_object_str' # Uncomment if representation needed
        )
        read_only_fields = fields
