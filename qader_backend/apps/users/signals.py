from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, RoleChoices  # Import RoleChoices if needed later
from .utils import generate_unique_referral_code  # Import the utility

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created: bool, **kwargs):
    """
    Signal handler to create UserProfile when a User object is created.
    Profile details (except referral code) will be filled later.
    """
    if created:
        # Profile is created empty initially, full_name added by signup view
        # Referral code generated here.
        profile = UserProfile.objects.create(user=instance)
        logger.info(
            f"UserProfile created for new user {instance.username} (ID: {instance.id})"
        )
        # Ensure referral code is generated even if save isn't called immediately
        if not profile.referral_code and instance.username:
            profile.referral_code = generate_unique_referral_code(instance.username)
            profile.save(update_fields=["referral_code"])  # Save just the code
            logger.info(
                f"Generated referral code '{profile.referral_code}' via signal."
            )

    # No need to update profile here on user update unless syncing fields like email
    # else:
    #     try:
    #         # If syncing email or username changes to profile fields, do it here.
    #         # instance.profile.save() # Maybe trigger update_at? Careful.
    #         pass
    #     except UserProfile.DoesNotExist:
    #         logger.error(f"UserProfile missing for existing user {instance.username} (ID: {instance.id}). Creating profile now.")
    #         UserProfile.objects.create(user=instance)
