import hashlib
import secrets
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from apps.notifications.services import create_notification
from apps.notifications.models import Notification, NotificationTypeChoices
from .constants import (
    AccountTypeChoices,
    GenderChoices,
    RoleChoices,
    DarkModePrefChoices,
    SubscriptionTypeChoices,
    SUBSCRIPTION_PLANS_CONFIG,  # Import config if needed directly in model logic
)

from apps.admin_panel.models import AdminPermission

# Import the utility function
from .utils import generate_unique_referral_code

import logging

logger = logging.getLogger(__name__)


# --- Models ---


class SerialCode(models.Model):
    """Manages serial codes used for activating subscriptions."""

    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_(
            "The unique serial code string (case-insensitive)."
        ),  # Added case-insensitivity note
    )
    subscription_type = models.CharField(
        _("Subscription Type"),
        max_length=20,
        choices=SubscriptionTypeChoices.choices,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Categorizes the intended duration or type of the code."),
    )
    duration_days = models.PositiveIntegerField(
        _("Duration (Days)"),
        default=30,
        help_text=_(
            "Subscription length in days granted by this code. Used for calculating expiry."
        ),
    )
    is_active = models.BooleanField(
        _("Is Active?"),
        default=True,
        help_text=_("Indicates if the code can currently be used for redemption."),
    )
    is_used = models.BooleanField(
        _("Is Used?"),
        default=False,
        db_index=True,
        help_text=_("Indicates if the code has already been redeemed."),
    )
    used_by = models.ForeignKey(
        User,
        verbose_name=_("Used By"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="redeemed_codes",
        help_text=_("The user who redeemed this code."),
    )
    used_at = models.DateTimeField(
        _("Used At"),
        null=True,
        blank=True,
        help_text=_("Timestamp when the code was redeemed."),
    )
    created_by = models.ForeignKey(
        User,
        verbose_name=_("Created By"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_codes",
        limit_choices_to={"is_staff": True},  # Keep limitation to staff/admin
        help_text=_("Admin or Sub-Admin who generated the code."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        null=True,
        help_text=_("Administrative notes (e.g., batch identifier, purpose)."),
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Serial Code")
        verbose_name_plural = _("Serial Codes")
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def clean(self):
        """Optional: Validation logic before saving."""
        if self.code:
            self.code = self.code.upper()

        # Simplified clean: Rely on creation logic (serializers/commands)
        # to set appropriate duration based on type.
        # Remove the previous check that logged warnings.
        # You *could* add a stricter check here if needed:
        # plan_config = SUBSCRIPTION_PLANS_CONFIG.get(self.subscription_type)
        # if plan_config and plan_config.get('duration_days') is not None:
        #     if self.duration_days != plan_config['duration_days']:
        #         raise ValidationError(
        #              _("Duration ({days}) doesn't match the specified plan type '{type}' ({expected} days).").format(...)
        #          )

        super().clean()

    def save(self, *args, **kwargs):
        self.clean()  # Ensure clean is called
        super().save(*args, **kwargs)

    def mark_used(self, user: User) -> bool:  # Added type hints
        """Marks the code as used by a specific user if it's valid and available."""
        if self.is_active and not self.is_used:
            self.is_used = True
            self.used_by = user
            self.used_at = timezone.now()
            # Only update relevant fields for efficiency
            self.save(update_fields=["is_used", "used_by", "used_at", "updated_at"])
            logger.info(
                f"Serial code {self.code} marked as used by user {user.username}"
            )
            return True
        logger.warning(
            f"Attempted to mark code {self.code} used by {user.username}, but it was not active or already used."
        )
        return False


class PasswordResetOTP(models.Model):
    """Stores OTPs and subsequent reset tokens for password reset."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_otps",
        verbose_name=_("User"),
    )
    # OTP specific fields
    otp_code_hash = models.CharField(
        _("OTP Code (Hashed)"),
        max_length=128,  # SHA256 hex digest is 64 chars, but let's give some room
        help_text=_("Hashed version of the OTP code."),
    )
    otp_created_at = models.DateTimeField(
        _("OTP Created At"), auto_now_add=True
    )  # Renamed for clarity
    otp_expires_at = models.DateTimeField(_("OTP Expires At"))  # Renamed for clarity

    # Reset Token specific fields (populated after OTP verification)
    reset_token_hash = models.CharField(
        _("Reset Token (Hashed)"),
        max_length=128,
        null=True,
        blank=True,
        unique=True,  # Ensures reset token is unique if generated globally
        db_index=True,
    )
    reset_token_expires_at = models.DateTimeField(
        _("Reset Token Expires At"), null=True, blank=True
    )

    is_used = models.BooleanField(
        _("Is Used?"),
        default=False,
        db_index=True,
        help_text=_("True if password has been successfully reset using this record."),
    )
    # General timestamps
    created_at = models.DateTimeField(
        auto_now_add=True
    )  # Redundant with otp_created_at, consider removing if otp_created_at is primary
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Password Reset OTP & Token")
        verbose_name_plural = _("Password Reset OTPs & Tokens")
        ordering = ["-otp_created_at"]  # Order by OTP creation time

    def __str__(self):
        status_parts = []
        if self.is_used:
            status_parts.append("Used")
        else:
            if timezone.now() > self.otp_expires_at:
                status_parts.append("OTP Expired")
            else:
                status_parts.append("OTP Active")
            if self.reset_token_hash:
                if (
                    self.reset_token_expires_at
                    and timezone.now() > self.reset_token_expires_at
                ):
                    status_parts.append("ResetToken Expired")
                else:
                    status_parts.append("ResetToken Active")
        return f"OTP/Token for {self.user.username} - ({', '.join(status_parts)})"

    def _hash_value(self, plain_value: str) -> str:
        """Hashes a value using SHA256."""
        return hashlib.sha256(plain_value.encode("utf-8")).hexdigest()

    def set_otp(self, otp_plain: str):
        """Sets the OTP by storing its hash and its expiry."""
        self.otp_code_hash = self._hash_value(otp_plain)
        self.otp_expires_at = timezone.now() + timedelta(
            minutes=settings.OTP_EXPIRY_MINUTES
        )

    def verify_otp(self, otp_plain: str) -> bool:
        """Verifies the provided plain OTP against the stored hashed OTP and checks OTP validity."""
        if self.is_used:  # Already fully used for password reset
            return False
        if timezone.now() > self.otp_expires_at:  # OTP itself has expired
            return False
        return self.otp_code_hash == self._hash_value(otp_plain)

    def generate_reset_token(self) -> str:
        """Generates a unique reset token, stores its hash and expiry, and returns the plain token."""
        plain_reset_token = secrets.token_urlsafe(
            32
        )  # Generates a secure URL-safe text string
        self.reset_token_hash = self._hash_value(plain_reset_token)
        # Reset token should have a shorter expiry, e.g., 5 minutes after OTP verification
        self.reset_token_expires_at = timezone.now() + timedelta(
            minutes=getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", 5)
        )
        # Do not mark is_used here. is_used is for when the password is changed.
        self.save(
            update_fields=["reset_token_hash", "reset_token_expires_at", "updated_at"]
        )
        return plain_reset_token

    def verify_reset_token(self, plain_reset_token: str) -> bool:
        """Verifies the provided plain reset token."""
        if self.is_used:
            return False
        if (
            not self.reset_token_hash or not self.reset_token_expires_at
        ):  # Token not generated
            return False
        if timezone.now() > self.reset_token_expires_at:  # Token expired
            return False
        return self.reset_token_hash == self._hash_value(plain_reset_token)

    def mark_used(self):
        """Marks the entire OTP/Token record as used (password reset successful)."""
        self.is_used = True
        # Optionally, clear token fields if desired after use, though is_used flag is primary
        # self.reset_token_hash = None
        # self.reset_token_expires_at = None
        self.save(update_fields=["is_used", "updated_at"])


class UserProfile(models.Model):
    """Stores additional information specific to Qader users, extending the built-in User model."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="profile",
        verbose_name=_("User"),
    )
    # Basic Info
    full_name = models.CharField(
        _("Full Name"), max_length=255, help_text=_("User's full legal name.")
    )
    preferred_name = models.CharField(
        _("Preferred Name"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("How the user prefers to be called."),
    )
    gender = models.CharField(
        _("Gender"), max_length=20, choices=GenderChoices.choices, blank=True, null=True
    )
    grade = models.CharField(
        _("Grade/Level"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Educational level (e.g., Grade 12, University Freshman)."),
    )
    has_taken_qiyas_before = models.BooleanField(
        _("Taken Qiyas Before?"),
        null=True,
        blank=True,  # Explicitly allowing null/blank
        help_text=_("Has the student taken an official Qiyas test previously?"),
    )
    profile_picture = models.ImageField(
        _("Profile Picture"), upload_to="profiles/", null=True, blank=True
    )
    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT,
        db_index=True,
    )
    # Subscription Details
    account_type = models.CharField(
        _("Account Type"),
        max_length=20,
        choices=AccountTypeChoices.choices,
        default=AccountTypeChoices.FREE_TRIAL,  # Default to Free Trial upon profile creation
        db_index=True,
        help_text=_(
            "Indicates the user's current subscription level (e.g., Free Trial, Subscribed)."
        ),
    )
    subscription_expires_at = models.DateTimeField(
        _("Subscription Expires At"), null=True, blank=True, db_index=True
    )
    # Renamed related_name for clarity
    serial_code_used = models.ForeignKey(
        SerialCode,
        verbose_name=_("Last Redeemed Serial Code"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activated_profiles",  # Changed from user_profiles for clarity
        help_text=_("The last serial code used to activate/extend subscription."),
    )

    # Gamification/Progress Tracking (Core fields managed here)
    points = models.PositiveIntegerField(_("Points"), default=0)
    current_streak_days = models.PositiveIntegerField(
        _("Current Study Streak (Days)"), default=0
    )
    longest_streak_days = models.PositiveIntegerField(
        _("Longest Study Streak (Days)"), default=0
    )
    # Consider if this should be updated by study app signals
    language = models.CharField(
        _("Preferred Language"),
        max_length=5,  # e.g., 'en', 'ar', 'en-us'
        choices=settings.LANGUAGES,  # Use LANGUAGES from settings
        default=settings.LANGUAGE_CODE,  # Default to site's default language
        help_text=_("User's preferred language for emails and interface elements."),
    )
    last_study_activity_at = models.DateTimeField(
        _("Last Study Activity At"),
        null=True,
        blank=True,
        help_text=_(
            "Timestamp of the last tracked study action for streak calculation."
        ),
    )

    # Learning Level Assessment (Managed by study app logic)
    current_level_verbal = models.FloatField(
        _("Current Verbal Level (%)"),
        null=True,
        blank=True,
        help_text=_("Assessed proficiency level (0-100) in the Verbal section."),
    )
    current_level_quantitative = models.FloatField(
        _("Current Quantitative Level (%)"),
        null=True,
        blank=True,
        help_text=_("Assessed proficiency level (0-100) in the Quantitative section."),
    )

    # User Settings & Preferences
    last_visited_study_option = models.CharField(
        _("Last Visited Study Option Slug"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Slug identifier of the last viewed section in 'Study Page'."),
    )
    dark_mode_preference = models.CharField(
        _("Dark Mode Preference"),
        max_length=10,
        choices=DarkModePrefChoices.choices,
        default=DarkModePrefChoices.LIGHT,
    )
    dark_mode_auto_enabled = models.BooleanField(
        _("Auto Dark Mode Enabled?"), default=False
    )
    dark_mode_auto_time_start = models.TimeField(
        _("Auto Dark Mode Start Time"), null=True, blank=True
    )
    dark_mode_auto_time_end = models.TimeField(
        _("Auto Dark Mode End Time"), null=True, blank=True
    )
    notify_reminders_enabled = models.BooleanField(
        _("Reminders Enabled?"), default=True
    )
    upcoming_test_date = models.DateField(
        _("Upcoming Test Date"),
        null=True,
        blank=True,
        help_text=_("User-set date for their upcoming official test."),
    )
    study_reminder_time = models.TimeField(
        _("Study Reminder Time"),
        null=True,
        blank=True,
        help_text=_("Preferred time of day for study reminders (HH:MM)."),
    )

    # Referral System
    referral_code = models.CharField(
        _("Referral Code"),
        max_length=20,  # Adjusted length if needed based on generation strategy
        unique=True,
        null=True,  # Generated on first save
        blank=True,
        db_index=True,
        help_text=_("User's unique code to share for referrals."),
    )
    referred_by = models.ForeignKey(
        User,
        verbose_name=_("Referred By User"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals_made",
        help_text=_("The user whose referral code this user signed up with."),
    )
    admin_permissions = models.ManyToManyField(
        AdminPermission,
        verbose_name=_("Admin Permissions"),
        blank=True,
        related_name="sub_admins",
        help_text=_("Specific permissions granted to this sub-admin user."),
    )
    assigned_mentor = models.ForeignKey(
        "self",  # Links to another UserProfile instance
        verbose_name=_("Assigned Mentor (Teacher/Trainer)"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mentees",  # Allows mentor.mentees.all()
        limit_choices_to={"role__in": [RoleChoices.TEACHER, RoleChoices.TRAINER]},
        help_text=_(
            "The Teacher or Trainer assigned to this student. Only applicable if role is Student."
        ),
    )

    # Timestamps
    created_at = models.DateTimeField(_("Profile Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Profile Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
        ordering = ["-created_at"]  # Added default ordering

    def __str__(self):
        return f"Profile for {self.user.username}"

    @property
    def is_subscribed(self) -> bool:
        """Check if the user currently has an active subscription."""
        if not self.subscription_expires_at:
            return False
        return timezone.now() < self.subscription_expires_at

    @property
    def is_free_trial_user(self) -> bool:
        """Check if the user's account type is currently Free Trial."""
        return self.account_type == AccountTypeChoices.FREE_TRIAL

    @property
    def is_paid_subscriber(self) -> bool:
        """Check if the user has a paid subscription type (not Free Trial)."""
        return self.account_type in [
            AccountTypeChoices.SUBSCRIBED,
            # Add other paid types here if they exist (PREMIUM, etc.)
        ]

    @property
    def level_determined(self) -> bool:
        """Check if both verbal and quantitative levels have been assessed."""
        # Check for non-null values
        return (
            self.current_level_verbal is not None
            and self.current_level_quantitative is not None
        )

    @property
    def is_profile_complete(self) -> bool:
        """
        Checks if the essential profile information required after activation is filled.
        Adjust required fields as necessary.
        """
        # Check if fields considered essential for using the platform are filled
        required_fields_filled = all(
            [
                self.gender,
                self.grade,
                self.has_taken_qiyas_before is not None,  # Check boolean specifically
                # Add other fields deemed essential for platform usage if any
            ]
        )
        # Also check if full_name exists (should be set during initial signup)
        return bool(self.full_name and required_fields_filled)

    @property
    def unread_notifications_count(self) -> int:
        """Returns the count of unread notifications for the user associated with this profile."""
        if hasattr(self, "user") and self.user_id:  # Efficiently check if user is set
            # Use user_id directly to avoid fetching the full user object if not already done
            return Notification.objects.filter(
                recipient_id=self.user_id, is_read=False
            ).count()
        return 0

    def apply_subscription(self, serial_code: SerialCode):  # Added type hint
        """Applies or extends subscription duration based on a valid SerialCode."""
        if not serial_code or serial_code.duration_days <= 0:
            logger.warning(
                f"Attempted to apply subscription for user {self.user.username} with invalid code or zero duration."
            )
            return

        now = timezone.now()
        start_date = now
        # Extend from current expiry only if it's actively in the future
        if self.subscription_expires_at and self.subscription_expires_at > now:
            start_date = self.subscription_expires_at

        try:
            new_expiry_date = start_date + timedelta(days=serial_code.duration_days)
            self.subscription_expires_at = new_expiry_date
            self.serial_code_used = serial_code
            self.account_type = AccountTypeChoices.SUBSCRIBED
            self.save(
                update_fields=[
                    "subscription_expires_at",
                    "serial_code_used",
                    "account_type",
                    "updated_at",
                ]
            )
            create_notification(
                recipient=self.user,
                verb=_("activated a subscription"),
                description=_(
                    "Your subscription has been successfully activated using code: {serial_code}."
                ).format(serial_code=self.serial_code_used.code),
                target=self.serial_code_used,  # The SerialCode instance
                notification_type=NotificationTypeChoices.SUBSCRIPTION,
                url="/profile/me/subscription",  # Example frontend URL
                extra_data={"serial_code_id": self.serial_code_used.id},
            )
            logger.info(
                f"Subscription for user {self.user.username} updated. Expires: {new_expiry_date}. Using code: {serial_code.code}"
            )
        except Exception as e:
            logger.exception(
                f"Error applying subscription timedelta for user {self.user.username} using code {serial_code.code}: {e}"
            )

    def grant_trial_subscription(self, duration_days: int = 1):
        """Grants a trial subscription if the user doesn't have an active one."""
        now = timezone.now()
        if not self.is_subscribed:  # Only grant if not already subscribed
            try:
                self.subscription_expires_at = now + timedelta(days=duration_days)
                self.serial_code_used = None  # Ensure no serial code is linked to trial
                # No save here, intended to be saved within a transaction in the calling view
                logger.info(
                    f"Granted {duration_days}-day trial subscription to user {self.user.username}. Expires: {self.subscription_expires_at}"
                )
                return True
            except Exception as e:
                logger.exception(
                    f"Error granting trial subscription to user {self.user.username}: {e}"
                )
                raise
        else:
            logger.info(
                f"User {self.user.username} already has an active subscription. Trial not granted."
            )
            return False

    def has_permission(self, perm_slug: str) -> bool:
        """
        Checks if the user (if a sub-admin) has the specified granular permission.
        Superusers/main admins implicitly have all permissions.
        """
        if (
            self.user.is_superuser
            or self.user.is_staff
            and self.role == RoleChoices.ADMIN
        ):
            return True
        if self.role == RoleChoices.SUB_ADMIN and self.user.is_staff:
            # Optimized check using exists()
            return self.admin_permissions.filter(slug=perm_slug).exists()
        return False

    def save(self, *args, **kwargs):
        if not self.referral_code:
            if hasattr(self, "user") and self.user and self.user.username:
                self.referral_code = generate_unique_referral_code(self.user.username)
                logger.info(
                    f"Generated referral code '{self.referral_code}' for user {self.user.username}"
                )
            else:
                logger.warning(
                    "Could not generate referral code during profile save: User or username not available."
                )

        # Auto-populate preferred_name from full_name if preferred_name is empty
        if self.full_name and not self.preferred_name:
            self.preferred_name = self.full_name
            logger.info(
                f"Preferred name for user {self.user.username} auto-populated from full name."
            )

        # Ensure is_staff is True for ADMIN, SUB_ADMIN, TEACHER, TRAINER roles
        staff_roles = [
            RoleChoices.ADMIN,
            RoleChoices.SUB_ADMIN,
            RoleChoices.TEACHER,
            RoleChoices.TRAINER,
        ]
        if hasattr(self, "user") and self.user:  # Ensure user object exists
            if self.role in staff_roles and not self.user.is_staff:
                self.user.is_staff = True
                if self.user.pk:  # Check if user is already saved
                    self.user.save(
                        update_fields=["is_staff"]
                    )  # Removed last_login to avoid issues on new user creation
            elif (
                self.role == RoleChoices.STUDENT and self.user.is_staff
            ):  # Demoting to student
                # Only turn off is_staff if they are not also a superuser
                if not self.user.is_superuser:
                    self.user.is_staff = False
                    if self.user.pk:
                        self.user.save(update_fields=["is_staff"])

        # If role is not Student, ensure assigned_mentor is cleared
        if self.role != RoleChoices.STUDENT and self.assigned_mentor is not None:
            self.assigned_mentor = None  # Mentors cannot have mentors

        # If role is not Teacher/Trainer, ensure mentees are cleared
        # This needs to be handled carefully if mentees is a M2M through 'assigned_mentor'
        # The current model structure handles this by assigned_mentor being null for non-students.
        # If a user's role changes FROM Teacher/Trainer, their mentees' assigned_mentor link to this user will be broken
        # if those students are reassigned or if we explicitly clear them.
        # For now, the model's current structure is okay. If a Teacher becomes a Student,
        # their 'mentees' field (reverse of assigned_mentor) becomes irrelevant for them in their new role.

        super().save(*args, **kwargs)
