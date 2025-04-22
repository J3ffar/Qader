from rest_framework import generics, viewsets, views, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import filters

# Correct import for drf-spectacular utilities
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)
from django.utils.translation import gettext_lazy as _  # Added for translation
from django.db.models import Prefetch

from apps.content import models
from . import serializers
from django.conf import settings  # If sourcing video URL from settings


@extend_schema_view(
    list=extend_schema(tags=["Public Content"], summary="List Static Pages (by slug)"),
    retrieve=extend_schema(
        tags=["Public Content"], summary="Retrieve Static Page Content"
    ),
)
class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows static pages (Terms, Story, etc.) to be viewed.
    Retrieves pages by their unique 'slug'.
    """

    queryset = models.Page.objects.filter(is_published=True)
    serializer_class = serializers.PageSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"  # Use slug instead of ID for lookup


@extend_schema(
    tags=["Public Content"],
    summary="Retrieve Homepage Content",
    description="Aggregates various content pieces needed to render the homepage.",
)
class HomepageView(views.APIView):
    """
    API endpoint to retrieve aggregated data for the homepage.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Use specific slugs defined for homepage content
        try:
            intro_page = models.Page.objects.get(
                slug="homepage-intro", is_published=True
            )
        except models.Page.DoesNotExist:
            intro_page = None

        try:
            praise_page = models.Page.objects.get(
                slug="homepage-praise", is_published=True
            )
        except models.Page.DoesNotExist:
            praise_page = None

        try:
            why_partner_page = models.Page.objects.get(
                slug="why-partner", is_published=True
            )
        except models.Page.DoesNotExist:
            why_partner_page = None

        feature_cards = models.HomepageFeatureCard.objects.filter(
            is_active=True
        ).order_by("order")
        statistics = models.HomepageStatistic.objects.filter(is_active=True).order_by(
            "order"
        )

        # Example: Get video URL from settings (adjust if stored elsewhere)
        video_url = getattr(settings, "HOMEPAGE_INTRO_VIDEO_URL", None)

        # Prepare context for the serializer
        context_data = {
            "intro": intro_page,
            "praise": praise_page,
            "intro_video_url": video_url,
            "features": feature_cards,
            "statistics": statistics,
            "why_partner_text": why_partner_page,
        }

        serializer = serializers.HomepageSerializer(
            instance=context_data, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema(
    tags=["Public Content"],
    summary="List FAQs by Category",
    description="Retrieves all active FAQ categories and their associated active FAQ items. Supports searching.",
    parameters=[
        # Use the correctly imported OpenApiParameter
        OpenApiParameter(
            name="search",
            description="Filter FAQs by text in question or answer",
            required=False,
            type=str,
        ),
    ],
)
class FAQListView(generics.ListAPIView):
    """
    API endpoint that lists all FAQ categories with their items.
    Supports searching within questions and answers.
    """

    serializer_class = serializers.FAQCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "name",
        "items__question",
        "items__answer",
    ]  # Search category name and item fields

    def get_queryset(self):
        # Prefetch related items for efficiency
        return models.FAQCategory.objects.prefetch_related(
            Prefetch(
                "items",
                queryset=models.FAQItem.objects.filter(is_active=True).order_by(
                    "order"
                ),
            )
        ).order_by("order", "name")


@extend_schema(
    tags=["Public Content"],
    summary="List Success Partner Categories",
    description="Retrieves the different types of partnerships offered.",
)
class PartnerCategoryListView(generics.ListAPIView):
    """
    API endpoint that lists active success partner categories.
    """

    queryset = models.PartnerCategory.objects.filter(is_active=True).order_by("order")
    serializer_class = serializers.PartnerCategorySerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Public Content"],
    summary="Submit Contact Us Message",
    description="Allows users to submit inquiries via the Contact Us form. Supports optional file attachment.",
    request={
        # Use the ContactMessageSerializer for the request schema
        "multipart/form-data": serializers.ContactMessageSerializer
    },
    responses={
        # Use the correctly imported OpenApiResponse and OpenApiExample
        201: OpenApiResponse(
            description="Message submitted successfully.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value={"detail": "Thank you for contacting us..."},
                )
            ],
        ),
        400: OpenApiResponse(description="Validation Error"),
    },
)
class ContactMessageCreateView(generics.CreateAPIView):
    """
    API endpoint to create a new contact message from the Contact Us form.
    """

    queryset = models.ContactMessage.objects.all()
    serializer_class = serializers.ContactMessageSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Potential future actions: Send email notification to admin
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Return the custom success message as per API docs
        return Response(
            # Use the translated string
            {
                "detail": _(
                    "Thank you for contacting us. We will get back to you as soon as possible, God willing."
                )
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
