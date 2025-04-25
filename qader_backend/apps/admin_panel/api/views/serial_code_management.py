from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.db import transaction, IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.users.models import SerialCode, SubscriptionTypeChoices  # Import the enum
from apps.users.utils import generate_unique_serial_code

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes


# Import the new SerialCodeCreateSerializer we will define below
from ..serializers.serial_code_management import (
    SerialCodeListSerializer,
    SerialCodeDetailSerializer,
    SerialCodeUpdateSerializer,
    SerialCodeGenerateSerializer,
    SerialCodeCreateSerializer,  # Import the new serializer
)

import logging

logger = logging.getLogger(__name__)

# --- Define Plan Configuration ---
# Similar to the management command
PLAN_CONFIG = {
    SubscriptionTypeChoices.MONTH_1: {
        "prefix": "QDR1M",
        "duration_days": 30,
    },
    SubscriptionTypeChoices.MONTH_6: {
        "prefix": "QDR6M",
        "duration_days": 183,
    },
    SubscriptionTypeChoices.MONTH_12: {
        "prefix": "QDR12M",
        "duration_days": 365,
    },
    # Define behavior for custom if needed, maybe a default prefix/duration
    SubscriptionTypeChoices.CUSTOM: {
        "prefix": "QDRCST",  # Example prefix for custom
        "duration_days": None,  # Duration must be specified separately for custom
    },
}


@extend_schema_view(
    list=extend_schema(
        tags=["Admin Panel - Serial Code Management"],
        summary="List Serial Codes",
        description="Retrieve a list of all serial codes. Supports filtering, searching, and ordering.",
        parameters=[  # Add common query parameters for documentation
            OpenApiTypes.INT,  # page
            OpenApiTypes.INT,  # page_size
            OpenApiTypes.BOOL,  # is_active
            OpenApiTypes.BOOL,  # is_used
            OpenApiTypes.STR,  # subscription_type (use enum values: 1_month, 6_months, etc.)
            OpenApiTypes.STR,  # created_by__username
            OpenApiTypes.STR,  # search
            OpenApiTypes.STR,  # ordering (e.g., 'created_at', '-used_at')
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SerialCodeListSerializer(many=True),
                description="List of serial codes retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Admin permission required."
            ),
        },
    ),
    create=extend_schema(
        tags=["Admin Panel - Serial Code Management"],
        summary="Create Single Serial Code",
        description="Manually create a single, specific serial code with defined properties.",
        request=SerialCodeCreateSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=SerialCodeDetailSerializer,
                description="Serial code created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation Error (e.g., code already exists, invalid input)."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Admin permission required."
            ),
        },
    ),
    retrieve=extend_schema(
        tags=["Admin Panel - Serial Code Management"],
        summary="Retrieve Serial Code Details",
        description="Get the detailed information for a specific serial code by its ID.",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SerialCodeDetailSerializer,
                description="Serial code details retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Admin permission required."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Serial code not found."
            ),
        },
    ),
    update=extend_schema(  # Covers PUT
        tags=["Admin Panel - Serial Code Management"],
        summary="Update Serial Code (Full)",
        description="Fully update the editable fields of a serial code (typically 'is_active' and 'notes'). Requires all fields from the update serializer.",
        request=SerialCodeUpdateSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SerialCodeDetailSerializer,  # Return full detail after update
                description="Serial code updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation Error."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Admin permission required."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Serial code not found."
            ),
        },
    ),
    partial_update=extend_schema(  # Covers PATCH
        tags=["Admin Panel - Serial Code Management"],
        summary="Partially Update Serial Code",
        description="Partially update the editable fields of a serial code (typically 'is_active' and 'notes'). Only include the fields to be changed.",
        request=SerialCodeUpdateSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SerialCodeDetailSerializer,  # Return full detail after update
                description="Serial code updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation Error."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Admin permission required."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Serial code not found."
            ),
        },
    ),
    destroy=extend_schema(
        tags=["Admin Panel - Serial Code Management"],
        summary="Delete Serial Code",
        description="Permanently delete a specific serial code by its ID.",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Serial code deleted successfully."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Admin permission required."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Serial code not found."
            ),
        },
    ),
    generate_codes=extend_schema(  # Custom action
        tags=["Admin Panel - Serial Code Management"],
        summary="Generate Batch of Serial Codes",
        description="Generate multiple serial codes based on a selected plan type (1 Month, 6 Months, 12 Months).",
        request=SerialCodeGenerateSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=inline_serializer(
                    name="GenerateCodesSuccessResponse",
                    fields={"detail": serializers.CharField()},
                ),
                description="Batch of serial codes generated successfully.",
                examples=[
                    OpenApiExample(
                        "Success Example",
                        value={
                            "detail": "50 serial codes generated successfully for plan '1 Month'."
                        },
                    )
                ],
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation Error (e.g., invalid plan type, count out of range)."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Admin permission required."
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="Database conflict during generation (rare)."
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Unexpected error during generation."
            ),
        },
    ),
)
class SerialCodeAdminViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing Serial Codes.
    Allows listing, retrieving, creating (single), updating, deleting (single),
    and generating batches of new serial codes based on plan types.
    """

    queryset = SerialCode.objects.select_related("used_by", "created_by").order_by(
        "-created_at"
    )
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "is_active",
        "is_used",
        "subscription_type",
        "created_by__username",
    ]
    search_fields = ["code", "notes", "used_by__username", "created_by__username"]
    ordering_fields = ["created_at", "used_at", "is_used", "is_active", "duration_days"]
    ordering = ["-created_at"]  # Default ordering

    def get_serializer_class(self):
        if self.action == "list":
            return SerialCodeListSerializer
        elif self.action == "retrieve":
            return SerialCodeDetailSerializer
        elif self.action in ["update", "partial_update"]:
            return SerialCodeUpdateSerializer
        elif self.action == "generate_codes":  # Custom action uses its own serializer
            return SerialCodeGenerateSerializer
        elif self.action == "create":  # Standard POST uses the create serializer
            return SerialCodeCreateSerializer
        # Default for other actions (like default destroy if enabled)
        return SerialCodeDetailSerializer

    # --- Enable Standard Create (POST for single code) ---
    def perform_create(self, serializer):
        """Set the creator automatically when creating a single code."""
        serializer.save(created_by=self.request.user)
        logger.info(
            f"Admin '{self.request.user.username}' created single serial code: {serializer.instance.code}"
        )

    # --- Enable Standard Destroy (DELETE for single code) ---
    # No override needed unless custom logic is required before deletion.
    # The default destroy method will be used. We add a log message for clarity.
    def perform_destroy(self, instance):
        code = instance.code  # Get code before deletion
        instance.delete()
        logger.info(f"Admin '{self.request.user.username}' deleted serial code: {code}")

    # --- Modified Custom Action for Batch Generation ---
    @action(detail=False, methods=["post"], url_path="generate-batch")
    def generate_codes(self, request, *args, **kwargs):
        """
        Generates a batch of unique serial codes based on the specified plan type.
        """
        serializer = SerialCodeGenerateSerializer(
            data=request.data,
            context=self.get_serializer_context(),  # Important to pass context
        )
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            plan_type = validated_data["plan_type"]
            count = validated_data["count"]
            notes = validated_data.get("notes")
            creator = request.user

            # Get config for the selected plan
            config = PLAN_CONFIG.get(plan_type)
            if not config:
                # Should be caught by serializer choices, but defensive check
                raise serializers.ValidationError(
                    {"plan_type": _("Invalid plan type specified.")}
                )

            prefix = config["prefix"]
            # Duration comes from config, unless it's CUSTOM (then it must be specified *if needed*)
            # In this simplified API version, we assume CUSTOM codes also get a default duration
            # or that the generator logic handles it. Let's assume CUSTOM isn't generated this way for simplicity
            # or requires a specific duration in the request (modify serializer if needed).
            # We'll stick to the defined durations for 1m, 6m, 12m.
            if plan_type == SubscriptionTypeChoices.CUSTOM:
                # Decide how to handle custom duration generation via API.
                # Option 1: Disallow generating CUSTOM via this batch endpoint.
                raise serializers.ValidationError(
                    {
                        "plan_type": _(
                            "Generating 'Custom' type codes via batch is not supported. Use standard POST to create custom codes individually."
                        )
                    }
                )
                # Option 2: Require 'duration_days' in SerialCodeGenerateSerializer if plan_type is CUSTOM.
                # duration_days = validated_data.get('duration_days') # Add to serializer if needed
                # if duration_days is None: raise serializers.ValidationError(...)
            else:
                duration_days = config["duration_days"]

            new_codes = []
            generated_code_strings = (
                set()
            )  # Keep track of codes generated in this batch

            # Use a transaction to ensure all codes are created or none are
            with transaction.atomic():
                for i in range(count):
                    # Loop to ensure uniqueness even with potential collisions during generation
                    while True:
                        # Pass the determined prefix to the utility function
                        code_str = generate_unique_serial_code(prefix=prefix)
                        # Check against DB (via util) and current batch
                        if code_str.upper() not in generated_code_strings:
                            generated_code_strings.add(code_str.upper())
                            break

                    new_codes.append(
                        SerialCode(
                            code=code_str,
                            duration_days=duration_days,
                            subscription_type=plan_type,  # Use the enum value directly
                            notes=notes,
                            created_by=creator,
                            is_active=True,  # New codes are active by default
                            is_used=False,
                        )
                    )

                # Use bulk_create for efficiency
                created_instances = SerialCode.objects.bulk_create(new_codes)
                logger.info(
                    f"Admin '{creator.username}' generated {len(created_instances)} serial codes (Plan: {plan_type}, Notes: {notes or 'N/A'})."
                )

                # Simpler response indicating success
                return Response(
                    {
                        "detail": _(
                            f"{len(created_instances)} serial codes generated successfully for plan '{plan_type}'."
                        )
                    },
                    status=status.HTTP_201_CREATED,
                )

        except serializers.ValidationError as e:
            logger.warning(
                f"Serial code batch generation validation failed for admin '{request.user.username}': {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            logger.error(
                f"Database integrity error during serial code batch generation by '{request.user.username}': {e}"
            )
            return Response(
                {
                    "detail": _(
                        "A database conflict occurred during code generation. Please try again."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error generating serial codes for admin '{request.user.username}': {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred during code generation.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
