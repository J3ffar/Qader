from rest_framework import serializers
from django.utils.timesince import timesince as timesince_filter
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification, NotificationTypeChoices
from apps.users.api.serializers import SimpleUserSerializer  # Assuming this exists

User = get_user_model()


# GenericRelatedField can be very complex to make truly generic and performant
# for various target types. For now, we'll create a simpler version that can be
# expanded upon.
class TargetObjectRelatedField(serializers.RelatedField):
    """
    Serializes target objects with their type and a basic representation.
    This needs to be customized based on the models you want to represent.
    """

    def to_representation(self, value):
        if value is None:
            return None

        # Example: Customize for specific models
        # from apps.community.models import CommunityPost # Example
        # from apps.community.api.serializers import BasicCommunityPostSerializer # Example

        # if isinstance(value, CommunityPost):
        #     return {"id": value.pk, "type": "community_post", "details": BasicCommunityPostSerializer(value).data}

        # Generic fallback
        return {
            "id": str(value.pk),  # Ensure pk is string for consistency (UUIDs)
            "type": value.__class__.__name__.lower(),
            "display_text": str(value),  # A simple string representation
        }


class NotificationSerializer(serializers.ModelSerializer):
    recipient = SimpleUserSerializer(read_only=True)  # From your users app
    actor = SimpleUserSerializer(read_only=True, allow_null=True)
    target = TargetObjectRelatedField(read_only=True, allow_null=True)
    action_object = TargetObjectRelatedField(read_only=True, allow_null=True)

    timesince = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    created_at_iso = serializers.DateTimeField(
        source="created_at", format="iso-8601", read_only=True
    )
    read_at_iso = serializers.DateTimeField(
        source="read_at", format="iso-8601", read_only=True, allow_null=True
    )

    class Meta:
        model = Notification
        fields = (
            "id",
            "recipient",
            "actor",
            "verb",
            "description",
            "target",
            "action_object",
            "notification_type",
            "notification_type_display",
            "is_read",
            "read_at_iso",  # Use ISO format for frontend consistency
            "url",
            "data",
            "created_at_iso",  # Use ISO format
            "timesince",
        )
        read_only_fields = fields  # All fields are read-only from this serializer

    def get_timesince(self, obj: Notification) -> str:
        if obj.created_at:
            return f"{timesince_filter(obj.created_at)} {_('ago')}"
        return ""


class NotificationMarkReadInputSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        required=True,
        help_text=_("A list of notification IDs to mark as read."),
    )

    def validate_notification_ids(self, ids_list: list[int]) -> list[int]:
        user = self.context["request"].user
        # Check if all provided IDs exist and belong to the user
        valid_notifications_count = Notification.objects.filter(
            recipient=user, id__in=ids_list
        ).count()

        if len(ids_list) != valid_notifications_count:
            raise serializers.ValidationError(
                _(
                    "One or more notification IDs are invalid or do not belong to the current user."
                )
            )
        return ids_list
