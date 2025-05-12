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


from apps.users.constants import (
    SUBSCRIPTION_PLANS_CONFIG,
)

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
        description="Generate multiple serial codes based on a selected standard plan type (e.g., 1 Month, 3 Months, 12 Months). Uses centralized configuration.",
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
        Generates a batch of unique serial codes using SUBSCRIPTION_PLANS_CONFIG.
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data

            plan_enum_value = validated_data[
                "plan_type"
            ]  # CHANGED: Use plan_type from serializer
            count = validated_data["count"]
            notes = validated_data.get("notes")
            creator = request.user

            config = SUBSCRIPTION_PLANS_CONFIG.get(plan_enum_value)

            # --- Validation (already handled by serializer's validate_plan_type) ---
            # No need for config or CUSTOM type check here if serializer handles it.
            # The serializer's validate_plan_type ensures 'config' will exist and 'duration_days' is present.

            duration_days = config["duration_days"]  # Now safe to access
            prefix = config.get("prefix", "QDRAPI")
            # --- End Validation ---

            new_codes = []
            generated_code_strings = (
                set()
            )  # To check uniqueness within the current batch

            with transaction.atomic():
                for i in range(count):
                    # Loop to ensure unique code generation, especially if generate_unique_serial_code
                    # might produce a duplicate already in generated_code_strings for this batch
                    while True:
                        code_str = generate_unique_serial_code(prefix=prefix)
                        # SerialCode model's clean method (if called by save) will uppercase.
                        # Or ensure generate_unique_serial_code returns uppercase.
                        # For batch check, ensure consistency.
                        code_upper = code_str.upper()
                        if (
                            not SerialCode.objects.filter(
                                code__iexact=code_upper
                            ).exists()
                            and code_upper not in generated_code_strings
                        ):
                            generated_code_strings.add(code_upper)
                            break
                        # Optional: Add a safety break if too many attempts to find unique code
                        # if attempts > MAX_ATTEMPS: raise Exception("...")

                    new_codes.append(
                        SerialCode(
                            code=code_upper,  # Store uppercase for consistency
                            duration_days=duration_days,
                            subscription_type=plan_enum_value,  # This is correct: model's type is the plan enum
                            notes=notes,
                            created_by=creator,
                            is_active=True,
                            is_used=False,
                        )
                    )

                created_instances = SerialCode.objects.bulk_create(new_codes)
                logger.info(
                    f"Admin '{creator.username}' generated {len(created_instances)} serial codes via API (Plan: {plan_enum_value}, Notes: {notes or 'N/A'})."
                )

                return Response(
                    {
                        "detail": _(
                            f"{len(created_instances)} serial codes generated successfully for plan '{SUBSCRIPTION_PLANS_CONFIG[plan_enum_value]['name']}'."
                        )  # Using plan name for better message
                    },
                    status=status.HTTP_201_CREATED,
                )

        except serializers.ValidationError as e:
            logger.warning(
                f"Serial code batch generation validation failed (API) for admin '{request.user.username}': {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            logger.error(
                f"Database integrity error during serial code batch generation (API) by '{request.user.username}': {e}"
            )
            # This could happen if generate_unique_serial_code is not robust enough
            # and bulk_create hits a unique constraint for 'code'
            return Response(
                {
                    "detail": _(
                        "A database conflict occurred during code generation. This might be due to a code collision. Please try again."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error generating serial codes (API) for admin '{request.user.username}': {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred during code generation.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
