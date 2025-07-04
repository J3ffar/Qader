from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.content import models


class PublicContentImageSerializer(serializers.ModelSerializer):
    """
    Public-facing serializer for ContentImage.
    Exposes fields needed for rendering, including the stable slug.
    """

    class Meta:
        model = models.ContentImage
        fields = [
            "id",
            "slug",
            "name",
            "image",  # This will be the full URL path
            "alt_text",
        ]


class PageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Page model, which now dynamically resolves image slugs
    in structured content to full URLs for public consumption.
    """

    images = PublicContentImageSerializer(many=True, read_only=True)
    content_structured_resolved = serializers.SerializerMethodField()

    class Meta:
        model = models.Page
        fields = [
            "slug",
            "title",
            "content",
            "content_structured_resolved",  # This resolved field is sent to the client
            "images",
            "icon_class",
            "updated_at",
        ]
        read_only_fields = ["updated_at", "images"]

    def get_content_structured_resolved(self, obj):
        """
        Resolves image slugs using the 'image_url_map' passed in the context.
        """
        if not obj.content_structured:
            return None

        # Get the pre-built map from the context
        image_map = self.context.get("image_url_map", {})

        resolved_content = obj.content_structured.copy()

        for key, item in resolved_content.items():
            if isinstance(item, dict) and item.get("type") == "image":
                image_slug = item.get("value")

                # Look up the slug in the map and replace it with the URL.
                # If the slug is not found (e.g., image not uploaded yet),
                # the value will be None.
                item["value"] = image_map.get(image_slug, None)

        return resolved_content


class FAQItemSerializer(serializers.ModelSerializer):
    """Serializer for individual FAQ items."""

    class Meta:
        model = models.FAQItem
        fields = ["id", "question", "answer"]


class FAQCategorySerializer(serializers.ModelSerializer):
    """Serializer for FAQ categories, including nested items."""

    items = FAQItemSerializer(many=True, read_only=True)

    class Meta:
        model = models.FAQCategory
        fields = ["id", "name", "items"]


class PartnerCategorySerializer(serializers.ModelSerializer):
    """Serializer for Success Partner categories."""

    class Meta:
        model = models.PartnerCategory
        fields = [
            "id",
            "name",
            "description",
            "icon_svg_or_class",
            "google_form_link",
        ]


class HomepageFeatureCardSerializer(serializers.ModelSerializer):
    """Serializer for Homepage Feature Cards."""

    class Meta:
        model = models.HomepageFeatureCard
        fields = ["title", "text", "svg_image", "icon_class"]


class HomepageStatisticSerializer(serializers.ModelSerializer):
    """Serializer for Homepage Statistics."""

    class Meta:
        model = models.HomepageStatistic
        fields = ["label", "value", "icon_class"]


class HomepageSerializer(serializers.Serializer):
    """Aggregates data for the homepage from various models."""

    intro = PageSerializer(read_only=True)
    praise = PageSerializer(read_only=True)
    about_us = PageSerializer(allow_null=True, required=False)
    features = HomepageFeatureCardSerializer(many=True, read_only=True)
    statistics = HomepageStatisticSerializer(many=True, read_only=True)
    why_partner_text = PageSerializer(read_only=True)
    call_to_action = PageSerializer(allow_null=True, required=False)


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating ContactMessage instances."""

    class Meta:
        model = models.ContactMessage
        fields = [
            "id",
            "full_name",
            "email",
            "subject",
            "message",
            "attachment",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate_subject(self, value):
        if len(value) < 5:
            raise serializers.ValidationError(
                _("Subject must be at least 5 characters long.")
            )
        return value
