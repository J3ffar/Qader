from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.db import transaction, DatabaseError
from django.db.utils import IntegrityError  # Import for specific exception handling
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)  # For model validation errors

from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request  # For type hinting
from rest_framework import serializers
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
)
from drf_spectacular.types import OpenApiTypes  # For response schema types

from typing import Optional

from apps.users.api.permissions import (
    IsCurrentlySubscribed,
)  # For type hinting

from .serializers import (
    ApplySerialCodeSerializer,
    AuthUserResponseSerializer,
    RegisterSerializer,
    SubscriptionDetailSerializer,
    SubscriptionPlanSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    # Removed unused imports: SimpleUserSerializer, SubscriptionDetailSerializer
)
from ..models import (
    SubscriptionTypeChoices,
    UserProfile,
    SerialCode,
)  # Added SerialCode import

import logging

logger = logging.getLogger(__name__)


# --- Authentication Views ---


@extend_schema(
    tags=["Authentication"],
    summary="Obtain JWT Tokens",
    description="Authenticate with username and password to receive JWT access and refresh tokens, along with basic user profile information.",
    # request=TokenObtainPairSerializer, # Implicitly handled by the view
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=serializers.Serializer,  # Generic Serializer as structure is defined in example
            description="Authentication successful.",
            examples=[
                OpenApiExample(
                    "Login Success",
                    summary="Successful login response",
                    description="Returns access/refresh tokens and nested user object.",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsIn...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
                        "user": {
                            "id": 15,
                            "username": "ali_student99",
                            "email": "ali.ahmed@example.com",
                            "full_name": "Ali Ahmed Mohamed",
                            "preferred_name": "Ali",
                            "role": "student",
                            "subscription": {
                                "is_active": True,
                                "expires_at": "2024-10-21T10:00:00Z",
                                "serial_code": "QADER-XYZ123-ABC",  # Example code
                            },
                            "profile_picture_url": None,  # Example
                            "level_determined": True,  # Example
                        },
                    },
                    response_only=True,
                )
            ],
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication failed: No active account found with the given credentials."
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Invalid input format (e.g., missing fields)."
        ),
    },
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Customize JWT response to include basic user profile info matching API docs.
    """

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
        try:
            # Use select_related for efficiency if accessing user fields often in serializer
            profile = UserProfile.objects.select_related(
                "user", "serial_code_used"
            ).get(user=user)
            context = {"request": request}
            user_data_serializer = AuthUserResponseSerializer(profile, context=context)
            data["user"] = user_data_serializer.data
            logger.info(
                f"User '{user.username}' (ID: {user.id}) logged in successfully."
            )

        except UserProfile.DoesNotExist:
            logger.error(
                f"CRITICAL: UserProfile not found during login for user '{user.username}' (ID: {user.id}). Data inconsistency."
            )
            # Return standard tokens but log error and potentially omit 'user' key or provide minimal data
            data["user"] = {
                "id": user.id,
                "username": user.username,
                "error": "Profile data missing.",
            }
        except Exception as e:
            logger.exception(
                f"Error adding user data to login response for user '{user.username}': {e}"
            )
            data["user"] = {
                "id": user.id,
                "username": user.username,
                "error": "Error fetching profile data.",
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

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": _("Refresh token is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
    summary="Register New Student User",
    description="Creates a new student user, activates subscription via serial code, creates profile, applies referral if provided, and returns JWT tokens.",
    request=RegisterSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=serializers.Serializer,  # Structure defined in example
            description="User registered successfully.",
            examples=[
                OpenApiExample(
                    "Registration Success",
                    summary="Successful registration response",
                    description="Returns access/refresh tokens and nested user object.",
                    value={
                        "access": "eyJhbGciOiJIUzI1NiIsIn...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
                        "user": {  # Matches AuthUserResponseSerializer structure
                            "id": 16,
                            "username": "new_student",
                            "email": "new@example.com",
                            "full_name": "New Student Name",
                            "preferred_name": "Newbie",
                            "role": "student",
                            "subscription": {
                                "is_active": True,
                                "expires_at": "2025-01-15T12:00:00Z",  # Example expiry
                                "serial_code": "QADER-NEWREG-456",  # Example code used
                            },
                            "profile_picture_url": None,
                            "level_determined": False,  # Starts as false
                        },
                    },
                    response_only=True,
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Validation errors (e.g., duplicate username/email, invalid serial/referral code, password mismatch)."
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            description="Internal Server Error: Unexpected issue during registration process."
        ),
    },
)
class RegisterView(generics.CreateAPIView):
    """Handles new user registration, profile creation, subscription activation, and returns tokens."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # serializer.save() handles the atomic transaction for User, Profile, SerialCode, Subscription
            user = serializer.save()
            profile = (
                user.profile
            )  # Profile is guaranteed to exist after serializer.save()

            # Generate JWT tokens for the new user
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Serialize the user/profile data for the response using AuthUserResponseSerializer
            context = {"request": request}
            user_data_serializer = AuthUserResponseSerializer(profile, context=context)

            response_data = {
                "user": user_data_serializer.data,
                "access": access_token,
                "refresh": refresh_token,
            }
            logger.info(
                f"User '{user.username}' (ID: {user.id}) registered successfully and tokens generated."
            )
            return Response(response_data, status=status.HTTP_201_CREATED)

        except DRFValidationError as e:
            # Handle validation errors raised by the serializer (including custom validation)
            logger.warning(
                f"Registration validation failed for {request.data.get('username', 'N/A')}: {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            # Catch specific database integrity errors (e.g., unique constraints missed by validation)
            logger.error(
                f"Database integrity error during registration save for {request.data.get('username', 'N/A')}: {e}"
            )
            return Response(
                {
                    "detail": _(
                        "Registration failed due to a data conflict. Please check your username and email."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,  # Treat as bad request from user perspective
            )
        except SerialCode.DoesNotExist:
            # Catch if serial code became invalid between validation and transaction lock
            logger.error(
                f"Serial code became invalid during registration transaction for {request.data.get('username')}."
            )
            return Response(
                {
                    "serial_code": [
                        _(
                            "Serial code became invalid during registration process. Please try again."
                        )
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Catch any other unexpected errors during the creation process
            logger.exception(
                f"Unexpected error during registration finalization for {request.data.get('username', 'N/A')}: {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred during registration.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Refresh JWT Access Token",
    description="Obtains a new JWT access token using a valid, non-blacklisted refresh token.",
    request=TokenRefreshSerializer,  # Standard request body: {"refresh": "..."}
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(
                name="TokenRefreshResponse", fields={"access": serializers.CharField()}
            ),
            description="Access token refreshed successfully.",
            examples=[
                OpenApiExample(
                    "Refresh Success", value={"access": "eyJhbGciOiJIUzI1NiIsIn..."}
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
        "**GET:** Returns the full profile details of the currently authenticated user.\n\n"
        "**PATCH:** Partially updates the authenticated user's profile. Allows updating fields like name, grade, preferences, and profile picture. "
        "Uses `multipart/form-data` encoding if `profile_picture` is included."
    ),
    request=UserProfileUpdateSerializer,  # Schema for PATCH request body
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserProfileSerializer,
            description="Profile retrieved or updated successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Validation errors on update (e.g., invalid image file, incorrect data format)."
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication required."
        ),
        status.HTTP_403_FORBIDDEN: OpenApiResponse(
            description="Permission denied (should not happen with IsAuthenticated)."
        ),
        status.HTTP_404_NOT_FOUND: OpenApiResponse(
            description="User profile not found (data integrity issue)."
        ),
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
            return profile
        except UserProfile.DoesNotExist:
            # This indicates a potential data integrity issue if user is authenticated
            logger.error(
                f"CRITICAL: UserProfile.DoesNotExist for authenticated user '{user.username}' (ID: {user.id})"
            )
            raise Http404(_("User profile not found."))

    def perform_update(self, serializer: UserProfileUpdateSerializer):
        """Handle the update logic, including deleting the old profile picture if a new one is saved."""
        profile: UserProfile = self.get_object()
        # Check if 'profile_picture' is part of the validated data to be saved
        new_picture_data = serializer.validated_data.get(
            "profile_picture", "NOT_PRESENT"
        )
        # `None` means user explicitly set picture to null, `NOT_PRESENT` means field wasn't sent
        new_picture_provided = new_picture_data != "NOT_PRESENT"
        old_picture_instance = (
            profile.profile_picture if profile.profile_picture else None
        )

        # Save the instance using the update serializer
        instance: UserProfile = serializer.save()

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

        logger.info(
            f"User profile updated for user '{self.request.user.username}' (ID: {self.request.user.id})"
        )

    # Override update to ensure the *response* uses the full UserProfileSerializer
    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", False)  # True for PATCH
        instance = self.get_object()
        # Validate incoming data using the update serializer
        update_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        try:
            update_serializer.is_valid(raise_exception=True)
        except DRFValidationError as e:
            logger.warning(
                f"Profile update validation failed for user '{request.user.username}': {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # Perform the update (calls serializer.save() via perform_update)
        self.perform_update(update_serializer)

        # Ensure any prefetched data is cleared if necessary
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        # Serialize the updated instance using the *read* serializer for the response
        context = self.get_serializer_context()
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
    tags=["Authentication"],  # Part of the auth flow
    summary="Request Password Reset",
    description="Initiates the password reset process. Sends an email with a unique reset link to the user associated with the provided email or username.",
    request=PasswordResetRequestSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Request received. If an active account matches the identifier, a password reset email will be sent. (Generic response for security).",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "detail": "If an account with this identifier exists, a password reset link has been sent."
                    },
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request: Invalid input format (e.g., identifier missing)."
        ),
    },
)
class PasswordResetRequestView(generics.GenericAPIView):
    """Handles requests to initiate the password reset flow."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # Validator returns the User object if found and active, otherwise None
            user: Optional[User] = serializer.validated_data.get("identifier")

            if user:
                # Proceed with sending the email only if user is found and active
                try:
                    token = default_token_generator.make_token(user)
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

                    # Construct the reset link using frontend URL from settings/env
                    frontend_reset_url_template = getattr(
                        settings, "PASSWORD_RESET_CONFIRM_URL_TEMPLATE", None
                    )
                    if not frontend_reset_url_template:
                        logger.error(
                            "PASSWORD_RESET_CONFIRM_URL_TEMPLATE setting is not configured."
                        )
                        # Still return 200 OK to user, but log the config error
                        return Response(
                            {
                                "detail": _(
                                    "Password reset request received, but system configuration error occurred."
                                )
                            },
                            status=status.HTTP_200_OK,  # Don't reveal server error
                        )

                    # Ensure template includes placeholders for uid and token
                    reset_link = frontend_reset_url_template.format(
                        uidb64=uidb64, token=token
                    )

                    context = {
                        "email": user.email,
                        "username": user.username,
                        "reset_link": reset_link,
                        "site_name": getattr(settings, "SITE_NAME", "Qader Platform"),
                        "user": user,
                    }
                    subject = render_to_string(
                        "emails/password_reset_subject.txt", context
                    ).strip()
                    html_body = render_to_string(
                        "emails/password_reset_body.html", context
                    )
                    text_body = render_to_string(
                        "emails/password_reset_body.txt", context
                    )

                    msg = EmailMultiAlternatives(
                        subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email]
                    )
                    msg.attach_alternative(html_body, "text/html")
                    msg.send()
                    logger.info(
                        f"Password reset email sent successfully to {user.email} for user '{user.username}'"
                    )

                except Exception as e:
                    # Log email sending failure but still return generic success to user
                    logger.exception(
                        f"Error sending password reset email to {user.email if user else 'unknown'}: {e}"
                    )

            else:
                # User not found or inactive, log if desired but don't reveal to requester
                logger.info(
                    f"Password reset requested for unknown or inactive identifier: {request.data.get('identifier')}"
                )

            # Always return a generic success message for security
            return Response(
                {
                    "detail": _(
                        "If an active account with that identifier exists, a password reset link has been sent."
                    )
                },
                status=status.HTTP_200_OK,
            )
        except DRFValidationError as e:
            # Handle validation errors from the serializer itself (e.g., field missing)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    summary="Confirm Password Reset",
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
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "subscription": {
                            "is_active": True,
                            "expires_at": "2025-02-15T10:00:00Z",
                            "serial_code": "QADER-NEWCODE-789",
                        }
                    },
                )
            ],
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
    tags=["Subscription Plans"],  # Maybe a new tag?
    summary="List Available Subscription Plans",
    description="Provides a list of available subscription plans, their details, and associated serial code types.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=SubscriptionPlanSerializer(many=True),
            description="List of available subscription plans.",
            examples=[
                OpenApiExample(
                    "Plans List",
                    value=[
                        {
                            "id": "1_month",
                            "name": "1 Month Access",
                            "description": "Full access for 30 days.",
                            "duration_days": 30,
                            "requires_code_type": "1_month",
                        },
                        {
                            "id": "6_months",
                            "name": "6 Months Access",
                            "description": "Full access for 183 days.",
                            "duration_days": 183,
                            "requires_code_type": "6_months",
                        },
                        {
                            "id": "12_months",
                            "name": "12 Months Access",
                            "description": "Full access for 365 days.",
                            "duration_days": 365,
                            "requires_code_type": "12_months",
                        },
                    ],
                )
            ],
        ),
        # No specific errors expected for simple GET list if data is hardcoded
    },
)
class SubscriptionPlanListView(views.APIView):
    """Lists available subscription plans (currently hardcoded)."""

    permission_classes = [AllowAny]  # Allow anyone to see the plans

    def get(self, request: Request, *args, **kwargs) -> Response:
        # TODO: Replace hardcoded data with fetching from a `SubscriptionPlan` model if created later.
        plans_data = [
            {
                "id": "1_month",
                "name": _("1 Month Access"),
                "description": _("Full access to all platform features for 30 days."),
                "duration_days": 30,
                "requires_code_type": SubscriptionTypeChoices.MONTH_1.value,  # Use value from choices
            },
            {
                "id": "6_months",
                "name": _("6 Months Access"),
                "description": _(
                    "Full access to all platform features for 183 days (approx. 6 months)."
                ),
                "duration_days": 183,
                "requires_code_type": SubscriptionTypeChoices.MONTH_6.value,
            },
            {
                "id": "12_months",
                "name": _("12 Months Access"),
                "description": _(
                    "Full access to all platform features for 365 days (1 year)."
                ),
                "duration_days": 365,
                "requires_code_type": SubscriptionTypeChoices.MONTH_12.value,
            },
            # Add a representation for custom codes if needed, though they aren't a 'plan'
            # {
            #     "id": "custom",
            #     "name": _("Custom Duration"),
            #     "description": _("Subscription duration determined by the specific serial code."),
            #     "duration_days": None, # Duration varies
            #     "requires_code_type": SubscriptionTypeChoices.CUSTOM.value
            # },
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
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "detail": "Subscription cancelled successfully.",
                        "subscription": {
                            "is_active": False,
                            "expires_at": None,
                            "serial_code": None,
                        },
                    },
                )
            ],
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
