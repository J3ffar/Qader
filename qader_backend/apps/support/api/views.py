from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

# Import spectacular utils
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

from ..models import SupportTicket, SupportTicketReply
from .serializers import (
    SupportTicketListSerializer,
    SupportTicketDetailSerializer,
    SupportTicketCreateSerializer,
    SupportTicketReplySerializer,
    SupportTicketReplyCreateSerializer,
    SupportTicketAdminUpdateSerializer,
    UserBasicInfoSerializer,  # Import the basic user info serializer
)
from .permissions import IsTicketOwner, IsTicketOwnerOrAdmin

# from apps.api.permissions import IsAdminOrSubAdminWithPermission

# --- User Facing Views ---


# Apply schema tag for the entire ViewSet
@extend_schema_view(
    list=extend_schema(summary="List your support tickets", tags=["Support (User)"]),
    create=extend_schema(
        summary="Create a new support ticket", tags=["Support (User)"]
    ),
    retrieve=extend_schema(
        summary="Retrieve details of your support ticket", tags=["Support (User)"]
    ),
    replies=extend_schema(  # Tag the custom action specifically
        summary="List or add replies to your support ticket",
        tags=["Support (User)"],
        request=SupportTicketReplyCreateSerializer,  # Explicitly define request for POST
        responses={  # Define responses for GET and POST
            200: SupportTicketReplySerializer(many=True),  # GET success
            201: SupportTicketReplySerializer,  # POST success
        },
    ),
)
class UserSupportTicketViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for the current user to manage their support tickets.
    Allows listing own tickets, creating new tickets, viewing details, and adding replies.
    """

    serializer_class = SupportTicketListSerializer  # Default for list
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only return tickets belonging to the current user."""
        return (
            SupportTicket.objects.filter(user=self.request.user)
            .select_related("user", "assigned_to")
            .prefetch_related("replies__user")
        )  # Optimize queries

    def get_serializer_class(self):
        """Return different serializers for different actions."""
        if self.action == "create":
            return SupportTicketCreateSerializer
        if self.action == "retrieve":
            return SupportTicketDetailSerializer
        if self.action == "replies":  # Custom action for replies
            # Determine if GET or POST inside the action method for response serializer if needed,
            # but request serializer is needed for schema generation on POST.
            if self.request.method == "POST":
                return SupportTicketReplyCreateSerializer
            return SupportTicketReplySerializer  # For GET response schema hint
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """Set the user automatically when creating a ticket."""
        serializer.save(user=self.request.user)
        # TODO: Send notification to admin/support team

    def retrieve(self, request, *args, **kwargs):
        """Ensure user owns the ticket before retrieval."""
        instance = self.get_object()  # Checks ownership via get_queryset filter
        serializer = self.get_serializer(instance)
        data = serializer.data

        # Filter out internal notes for non-staff users
        if not request.user.is_staff:
            data["replies"] = [
                reply
                for reply in data.get("replies", [])
                if not reply.get("is_internal_note")
            ]
        return Response(data)

    # --- Nested Replies ---
    # Note: @extend_schema is now applied via @extend_schema_view above
    @action(detail=True, methods=["post", "get"], permission_classes=[IsTicketOwner])
    def replies(self, request, pk=None):
        """
        GET: List replies for a specific support ticket.
        POST: Add a reply to a specific support ticket.
        """
        ticket = self.get_object()  # Ensures user owns ticket

        if request.method == "POST":
            serializer = SupportTicketReplyCreateSerializer(
                data=request.data,
                context={
                    "request": request,
                    "ticket": ticket,
                },  # Pass request and ticket
            )
            serializer.is_valid(raise_exception=True)
            reply = serializer.save(user=request.user, ticket=ticket)
            # Update ticket status if user replies to a ticket pending their response
            if ticket.status == SupportTicket.Status.PENDING_USER:
                ticket.status = SupportTicket.Status.OPEN
                ticket.save(update_fields=["status", "updated_at"])
            # TODO: Send notification to assigned admin
            # Use the correct serializer for the response
            return Response(
                SupportTicketReplySerializer(reply).data, status=status.HTTP_201_CREATED
            )

        elif request.method == "GET":
            replies = ticket.replies.select_related("user").order_by("created_at")
            if not request.user.is_staff:
                replies = replies.filter(is_internal_note=False)

            # Paginate replies if desired
            # page = self.paginate_queryset(replies)
            # if page is not None:
            #     serializer = SupportTicketReplySerializer(page, many=True)
            #     return self.get_paginated_response(serializer.data)

            serializer = SupportTicketReplySerializer(replies, many=True)
            return Response(serializer.data)


# --- Admin Facing Views ---


# Apply schema tag for the entire Admin ViewSet
@extend_schema_view(
    list=extend_schema(
        summary="List all support tickets (Admin)", tags=["Admin Panel - Support"]
    ),
    create=extend_schema(
        summary="Create a support ticket (Admin - Less Common)",
        tags=["Admin Panel - Support"],
    ),
    retrieve=extend_schema(
        summary="Retrieve details of any support ticket (Admin)",
        tags=["Admin Panel - Support"],
    ),
    update=extend_schema(
        summary="Update ticket status/assignment/priority (Admin)",
        tags=["Admin Panel - Support"],
    ),
    partial_update=extend_schema(
        summary="Partially update ticket status/assignment/priority (Admin)",
        tags=["Admin Panel - Support"],
    ),
    destroy=extend_schema(
        summary="Delete a support ticket (Admin)", tags=["Admin Panel - Support"]
    ),
    replies=extend_schema(  # Tag the custom action specifically
        summary="List or add admin replies/internal notes to a ticket",
        tags=["Admin Panel - Support"],
        request=SupportTicketReplyCreateSerializer,  # Explicitly define request for POST
        responses={  # Define responses for GET and POST
            200: SupportTicketReplySerializer(many=True),  # GET success
            201: SupportTicketReplySerializer,  # POST success
        },
    ),
)
class AdminSupportTicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Admins/Sub-Admins to manage all support tickets.
    Allows listing, viewing, updating (status, assignment, priority),
    adding replies/internal notes, and deleting tickets.
    """

    queryset = (
        SupportTicket.objects.all()
        .select_related("user", "assigned_to")
        .prefetch_related("replies__user")
    )
    serializer_class = SupportTicketListSerializer  # Default for list
    # Make sure IsAdminOrSubAdminWithPermission is correctly implemented and imported
    permission_classes = [
        permissions.IsAdminUser
    ]  # Replace/extend with IsAdminOrSubAdminWithPermission('manage_support')
    filterset_fields = ["status", "issue_type", "priority", "assigned_to", "user"]
    search_fields = [
        "subject",
        "description",
        "user__username",
        "user__email",
        "assigned_to__username",
    ]
    ordering_fields = ["created_at", "updated_at", "priority", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SupportTicketDetailSerializer
        # Use AdminUpdateSerializer only for update/partial_update
        if self.action in ["update", "partial_update"]:
            return SupportTicketAdminUpdateSerializer
        if self.action == "replies":
            if self.request.method == "POST":
                return SupportTicketReplyCreateSerializer
            return SupportTicketReplySerializer  # For GET response schema hint
        # For 'create', we might need a specific AdminCreateSerializer or use Detail
        # For 'list', the default serializer_class is used
        return super().get_serializer_class()

    def perform_update(self, serializer):
        """Handle side effects of updating, e.g., setting closed_at."""
        instance = serializer.instance
        # Check if 'status' is actually being updated before accessing it
        new_status = serializer.validated_data.get("status", instance.status)

        closed_at_update = None
        if (
            new_status == SupportTicket.Status.CLOSED
            and instance.status != SupportTicket.Status.CLOSED
        ):
            closed_at_update = timezone.now()
        elif (
            new_status != SupportTicket.Status.CLOSED
            and instance.status == SupportTicket.Status.CLOSED
        ):
            closed_at_update = None

        # Save with potentially updated closed_at timestamp
        if closed_at_update is not None:
            serializer.save(closed_at=closed_at_update)
        else:
            # If only priority/assignment is changed, closed_at remains unchanged
            serializer.save()

        # TODO: Send notification to user about status change/assignment

    # Note: @extend_schema is now applied via @extend_schema_view above
    @action(
        detail=True,
        methods=["post", "get"],
        permission_classes=[permissions.IsAdminUser],
    )  # Extend with sub-admin permission
    def replies(self, request, pk=None):
        """
        GET: List all replies (including internal notes) for a ticket.
        POST: Add an admin reply or internal note to a ticket.
        """
        ticket = self.get_object()

        if request.method == "POST":
            serializer = SupportTicketReplyCreateSerializer(
                data=request.data,
                context={"request": request, "ticket": ticket},  # Pass request context
            )
            serializer.is_valid(raise_exception=True)
            # User is automatically set via HiddenField/CurrentUserDefault
            reply = serializer.save(ticket=ticket)

            # Update ticket status based on admin action
            is_internal = serializer.validated_data.get("is_internal_note", False)
            if not is_internal:
                # If it's a public reply, set status to pending user unless already closed
                if ticket.status != SupportTicket.Status.CLOSED:
                    ticket.status = (
                        SupportTicket.Status.PENDING_USER
                    )  # Or PENDING_ADMIN based on workflow
                    ticket.save(update_fields=["status", "updated_at"])
                # TODO: Send notification to user

            # Return the created reply using the display serializer
            return Response(
                SupportTicketReplySerializer(reply).data, status=status.HTTP_201_CREATED
            )

        elif request.method == "GET":
            # Admin sees all replies, including internal notes
            replies = ticket.replies.select_related("user").order_by("created_at")

            # Optional Pagination for replies
            # page = self.paginate_queryset(replies)
            # if page is not None:
            #     serializer = SupportTicketReplySerializer(page, many=True)
            #     return self.get_paginated_response(serializer.data)

            serializer = SupportTicketReplySerializer(replies, many=True)
            return Response(serializer.data)
