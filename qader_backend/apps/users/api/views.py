from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from ..models import UserProfile

# --- Authentication Views ---


class CustomTokenObtainPairView(TokenObtainPairView):
    """Customize JWT payload if needed"""

    # If you need to add custom claims to the token payload, override the serializer:
    # serializer_class = CustomTokenObtainPairSerializer
    pass


class LogoutView(views.APIView):
    """Blacklists the refresh token to log out"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"detail": "Invalid token or token not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    # Optionally override create to customize response (e.g., return basic user info)
    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     user = self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     # Example: Return basic user info without tokens
    #     user_data = {
    #         "id": user.id,
    #         "username": user.username,
    #         "email": user.email,
    #         "message": "Registration successful. Please log in."
    #     }
    #     return Response(user_data, status=status.HTTP_201_CREATED, headers=headers)


# --- User Profile Views ---


class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET, PATCH the profile for the logged-in user (/me/)"""

    permission_classes = [IsAuthenticated]
    # Use different serializers for retrieve vs update
    # serializer_class = UserProfileSerializer # Default for GET

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UserProfileUpdateSerializer
        return UserProfileSerializer  # Default for GET

    def get_object(self):
        # Assumes UserProfile exists (created by signal)
        # Handle potential DoesNotExist if signal fails or user deleted somehow
        try:
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            # This indicates a data integrity issue
            from django.http import Http404

            raise Http404("UserProfile not found for this user.")


# --- Password Management Views ---


class PasswordChangeView(generics.GenericAPIView):
    """Change password for the logged-in user"""

    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"detail": "Password updated successfully."}, status=status.HTTP_200_OK
        )


class PasswordResetRequestView(generics.GenericAPIView):
    """Request a password reset email"""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            # Generate token and uid
            token = default_token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

            # Build reset link (adjust URL)
            reset_link = f"https://domain.com/reset-password/{uidb64}/{token}/"

            # Send email
            context = {
                "email": user.email,
                "username": user.username,
                "reset_link": reset_link,
                "site_name": "Qader Platform",  # Or get from settings/DB
            }
            subject = render_to_string(
                "emails/password_reset_subject.txt", context
            ).strip()
            body = render_to_string(
                "emails/password_reset_body.html", context
            )  # HTML email
            text_body = render_to_string(
                "emails/password_reset_body.txt", context
            )  # Plain text fallback

            # Use send_mail or EmailMultiAlternatives for HTML emails
            from django.core.mail import EmailMultiAlternatives

            msg = EmailMultiAlternatives(
                subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email]
            )
            msg.attach_alternative(body, "text/html")
            msg.send()

        except User.DoesNotExist:
            # Don't reveal if user exists or not
            pass
        except Exception as e:
            # Log the error for debugging
            print(
                f"Error sending password reset email: {e}"
            )  # Replace with proper logging
            # Still return success message to user
            pass

        return Response(
            {
                "detail": "If an account with this email exists, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset using token"""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data["uidb64"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
        else:
            # Use a generic error message
            return Response(
                {"detail": "Invalid token or user ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# TODO: Add view for profile picture upload separately (using multipart/form-data)
# class ProfilePictureUploadView(views.APIView):
#     permission_classes = [IsAuthenticated]
#     # parser_classes = [MultiPartParser, FormParser]
#     def post(self, request, format=None):
#         # ... logic to handle file upload and save to profile_picture field ...
#         pass
