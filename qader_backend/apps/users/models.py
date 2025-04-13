from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
import uuid


class GenderChoices(models.TextChoices):
    MALE = "male", _("Male")
    FEMALE = "female", _("Female")


class RoleChoices(models.TextChoices):
    STUDENT = "student", _("Student")
    ADMIN = "admin", _("Admin")
    SUB_ADMIN = "sub_admin", _("Sub-Admin")


class DarkModePrefChoices(models.TextChoices):
    LIGHT = "light", _("Light")
    DARK = "dark", _("Dark")
    SYSTEM = "system", _("System")


class SerialCode(models.Model):
    code = models.CharField(max_length=50, unique=True, db_index=True)
    duration_days = models.IntegerField(
        default=30, help_text="Subscription length in days granted by this code."
    )
    is_active = models.BooleanField(default=True, help_text="Can this code be used?")
    is_used = models.BooleanField(
        default=False, db_index=True, help_text="Has this code already been redeemed?"
    )
    used_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="redeemed_codes",
    )
    used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_codes",
        help_text="Admin who generated the code.",
    )
    notes = models.TextField(
        blank=True, null=True, help_text="Admin notes about the code."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def mark_used(self, user):
        """Marks the code as used by a specific user."""
        if self.is_active and not self.is_used:
            self.is_used = True
            self.used_by = user
            self.used_at = timezone.now()
            self.save(update_fields=["is_used", "used_by", "used_at", "updated_at"])
            return True
        return False


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="profile"
    )
    full_name = models.CharField(max_length=255)
    preferred_name = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(
        max_length=20, choices=GenderChoices.choices, blank=True, null=True
    )
    grade = models.CharField(max_length=100, blank=True, null=True)
    has_taken_qiyas_before = models.BooleanField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT,
        db_index=True,
    )

    # Subscription Details
    subscription_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    serial_code_used = models.ForeignKey(
        SerialCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profiles",
    )

    # Gamification/Progress
    points = models.IntegerField(default=0)
    current_streak_days = models.IntegerField(default=0)
    longest_streak_days = models.IntegerField(default=0)
    last_study_activity_at = models.DateTimeField(null=True, blank=True)

    # Learning Levels
    current_level_verbal = models.FloatField(null=True, blank=True)
    current_level_quantitative = models.FloatField(null=True, blank=True)

    # Settings/Preferences
    last_visited_study_option = models.CharField(
        max_length=100, blank=True, null=True
    )  # Store slug
    dark_mode_preference = models.CharField(
        max_length=10,
        choices=DarkModePrefChoices.choices,
        default=DarkModePrefChoices.LIGHT,
    )
    dark_mode_auto_enabled = models.BooleanField(default=False)
    dark_mode_auto_time_start = models.TimeField(null=True, blank=True)
    dark_mode_auto_time_end = models.TimeField(null=True, blank=True)
    notify_reminders_enabled = models.BooleanField(default=True)
    upcoming_test_date = models.DateField(null=True, blank=True)
    study_reminder_time = models.TimeField(null=True, blank=True)

    # Referral System
    referral_code = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True
    )
    referred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals_made",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    @property
    def is_subscribed(self):
        """Check if the user currently has an active subscription."""
        if self.subscription_expires_at:
            return timezone.now() < self.subscription_expires_at
        return False

    @property
    def level_determined(self):
        """Check if both verbal and quantitative levels have been set."""
        return (
            self.current_level_verbal is not None
            and self.current_level_quantitative is not None
        )

    def apply_subscription(self, serial_code: SerialCode):
        """Applies subscription duration from a serial code."""
        if serial_code and serial_code.duration_days > 0:
            now = timezone.now()
            # Extend from now or current expiry, whichever is later
            start_date = (
                self.subscription_expires_at
                if self.subscription_expires_at and self.subscription_expires_at > now
                else now
            )
            self.subscription_expires_at = start_date + timedelta(
                days=serial_code.duration_days
            )
            self.serial_code_used = serial_code
            self.save(
                update_fields=[
                    "subscription_expires_at",
                    "serial_code_used",
                    "updated_at",
                ]
            )

    def save(self, *args, **kwargs):
        # Generate referral code on first save if needed
        if not self.referral_code:
            # Simple unique code generation strategy
            self.referral_code = (
                f"{self.user.username[:8].upper()}-{uuid.uuid4().hex[:4].upper()}"
            )
            # Ensure uniqueness (rare collision chance, but good practice)
            while UserProfile.objects.filter(referral_code=self.referral_code).exists():
                self.referral_code = (
                    f"{self.user.username[:8].upper()}-{uuid.uuid4().hex[:4].upper()}"
                )
        super().save(*args, **kwargs)


# Signal to create/update UserProfile when User is created/saved
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    # instance.profile.save() # Removed: save is handled by the profile itself or calling code
