from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from decouple import config


from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from drf_spectacular.utils import OpenApiExample
from drf_spectacular.utils import extend_schema, OpenApiResponse

from rest_framework import serializers
from .serializers import (
    AuthUserResponseSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    SimpleUserSerializer,
    SubscriptionDetailSerializer,
)
from ..models import UserProfile

import logging

logger = logging.getLogger(__name__)


# --- Authentication Views ---


@extend_schema(
    tags=["Authentication"],
    summary="Obtain JWT Access and Refresh Tokens",
    description="Authenticate with username and password to receive JWT tokens.",
    responses={
        200: OpenApiResponse(
            response=AuthUserResponseSerializer,
            description="Authentication successful, returns tokens and basic user info.",
            examples=[
                OpenApiExample(
                    name="Success",
                    description="Successful login response",
                    value={
                        "user": {
                            "id": 15,
                            "username": "ali_student99",
                            "preferred_name": "Ali",
                            "role": "student",
                            "subscription": {
                                "is_active": True,
                                "expires_at": "2024-10-21T10:00:00Z",
                                "serial_code": "QADER-PREV1-XYZ",
                            },
                            "profile_picture_url": "/media/profiles/ali_pic.jpg",
                            "level_determined": True,
                        },
                        "access": "eyJhbGciOiJIUzI1NiIsIn...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
                    },
                    response_only=True,
                    status_codes=["200"],
                )
            ],
        ),
        401: OpenApiResponse(
            description="Authentication failed (invalid credentials)."
        ),
    },
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Customize JWT payload and response to include basic user info upon login,
    matching the API documentation.
    """

    # Use the default TokenObtainPairSerializer or create a custom one if claims need modification
    # serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Catch potential validation errors (e.g., invalid credentials)
            logger.warning(f"Login failed for user {request.data.get('username')}: {e}")
            raise e  # Re-raise to let DRF handle the 401 response

        # Standard response data (access, refresh tokens)
        data = serializer.validated_data

        # Add custom user data to the response
        user = serializer.user  # User instance is attached by the serializer
        try:
            profile = user.profile  # Assumes profile exists for logged-in user
            # --- Use AuthUserResponseSerializer for the 'user' object ---
            context = {"request": request}
            user_data_serializer = AuthUserResponseSerializer(profile, context=context)
            data["user"] = user_data_serializer.data

            logger.info(f"User {user.username} logged in successfully.")
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found during login for user ID: {user.id}")
            # Return standard tokens but log the error
            data["user"] = {"error": "Profile data unavailable."}
        except Exception as e:
            logger.exception(
                f"Error adding user data to login response for user {user.username}: {e}"
            )
            data["user"] = {"error": "Error fetching profile data."}

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    summary="Logout User",
    description="Blacklists the provided refresh token to effectively log the user out on the backend.",
    request={
        "application/json": {
            "required": True,
            "properties": {"refresh": {"type": "string"}},
        }
    },
    responses={
        204: OpenApiResponse(description="Logout successful (No Content)."),
        400: OpenApiResponse(
            description="Bad Request (e.g., invalid or missing refresh token)."
        ),
        401: OpenApiResponse(description="Authentication required to logout."),
    },
)
class LogoutView(views.APIView):
    """Blacklists the refresh token provided in the request body."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
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
                f"User ID {request.user.id} logged out successfully (token blacklisted)."
            )
            # Return 204 No Content for successful logout as per common practices
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            # Handle potential errors like token already blacklisted or invalid format
            logger.warning(f"Logout failed for user ID {request.user.id}: {e}")
            return Response(
                {"detail": _("Invalid token or error blacklisting token.")},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Register New User",
    description="Creates a new user account, activates subscription using a serial code, creates a profile, and returns JWT tokens.",  # Updated description
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=AuthUserResponseSerializer,
            description="User registered successfully.",
            examples=[
                OpenApiExample(
                    name="Success",
                    description="Successful registration response",
                    value={
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
                                "serial_code": "QADER-XYZ123-ABC",
                            },
                            "profile_picture_url": None,
                            "level_determined": False,
                        },
                        "access": "eyJhbGciOiJIUzI1NiIsIn...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
                    },
                    response_only=True,
                    status_codes=["201"],
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad Request (validation errors like duplicate username/email, invalid serial code, password mismatch)."
        ),
        # Add 500 for truly unexpected errors, although serializer should prevent most
        500: OpenApiResponse(description="Internal Server Error."),
    },
)
class RegisterView(generics.CreateAPIView):
    """Handles new user registration and returns tokens."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = serializer.save()  # Calls serializer.create()
            profile = (
                user.profile
            )  # Get the profile created/updated in serializer.create

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # --- Use AuthUserResponseSerializer for the 'user' object ---
            # Pass request in context if needed (e.g., for build_absolute_uri)
            context = {"request": request}
            user_data_serializer = AuthUserResponseSerializer(profile, context=context)

            response_data = {
                "user": user_data_serializer.data,
                "access": access_token,
                "refresh": refresh_token,
            }
            logger.info(
                f"User {user.username} registered successfully and tokens generated."
            )
            return Response(response_data, status=status.HTTP_201_CREATED)
        # Catch specific expected errors from serializer.save() if any,
        # otherwise catch broader exceptions that indicate a server issue.
        except (
            IntegrityError
        ) as e:  # Example: Catch DB constraint errors not caught by serializer
            logger.error(f"Database integrity error during registration save: {e}")
            # Return a specific 400 or a generic 500 depending on context
            return Response(
                {"detail": _("Registration failed due to a database conflict.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Log unexpected errors during the user/profile/token creation process
            logger.exception(
                f"Unexpected error during registration finalization for {request.data.get('username')}: {e}"
            )
            return Response(
                {
                    "detail": _(
                        "An unexpected error occurred after validation during registration."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Refresh JWT Access Token",
    description="Obtains a new JWT access token by providing a valid refresh token.",
    request=TokenRefreshSerializer,  # Use the standard serializer for request schema
    responses={
        200: OpenApiResponse(
            response=serializers,
            description="Access token refreshed successfully.",
            examples=[
                OpenApiExample(
                    name="Success",
                    value={"access": "eyJhbGciOiJIUzI1NiIsIn..."},
                )
            ],
        ),
        400: OpenApiResponse(description="Bad Request (e.g., missing refresh token)."),
        401: OpenApiResponse(description="Token is invalid or expired."),
    },
)
class CustomTokenRefreshView(TokenRefreshView):
    """Subclass to add custom documentation via @extend_schema."""

    pass  # Inherits all functionality, just adds schema


# --- User Profile Views ---


@extend_schema(
    tags=["User Profile"],
    summary="Retrieve or Update Current User Profile",
    description="GET: Returns the profile details of the currently authenticated user.\nPATCH: Partially updates profile details. Accepts `multipart/form-data` for updates, allowing profile picture upload alongside other fields.",
    # Update request body example for PATCH if needed, show profile_picture as optional field
    request=UserProfileUpdateSerializer,
    responses={
        200: UserProfileSerializer,
        400: OpenApiResponse(
            description="Bad Request (validation errors, invalid file type/size)."
        ),  # Added possibility of file errors
        401: OpenApiResponse(description="Authentication required."),
        404: OpenApiResponse(
            description="User profile not found (data integrity issue)."
        ),
    },
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve profile for the logged-in user (/me/).
    PATCH: Update profile for the logged-in user (/me/). Handles multipart/form-data for potential profile picture uploads.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # Keep get_serializer_class to determine the correct serializer for *input validation*
    def get_serializer_class(self):
        """Return appropriate serializer based on HTTP method."""
        if self.request.method == "PATCH" or self.request.method == "PUT":
            # Use this for validating the incoming update data
            return UserProfileUpdateSerializer
        # Use this for GET requests and for serializing the response after update
        return UserProfileSerializer

    def get_object(self):
        """Return the profile of the current user."""
        try:
            # Ensure profile exists, create if necessary (though signal should handle this)
            profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            if created:
                logger.warning(
                    f"UserProfile created on-the-fly for user ID {self.request.user.id} in UserProfileView.get_object. Check signal."
                )
                # Populate required fields if necessary, though ideally signal handles defaults
                # profile.full_name = self.request.user.get_full_name() or self.request.user.username
                # profile.save()
            return profile
        except User.profile.RelatedObjectDoesNotExist:  # More specific exception
            logger.error(
                f"CRITICAL: UserProfile.DoesNotExist for authenticated user ID: {self.request.user.id}"
            )
            raise Http404(_("User profile not found."))

    def perform_update(self, serializer):
        """Called by RetrieveUpdateAPIView during PATCH/PUT request. Handles old picture deletion."""
        profile = self.get_object()
        new_picture_uploaded = "profile_picture" in serializer.validated_data
        old_picture_instance = (
            profile.profile_picture if profile.profile_picture else None
        )

        instance = serializer.save()

        # --- Delete old picture *after* successfully saving the new one ---
        if old_picture_instance and new_picture_uploaded:
            # Check if the picture actually changed
            if instance.profile_picture != old_picture_instance:
                try:
                    # Delete the old file; model instance is already saved without it.
                    old_picture_instance.delete(save=False)
                    logger.info(
                        f"Deleted old profile picture for user {profile.user.id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not delete old profile picture '{old_picture_instance.name}' for user {profile.user.id}: {e}"
                    )

        logger.info(f"User profile updated for user ID: {self.request.user.id}")

    # Override update to ensure the response uses the UserProfileSerializer (read serializer)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)  # Typically True for PATCH
        instance = self.get_object()
        # Use UserProfileUpdateSerializer for validation
        update_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        update_serializer.is_valid(raise_exception=True)
        self.perform_update(update_serializer)  # This calls serializer.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been used, clear the cache to see updates.
            instance._prefetched_objects_cache = {}

        # --- Explicitly use UserProfileSerializer for the response ---
        # Pass the same context (like the request) to the read serializer
        context = self.get_serializer_context()
        read_serializer = UserProfileSerializer(instance, context=context)
        return Response(read_serializer.data)


# --- Password Management Views ---


@extend_schema(
    tags=["User Profile"],
    summary="Change Current User Password",
    description="Allows the authenticated user to change their own password by providing the current one.",
    request=PasswordChangeSerializer,
    responses={
        200: OpenApiResponse(description="Password updated successfully."),
        400: OpenApiResponse(
            description="Bad Request (e.g., incorrect current password, passwords mismatch)."
        ),
        401: OpenApiResponse(description="Authentication required."),
    },
)
class PasswordChangeView(generics.GenericAPIView):
    """Handles password change for the logged-in user."""

    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            logger.info(f"Password changed successfully for user ID: {user.id}")
            # Consider logging the user out of other sessions after password change
            return Response(
                {"detail": _("Password updated successfully.")},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.warning(
                f"Password change failed for user ID {request.user.id}: {e.message}"
            )
            return Response(e.message, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    summary="Request Password Reset",
    description="Initiates the password reset process by sending an email with a reset link to the user identified by email or username.",
    request=PasswordResetRequestSerializer,
    responses={
        200: OpenApiResponse(
            description="If an account exists for the identifier, a reset email has been sent (generic response for security)."
        ),
        400: OpenApiResponse(description="Bad Request (invalid input format)."),
    },
)
class PasswordResetRequestView(generics.GenericAPIView):
    """Handles requests to initiate password reset."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # The validator returns the user object if found, or None
            user = serializer.validated_data.get(
                "identifier"
            )  # Changed validator to return user

            if user:
                try:
                    # Generate token and uid
                    token = default_token_generator.make_token(user)
                    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

                    # Build reset link
                    frontend_url = config(
                        "PASSWORD_RESET_URL",
                        default="https://example.com/reset-password-confirm",
                    )
                    reset_link = f"{frontend_url}/{uidb64}/{token}/"

                    # Send email using templates
                    context = {
                        "email": user.email,
                        "username": user.username,
                        "reset_link": reset_link,
                        "site_name": "Qader Platform",  # Get from settings or DB
                        "user": user,  # Pass user object to template if needed
                    }
                    subject = render_to_string(
                        "emails/password_reset_subject.txt", context
                    ).strip()
                    html_body = render_to_string(
                        "emails/password_reset_body.html", context
                    )  # HTML email
                    text_body = render_to_string(
                        "emails/password_reset_body.txt", context
                    )  # Plain text fallback

                    msg = EmailMultiAlternatives(
                        subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email]
                    )
                    msg.attach_alternative(html_body, "text/html")
                    msg.send()
                    logger.info(
                        f"Password reset email sent successfully to {user.email} for user {user.username}"
                    )

                except Exception as e:
                    # Log error but still return success to user
                    logger.exception(
                        f"Error sending password reset email to {user.email if user else 'unknown'}: {e}"
                    )

            else:
                # User not found, log this if desired, but don't tell the requester
                logger.info(
                    f"Password reset request for unknown identifier: {request.data.get('identifier')}"
                )

            # Always return a generic success message for security reasons
            return Response(
                {
                    "detail": _(
                        "If an account with that identifier exists, a password reset link has been sent."
                    )
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            # Handle validation errors from the serializer itself (e.g., invalid format)
            return Response(e.message, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    summary="Confirm Password Reset",
    description="Sets a new password for the user using the UID and token provided in the password reset link.",
    request=PasswordResetConfirmSerializer,
    responses={
        200: OpenApiResponse(description="Password has been reset successfully."),
        400: OpenApiResponse(
            description="Bad Request (invalid token, user ID, or password mismatch)."
        ),
    },
)
class PasswordResetConfirmView(generics.GenericAPIView):
    """Handles the confirmation step of password reset."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            uidb64 = serializer.validated_data["uidb64"]
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            user = self.get_user_from_uidb64(uidb64)

            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                logger.info(
                    f"Password reset confirmed successfully for user ID: {user.id}"
                )
                # Consider logging the user out of other sessions here
                return Response(
                    {"detail": _("Password has been reset successfully.")},
                    status=status.HTTP_200_OK,
                )
            else:
                logger.warning(
                    f"Invalid password reset token attempt. UIDB64: {uidb64}"
                )
                # Use a generic error message for invalid token/user
                return Response(
                    {"detail": _("Invalid password reset link.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except ValidationError as e:
            # Handle password mismatch validation errors
            return Response(e.message, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during password reset confirmation: {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_user_from_uidb64(self, uidb64):
        """Helper method to decode uidb64 and get the user object."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            return user
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            Exception,
        ) as e:
            logger.debug(f"Failed to get user from UIDB64 {uidb64}: {e}")
            return None
