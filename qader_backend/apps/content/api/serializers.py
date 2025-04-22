from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.content import models


class PageSerializer(serializers.ModelSerializer):
    """Serializer for the Page model (Terms, Story, etc.)."""

    class Meta:
        model = models.Page
        fields = [
            "slug",
            "title",
            "content",
            "icon_class",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]  # Ensure updated_at is read-only


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
        fields = [
            "title",
            "text",
            "svg_image",
            "icon_class",
        ]  # Removed order/is_active as not needed for API consumer


class HomepageStatisticSerializer(serializers.ModelSerializer):
    """Serializer for Homepage Statistics."""

    class Meta:
        model = models.HomepageStatistic
        fields = ["label", "value", "icon_class"]  # Removed order/is_active


class HomepageSerializer(serializers.Serializer):
    """Aggregates data for the homepage from various models."""

    intro = PageSerializer(read_only=True)
    praise = PageSerializer(read_only=True)
    intro_video_url = serializers.URLField(
        read_only=True
    )  # Assuming this comes from settings or another model
    features = HomepageFeatureCardSerializer(many=True, read_only=True)
    statistics = HomepageStatisticSerializer(many=True, read_only=True)
    why_partner_text = PageSerializer(read_only=True)  # Added based on partners API doc

    # If intro_video_url needs to be sourced differently, adjust accordingly
    # Example: source from Django settings
    # intro_video_url = serializers.SerializerMethodField()
    # def get_intro_video_url(self, obj):
    #     return getattr(settings, 'HOMEPAGE_INTRO_VIDEO_URL', None)


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating ContactMessage instances."""

    class Meta:
        model = models.ContactMessage
        fields = [
            "id",  # ReadOnly on create, useful in response
            "full_name",
            "email",
            "subject",
            "message",
            "attachment",
            "status",  # ReadOnly on create
            "created_at",  # ReadOnly on create
            "updated_at",  # ReadOnly on create
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate_subject(self, value):
        # Example validation
        if len(value) < 5:
            raise serializers.ValidationError(
                _("Subject must be at least 5 characters long.")
            )
        return value

    # Add more validation as needed (e.g., attachment size/type if required)
