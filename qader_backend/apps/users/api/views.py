from datetime import timedelta
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.db import (
    transaction,
    DatabaseError,
    IntegrityError,
)
from django.db.utils import IntegrityError  # Import for specific exception handling
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)  # For model validation errors
from apps.users.utils import (
    get_user_from_uidb64,
    send_confirmation_email,
    generate_otp,
    send_password_reset_otp_email,
)
from rest_framework import generics, status, views, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request  # For type hinting
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
)  # Distinguish from Django's
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
    OpenApiParameter,
)
from drf_spectacular.types import OpenApiTypes

from typing import Optional

from apps.users.api.permissions import (
    IsCurrentlySubscribed,
)
from apps.notifications.models import NotificationTypeChoices
from apps.notifications.services import create_notification

from .serializers import (
    ApplySerialCodeSerializer,
    AuthUserResponseSerializer,
    CompleteProfileSerializer,
    EmailLoginSerializer,
    InitialSignupSerializer,
    SubscriptionDetailSerializer,
    SubscriptionPlanSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifyOTPSerializer,  # New import
    PasswordResetConfirmOTPSerializer,
    PasswordResetConfirmSerializer,
    UserRedeemedSerialCodeSerializer,
    # Removed unused imports: SimpleUserSerializer, SubscriptionDetailSerializer
)
from ..constants import (
    SUBSCRIPTION_PLANS_CONFIG,
    SubscriptionTypeChoices,
    GradeChoices,
)
from ..models import (
    UserProfile,
    SerialCode,
    PasswordResetOTP,
)  # Added SerialCode import

import logging

logger = logging.getLogger(__name__)

# ---> Define reusable error responses (Optional but DRY) <---
COMMON_ERRORS = {
    status.HTTP_400_BAD_REQUEST: OpenApiResponse(
        description="Bad Request: Invalid input data or parameters. Check response body for details.",
        response=inline_serializer(  # Generic error structure
            name="ValidationErrorResponse",
            fields={
                "detail": serializers.CharField(required=False),
                "field_name": serializers.ListField(
                    child=serializers.CharField(), required=False
                ),
            },
        ),
        examples=[
            OpenApiExample(
                "Field Error", value={"field_name": ["This field is required."]}
            ),
            OpenApiExample("Non-Field Error", value={"detail": "Invalid token."}),
        ],
    ),
    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
        description="Unauthorized: Authentication credentials were not provided or are invalid.",
        examples=[
            OpenApiExample(
                "Auth Required",
                value={"detail": "Authentication credentials were not provided."},
            )
        ],
        # No response body needed typically, or a simple detail like DRF default
    ),
    status.HTTP_403_FORBIDDEN: OpenApiResponse(
        description="Forbidden: You do not have permission to perform this action.",
        examples=[
            OpenApiExample(
                "Permission Denied",
                value={"detail": "You do not have permission to perform this action."},
            )
        ],
        # No response body needed typically, or a simple detail like DRF default
    ),
    status.HTTP_404_NOT_FOUND: OpenApiResponse(
        description="Not Found: The requested resource could not be found.",
        examples=[OpenApiExample("Not Found", value={"detail": "Not found."})],
        # No response body needed typically, or a simple detail like DRF default
    ),
}

# --- Authentication Views ---


@extend_schema(
    tags=["Authentication"],
    summary="Obtain JWT Tokens",
    description="Authenticate with email and password to receive JWT access and refresh tokens, along with basic user profile information. Also establishes a session for WebSocket authentication.",
    request=EmailLoginSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(
                name="LoginSuccessResponse",
                fields={
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "user": AuthUserResponseSerializer(),  # <-- Reference the actual serializer
                },
            ),  # Generic Serializer as structure is defined in example
            description="Authentication successful.",
        ),
        status.HTTP_401_UNAUTHORIZED: COMMON_ERRORS[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(  # Specific 400 for login
            description="Authentication failed (e.g., wrong password, user inactive/not found).",
            examples=[
                OpenApiExample(
                    "Auth Failed",
                    value={
                        "detail": "No active account found with the given credentials."
                    },
                )
            ],
        ),
    },
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Customize JWT response to include user profile info.
    Accepts email and password for login.
    """

    serializer_class = EmailLoginSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError as e:
            # DRF handles 400/401 based on validation errors
            logger.warning(
                f"Login validation failed for identifier '{request.data.get('username')}': {e.detail}"
            )
            raise e
        except Exception as e:
            # Catch unexpected errors during validation
            logger.exception(
                f"Unexpected error during login validation for '{request.data.get('username')}': {e}"
            )
            raise e  # Let DRF handle the 500 or appropriate response

        # Standard response data (access, refresh tokens)
        data = serializer.validated_data

        # Add custom user data
        user: User = serializer.user

        if user is not None and user.is_active:
            try:
                # Log the user into the session backend
                login(request, user)
                logger.info(
                    f"User '{user.username}' (ID: {user.id}) logged into session for WebSocket auth."
                )
            except Exception as e:
                # Handle potential errors during login (though unlikely for valid user)
                logger.exception(
                    f"Error logging user '{user.username}' into session during JWT login: {e}"
                )
                # Decide how to proceed: maybe still issue JWTs but log error?
                # For now, we'll continue but the log indicates a potential issue.
        else:
            # This case should be prevented by the serializer validation raising an exception above
            logger.error(
                f"Login attempt succeeded validation but user '{user.username if user else 'None'}' is None or inactive."
            )
            return Response(
                {"detail": "Login failed: User account issue."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Ensure the profile is fetched with necessary related objects if AuthUserResponseSerializer needs them
            # The unread_notifications_count is a property, so it doesn't need explicit prefetching here
            profile = UserProfile.objects.select_related(
                "user",
                "serial_code_used",
                "assigned_mentor__user",  # Add assigned_mentor related fields if needed
            ).get(user=user)

            # Check and reset the user's streak if it's broken upon login.
            profile.check_and_reset_streak()

            context = {
                "request": request
            }  # Ensure request context is passed for URL building
            user_data_serializer = AuthUserResponseSerializer(profile, context=context)
            data["user"] = user_data_serializer.data
            logger.info(
                f"User '{user.username}' (ID: {user.id}) logged in successfully."
            )

        except UserProfile.DoesNotExist:
            logger.error(
                f"CRITICAL: UserProfile not found during login for user '{user.username}' (ID: {user.id}). Data inconsistency."
            )
            data["user"] = {  # Minimal user data on profile error
                "id": user.id,
                "username": user.username,
                "email": user.email,  # Add email for consistency
                "error": "Profile data missing.",
                "unread_notifications_count": 0,  # Default on error
            }
        except Exception as e:
            logger.exception(
                f"Error adding user data to login response for user '{user.username}': {e}"
            )
            data["user"] = {  # Minimal user data on other errors
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "error": "Error fetching profile data.",
                "unread_notifications_count": 0,
            }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    summary="Logout User (Invalidate Token)",
    description="Blacklists the provided refresh token on the server-side. The client should also discard both access and refresh tokens.",
    request=inline_serializer(  # Define request schema inline
        name="LogoutRequest",
        fields={
            "refresh": serializers.CharField(
                required=True, help_text="The refresh token to invalidate."
            )
        },
    ),
    responses={
        status.HTTP_204_NO_CONTENT: OpenApiResponse(
            description="Logout successful (Token blacklisted)."
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Refresh token missing or invalid format."
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication required to perform logout."
        ),
    },
)
class LogoutView(views.APIView):
    """Blacklists the provided refresh token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        user_identifier = f"'{request.user.username}' (ID: {request.user.id})"
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": _("Refresh token is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            logout(request)
            logger.info(f"User {user_identifier} session cleared.")
        except Exception as e:
            # Log error but potentially continue to blacklist token if provided
            logger.exception(
                f"Error clearing session for user {user_identifier} during logout: {e}"
            )

        # --- Blacklist JWT Refresh Token ---
        if not refresh_token:
            # Still return success (204) even if token wasn't provided, as session logout succeeded
            logger.warning(
                f"Logout called for {user_identifier} without providing refresh token for blacklisting."
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(
                f"User '{request.user.username}' (ID: {request.user.id}) logged out successfully (token blacklisted)."
            )
            # 204 No Content is standard for successful logout/delete actions
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Handle various token errors (already blacklisted, invalid, expired)
            logger.warning(
                f"Logout failed for user '{request.user.username}' (ID: {request.user.id}): {e}"
            )
            # Return a generic 400 for security, don't reveal specific token status
            return Response(
                {"detail": _("Invalid refresh token or error during logout.")},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Initial User Signup (Stage 1)",
    description="Registers a new user with email, full name, and password. Creates an *inactive* user account and sends a confirmation email. The user must click the link in the email to activate their account and log in.",  # Clarify inactive state
    request=InitialSignupSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            description="Registration initiated successfully. Confirmation email sent.",
            response=inline_serializer(
                name="SignupSuccess", fields={"detail": serializers.CharField()}
            ),
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "detail": "Confirmation email sent. Please check your inbox."
                    },
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Validation errors (e.g., duplicate email, password mismatch, password policy violation). See response body for details.",
            response=InitialSignupSerializer,  # Errors often mirror the request structure
            examples=[
                OpenApiExample(
                    "Duplicate Email",
                    value={"email": ["A user with this email already exists."]},
                ),
                OpenApiExample(
                    "Password Mismatch",
                    value={"password_confirm": ["Password fields didn't match."]},
                ),
            ],
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            description="Internal Server Error: Failed to send confirmation email or other unexpected issue.",
            response=inline_serializer(
                name="SignupError", fields={"detail": serializers.CharField()}
            ),
            examples=[
                OpenApiExample(
                    "Email Send Fail",
                    value={
                        "detail": "Account created but failed to send confirmation email. Please contact support."
                    },
                )
            ],
        ),
    },
)
class InitialSignupView(generics.CreateAPIView):
    """Handles Stage 1 of user registration."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = InitialSignupSerializer

    def perform_create(self, serializer):
        """Creates inactive user and triggers confirmation email."""
        try:
            user = serializer.save()  # Creates inactive user, sets profile.full_name

            # Send confirmation email
            email_sent = send_confirmation_email(user, request=self.request)
            if not email_sent:
                # Although user is created, the process failed from user perspective
                logger.error(
                    f"Failed to send confirmation email to {user.email} during signup."
                )
                # Option 1: Delete the created user (rollback?) - complicates transaction
                # Option 2: Leave user inactive, return error. Needs manual resend?
                # Let's return an error indicating email failure.
                # Raising validation error here feels wrong as user *was* saved.
                # We'll let the response handling below indicate failure.
                raise Exception(
                    "Failed to send confirmation email."
                )  # Will be caught below

            logger.info(
                f"Initial signup successful for {user.email}. Confirmation email triggered."
            )
            # Don't return user data here, just confirmation message.
        except Exception as e:
            # Catch errors from serializer.save() or email sending
            logger.exception(
                f"Error during perform_create in InitialSignupView for {serializer.validated_data.get('email')}: {e}"
            )
            # Re-raise to be handled by DRF exception handler or custom handling in create()
            raise e

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)  # Calls save() and sends email
            return Response(
                {"detail": _("Confirmation email sent. Please check your inbox.")},
                status=status.HTTP_201_CREATED,
            )
        except DRFValidationError as e:
            logger.warning(f"Initial signup validation failed: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Catch error from perform_create (e.g., email send failure)
            logger.exception(
                f"Initial signup failed after validation for {request.data.get('email')}: {e}"
            )
            # Determine appropriate response based on error
            if "Failed to send confirmation email" in str(e):
                return Response(
                    {
                        "detail": _(
                            "Account created but failed to send confirmation email. Please contact support."
                        )
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Or 400 if considered client issue?
                )
            return Response(
                {"detail": _("An unexpected error occurred during registration.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Confirm Email Address (Stage 2)",
    description="Confirms the user's email address using the link sent. Activates the account, generates JWT tokens, establishes a session for WebSocket auth, and indicates if profile completion is needed.",
    parameters=[
        OpenApiParameter(
            "uidb64",
            OpenApiTypes.STR,
            OpenApiParameter.PATH,
            required=True,
            description="User ID encoded in base64.",
        ),
        OpenApiParameter(
            "token",
            OpenApiTypes.STR,
            OpenApiParameter.PATH,
            required=True,
            description="Confirmation token.",
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(  # Same structure as login
                name="ConfirmEmailSuccessResponse",
                fields={
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "user": AuthUserResponseSerializer(),
                },
            ),
            description="Email confirmed successfully. Returns JWT tokens and user profile status.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Invalid or expired confirmation link/token."
        ),
        status.HTTP_404_NOT_FOUND: OpenApiResponse(
            description="Not Found: User associated with the link not found."
        ),
    },
)
class ConfirmEmailView(views.APIView):
    """Handles email confirmation link click."""

    permission_classes = [AllowAny]

    @transaction.atomic
    def get(
        self, request: Request, uidb64: str, token: str, *args, **kwargs
    ) -> Response:
        user = get_user_from_uidb64(uidb64)  # Util function fetches user by pk

        if user is None:
            logger.warning(
                f"Email confirmation failed: User not found for uidb64 {uidb64}"
            )
            return Response(
                {"detail": _("Invalid confirmation link.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_active:
            logger.warning(
                f"Email confirmation attempt for already active user: {user.email}"
            )
            # Optional: Re-issue tokens if they are already active? Or just say already confirmed?
            # Let's treat it as potentially needing login tokens again.
            # return Response({"detail": _("Email address already confirmed.")}, status=status.HTTP_400_BAD_REQUEST)

        # Check the token using the default generator
        if default_token_generator.check_token(user, token):
            account_already_active = user.is_active  # Check before activating
            if not account_already_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
                logger.info(
                    f"User {user.email} successfully activated via email confirmation."
                )

            # --- Log user into session after successful confirmation ---
            # This ensures a session is established if they click an old link after logging out
            try:
                login(request, user)
                logger.info(
                    f"User '{user.username}' (ID: {user.id}) logged into session {'after' if not account_already_active else 'again after'} email confirmation."
                )
            except Exception as e:
                logger.exception(
                    f"Error logging user '{user.username}' into session during email confirmation: {e}"
                )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Get profile and check completion status
            profile = user.profile  # Assumes profile exists via signal
            context = {"request": request}
            user_data_serializer = AuthUserResponseSerializer(profile, context=context)

            response_data = {
                "user": user_data_serializer.data,
                "access": access_token,
                "refresh": refresh_token,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            logger.warning(
                f"Email confirmation failed: Invalid token for user {user.email} (uidb64: {uidb64})"
            )
            return Response(
                {"detail": _("Invalid or expired confirmation link.")},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["User Profile"],
    summary="Complete User Profile (Post-Confirmation)",
    description=(
        "**Requires Authentication.** Allows a user whose profile is incomplete (`profile_complete=false`) to submit required details "
        "(`gender`, `grade`, `has_taken_qiyas_before`) and optional details (`preferred_name`, `profile_picture`, `serial_code`, `referral_code_used`).\n\n"
        "*   **Subscription:** Activates subscription via `serial_code` if provided and valid. If no code is provided and user has no active subscription, a **1-day trial** is automatically granted.\n"
        "*   **Referral:** Applies referral bonus (e.g., extra subscription days for the referrer) if `referral_code_used` is valid and belongs to another user.\n"
        "*   **Encoding:** Use `application/json` by default. Use `multipart/form-data` if including the `profile_picture` field."  # Explicit encoding mention
    ),
    request={  # Define potential request content types
        "multipart/form-data": CompleteProfileSerializer,
        "application/json": CompleteProfileSerializer,
    },
    responses={
        # ---> Use the specific response serializer <---
        status.HTTP_200_OK: OpenApiResponse(
            response=UserProfileSerializer,  # Returns the *full* profile on success
            description="Profile completed successfully. Subscription activated or trial granted if applicable. Referral processed if provided.",
        ),
        # ---> Use common errors <---
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(  # More specific examples for this endpoint
            description="Bad Request: Validation errors (e.g., missing required fields, invalid serial/referral code, invalid image format/size).",
            response=CompleteProfileSerializer,  # Errors often mirror request structure
            examples=[
                OpenApiExample(
                    "Missing Field",
                    value={
                        "gender": ["This field is required to complete your profile."]
                    },
                ),
                OpenApiExample(
                    "Invalid Serial",
                    value={"serial_code": ["Invalid or already used serial code."]},
                ),
                OpenApiExample(
                    "Invalid Referral",
                    value={"referral_code_used": ["Invalid referral code provided."]},
                ),
                OpenApiExample(
                    "Image Too Large",
                    value={"profile_picture": ["Image size cannot exceed 5MB."]},
                ),
            ],
        ),
        status.HTTP_401_UNAUTHORIZED: COMMON_ERRORS[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_403_FORBIDDEN: OpenApiResponse(  # Specific forbidden message
            description="Forbidden: Profile is already complete or other permission issue.",
            examples=[
                OpenApiExample(
                    "Profile Complete", value={"detail": "Profile is already complete."}
                )
            ],
        ),
        status.HTTP_404_NOT_FOUND: COMMON_ERRORS[
            status.HTTP_404_NOT_FOUND
        ],  # Profile not found for logged-in user
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            description="Internal Server Error: Issue during database update, subscription, or referral processing.",
            response=inline_serializer(
                name="CompleteProfileServerError",
                fields={"detail": serializers.CharField()},
            ),
            examples=[
                OpenApiExample(
                    "Server Error",
                    value={"detail": "An error occurred while completing the profile."},
                )
            ],
        ),
    },
)
class CompleteProfileView(generics.UpdateAPIView):
    """Handles PATCH request to complete the user profile."""

    serializer_class = CompleteProfileSerializer
    permission_classes = [IsAuthenticated]  # Must be logged in
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # Handle image upload

    def get_object(self) -> UserProfile:
        """Return the profile of the current user."""
        try:
            profile = self.request.user.profile
            # Optional: Add check if profile is already complete?
            if profile.is_profile_complete:
                raise PermissionDenied(_("Profile is already complete."))
            return profile
        except UserProfile.DoesNotExist:  # pylint: disable=no-member
            logger.error(
                f"CRITICAL: UserProfile.DoesNotExist for authenticated user '{self.request.user.username}'"
            )
            raise Http404(_("User profile not found."))

    @transaction.atomic  # Crucial for atomicity
    @transaction.atomic  # Already here, good
    def perform_update(self, serializer: CompleteProfileSerializer):
        profile: UserProfile = self.get_object()  # This is UserProfile instance
        user: User = profile.user  # Get the related User instance
        validated_data = serializer.validated_data

        # --- Update username if provided ---
        new_username = validated_data.get("username")
        if new_username and new_username != user.username:
            user.username = new_username
            try:
                # Save the User model separately for username change
                user.save(update_fields=["username"])
                logger.info(
                    f"Username updated to '{user.username}' for user ID {user.id} during profile completion."
                )
            except IntegrityError:
                # This should ideally be caught by serializer's validate_username,
                # but a race condition could still occur.
                logger.error(
                    f"IntegrityError (race condition?) while updating username to '{new_username}' for user ID {user.id}."
                )
                raise DRFValidationError(
                    {
                        "username": [
                            _("This username has just been taken. Please try another.")
                        ]
                    }
                )

        # Extract optional codes before saving profile data
        serial_code_obj: Optional[SerialCode] = validated_data.get(
            "serial_code"
        )  # Validated instance or None
        referring_user: Optional[User] = validated_data.get(
            "referral_code_used"
        )  # Validated instance or None

        # Handle profile picture deletion logic (similar to UserProfileView)
        new_picture_data = validated_data.get("profile_picture", "NOT_PRESENT")
        new_picture_provided = new_picture_data != "NOT_PRESENT"
        old_picture_instance = (
            profile.profile_picture if profile.profile_picture else None
        )

        # Save the profile data using the serializer instance
        # This updates gender, grade, etc.
        instance: UserProfile = (
            serializer.save()
        )  # serializer is already initialized with instance

        # --- Subscription Logic ---
        subscription_updated = False
        if serial_code_obj:
            # Re-fetch with lock inside transaction
            try:
                code_to_use = SerialCode.objects.select_for_update().get(
                    pk=serial_code_obj.pk, is_active=True, is_used=False
                )
                if code_to_use.mark_used(user):  # Mark used *before* applying
                    instance.apply_subscription(code_to_use)
                    subscription_updated = True
                    logger.info(
                        f"User {user.username} completed profile and applied serial code {code_to_use.code}"
                    )
                else:
                    # Should not happen if lock works, but handle defensively
                    logger.error(
                        f"Failed to mark serial code {code_to_use.code} used during profile completion for {user.username}"
                    )
                    raise DRFValidationError(
                        {
                            "serial_code": [
                                _("Failed to process serial code. Please try again.")
                            ]
                        }
                    )
            except SerialCode.DoesNotExist:
                logger.warning(
                    f"Serial code {serial_code_obj.code} became invalid during profile completion transaction for {user.username}"
                )
                raise DRFValidationError(
                    {
                        "serial_code": [
                            _("Serial code became invalid during processing.")
                        ]
                    }
                )

        # Grant trial ONLY if no serial code was successfully applied AND user isn't already subscribed
        if not subscription_updated and not instance.is_subscribed:
            if instance.grant_trial_subscription(
                duration_days=1
            ):  # Prepare expiry date changes
                instance.save(
                    update_fields=[
                        "subscription_expires_at",
                        "serial_code_used",
                        "updated_at",
                    ]
                )
                subscription_updated = True
                logger.info(
                    f"User {user.username} completed profile and received 1-day trial."
                )
            else:
                # grant_trial_subscription failed (should only happen on exception)
                logger.error(
                    f"Failed to grant trial subscription during profile completion for {user.username}"
                )
                # Raise an error? Or just log and continue? Let's raise.
                raise Exception("Failed to grant trial subscription.")

        # --- Referral Logic ---
        if referring_user:
            # Ensure the referred_by field is set correctly on the profile
            if instance.referred_by != referring_user:
                instance.referred_by = referring_user
                instance.save(update_fields=["referred_by", "updated_at"])
                logger.info(
                    f"User {user.username} completed profile using referral code from {referring_user.username}"
                )

                # Apply bonus to referrer (example: 3 days) - MAKE THIS CONFIGURABLE
                try:
                    referrer_profile = referring_user.profile
                    days_to_add = getattr(settings, "REFERRAL_BONUS_DAYS", 3)
                    if days_to_add > 0:
                        # Use apply_subscription logic or similar for referrer? Simpler: direct update.
                        current_expiry = (
                            referrer_profile.subscription_expires_at or timezone.now()
                        )
                        # Ensure expiry is in the future before adding days relative to it
                        start_date = max(current_expiry, timezone.now())
                        new_expiry = start_date + timedelta(days=days_to_add)

                        referrer_profile.subscription_expires_at = new_expiry
                        referrer_profile.save(
                            update_fields=["subscription_expires_at", "updated_at"]
                        )
                        logger.info(
                            f"Granted {days_to_add} referral bonus days to user {referring_user.username}"
                        )
                        # TODO: Add notification/point system integration here?
                except UserProfile.DoesNotExist:
                    logger.error(
                        f"Could not find profile for referring user {referring_user.username} to grant bonus."
                    )
                except Exception as e:
                    logger.exception(
                        f"Error granting referral bonus to {referring_user.username}: {e}"
                    )
                    # Don't fail the whole request for bonus failure, just log.

        # --- Delete old picture ---
        if old_picture_instance and new_picture_provided:
            if instance.profile_picture != old_picture_instance:
                try:
                    old_picture_instance.delete(save=False)
                    logger.info(f"Deleted old profile picture for user {user.username}")
                except Exception as e:
                    logger.warning(
                        f"Could not delete old profile picture for user {user.username}: {e}"
                    )
        create_notification(
            recipient=user,
            actor=user,
            verb=_("completed your profile"),
            description=_("Your profile is now complete! You can start exploring."),
            notification_type=NotificationTypeChoices.USER_PROFILE,
            url=f"/profile/me/",  # Example frontend URL
            extra_data={"profile_completion_step": "final"},  # Example extra data
        )
        logger.info(f"Profile completed successfully for user {user.username}")

    def update(self, request: Request, *args, **kwargs) -> Response:
        # ... (existing update method structure) ...
        # Ensure it calls perform_update and returns UserProfileSerializer data
        partial = kwargs.pop("partial", True)
        instance = self.get_object()  # UserProfile
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )  # CompleteProfileSerializer
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            instance.refresh_from_db()  # Refresh UserProfile instance
            # If user was updated (e.g. username), the user object related to profile also needs to be fresh.
            # refresh_from_db on profile should also update related objects if they are accessed fresh.
            # Or explicitly: instance.user.refresh_from_db() if needed, but usually not.

            context = self.get_serializer_context()
            response_serializer = UserProfileSerializer(instance, context=context)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except DRFValidationError as e:
            logger.warning(
                f"Profile completion validation failed for user '{request.user.username}': {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except (DatabaseError, IntegrityError, Exception) as e:
            logger.exception(
                f"Error during profile completion update for user '{request.user.username}': {e}"
            )
            return Response(
                {"detail": _("An error occurred while completing the profile.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Refresh JWT Access Token",
    description="Obtains a new JWT access token using a valid, non-blacklisted refresh token. And it's using the refresh token rotation, which you need to get refresh token also.",
    request=TokenRefreshSerializer,  # Standard request body: {"refresh": "..."}
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(
                name="TokenRefreshResponse", fields={"access": serializers.CharField()}
            ),
            description="Access token refreshed successfully.",
            examples=[
                OpenApiExample(
                    "Access and Refresh Success",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsIn...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
                    },
                )
            ],
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication Failed: Token is invalid or expired (check 'detail' and 'code' fields).",
            examples=[
                OpenApiExample(
                    "Invalid Token",
                    value={
                        "detail": "Token is invalid or expired",
                        "code": "token_not_valid",
                    },
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Refresh token not provided."
        ),
    },
)
class CustomTokenRefreshView(TokenRefreshView):
    """Standard token refresh view, subclassed for documentation purposes."""

    pass


# --- User Profile Views ---


@extend_schema(
    tags=["User Profile"],
    summary="Retrieve or Update Current User Profile",
    description=(
        "**Requires Authentication.**\n\n"
        "**GET:** Returns the full profile details of the currently authenticated user.\n\n"
        "**PATCH:** Partially updates the authenticated user's profile. Allows updating fields like name, grade, preferences, and profile picture. "
        "Use `application/json` for non-file updates, use `multipart/form-data` if including `profile_picture`."  # Explicit encoding
    ),
    # Request schema only needed for PATCH
    request={  # Separate for PATCH encoding
        "multipart/form-data": UserProfileUpdateSerializer,
        "application/json": UserProfileUpdateSerializer,
    },
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserProfileSerializer,  # GET and successful PATCH return full profile
            description="Profile retrieved (GET) or updated (PATCH) successfully.",
        ),
        # PATCH specific errors
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="(PATCH only) Bad Request: Validation errors on update (e.g., invalid image file, incorrect data format).",
            response=UserProfileUpdateSerializer,  # Errors map to update fields
            examples=[
                OpenApiExample(
                    "Invalid Time",
                    value={
                        "dark_mode_auto_time_start": [
                            "Auto dark mode start time must be before end time."
                        ]
                    },
                ),
                OpenApiExample(
                    "Image Too Large",
                    value={"profile_picture": ["Image size cannot exceed 5MB."]},
                ),
            ],
        ),
        # Common errors apply to both GET and PATCH
        status.HTTP_401_UNAUTHORIZED: COMMON_ERRORS[status.HTTP_401_UNAUTHORIZED],
        # 403 unlikely here with IsAuthenticated, but include for completeness
        status.HTTP_403_FORBIDDEN: COMMON_ERRORS[status.HTTP_403_FORBIDDEN],
        status.HTTP_404_NOT_FOUND: COMMON_ERRORS[
            status.HTTP_404_NOT_FOUND
        ],  # If profile somehow missing
    },
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve profile for the logged-in user (/me/).
    PATCH: Update profile for the logged-in user (/me/).
    Handles JSON and multipart/form-data.
    """

    permission_classes = [IsAuthenticated]
    # Allow both JSON and file uploads
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_serializer_class(self):
        """Return appropriate serializer based on HTTP method."""
        if self.request.method in ["PATCH", "PUT"]:
            return UserProfileUpdateSerializer  # Use for validating input on update
        return (
            UserProfileSerializer  # Use for GET response and successful update response
        )

    def get_object(self) -> UserProfile:
        """Return the profile of the current user, ensuring it exists."""
        user: User = self.request.user
        try:
            # Use select_related to optimize fetching related user/code if needed by response serializer
            profile = UserProfile.objects.select_related(
                "user", "serial_code_used"
            ).get(user=user)

            # ---> The key change is here <---
            # Before returning the profile for serialization (on GET) or update (on PATCH),
            # check if the streak needs to be reset. This ensures data is consistent.
            if self.request.method == "GET":
                profile.check_and_reset_streak()

            return profile
        except UserProfile.DoesNotExist:
            # This indicates a potential data integrity issue if user is authenticated
            logger.error(
                f"CRITICAL: UserProfile.DoesNotExist for authenticated user '{user.username}' (ID: {user.id})"
            )
            raise Http404(_("User profile not found."))

    # Apply transaction.atomic to the update method for atomicity
    @transaction.atomic
    def perform_update(self, serializer: UserProfileUpdateSerializer):
        profile: UserProfile = self.get_object()  # UserProfile instance
        user: User = profile.user  # User instance
        validated_data = serializer.validated_data

        # --- Update username if provided ---
        new_username = validated_data.get("username")
        if new_username and new_username != user.username:
            user.username = new_username
            try:
                user.save(update_fields=["username"])
                logger.info(
                    f"Username updated to '{user.username}' for user ID {user.id}."
                )
            except IntegrityError:
                logger.error(
                    f"IntegrityError (race condition?) while updating username to '{new_username}' for user ID {user.id}."
                )
                raise DRFValidationError(
                    {
                        "username": [
                            _("This username has just been taken. Please try another.")
                        ]
                    }
                )

        # Check if 'profile_picture' is part of the validated data to be saved
        new_picture_data = serializer.validated_data.get(
            "profile_picture", "NOT_PRESENT"
        )
        # `None` means user explicitly set picture to null, `NOT_PRESENT` means field wasn't sent
        new_picture_provided = new_picture_data != "NOT_PRESENT"
        old_picture_instance = (
            profile.profile_picture if profile.profile_picture else None
        )

        # Save UserProfile fields using the serializer
        instance: UserProfile = (
            serializer.save()
        )  # `instance` is the updated UserProfile

        # Delete old picture *after* successfully saving the new one or nulling the field
        if old_picture_instance and new_picture_provided:
            # Check if the new picture is different or explicitly set to None
            if instance.profile_picture != old_picture_instance:
                try:
                    # Delete the old file from storage; model instance is already saved
                    old_picture_instance.delete(save=False)
                    logger.info(
                        f"Deleted old profile picture '{old_picture_instance.name}' for user '{profile.user.username}' (ID: {profile.user_id})"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not delete old profile picture '{old_picture_instance.name}' for user '{profile.user.username}': {e}"
                    )

        logger.info(f"User profile updated for user '{user.username}' (ID: {user.id})")

    # The update method itself can be kept as is, as perform_update is now transactional
    # and handles both User and UserProfile updates.
    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", True)  # PATCH implies partial=True
        instance = self.get_object()  # UserProfile
        update_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )  # UserProfileUpdateSerializer

        try:
            update_serializer.is_valid(raise_exception=True)
        except DRFValidationError as e:
            logger.warning(
                f"Profile update validation failed for user '{request.user.username}': {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # perform_update is now transactional
        self.perform_update(
            update_serializer
        )  # This saves UserProfile and potentially User (username)

        # Ensure any prefetched data is cleared if necessary
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        # instance might have been updated, refresh_from_db if necessary, though serializer.save() returns the updated one.
        # For the response, we use the full UserProfileSerializer with the latest instance data.
        # The instance from get_object() is what serializer.save() updates.

        context = self.get_serializer_context()
        # After perform_update, 'instance' (the UserProfile) is up-to-date.
        # Its related 'user' object (if username changed) is also up-to-date in the DB.
        # When UserProfileSerializer accesses instance.user.username, it gets the fresh value.
        read_serializer = UserProfileSerializer(instance, context=context)
        return Response(read_serializer.data)


# --- Password Management Views ---


@extend_schema(
    tags=["User Profile"],  # Keep under User Profile as it's self-service
    summary="Change Current User Password",
    description="Allows the authenticated user to change their own password by providing the current password and a new password.",
    request=PasswordChangeSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Password updated successfully.",
            examples=[
                OpenApiExample(
                    "Success", value={"detail": "Password updated successfully."}
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Validation errors (e.g., incorrect current password, new passwords mismatch, policy violation)."
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication required."
        ),
    },
)
class PasswordChangeView(generics.GenericAPIView):
    """Handles password change for the currently authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(
                raise_exception=True
            )  # Handles current_password check and new password match
            user: User = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save(update_fields=["password"])  # Only update password field
            logger.info(
                f"Password changed successfully for user '{user.username}' (ID: {user.id})"
            )
            # TODO: Consider security implications - log out other sessions? Send notification?
            return Response(
                {"detail": _("Password updated successfully.")},
                status=status.HTTP_200_OK,
            )
        except DRFValidationError as e:
            logger.warning(
                f"Password change failed for user '{request.user.username}' (ID: {request.user.id}): {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    summary="Request Password Reset OTP",
    description=(
        "Initiates the password reset process. If the provided identifier (email or username) "
        "corresponds to an active account, an OTP (One-Time Password) will be sent to the user's registered email. "
        "This endpoint always returns a generic success response to prevent user account enumeration."
    ),
    request=PasswordResetRequestSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Request processed. If your account exists and is active, an OTP has been sent to your email address.",
            response=inline_serializer(
                name="PasswordResetOTPSent", fields={"detail": serializers.CharField()}
            ),
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "detail": "If your account exists and is active, an OTP has been sent to your email address."
                    },
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: COMMON_ERRORS[
            status.HTTP_400_BAD_REQUEST
        ],  # For invalid input format
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            description="Internal Server Error: Issue during OTP generation or email sending.",
            response=inline_serializer(
                name="PasswordResetOTPError", fields={"detail": serializers.CharField()}
            ),
        ),
    },
)
class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @transaction.atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            if not serializer.is_valid():
                logger.warning(
                    f"Password reset OTP request failed basic validation: {serializer.errors}"
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            user: Optional[User] = serializer.validated_data.get("identifier")
            identifier_from_request = request.data.get("identifier", "N/A")

            if user:
                # Invalidate (mark as used and expired) any previous, non-fully-used OTPs
                # AND non-fully-used reset tokens for this user.
                # This ensures only one active OTP/reset path per user.
                PasswordResetOTP.objects.filter(user=user, is_used=False).update(
                    is_used=True,  # Mark as if this path was abandoned
                    otp_expires_at=timezone.now() - timedelta(seconds=1),
                    reset_token_expires_at=timezone.now() - timedelta(seconds=1),
                )

                otp_plain_text = generate_otp()
                new_otp_record = PasswordResetOTP(user=user)
                new_otp_record.set_otp(otp_plain_text)  # Sets hash and otp_expires_at
                # reset_token fields are not set here yet.
                new_otp_record.save()

                email_sent = send_password_reset_otp_email(user, otp_plain_text)
                if not email_sent:
                    logger.error(
                        f"Failed to send password reset OTP email to user '{user.username}' (identifier: {identifier_from_request}) after OTP generation."
                    )
                    raise Exception(
                        "Failed to send OTP email."
                    )  # Will rollback transaction
                logger.info(
                    f"Password reset OTP generated and email sent for user '{user.username}' (identifier: {identifier_from_request})."
                )
            else:
                logger.info(
                    f"Password reset OTP request for non-existent or inactive identifier: {identifier_from_request}. No email sent (anti-enumeration)."
                )

            return Response(
                {
                    "detail": _(
                        "If your account exists and is active, an OTP has been sent to your email address."
                    )
                },
                status=status.HTTP_200_OK,
            )
        except DRFValidationError as e:
            logger.warning(f"Password reset OTP request validation failed: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            identifier_from_request = request.data.get("identifier", "N/A")
            logger.exception(
                f"Unexpected error during password reset OTP request for identifier '{identifier_from_request}': {e}"
            )
            if "Failed to send OTP email" in str(e):
                return Response(
                    {
                        "detail": _(
                            "We encountered an issue sending the OTP. Please try again later or contact support."
                        )
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {
                    "detail": _(
                        "An unexpected error occurred. Please try again later or contact support."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Verify Password Reset OTP",
    description="Verifies the OTP sent to the user's email. If successful, returns a short-lived reset token to be used for confirming the password change.",
    request=PasswordResetVerifyOTPSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="OTP verified successfully. Use the provided reset_token to set a new password.",
            response=inline_serializer(
                name="OTPVerifiedResponse",
                fields={
                    "reset_token": serializers.CharField(),
                    "detail": serializers.CharField(),
                },
            ),
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "reset_token": "some_secure_token_string",
                        "detail": "OTP verified successfully.",
                    },
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: COMMON_ERRORS[
            status.HTTP_400_BAD_REQUEST
        ],  # For invalid OTP, identifier, etc.
    },
)
class PasswordResetVerifyOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetVerifyOTPSerializer

    @transaction.atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            # user = serializer.validated_data['user'] # Not directly needed here if otp_record has user
            otp_record: PasswordResetOTP = serializer.validated_data["otp_record"]

            # Generate and store the reset token within the OTP record
            plain_reset_token = (
                otp_record.generate_reset_token()
            )  # This saves the otp_record

            logger.info(
                f"OTP verified for user '{otp_record.user.username}'. Reset token generated."
            )
            return Response(
                {
                    "reset_token": plain_reset_token,
                    "detail": _(
                        "OTP verified successfully. Please use the provided token to reset your password."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except DRFValidationError as e:
            logger.warning(f"Password reset OTP verification failed: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during OTP verification for '{request.data.get('identifier', 'N/A')}': {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred during OTP verification.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Confirm Password Reset with OTP",
    description="Sets a new password using the identifier (email/username), the OTP received via email, and the new password. Validates the OTP and updates the user's password upon success.",
    request=PasswordResetConfirmOTPSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Password has been reset successfully.",
            response=inline_serializer(
                name="PasswordResetSuccess", fields={"detail": serializers.CharField()}
            ),
            examples=[
                OpenApiExample(
                    "Success", value={"detail": "Password has been reset successfully."}
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: COMMON_ERRORS[
            status.HTTP_400_BAD_REQUEST
        ],  # Covers invalid OTP, password issues, etc.
        # No explicit 404 as identifier validation is part of the 400 bad request if user not found.
    },
)
class PasswordResetConfirmOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmOTPSerializer

    @transaction.atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            user: User = serializer.validated_data[
                "user"
            ]  # User derived from valid reset_token
            new_password = serializer.validated_data["new_password"]
            otp_record: PasswordResetOTP = serializer.validated_data[
                "otp_record"
            ]  # The record tied to the reset_token

            # Double-check password policies for the specific user if needed
            # validate_password(new_password, user=user) # Already done by serializer

            user.set_password(new_password)
            user.save(update_fields=["password"])

            otp_record.mark_used()  # Mark the entire record as used

            logger.info(
                f"Password reset confirmed and updated successfully for user '{user.username}' using reset_token."
            )
            return Response(
                {"detail": _("Password has been reset successfully.")},
                status=status.HTTP_200_OK,
            )
        except DjangoValidationError as e:
            logger.warning(
                f"Password reset (token) confirmation failed for reset_token '{request.data.get('reset_token', 'N/A')}': New password validation failed: {e.messages}"
            )
            return Response(
                {"new_password": e.messages}, status=status.HTTP_400_BAD_REQUEST
            )
        except DRFValidationError as e:
            logger.warning(
                f"Password reset (token) confirmation failed due to validation for reset_token '{request.data.get('reset_token', 'N/A')}': {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during password reset (token) confirmation for reset_token '{request.data.get('reset_token', 'N/A')}': {e}"
            )
            return Response(
                {
                    "detail": _(
                        "An unexpected error occurred while resetting your password. Please try again."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Confirm Password Reset from Admin when send to reset the user password",
    description="Sets a new password using the uidb64 and token from the password reset email link. Validates the token and updates the user's password.",
    request=PasswordResetConfirmSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Password has been reset successfully.",
            examples=[
                OpenApiExample(
                    "Success", value={"detail": "Password has been reset successfully."}
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Invalid token, expired link, user not found, password mismatch, or password policy violation."
        ),
    },
)
class PasswordResetConfirmView(generics.GenericAPIView):
    """Handles the confirmation step of resetting a user's password."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            uidb64 = serializer.validated_data["uidb64"]
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            user = self.get_user_from_uidb64(uidb64)

            if user is not None and default_token_generator.check_token(user, token):
                # Token is valid, set the new password
                try:
                    validate_password(
                        new_password, user
                    )  # Validate against password policies
                    user.set_password(new_password)
                    user.save(update_fields=["password"])
                    logger.info(
                        f"Password reset confirmed and updated successfully for user '{user.username}' (ID: {user.id})"
                    )
                    # TODO: Security enhancement: Log out all other sessions for this user.
                    return Response(
                        {"detail": _("Password has been reset successfully.")},
                        status=status.HTTP_200_OK,
                    )
                except DjangoValidationError as e:
                    logger.warning(
                        f"Password reset confirmation failed for user '{user.username}': New password validation failed: {e.messages}"
                    )
                    return Response(
                        {"new_password": e.messages}, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Invalid token or user ID
                logger.warning(
                    f"Invalid password reset token or UID attempt. UIDB64: {uidb64}"
                )
                return Response(
                    {"detail": _("Invalid or expired password reset link.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except DRFValidationError as e:
            # Handle validation errors from the serializer (e.g., password mismatch)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during password reset confirmation: {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_user_from_uidb64(self, uidb64: str) -> Optional[User]:
        """Helper to safely decode uidb64 and retrieve the User object."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, is_active=True)  # Ensure user is active
            return user
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            DjangoValidationError,
        ) as e:
            # Catch various potential errors during decoding or user lookup
            logger.debug(f"Failed to get active user from UIDB64 '{uidb64}': {e}")
            return None


@extend_schema(
    tags=["User Profile"],
    summary="Apply New Serial Code",
    description="Applies a new, valid serial code to activate or extend the authenticated user's subscription.",
    request=ApplySerialCodeSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=SubscriptionDetailSerializer,  # Shows updated subscription
            description="Serial code applied successfully. Returns updated subscription details.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Serial code is missing, invalid, inactive, or already used."
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication required."
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            description="Internal server error during code application."
        ),
    },
)
class ApplySerialCodeView(generics.GenericAPIView):
    """Allows authenticated users to apply a new serial code."""

    permission_classes = [IsAuthenticated]
    serializer_class = ApplySerialCodeSerializer  # For request validation

    @transaction.atomic  # Ensure code marking and profile update are atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # Serializer validation returns the valid SerialCode object
            serial_code: SerialCode = serializer.validated_data["serial_code"]
            user: User = request.user
            profile: UserProfile = user.profile

            # Re-fetch code inside transaction with lock to prevent race conditions
            try:
                code_to_use = SerialCode.objects.select_for_update().get(
                    pk=serial_code.pk, is_active=True, is_used=False
                )
            except SerialCode.DoesNotExist:
                # Code became invalid between initial validation and lock acquisition
                logger.warning(
                    f"Serial code {serial_code.code} became invalid during transaction for user {user.username}"
                )
                raise DRFValidationError(
                    {
                        "serial_code": [
                            _(
                                "Serial code became invalid or used before application could complete."
                            )
                        ]
                    }
                )

            # Mark used and apply subscription
            if code_to_use.mark_used(user):
                profile.apply_subscription(code_to_use)
                profile.refresh_from_db()  # Get the updated profile state

                # Serialize the updated subscription details for the response
                response_serializer = SubscriptionDetailSerializer(
                    profile
                )  # Source is '*' by default
                logger.info(
                    f"User '{user.username}' successfully applied serial code '{code_to_use.code}'. New expiry: {profile.subscription_expires_at}"
                )
                # Return the nested structure as requested
                return Response(
                    {"subscription": response_serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                # This should ideally not happen if re-fetched correctly, but handle defensively
                logger.error(
                    f"Failed to mark serial code {code_to_use.code} used for user {user.username} within transaction despite lock."
                )
                raise DRFValidationError(
                    {
                        "serial_code": [
                            _("Failed to process serial code. Please try again.")
                        ]
                    }
                )

        except DRFValidationError as e:
            # Catch validation errors from serializer or raised manually
            logger.warning(
                f"Applying serial code failed for user '{request.user.username}': {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except (DatabaseError, Exception) as e:
            # Catch potential DB errors during transaction or other unexpected issues
            logger.exception(
                f"Database or unexpected error applying serial code for user '{request.user.username}': {e}"
            )
            return Response(
                {"detail": _("An error occurred while applying the serial code.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["User Profile"],  # Keep under User Profile for now
    summary="List Redeemed Serial Codes",
    description="Retrieves a list of serial codes that the currently authenticated user has redeemed.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserRedeemedSerialCodeSerializer(many=True),
            description="List of redeemed serial codes retrieved successfully.",
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication credentials were not provided."
        ),
    },
)
class UserRedeemedCodesListView(generics.ListAPIView):
    """
    Provides a list of Serial Codes redeemed by the currently authenticated user.
    """

    serializer_class = UserRedeemedSerialCodeSerializer
    permission_classes = [IsAuthenticated]
    # Apply pagination from settings by default

    def get_queryset(self):
        """
        This view should return a list of all the serial codes
        for the currently authenticated user.
        """
        user = self.request.user
        # Filter codes where used_by is the current user and order by most recent
        return SerialCode.objects.filter(used_by=user).order_by("-used_at")


@extend_schema(
    tags=["User Profile"],
    summary="List Available Educational Grades",
    description="Provides a list of all available educational grades for user profiles.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(
                name="GradeListResponse",
                fields={
                    "key": serializers.CharField(),
                    "label": serializers.CharField(),
                },
                many=True,
            ),
            description="List of available grades.",
        ),
    },
)
class GradeListView(views.APIView):
    """Lists available educational grades."""

    permission_classes = [AllowAny]

    def get(self, request: Request, *args, **kwargs) -> Response:
        grades = [
            {"key": choice[0], "label": choice[1]} for choice in GradeChoices.choices
        ]
        return Response(grades, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Subscription Plans"],  # Apply the new tag
    summary="List Available Subscription Plans",
    description="Provides a list of available standard subscription plans (1, 3, 12 months) based on system configuration.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=SubscriptionPlanSerializer(),
            description="List of available subscription plans.",
            examples=[
                OpenApiExample(
                    "Plans List",
                    value=[
                        # Example based on new config
                        {
                            "id": "1_month",
                            "name": "1 Month Access",
                            "description": "Full access to all platform features for 30 days.",
                            "duration_days": 30,
                            "requires_code_type": "1_month",
                        },
                        {
                            "id": "3_months",
                            "name": "3 Months Access",
                            "description": "Full access to all platform features for 91 days (approx. 3 months).",
                            "duration_days": 91,
                            "requires_code_type": "3_months",
                        },
                        {
                            "id": "12_months",
                            "name": "12 Months Access",
                            "description": "Full access to all platform features for 365 days (1 year).",
                            "duration_days": 365,
                            "requires_code_type": "12_months",
                        },
                    ],
                )
            ],
        ),
    },
)
class SubscriptionPlanListView(views.APIView):
    """Lists available subscription plans (currently hardcoded)."""

    permission_classes = [AllowAny]  # Allow anyone to see the plans

    def get(self, request: Request, *args, **kwargs) -> Response:
        # Get plan data from the imported configuration
        # Exclude 'CUSTOM' type if it exists in config and shouldn't be listed as a plan
        plans_data = [
            plan_details
            for plan_enum, plan_details in SUBSCRIPTION_PLANS_CONFIG.items()
            if plan_enum
            != SubscriptionTypeChoices.CUSTOM  # Exclude CUSTOM from listed plans
        ]

        serializer = SubscriptionPlanSerializer(plans_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["User Profile"],
    summary="Cancel Active Subscription",
    description="Allows an authenticated user with an active subscription to cancel it. This typically sets the expiry date to the past or nullifies it.",
    request=None,  # No request body needed for basic cancel
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(  # Define response schema inline
                name="CancelSubscriptionResponse",
                fields={
                    "detail": serializers.CharField(),
                    "subscription": SubscriptionDetailSerializer(),  # Include updated status
                },
            ),
            description="Subscription cancelled successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: No active subscription found to cancel."
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication required."
        ),
        status.HTTP_403_FORBIDDEN: OpenApiResponse(
            description="Permission Denied: User does not have an active subscription."
        ),
    },
)
class CancelSubscriptionView(generics.GenericAPIView):
    """Allows authenticated, subscribed users to cancel their active subscription."""

    permission_classes = [
        IsAuthenticated,
        IsCurrentlySubscribed,
    ]  # Must be logged in AND subscribed

    def post(self, request: Request, *args, **kwargs) -> Response:
        user: User = request.user
        try:
            profile: UserProfile = user.profile

            # Double check subscription status (already checked by permission, but good practice)
            if not profile.is_subscribed:
                # This case should ideally be caught by IsCurrentlySubscribed permission
                logger.warning(
                    f"Cancel subscription attempt by user '{user.username}' who is not subscribed (permission bypass?)."
                )
                return Response(
                    {"detail": _("No active subscription to cancel.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Perform cancellation: Nullify expiry date and related code
            profile.subscription_expires_at = None
            profile.serial_code_used = None
            # Add any other fields related to active subscription status if needed
            profile.save(
                update_fields=[
                    "subscription_expires_at",
                    "serial_code_used",
                    "updated_at",
                ]
            )

            logger.info(
                f"Subscription cancelled successfully for user '{user.username}' (ID: {user.id})."
            )

            # Return confirmation and updated (now inactive) subscription status
            response_serializer = SubscriptionDetailSerializer(profile)
            return Response(
                {
                    "detail": _("Subscription cancelled successfully."),
                    "subscription": response_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except UserProfile.DoesNotExist:
            logger.error(
                f"CRITICAL: UserProfile not found during subscription cancellation for authenticated user '{user.username}' (ID: {user.id})."
            )
            return Response(
                {"detail": _("User profile not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )  # Or 500 if it's unexpected
        except Exception as e:
            logger.exception(
                f"Unexpected error cancelling subscription for user '{user.username}': {e}"
            )
            return Response(
                {"detail": _("An error occurred while cancelling the subscription.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
