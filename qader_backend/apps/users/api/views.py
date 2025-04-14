from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decouple import config


from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ProfilePictureSerializer,
    SimpleUserSerializer,  # Needed for some responses
    SubscriptionDetailSerializer,  # Needed for login response customization
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
            description="Authentication successful, returns tokens and basic user info.",
            examples=[
                OpenApiResponse(
                    description="Success",
                    examples={
                        "access": "eyJhbGciOiJIUzI1NiIsIn...",
                        "refresh": "eyJhbGciOiJIUzI1NiIsIn...",
                        "user": {
                            "id": 15,
                            "username": "ali_student99",
                            "preferred_name": "Ali",
                            "role": "student",
                            "subscription": {
                                "is_active": True,
                                "expires_at": "2024-10-21T10:00:00Z",
                            },
                            "profile_picture_url": "/media/profiles/ali_pic.jpg",
                            "level_determined": True,
                        },
                    },
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
            profile = user.profile
            profile_serializer = UserProfileSerializer(
                profile, context={"request": request}
            )
            subscription_serializer = SubscriptionDetailSerializer(profile)

            data["user"] = {
                "id": user.id,
                "username": user.username,
                "preferred_name": profile.preferred_name,
                "role": profile.role,
                "subscription": subscription_serializer.data,
                "profile_picture_url": profile_serializer.get_profile_picture_url(
                    profile
                ),
                "level_determined": profile.level_determined,
            }
            logger.info(f"User {user.username} logged in successfully.")
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found during login for user ID: {user.id}")
            # Return standard tokens but log the error
            data["user"] = {
                "id": user.id,
                "username": user.username,
                "error": "Profile data unavailable.",
            }
        except Exception as e:
            logger.exception(
                f"Error adding user data to login response for user {user.username}: {e}"
            )
            data["user"] = {
                "id": user.id,
                "username": user.username,
                "error": "Error fetching profile data.",
            }

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
    description="Creates a new user account, activates subscription using a serial code, and creates a user profile.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="User registered successfully.",
            examples=[
                OpenApiResponse(
                    description="Success",
                    examples={
                        "id": 1,
                        "username": "newuser",
                        "email": "new@example.com",
                        "profile": {  # Optionally return profile snippet
                            "full_name": "New User Test",
                            "role": "student",
                        },
                        "message": "Registration successful. Please log in.",
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad Request (validation errors like duplicate username/email, invalid serial code, password mismatch)."
        ),
    },
)
class RegisterView(generics.CreateAPIView):
    """Handles new user registration."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()  # Calls serializer.create()
            headers = self.get_success_headers(serializer.data)

            # Customize the success response
            response_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                # Optionally include basic profile info if needed immediately after registration
                # "profile": {
                #     "full_name": user.profile.full_name,
                #     "role": user.profile.role
                # },
                "message": _("Registration successful. Please log in."),
            }
            return Response(
                response_data, status=status.HTTP_201_CREATED, headers=headers
            )
        except ValidationError as e:
            logger.warning(f"Registration validation failed: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during registration: {e}"
            )  # Log full traceback
            return Response(
                {"detail": _("An unexpected error occurred during registration.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# --- User Profile Views ---


@extend_schema(
    tags=["User Profile"],
    summary="Retrieve or Update Current User Profile",
    description="GET: Returns the profile details of the currently authenticated user.\nPATCH: Partially updates the profile details.",
    responses={
        200: UserProfileSerializer,
        401: OpenApiResponse(description="Authentication required."),
        404: OpenApiResponse(
            description="User profile not found (data integrity issue)."
        ),
    },
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET and PATCH endpoint for the logged-in user's profile (/me/)."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on HTTP method."""
        if self.request.method == "PATCH":
            return UserProfileUpdateSerializer
        return UserProfileSerializer  # Default for GET

    def get_object(self):
        """Return the profile of the current user."""
        try:
            # Profile should always exist for an authenticated user due to the signal
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            # This indicates a data integrity issue if a logged-in user has no profile
            logger.error(
                f"CRITICAL: UserProfile.DoesNotExist for authenticated user ID: {self.request.user.id}"
            )
            raise Http404(_("User profile not found."))

    def perform_update(self, serializer):
        """Called by RetrieveUpdateAPIView during PATCH request."""
        serializer.save()  # Save the updated profile
        logger.info(f"User profile updated for user ID: {self.request.user.id}")


@extend_schema(
    tags=["User Profile"],
    summary="Upload/Update Profile Picture",
    description="Uploads a new profile picture for the authenticated user. Replaces the existing one if present.",
    request={"multipart/form-data": ProfilePictureSerializer},
    responses={
        200: OpenApiResponse(
            description="Profile picture updated successfully.",
            examples=[
                OpenApiResponse(
                    description="Success",
                    examples={
                        "profile_picture_url": "/media/profiles/new_pic_name.jpg"
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., invalid file format, size limit exceeded)."
        ),
        401: OpenApiResponse(description="Authentication required."),
    },
)
class ProfilePictureUploadView(views.APIView):
    """Handles profile picture uploads."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Support file uploads

    def post(self, request, format=None):
        profile = request.user.profile  # Get profile via user relation
        # Pass the profile instance to the serializer for update context
        serializer = ProfilePictureSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            # The serializer's save method will handle updating the instance
            # Optional: Delete the old picture *before* saving the new one
            if profile.profile_picture and "profile_picture" in request.FILES:
                try:
                    profile.profile_picture.delete(
                        save=False
                    )  # Delete file, don't save model yet
                except Exception as e:
                    logger.warning(
                        f"Could not delete old profile picture for user {profile.user.id}: {e}"
                    )

            serializer.save()  # Saves the new picture to the profile instance

            # Return the URL of the newly saved picture
            # Re-serialize the relevant part or just construct the URL
            updated_profile_serializer = UserProfileSerializer(
                profile, context={"request": request}
            )
            new_url = updated_profile_serializer.get_profile_picture_url(profile)

            logger.info(f"Profile picture updated for user ID: {request.user.id}")
            return Response({"profile_picture_url": new_url}, status=status.HTTP_200_OK)
        else:
            logger.warning(
                f"Profile picture upload failed for user ID {request.user.id}: {serializer.errors}"
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
                f"Password change failed for user ID {request.user.id}: {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


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
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


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
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
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
