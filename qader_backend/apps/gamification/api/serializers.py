from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from ..models import Badge, UserBadge, RewardStoreItem, PointLog
from apps.users.models import UserProfile  # Assuming UserProfile is here

User = get_user_model()


class GamificationSummarySerializer(serializers.Serializer):
    """Serializer for the gamification summary endpoint."""

    points = serializers.IntegerField(read_only=True)
    current_streak = serializers.IntegerField(
        source="current_streak_days", read_only=True
    )
    longest_streak = serializers.IntegerField(
        source="longest_streak_days", read_only=True
    )

    class Meta:
        # Although not a ModelSerializer, defining Meta helps clarity
        fields = ("points", "current_streak", "longest_streak")


class BadgeSerializer(serializers.ModelSerializer):
    """Serializer for Badge definitions, including user-specific earned status."""

    is_earned = serializers.SerializerMethodField()
    earned_at = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "icon_class_or_image",
            "criteria_description",
            "is_earned",
            "earned_at",
        )
        read_only_fields = fields  # Badges are defined by admin

    def get_is_earned(self, obj):
        """Check if the current user has earned this badge."""
        user = self.context.get("request").user
        if not user or not user.is_authenticated:
            return False
        # Check if the pre-fetched/annotated data exists
        if hasattr(obj, "user_earned_badge"):
            return obj.user_earned_badge is not None
        # Fallback query (less efficient if not optimized in view)
        return UserBadge.objects.filter(user=user, badge=obj).exists()

    def get_earned_at(self, obj):
        """Get the timestamp when the current user earned this badge."""
        user = self.context.get("request").user
        if not user or not user.is_authenticated:
            return None
        # Check if the pre-fetched/annotated data exists
        if hasattr(obj, "user_earned_badge") and obj.user_earned_badge:
            return obj.user_earned_badge.earned_at
        # Fallback query (less efficient)
        try:
            user_badge = UserBadge.objects.get(user=user, badge=obj)
            return user_badge.earned_at
        except UserBadge.DoesNotExist:
            return None


class RewardStoreItemSerializer(serializers.ModelSerializer):
    """Serializer for items available in the reward store."""

    class Meta:
        model = RewardStoreItem
        fields = (
            "id",
            "name",
            "description",
            "item_type",
            "cost_points",
            "asset_url_or_data",
            # 'is_active' might not be needed for user view if filtered in queryset
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

    # Optionally add related object representation if needed
    # related_object_str = serializers.StringRelatedField(source='related_object', read_only=True)

    class Meta:
        model = PointLog
        fields = (
            "id",
            "points_change",
            "reason_code",
            "description",
            "timestamp",
            # 'related_object_str' # Uncomment if representation needed
        )
        read_only_fields = fields
