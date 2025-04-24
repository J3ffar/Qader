from rest_framework import serializers
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.content import models as content_models
from apps.users.api.serializers import SimpleUserSerializer  # For responder


class AdminPageSerializer(serializers.ModelSerializer):
    """Admin Serializer for managing Page models."""

    class Meta:
        model = content_models.Page
        fields = [
            "id",
            "slug",
            "title",
            "content",
            "icon_class",
            "is_published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminFAQItemSerializer(serializers.ModelSerializer):
    """Admin Serializer for managing FAQItem models."""

    class Meta:
        model = content_models.FAQItem
        fields = [
            "id",
            "category",
            "question",
            "answer",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminFAQCategorySerializer(serializers.ModelSerializer):
    """Admin Serializer for managing FAQCategory models."""

    # items = AdminFAQItemSerializer(many=True, read_only=True) # Optional: for read-only nested view

    class Meta:
        model = content_models.FAQCategory
        fields = [
            "id",
            "name",
            "order",
            # "items", # Add if nested view is desired on list/retrieve
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminPartnerCategorySerializer(serializers.ModelSerializer):
    """Admin Serializer for managing PartnerCategory models."""

    class Meta:
        model = content_models.PartnerCategory
        fields = [
            "id",
            "name",
            "description",
            "icon_svg_or_class",
            "google_form_link",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminHomepageFeatureCardSerializer(serializers.ModelSerializer):
    """Admin Serializer for managing HomepageFeatureCard models."""

    class Meta:
        model = content_models.HomepageFeatureCard
        fields = [
            "id",
            "title",
            "text",
            "svg_image",
            "icon_class",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminHomepageStatisticSerializer(serializers.ModelSerializer):
    """Admin Serializer for managing HomepageStatistic models."""

    class Meta:
        model = content_models.HomepageStatistic
        fields = [
            "id",
            "label",
            "value",
            "icon_class",
            "order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminContactMessageSerializer(serializers.ModelSerializer):
    """Admin Serializer for viewing and managing ContactMessage models."""

    # Use a summary serializer for the responder to avoid exposing too much user data
    responder = SimpleUserSerializer(read_only=True)

    class Meta:
        model = content_models.ContactMessage
        fields = [
            "id",
            "full_name",
            "email",
            "subject",
            "message",
            "attachment",
            "status",
            "responder",
            "response",
            "responded_at",
            "created_at",
            "updated_at",
        ]
        # Admins primarily update status and response
        read_only_fields = [
            "id",
            "full_name",
            "email",
            "subject",
            "message",
            "attachment",  # Attachment cannot be changed after creation
            "created_at",
            "updated_at",
            "responder",  # Automatically set on update
            "responded_at",  # Automatically set on update
        ]

    def update(self, instance, validated_data):
        # Set responder and responded_at automatically when response/status changes
        if "response" in validated_data or "status" in validated_data:
            if (
                instance.status != content_models.ContactMessage.STATUS_REPLIED
                and validated_data.get("status")
                == content_models.ContactMessage.STATUS_REPLIED
            ):
                # Only set responder/time if status changes to 'replied'
                # or if response is added/changed while status is already 'replied'
                if self.context["request"].user.is_authenticated:
                    instance.responder = self.context["request"].user
                    instance.responded_at = timezone.now()

        # Ensure status is valid if provided
        status = validated_data.get("status", instance.status)
        if status not in dict(content_models.ContactMessage.STATUS_CHOICES):
            raise serializers.ValidationError({"status": _("Invalid status value.")})
        instance.status = status

        instance.response = validated_data.get("response", instance.response)

        instance.save()
        return instance
