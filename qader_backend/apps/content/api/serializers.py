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

    def get_content_structured_resolved(self, page_instance):
        """
        This method takes the raw `content_structured` JSON, finds all references
        to image slugs, and replaces them with their corresponding full URLs from
        the page's prefetched `images` list.
        """
        content = page_instance.content_structured
        if not content or not isinstance(content, dict):
            return None

        # Create a lookup map of slug -> full_image_url for O(1) access.
        # This relies on the view prefetching `images` for this to be efficient.
        try:
            image_map = {
                image.slug: self.context["request"].build_absolute_uri(image.image.url)
                for image in page_instance.images.all()
                if image.slug and image.image
            }
        except (KeyError, AttributeError):
            # Fallback if request context is not available (e.g., in management commands)
            image_map = {
                image.slug: image.image.url
                for image in page_instance.images.all()
                if image.slug and image.image
            }

        def resolve_content(data_node):
            if isinstance(data_node, dict):
                # Check if this dictionary represents one of our keyed image objects
                if (
                    data_node.get("type") == "image"
                    and data_node.get("value") in image_map
                ):
                    # It's an image block, replace the slug with the full URL
                    return {**data_node, "value": image_map[data_node.get("value")]}
                # If not an image block, recurse through its values
                return {key: resolve_content(value) for key, value in data_node.items()}
            elif isinstance(data_node, list):
                # If it's a list, recurse through its items
                return [resolve_content(item) for item in data_node]
            else:
                # It's a primitive (string, number, etc.), return as is
                return data_node

        return resolve_content(content)


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
    intro_video_url = serializers.URLField(read_only=True)
    features = HomepageFeatureCardSerializer(many=True, read_only=True)
    statistics = HomepageStatisticSerializer(many=True, read_only=True)
    why_partner_text = PageSerializer(read_only=True)


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
