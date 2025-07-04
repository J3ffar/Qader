from rest_framework import generics, viewsets, views, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import filters
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch
from django.conf import settings

from apps.content import models
from . import serializers


@extend_schema_view(
    list=extend_schema(tags=["Public Content"], summary="List Static Pages"),
    retrieve=extend_schema(
        tags=["Public Content"], summary="Retrieve Static Page Content"
    ),
)
class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows static pages (Terms, Story, etc.) to be viewed.
    Retrieves pages by their unique 'slug'.
    """

    # Use prefetch_related to fetch all associated images in a single extra query.
    queryset = models.Page.objects.filter(is_published=True).prefetch_related("images")
    serializer_class = serializers.PageSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"


@extend_schema(
    tags=["Public Content"],
    summary="Retrieve Homepage Content",
    description="Aggregates various content pieces needed to render the homepage.",
)
class HomepageView(views.APIView):
    """
    API endpoint to retrieve aggregated data for the homepage.
    Optimized to fetch all required page content efficiently.
    """

    serializer_class = serializers.HomepageSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        required_slugs = ["homepage-intro", "homepage-praise", "why-partner"]
        pages_qs = models.Page.objects.filter(
            slug__in=required_slugs, is_published=True
        ).prefetch_related("images")

        pages = {page.slug: page for page in pages_qs}

        feature_cards = models.HomepageFeatureCard.objects.filter(
            is_active=True
        ).order_by("order")
        statistics = models.HomepageStatistic.objects.filter(is_active=True).order_by(
            "order"
        )
        video_url = getattr(settings, "HOMEPAGE_INTRO_VIDEO_URL", None)

        context_data = {
            "intro": pages.get("homepage-intro"),
            "praise": pages.get("homepage-praise"),
            "intro_video_url": video_url,
            "features": feature_cards,
            "statistics": statistics,
            "why_partner_text": pages.get("why-partner"),
        }

        serializer = serializers.HomepageSerializer(
            instance=context_data, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema(
    tags=["Public Content"],
    summary="List FAQs by Category",
    parameters=[
        OpenApiParameter(
            name="search",
            description="Filter FAQs by text in question or answer",
            required=False,
            type=str,
        ),
    ],
)
class FAQListView(generics.ListAPIView):
    """API endpoint that lists all FAQ categories with their items."""

    serializer_class = serializers.FAQCategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "items__question", "items__answer"]

    def get_queryset(self):
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
    description="Retrieves partnership types and the 'Why Partner' explanatory text.",
)
class PartnerCategoryListView(views.APIView):
    """API endpoint listing active partner categories and the 'Why Partner' text."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        categories = models.PartnerCategory.objects.filter(is_active=True).order_by(
            "order"
        )

        why_partner_page = (
            models.Page.objects.filter(slug="why-partner", is_published=True)
            .prefetch_related("images")
            .first()
        )

        category_serializer = serializers.PartnerCategorySerializer(
            categories, many=True
        )
        page_serializer = serializers.PageSerializer(
            why_partner_page, context={"request": request}
        )

        response_data = {
            "partner_categories": category_serializer.data,
            "why_partner_text": page_serializer.data if why_partner_page else None,
        }

        return Response(response_data)


@extend_schema(
    tags=["Public Content"],
    summary="Submit Contact Us Message",
    request={"multipart/form-data": serializers.ContactMessageSerializer},
    responses={
        201: OpenApiResponse(description="Message submitted successfully."),
        400: OpenApiResponse(description="Validation Error"),
    },
)
class ContactMessageCreateView(generics.CreateAPIView):
    """API endpoint to create a new contact message from the Contact Us form."""

    queryset = models.ContactMessage.objects.all()
    serializer_class = serializers.ContactMessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "detail": _(
                    "Thank you for contacting us. We will get back to you as soon as possible, God willing."
                )
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
