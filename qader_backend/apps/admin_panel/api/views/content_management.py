from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, filters, mixins
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.parsers import MultiPartParser, FormParser

from apps.content import models as content_models
from apps.admin_panel.api.serializers import content_management as admin_serializers

# Assuming you have a standard IsAdmin permission, otherwise use IsAdminUser
# from apps.api.permissions import IsAdmin
from rest_framework.permissions import IsAdminUser  # Using built-in for simplicity
from ..permissions import (
    IsAdminUserOrSubAdminWithPermission,
)  # Import the custom permission


ADMIN_CONTENT_TAG = ["Admin Panel - Content Management"]


@extend_schema_view(
    list=extend_schema(tags=ADMIN_CONTENT_TAG, summary="List Pages (Admin)"),
    create=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Create Page (Admin)"),
    retrieve=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Retrieve Page (Admin)"),
    update=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Update Page (Admin)"),
    partial_update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Partially Update Page (Admin)"
    ),
    destroy=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Delete Page (Admin)"),
)
class PageAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing static Pages."""

    queryset = content_models.Page.objects.all().order_by(  # pylint: disable=no-member
        "title"
    )
    serializer_class = admin_serializers.AdminPageSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]  # Or your custom IsAdmin
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["slug", "title", "content"]
    ordering_fields = [
        "id",
        "title",
        "slug",
        "is_published",
        "created_at",
        "updated_at",
    ]
    lookup_field = "slug"  # Maintain consistency with public view

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(tags=ADMIN_CONTENT_TAG, summary="List FAQ Categories (Admin)"),
    create=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Create FAQ Category (Admin)"),
    retrieve=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Retrieve FAQ Category (Admin)"
    ),
    update=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Update FAQ Category (Admin)"),
    partial_update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Partially Update FAQ Category (Admin)"
    ),
    destroy=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Delete FAQ Category (Admin)"
    ),
)
class FAQCategoryAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing FAQ Categories."""

    queryset = (
        content_models.FAQCategory.objects.all().order_by(  # pylint: disable=no-member
            "order", "name"
        )
    )
    serializer_class = admin_serializers.AdminFAQCategorySerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "order", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(tags=ADMIN_CONTENT_TAG, summary="List FAQ Items (Admin)"),
    create=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Create FAQ Item (Admin)"),
    retrieve=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Retrieve FAQ Item (Admin)"),
    update=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Update FAQ Item (Admin)"),
    partial_update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Partially Update FAQ Item (Admin)"
    ),
    destroy=extend_schema(tags=ADMIN_CONTENT_TAG, summary="Delete FAQ Item (Admin)"),
)
class FAQItemAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing FAQ Items."""

    queryset = (
        content_models.FAQItem.objects.select_related(  # pylint: disable=no-member
            "category"
        )
        .all()
        .order_by("category__order", "order", "question")
    )
    serializer_class = admin_serializers.AdminFAQItemSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "is_active"]
    search_fields = ["question", "answer", "category__name"]
    ordering_fields = ["category__name", "order", "question", "is_active", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="List Partner Categories (Admin)"
    ),
    create=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Create Partner Category (Admin)"
    ),
    retrieve=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Retrieve Partner Category (Admin)"
    ),
    update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Update Partner Category (Admin)"
    ),
    partial_update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Partially Update Partner Category (Admin)"
    ),
    destroy=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Delete Partner Category (Admin)"
    ),
)
class PartnerCategoryAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Partner Categories."""

    queryset = content_models.PartnerCategory.objects.all().order_by(  # pylint: disable=no-member
        "order", "name"
    )
    serializer_class = admin_serializers.AdminPartnerCategorySerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "order", "is_active", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="List Homepage Feature Cards (Admin)"
    ),
    create=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Create Homepage Feature Card (Admin)"
    ),
    retrieve=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Retrieve Homepage Feature Card (Admin)"
    ),
    update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Update Homepage Feature Card (Admin)"
    ),
    partial_update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Partially Update Homepage Feature Card (Admin)"
    ),
    destroy=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Delete Homepage Feature Card (Admin)"
    ),
)
class HomepageFeatureCardAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Homepage Feature Cards."""

    queryset = content_models.HomepageFeatureCard.objects.all().order_by(  # pylint: disable=no-member
        "order"
    )
    serializer_class = admin_serializers.AdminHomepageFeatureCardSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "text"]
    ordering_fields = ["title", "order", "is_active", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="List Homepage Statistics (Admin)"
    ),
    create=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Create Homepage Statistic (Admin)"
    ),
    retrieve=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Retrieve Homepage Statistic (Admin)"
    ),
    update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Update Homepage Statistic (Admin)"
    ),
    partial_update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Partially Update Homepage Statistic (Admin)"
    ),
    destroy=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Delete Homepage Statistic (Admin)"
    ),
)
class HomepageStatisticAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Homepage Statistics."""

    queryset = content_models.HomepageStatistic.objects.all().order_by(  # pylint: disable=no-member
        "order"
    )
    serializer_class = admin_serializers.AdminHomepageStatisticSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["label", "value"]
    ordering_fields = ["label", "order", "is_active", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


# For Contact Messages, we don't want Admins to 'create' them.
# We only need List, Retrieve, Update (status/response), and Destroy.
@extend_schema_view(
    list=extend_schema(tags=ADMIN_CONTENT_TAG, summary="List Contact Messages (Admin)"),
    retrieve=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Retrieve Contact Message (Admin)"
    ),
    update=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Update Contact Message Status/Response (Admin)"
    ),
    partial_update=extend_schema(
        tags=ADMIN_CONTENT_TAG,
        summary="Partially Update Contact Message Status/Response (Admin)",
    ),
    destroy=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Delete Contact Message (Admin)"
    ),
)
class ContactMessageAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Admin ViewSet for managing Contact Messages.
    Allows viewing, updating status/response, and deleting. Does NOT allow creation.
    """

    queryset = (
        content_models.ContactMessage.objects.select_related(
            "responder"
        )  # pylint: disable=no-member
        .all()
        .order_by("-created_at")
    )
    serializer_class = admin_serializers.AdminContactMessageSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "email"]
    search_fields = ["full_name", "email", "subject", "message", "response"]
    ordering_fields = ["status", "created_at", "responded_at", "full_name", "email"]

    # The update method in the serializer handles setting responder/responded_at
    def perform_update(self, serializer):
        # Pass request context to serializer for accessing the user
        serializer.save()

    def get_permissions(self):
        if self.action == "list":
            self.required_permissions = ["view_contact_messages"]
        elif self.action == "retrieve":
            self.required_permissions = ["view_contact_messages"]
        elif self.action in ["update", "partial_update"]:
            self.required_permissions = ["reply_contact_messages"]
        elif self.action == "destroy":
            self.required_permissions = [
                "api_destroy_any"
            ]  # Or a more specific 'delete_contact_messages'
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="List General Media Images (Admin)"
    ),
    create=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Upload General Media Image (Admin)"
    ),
)
class ContentImageAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing the general media library (images NOT attached to a specific page)."""

    queryset = content_models.ContentImage.objects.filter(
        page__isnull=True
    ).select_related("uploaded_by")
    serializer_class = admin_serializers.AdminContentImageSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "alt_text", "slug"]
    ordering_fields = ["name", "created_at", "slug"]

    def get_permissions(self):
        self.required_permissions = ["api_manage_content"]
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="List Page-Specific Images (Admin)"
    ),
    create=extend_schema(
        tags=ADMIN_CONTENT_TAG, summary="Upload Image for a Specific Page (Admin)"
    ),
)
class PageContentImageAdminViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing images associated with a specific Page."""

    queryset = content_models.ContentImage.objects.all()
    serializer_class = admin_serializers.AdminContentImageSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return self.queryset.filter(page__slug=self.kwargs.get("page_slug"))

    def perform_create(self, serializer):
        page = get_object_or_404(content_models.Page, slug=self.kwargs.get("page_slug"))
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(page=page, uploaded_by=user)

    def get_permissions(self):
        self.required_permissions = ["api_manage_content"]
        return [permission() for permission in self.permission_classes]
