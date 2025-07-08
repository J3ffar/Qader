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

    def get_serializer_context(self):
        """
        Overrides the default context to add a map of resolved image URLs.
        This is crucial for the PageSerializer to resolve slugs within structured content.
        """
        # Get the default context from the parent class
        context = super().get_serializer_context()
        request = context.get("request")

        # This logic only applies to the 'retrieve' action (getting a single page)
        if self.action == "retrieve" and request:
            # `self.get_object()` gets the current Page instance being viewed
            page = self.get_object()
            image_url_map = {}

            if page and page.content_structured:
                # 1. Collect all image slugs from this page's structured content
                image_slugs = {
                    item.get("value")
                    for item in page.content_structured.values()
                    if isinstance(item, dict)
                    and item.get("type") == "image"
                    and item.get("value")
                }

                # Also collect slugs from repeater fields (like the story cards)
                for item in page.content_structured.values():
                    if (
                        isinstance(item, dict)
                        and item.get("type") == "repeater"
                        and isinstance(item.get("value"), list)
                    ):
                        for sub_item in item.get("value"):
                            if (
                                isinstance(sub_item, dict)
                                and sub_item.get("icon_type") == "image"
                            ):
                                if sub_item.get("icon_value"):
                                    image_slugs.add(sub_item.get("icon_value"))

                # 2. Query the database once for all required images
                # We can use the prefetched `page.images` for efficiency
                image_objects = page.images.filter(slug__in=list(image_slugs))

                # 3. Create the slug -> URL map
                image_url_map = {
                    img.slug: request.build_absolute_uri(img.image.url)
                    for img in image_objects
                    if img.image
                }

            # 4. Add the map to the context
            context["image_url_map"] = image_url_map

        return context


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
        required_slugs = [
            "homepage-intro",
            "homepage-about-us",
            "homepage-praise",
            "homepage-why-partner",
            "homepage-cta",
        ]
        pages_qs = models.Page.objects.filter(
            slug__in=required_slugs, is_published=True
        ).prefetch_related("images")

        pages = {page.slug: page for page in pages_qs}

        # 1. Collect all image slugs referenced in the structured content of all pages.
        all_image_slugs = set()
        for page in pages.values():
            if not page.content_structured:
                continue
            for item in page.content_structured.values():
                if isinstance(item, dict) and item.get("type") == "image":
                    if item.get("value"):
                        all_image_slugs.add(item.get("value"))

        # 2. Perform a single database query to get all required images.
        image_objects = models.ContentImage.objects.filter(
            slug__in=list(all_image_slugs)
        )

        # 3. Create a map of {slug: "full/url/to/image.png"}
        image_url_map = {
            img.slug: request.build_absolute_uri(img.image.url)
            for img in image_objects
            if img.image
        }

        # 4. Prepare the context to be passed to the serializer
        serializer_context = {
            "request": request,
            "image_url_map": image_url_map,  # Pass the map to the serializer
        }

        feature_cards = models.HomepageFeatureCard.objects.filter(
            is_active=True
        ).order_by("order")
        statistics = models.HomepageStatistic.objects.filter(is_active=True).order_by(
            "order"
        )

        context_data = {
            "intro": pages.get("homepage-intro"),
            "praise": pages.get("homepage-praise"),
            "about_us": pages.get("homepage-about-us"),
            "features": feature_cards,
            "statistics": statistics,
            "why_partner_text": pages.get("homepage-why-partner"),
            "call_to_action": pages.get("homepage-cta"),
        }

        serializer = serializers.HomepageSerializer(
            instance=context_data, context=serializer_context
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

    def get(self, request, *args, **kwargs):
        # Fetch FAQ data
        faq_categories = models.FAQCategory.objects.prefetch_related(
            Prefetch(
                "items",
                queryset=models.FAQItem.objects.filter(is_active=True).order_by(
                    "order"
                ),
            )
        ).order_by("order", "name")

        # Fetch Page content
        page_content = models.Page.objects.filter(
            slug="faq-page", is_published=True
        ).first()

        faq_serializer = serializers.FAQCategorySerializer(faq_categories, many=True)
        page_serializer = serializers.PageSerializer(
            page_content, context={"request": request}
        )

        response_data = {
            "faq_data": faq_serializer.data,
            "page_content": page_serializer.data if page_content else None,
        }

        return Response(response_data)


@extend_schema(
    tags=["Public Content"],
    summary="List Success Partner Categories",
    description="Retrieves partnership types and related page content.",
)
class PartnerCategoryListView(views.APIView):
    """API endpoint listing active partner categories and related page content."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        categories = models.PartnerCategory.objects.filter(is_active=True).order_by(
            "order"
        )

        page_content = (
            models.Page.objects.filter(slug="partners-page", is_published=True)
            .prefetch_related("images")
            .first()
        )

        # --- START OF CHANGE ---
        # The logic for resolving partner icons is no longer needed here.
        # We only need to resolve the single image from the page_content.
        image_url_map = {}
        if page_content and page_content.content_structured:
            image_slug = page_content.content_structured.get(
                "why_partner_image", {}
            ).get("value")
            if image_slug:
                image_obj = models.ContentImage.objects.filter(slug=image_slug).first()
                if image_obj and image_obj.image:
                    image_url_map[image_slug] = request.build_absolute_uri(
                        image_obj.image.url
                    )

        page_serializer_context = {"request": request, "image_url_map": image_url_map}
        # --- END OF CHANGE ---

        # The PartnerCategorySerializer will now handle the icon_image URL automatically
        category_serializer = serializers.PartnerCategorySerializer(
            categories, many=True, context={"request": request}
        )
        page_content_serializer = serializers.PageSerializer(
            page_content, context=page_serializer_context
        )

        response_data = {
            "partner_categories": category_serializer.data,
            "page_content": page_content_serializer.data if page_content else None,
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
