from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
import uuid

# --- Choices ---


class GenderChoices(models.TextChoices):
    MALE = "male", _("Male")
    FEMALE = "female", _("Female")


class RoleChoices(models.TextChoices):
    STUDENT = "student", _("Student")
    ADMIN = "admin", _("Admin")
    SUB_ADMIN = "sub_admin", _("Sub-Admin")
    # Add other roles if required (e.g., Trainer, School Representative)


class DarkModePrefChoices(models.TextChoices):
    LIGHT = "light", _("Light")
    DARK = "dark", _("Dark")
    SYSTEM = "system", _("System")


class SubscriptionTypeChoices(models.TextChoices):
    MONTH_1 = "1_month", _("1 Month")
    MONTH_6 = "6_months", _("6 Months")
    MONTH_12 = "12_months", _("12 Months")
    CUSTOM = "custom", _("Custom")


# --- Models ---


class SerialCode(models.Model):
    """Manages serial codes used for activating subscriptions."""

    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_("The unique serial code string."),
    )
    # Add the subscription type field
    subscription_type = models.CharField(
        _("Subscription Type"),
        max_length=20,
        choices=SubscriptionTypeChoices.choices,
        null=True,  # Allow null initially for existing codes / flexibility
        blank=True,  # Allow blank in forms
        db_index=True,
        help_text=_(
            "Categorizes the intended duration of the code (e.g., 1 Month, 6 Months)."
        ),
    )
    duration_days = models.PositiveIntegerField(
        _("Duration (Days)"),
        default=30,
        help_text=_(
            "Subscription length in days granted by this code. Should align with Subscription Type if set."
        ),
    )
    is_active = models.BooleanField(
        _("Is Active?"),
        default=True,
        help_text=_("Indicates if the code can currently be used."),
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
        on_delete=models.SET_NULL,  # Keep record even if user is deleted
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
        on_delete=models.SET_NULL,  # Keep record even if admin user is deleted
        null=True,
        blank=True,
        related_name="generated_codes",
        limit_choices_to={
            "is_staff": True
        },  # Optional: Limit creator choices to staff/admins
        help_text=_("Admin or Sub-Admin who generated the code."),
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        null=True,
        help_text=_(
            "Administrative notes about this code (e.g., batch identifier, purpose)."
        ),
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
        """
        Optional: Add validation to suggest correct duration_days based on type.
        This runs before saving in the admin or via ModelForms.
        """
        from django.core.exceptions import ValidationError

        if self.subscription_type:
            expected_duration = None
            if self.subscription_type == SubscriptionTypeChoices.MONTH_1:
                expected_duration = 30  # Or 31? Be consistent.
            elif self.subscription_type == SubscriptionTypeChoices.MONTH_6:
                expected_duration = 183  # Approx 6 months
            elif self.subscription_type == SubscriptionTypeChoices.MONTH_12:
                expected_duration = 365  # Approx 12 months

            # Only warn if duration doesn't match *and* it's not 'custom'
            if (
                expected_duration is not None
                and self.duration_days != expected_duration
                and self.subscription_type != SubscriptionTypeChoices.CUSTOM
            ):
                # We won't raise ValidationError here to allow flexibility, but you could.
                # A warning in the admin interface might be better.
                pass
                # Example if you wanted to enforce:
                # raise ValidationError(
                #    _("Duration in days ({days}) does not match the expected duration ({expected}) for the selected subscription type '{type}'. Use 'Custom' type or adjust days.").format(
                #       days=self.duration_days, expected=expected_duration, type=self.get_subscription_type_display()
                #    )
                # )
            if expected_duration is not None:
                self.duration_days = expected_duration

        super().clean()

    def save(self, *args, **kwargs):
        self.clean()  # Ensure clean is called even if not using ModelForm
        super().save(*args, **kwargs)

    def mark_used(self, user: User) -> bool:
        """Marks the code as used by a specific user if it's valid."""
        if self.is_active and not self.is_used:
            self.is_used = True
            self.used_by = user
            self.used_at = timezone.now()
            # Only update relevant fields for efficiency
            self.save(update_fields=["is_used", "used_by", "used_at", "updated_at"])
            return True
        return False


class UserProfile(models.Model):
    """Stores additional information specific to Qader users, extending the built-in User model."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,  # If User is deleted, Profile is also deleted
        primary_key=True,
        related_name="profile",
        verbose_name=_("User"),
    )
    # Basic Info
    full_name = models.CharField(_("Full Name"), max_length=255)
    preferred_name = models.CharField(
        _("Preferred Name"), max_length=100, blank=True, null=True
    )
    gender = models.CharField(
        _("Gender"), max_length=20, choices=GenderChoices.choices, blank=True, null=True
    )
    grade = models.CharField(_("Grade"), max_length=100, blank=True, null=True)
    has_taken_qiyas_before = models.BooleanField(
        _("Taken Qiyas Before?"),
        null=True,
        blank=True,
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
    subscription_expires_at = models.DateTimeField(
        _("Subscription Expires At"), null=True, blank=True, db_index=True
    )
    serial_code_used = models.ForeignKey(
        SerialCode,
        verbose_name=_("Serial Code Used"),
        on_delete=models.SET_NULL,  # Keep profile even if code is deleted
        null=True,
        blank=True,
        related_name="user_profiles",  # Allows SerialCode.user_profiles.all()
        help_text=_("The last serial code used to activate/extend subscription."),
    )

    # Gamification/Progress Tracking
    points = models.PositiveIntegerField(_("Points"), default=0)
    current_streak_days = models.PositiveIntegerField(
        _("Current Study Streak"), default=0
    )
    longest_streak_days = models.PositiveIntegerField(
        _("Longest Study Streak"), default=0
    )
    last_study_activity_at = models.DateTimeField(
        _("Last Study Activity At"),
        null=True,
        blank=True,
        help_text=_(
            "Timestamp of the last tracked study action (e.g., question answered)."
        ),
    )

    # Learning Level Assessment
    current_level_verbal = models.FloatField(
        _("Current Verbal Level"),
        null=True,
        blank=True,
        help_text=_(
            "Assessed proficiency level in the Verbal section (e.g., percentage)."
        ),
    )
    current_level_quantitative = models.FloatField(
        _("Current Quantitative Level"),
        null=True,
        blank=True,
        help_text=_(
            "Assessed proficiency level in the Quantitative section (e.g., percentage)."
        ),
    )

    # User Settings & Preferences
    last_visited_study_option = models.CharField(
        _("Last Visited Study Option"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_(
            "Slug or identifier of the last viewed section in the 'Study Page'."
        ),
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
        help_text=_("Preferred time of day for study reminders."),
    )

    # Referral System
    referral_code = models.CharField(
        _("Referral Code"),
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("User's unique code to share for referrals."),
    )
    referred_by = models.ForeignKey(
        User,
        verbose_name=_("Referred By"),
        on_delete=models.SET_NULL,  # Keep record even if referrer is deleted
        null=True,
        blank=True,
        related_name="referrals_made",  # Allows User.referrals_made.all()
        help_text=_("The user who referred this user."),
    )

    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"Profile for {self.user.username}"

    @property
    def is_subscribed(self) -> bool:
        """Check if the user currently has an active subscription."""
        if self.subscription_expires_at:
            return timezone.now() < self.subscription_expires_at
        return False

    @property
    def level_determined(self) -> bool:
        """Check if both verbal and quantitative levels have been assessed."""
        return (
            self.current_level_verbal is not None
            and self.current_level_quantitative is not None
        )

    def apply_subscription(self, serial_code: SerialCode):
        """Applies or extends subscription duration based on a SerialCode."""
        if not serial_code or serial_code.duration_days <= 0:
            return  # No duration to apply

        now = timezone.now()
        # Start the new duration from now, or extend from the current expiry date if it's in the future
        start_date = now
        if self.subscription_expires_at and self.subscription_expires_at > now:
            start_date = self.subscription_expires_at

        new_expiry_date = start_date + timedelta(days=serial_code.duration_days)

        self.subscription_expires_at = new_expiry_date
        self.serial_code_used = serial_code  # Track the code that granted this expiry
        self.save(
            update_fields=["subscription_expires_at", "serial_code_used", "updated_at"]
        )

    def _generate_referral_code(self):
        """Generates a unique referral code."""
        # Simple strategy: Username prefix + short UUID hex
        # Ensure it fits within max_length=20
        prefix = (
            self.user.username[:8].upper().replace("_", "")
        )  # Remove underscores, take first 8 chars
        unique_part = uuid.uuid4().hex[:6].upper()  # Use 6 hex chars for uniqueness
        code = f"{prefix}-{unique_part}"
        # Extremely unlikely collision, but check just in case
        while UserProfile.objects.filter(referral_code=code).exists():
            unique_part = uuid.uuid4().hex[:6].upper()
            code = f"{prefix}-{unique_part}"
        return code

    def save(self, *args, **kwargs):
        # Generate referral code on first save if it doesn't exist
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)
