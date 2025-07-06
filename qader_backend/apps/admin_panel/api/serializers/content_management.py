from rest_framework import serializers
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.content import models as content_models
from apps.users.api.serializers import SimpleUserSerializer


class AdminContentImageSerializer(serializers.ModelSerializer):
    """Serializer for managing ContentImage uploads in the admin panel."""

    image_url = serializers.ImageField(source="image", read_only=True)
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = content_models.ContentImage
        fields = [
            "id",
            "page",
            "slug",
            "name",
            "image",
            "image_url",
            "alt_text",
            "uploaded_by",
            "uploaded_by_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "uploaded_by",
            "uploaded_by_name",
            "image_url",
        ]
        extra_kwargs = {
            "page": {"write_only": True, "required": False, "allow_null": True},
            "image": {
                "write_only": True,
                "required": True,
            },  # Image file is required for creation
            "slug": {"required": False, "allow_blank": True},  # Can be auto-generated
        }

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["uploaded_by"] = request.user
        return super().create(validated_data)


class AdminPageSerializer(serializers.ModelSerializer):
    """Admin Serializer for managing Page models."""

    images = AdminContentImageSerializer(many=True, read_only=True)

    class Meta:
        model = content_models.Page
        fields = [
            "id",
            "slug",
            "title",
            "content",
            "content_structured",
            "icon_class",
            "is_published",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "images"]
        extra_kwargs = {
            "content": {"required": False, "allow_blank": True, "allow_null": True},
            "content_structured": {"required": False, "allow_null": True},
        }


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
            "icon_image",
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
        read_only_fields = [
            "id",
            "full_name",
            "email",
            "subject",
            "message",
            "attachment",
            "created_at",
            "updated_at",
            "responder",
            "responded_at",
        ]

    def update(self, instance, validated_data):
        if "response" in validated_data or "status" in validated_data:
            if (
                instance.status != content_models.ContactMessage.STATUS_REPLIED
                and validated_data.get("status")
                == content_models.ContactMessage.STATUS_REPLIED
            ):
                if self.context["request"].user.is_authenticated:
                    instance.responder = self.context["request"].user
                    instance.responded_at = timezone.now()

        status = validated_data.get("status", instance.status)
        if status not in dict(content_models.ContactMessage.STATUS_CHOICES):
            raise serializers.ValidationError({"status": _("Invalid status value.")})
        instance.status = status
        instance.response = validated_data.get("response", instance.response)
        instance.save()
        return instance
